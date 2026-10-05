#!/usr/bin/env bash
# Front-Gate Structural Control & Discernment Witness Intercept
# Enforces mandatory Stateless Airblocked Witness execution & build hash verification before any pipeline starts.

set -e

# Environment Sanitization & Security Lockdown Invariant
unset DYLD_INSERT_LIBRARIES
unset DYLD_LIBRARY_PATH
unset LD_PRELOAD
unset LD_LIBRARY_PATH
export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"

ROOT="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain"
WITNESS_BIN="$ROOT/core/ops/bin/stateless_airblocked_witness"
DB_PATH="$ROOT/.sovereign/provenance/lineage_dag.db"
MERKLE_FILE="$ROOT/memory/tri_brain/merkle_root.hash"
MANIFEST_HASH_FILE="$ROOT/core/ops/bin/witness_build.sha256"

echo "=========================================================================="
echo "  DISCERNMENT BOARD FRONT-GATE CONTROL: WITNESS PRE-FLIGHT INTERCEPT"
echo "=========================================================================="

if [ ! -f "$WITNESS_BIN" ]; then
    echo "❌ STRUCTURAL CONTROL FAIL CLOSED: Native witness binary missing at $WITNESS_BIN"
    exit 1
fi

if [ ! -x "$WITNESS_BIN" ]; then
    echo "❌ STRUCTURAL CONTROL FAIL CLOSED: Native witness binary lacks executable permissions."
    exit 1
fi

# Verify witness binary SHA-256 build hash against manifest if present
if [ -f "$MANIFEST_HASH_FILE" ]; then
    EXPECTED_HASH=$(/usr/bin/tr -d ' \n\r' < "$MANIFEST_HASH_FILE")
    ACTUAL_HASH=$(/usr/bin/shasum -a 256 "$WITNESS_BIN" | /usr/bin/awk '{print $1}')
    if [ "$EXPECTED_HASH" != "$ACTUAL_HASH" ]; then
        echo "❌ STRUCTURAL CONTROL FAIL CLOSED: Witness Binary Corrupted or Tampered!"
        echo "   Expected: $EXPECTED_HASH"
        echo "   Actual:   $ACTUAL_HASH"
        exit 1
    fi
fi

# Execute Stateless Airblocked Witness in isolated text-only output scope
"$WITNESS_BIN" "$DB_PATH" "$MERKLE_FILE"

echo "✅ DISCERNMENT FRONT-GATE AUTHORIZED: Witness verified output claims clean."
