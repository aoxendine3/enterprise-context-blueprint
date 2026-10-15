#!/bin/bash
# =============================================================================
# ops/reproducibility/ci_reproducible_build_step.sh
# =============================================================================
# XORAS FIVE-MOVE DETERMINISTIC REPRODUCIBILITY CI STEP
# -----------------------------------------------------------------------------
# Move 1: Verify pinned Zig compiler version (0.16.0)
# Move 2: Fix SOURCE_DATE_EPOCH=1700000000 and LC_ALL=C
# Move 3: Strip debug/local symbols via -fstrip -fno-incremental
# Move 4: Deterministically sort input files with LC_ALL=C sort
# Move 5: Audit bit-for-bit differential using cmp -l across dual clean sandboxes
# =============================================================================

set -eo pipefail

echo "================================================================================"
echo "          XORAS CI/CD DETERMINISTIC REPRODUCIBILITY AUDIT STEP                 "
echo "================================================================================"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOCK_FILE="$ROOT/core/ops/reproducibility/sovrac.lock"
SOURCE_FILE="$ROOT/ops/runtime/sovrac_v3_1.zig"

if [ ! -f "$LOCK_FILE" ]; then
    echo "❌ Error: Lockfile not found at $LOCK_FILE"
    exit 1
fi

EXPECTED_HASH=$(python3 -c "import json; print(json.load(open('$LOCK_FILE'))['expected_output']['sha256'])")
EXPECTED_BYTES=$(python3 -c "import json; print(json.load(open('$LOCK_FILE'))['expected_output']['bytes'])")
PINNED_ZIG=$(python3 -c "import json; print(json.load(open('$LOCK_FILE'))['toolchain']['zig_version'])")

# Move 1: Toolchain Verification
ZIG_CMD=$(which zig || echo "/opt/homebrew/bin/zig")
if [ ! -x "$ZIG_CMD" ]; then
    echo "❌ Pinned Zig binary not found in PATH or /opt/homebrew/bin/zig"
    exit 1
fi

ACTUAL_ZIG=$("$ZIG_CMD" version)
echo "[*] Move 1: Checking Pinned Compiler Toolchain..."
echo "    - Pinned: $PINNED_ZIG | Detected: $ACTUAL_ZIG"
if [ "$ACTUAL_ZIG" != "$PINNED_ZIG" ]; then
    echo "❌ Toolchain drift detected: expected $PINNED_ZIG, got $ACTUAL_ZIG"
    exit 1
fi
echo "    [PASS] Toolchain version matches exactly."

# Move 2: Timestamp and Locale Freezing
echo -e "\n[*] Move 2: Freezing Build Timestamps and Locale..."
export LC_ALL=C
export SOURCE_DATE_EPOCH=1700000000
export ZERO_AR_DATE=1
echo "    - LC_ALL=$LC_ALL"
echo "    - SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH"
echo "    [PASS] Environment frozen."

# Move 4: Sorted Input File Inspection
echo -e "\n[*] Move 4: Verifying Input Sorting..."
find "$ROOT/ops/runtime" -maxdepth 1 -name "*.sovra" | LC_ALL=C sort > /tmp/xoras_ci_sorted_inputs.txt
INPUT_COUNT=$(wc -l < /tmp/xoras_ci_sorted_inputs.txt | tr -d ' ')
echo "    - Indexed $INPUT_COUNT contract inputs deterministically."
echo "    [PASS] Inputs sorted."

# Move 3 & 5: Clean-Room Build and Differential Audit
echo -e "\n[*] Move 3 & 5: Clean-Room Compilation & Differential Audit..."
DIR_A=$(mktemp -d "/tmp/xoras_ci_build_A_XXXXXX")
DIR_B=$(mktemp -d "/tmp/xoras_ci_build_B_XXXXXX")

trap 'rm -rf "$DIR_A" "$DIR_B" /tmp/xoras_ci_sorted_inputs.txt' EXIT

# Build A
"$ZIG_CMD" build-exe \
    -O ReleaseFast \
    -fstrip \
    -fno-incremental \
    --global-cache-dir "$DIR_A/gcache" \
    --cache-dir "$DIR_A/lcache" \
    "$SOURCE_FILE" \
    "-femit-bin=$DIR_A/sovrac"

# Build B
"$ZIG_CMD" build-exe \
    -O ReleaseFast \
    -fstrip \
    -fno-incremental \
    --global-cache-dir "$DIR_B/gcache" \
    --cache-dir "$DIR_B/lcache" \
    "$SOURCE_FILE" \
    "-femit-bin=$DIR_B/sovrac"

HASH_A=$(shasum -a 256 "$DIR_A/sovrac" | awk '{print $1}')
HASH_B=$(shasum -a 256 "$DIR_B/sovrac" | awk '{print $1}')
BYTES_A=$(stat -f%z "$DIR_A/sovrac" 2>/dev/null || stat -c%s "$DIR_A/sovrac")

echo "    - Build A SHA-256: $HASH_A ($BYTES_A bytes)"
echo "    - Build B SHA-256: $HASH_B"

DIFF_BYTES=$(cmp -l "$DIR_A/sovrac" "$DIR_B/sovrac" | wc -l | tr -d ' ')
echo "    - Differential Audit (cmp -l): $DIFF_BYTES differing bytes"

if [ "$DIFF_BYTES" -ne 0 ]; then
    echo "❌ FATAL: Non-deterministic build detected! $DIFF_BYTES differing bytes between runs."
    exit 1
fi

if [ "$HASH_A" != "$EXPECTED_HASH" ]; then
    echo "❌ FATAL: Hash drift against canonical lockfile!"
    echo "    - Expected: $EXPECTED_HASH"
    echo "    - Built:    $HASH_A"
    exit 1
fi

echo -e "\n================================================================================"
echo ">>> CI REPRODUCIBILITY AUDIT PASSED: ZERO DRIFT, BIT-FOR-BIT IDENTICAL."
echo ">>> SHA-256: $HASH_A"
echo "================================================================================"
exit 0
