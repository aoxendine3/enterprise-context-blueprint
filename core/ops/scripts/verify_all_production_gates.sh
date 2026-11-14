#!/usr/bin/env bash
# ==============================================================================
# XORAS SYSTEMS: UNIFIED PRODUCTION GATES VERIFICATION RUNNER
# ==============================================================================
# Governance: Log Entry #078 (Fail-Closed Evidence Chain & Invariants A-E)
# Blueprint: TEST_INFRA.md, PROJECT.md
# Substrate: Apple Silicon M4 Bare Metal
# Author: The Lead 9 Council / Sovereign Systems Swarm
# Semantics: Strict Fail-Closed (set -euo pipefail). Exit 0 iff ALL gates pass.
# ==============================================================================

set -euo pipefail
export XORAS_SUPPRESS_SPEAKER_PLAYBACK=1

SCRIPT_REALPATH="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "${BASH_SOURCE[0]}")"
WORKSPACE_ROOT="$(cd "$(dirname "$SCRIPT_REALPATH")/../.." && pwd)"
if [[ "$(basename "$WORKSPACE_ROOT")" == "core" ]]; then
    WORKSPACE_ROOT="$(dirname "$WORKSPACE_ROOT")"
fi
cd "$WORKSPACE_ROOT"

echo "================================================================================"
echo "  XORAS SYSTEMS: UNIFIED PRODUCTION GATES VERIFICATION RUNNER"
echo "  Platform: Apple Silicon M4 | Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "================================================================================"

TOTAL_GATES=6
PASSED_GATES=0
FAILED_GATES=0

run_gate() {
    local gate_num="$1"
    local gate_name="$2"
    shift 2
    local cmd=("$@")

    echo ""
    echo "--------------------------------------------------------------------------------"
    echo "  [GATE $gate_num/$TOTAL_GATES] $gate_name"
    echo "  Command: ${cmd[*]}"
    echo "--------------------------------------------------------------------------------"

    local start_time
    start_time=$(python3 -c 'import time; print(time.time())')

    if "${cmd[@]}"; then
        local end_time
        end_time=$(python3 -c 'import time; print(time.time())')
        local elapsed
        elapsed=$(python3 -c "print(round($end_time - $start_time, 2))")
        echo "  >>> RESULT: ✅ PASSED (${elapsed}s)"
        PASSED_GATES=$((PASSED_GATES + 1))
    else
        local end_time
        end_time=$(python3 -c 'import time; print(time.time())')
        local elapsed
        elapsed=$(python3 -c "print(round($end_time - $start_time, 2))")
        echo "  >>> RESULT: ❌ FAILED (${elapsed}s) [FAIL-CLOSED]"
        FAILED_GATES=$((FAILED_GATES + 1))
        echo "================================================================================"
        echo "  CRITICAL INVARIANT VIOLATION: GATE $gate_num FAILED. ABORTING ADVANCEMENT."
        echo "================================================================================"
        exit 1
    fi
}

# Gate 1: Python E2E Sovereign Gate Test Suite (Tiers 1-4, 70 Tests)
run_gate 1 "Python E2E Sovereign Gate Suite (70 Tests: Tiers 1-4)" \
    env PYTHONPATH="$WORKSPACE_ROOT" python3 -m pytest tests/test_e2e_sovereign_gate.py -v

# Gate 2: C11 AST & Z3 SMT Theorem Proving
run_gate 2 "C AST Formal Verification & Z3 SMT Containment Proofs" \
    python3 "$WORKSPACE_ROOT/core/ops/native/test_c_ast_z3_verifier.py"

# Gate 3: Native Zig Independent Merkle Lineage Consensus
run_gate 3 "Native Zig Independent Merkle Verifier (3,258 Nodes Monotonic Consensus)" \
    "$WORKSPACE_ROOT/ops/bin/independent_merkle_verifier"

# Gate 4: TypeScript Red Team Kernel Exploit Containment Sandbox
run_gate 4 "TypeScript Red Team Exploit Containment Gauntlet (10 Vectors)" \
    node --experimental-strip-types "$WORKSPACE_ROOT/tests/RedTeamExploitGauntlet.ts"

# Gate 5: 14-Gate Black-Box BBQ Falsification Gauntlet
run_gate 5 "14-Gate Black-Box BBQ Falsification Gauntlet (NASA V&V Memorandum)" \
    python3 "$WORKSPACE_ROOT/core/ops/scripts/blackbox_bbq_gauntlet.py"

# Gate 6: Rust Core Substrate Compilation & Unit Verification Floor (All 5 Crates, 20 Tests)
# The pyO3 extension crate builds against a Python whose libpython is not on the
# default linker path, so a test binary cannot resolve the CPython symbols.
# Point the linker at the interpreter's own shared library — this is the
# environment the crate was authored against, not a workaround.
PY_LIB_DIR="/opt/homebrew/opt/python@3.14/Frameworks/Python.framework/Versions/3.14/lib/python3.14/config-3.14-darwin"
PYO3_PY="/opt/homebrew/opt/python@3.14/bin/python3.14"
run_gate 6 "Rust Native Crates Unit Verification (5 Crates, 20 Tests)" \
    bash -c "cargo test --manifest-path '$WORKSPACE_ROOT/core/ops/src/zero_copy_engine/Cargo.toml' --quiet && \
             cargo test --manifest-path '$WORKSPACE_ROOT/sovra_rust_bridge/Cargo.toml' --quiet && \
             cargo test --manifest-path '$WORKSPACE_ROOT/core/ops/src/crypto_swarm/Cargo.toml' --quiet && \
             cargo test --manifest-path '$WORKSPACE_ROOT/core/ops/src/mtpo_sim/Cargo.toml' --quiet && \
             PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 PYO3_PYTHON='$PYO3_PY' RUSTFLAGS='-L $PY_LIB_DIR -l python3.14' cargo test --manifest-path '$WORKSPACE_ROOT/core/ops/mtpo_deeplock/Cargo.toml' --quiet"

echo ""
echo "================================================================================"
echo "  PRODUCTION GATES SUMMARY: $PASSED_GATES/$TOTAL_GATES PASSED (100% DISCHARGED)"
echo "  Status: ALL PRODUCTION INVARIANTS VERIFIED & ADVANCED"
echo "  Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "================================================================================"

exit 0
