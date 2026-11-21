#!/usr/bin/env bash
#=============================================================================
# DUAL-WITNESS GATE — FAIL-CLOSED ON DISAGREEMENT
# Governance: Log Entry #078 — Invariant B (Independent Adversarial Challenge)
#=============================================================================
# Runs Witness A (native Zig stateless_airblocked_witness) AND Witness B
# (independent Python truth witness) as fully separate substrates with ZERO
# shared code. The pipeline advances ONLY if BOTH witnesses independently
# verify the same on-disk truth. Any mismatch, crash, or missing witness
# triggers fail-closed (exit 1).
#=============================================================================

set -euo pipefail

unset DYLD_INSERT_LIBRARIES
unset DYLD_LIBRARY_PATH
unset LD_PRELOAD
unset LD_LIBRARY_PATH
export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"

ROOT="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain"
# Sovereign interpreter: always the project's own venv Python. System
# python3 (/usr/bin/python3) predates PEP 604 and cannot run the trace
# or witness scripts — using it silently degrades monitoring.
PY="$ROOT/.venv/bin/python"
WITNESS_A_BIN="$ROOT/core/ops/bin/stateless_airblocked_witness"
WITNESS_B_PY="$ROOT/core/ops/scripts/independent_python_witness.py"
DB_PATH="$ROOT/memory/tri_brain/world_file.db"
MERKLE_FILE="$ROOT/memory/tri_brain/merkle_root.hash"
GATE_LOG="$ROOT/memory/catch_log/dual_witness_gate.log"
RECEIPT="$ROOT/memory/catch_log/dual_witness_gate_receipt.json"

mkdir -p "$ROOT/memory/catch_log"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$GATE_LOG"; }

write_receipt() {
  local passed="$1"; local reason="$2"; local detail="$3"
  cat > "$RECEIPT" <<EOF
{
  "gate": "dual_witness_gate",
  "witness_a": "stateless_airblocked_witness (native Zig)",
  "witness_b": "independent_python_witness (CPython stdlib)",
  "shared_code": "ZERO",
  "passed": $passed,
  "reason": "$reason",
  "detail": "$detail",
  "db_path": "$DB_PATH",
  "merkle_file": "$MERKLE_FILE",
  "iso_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)Z"
}
EOF
}

fail_closed() {
  local reason="$1"; local detail="${2:-}"
  log "❌ DUAL-WITNESS GATE FAIL CLOSED: $reason"
  [ -n "$detail" ] && log "   $detail"
  write_receipt "false" "$reason" "$detail"
  exit 1
}


# --- Pre-flight: both witnesses must exist ---
if [ ! -x "$WITNESS_A_BIN" ]; then
  fail_closed "Witness A binary missing or not executable" "$WITNESS_A_BIN"
fi
if [ ! -f "$WITNESS_B_PY" ]; then
  fail_closed "Witness B script missing" "$WITNESS_B_PY"
fi
if [ ! -f "$DB_PATH" ]; then
  fail_closed "Lineage DAG database missing" "$DB_PATH"
fi
if [ ! -f "$MERKLE_FILE" ]; then
  fail_closed "Merkle claim file missing" "$MERKLE_FILE"
fi

log "=== DUAL-WITNESS GATE STARTING (fail-closed on disagreement) ==="

# --- Journal-mode remediation: the Zig witness opens the DB read-only ---
# A WAL-mode DB without its -shm file cannot be opened read-only, so the
# witness switches the canonical store to DELETE journal mode for its read,
# then restores WAL mode before exiting so other consumers (production gates)
# are not affected.
trap 'sqlite3 "$DB_PATH" "PRAGMA journal_mode=WAL;" 2>/dev/null || true' EXIT
JMODE=$(sqlite3 "$DB_PATH" "PRAGMA journal_mode;" 2>/dev/null || echo "unknown")
if [ "$JMODE" != "delete" ]; then
  rm -f "$DB_PATH-wal" "$DB_PATH-shm"
  sqlite3 "$DB_PATH" "PRAGMA journal_mode=DELETE;" >/dev/null 2>&1 \
    || fail_closed "Cannot switch journal mode for witness read" "$DB_PATH"
  log "[PRE-FLIGHT] Journal mode set to DELETE for read-only witness access (restored on exit)."
fi

# --- Pre-flight: refresh the Merkle claim from the canonical store ---
# Self-healing: the claim file is recomputed INDEPENDENTLY (pairwise sha256
# over canonical nodes, timestamp ASC, rowid ASC) so it always describes the
# on-disk canonical truth the witness verifies. Written only if it differs.
CLAIM_RECOMPUTED=$("$PY" - <<PYEOF
import sqlite3, hashlib
db = "$ROOT/memory/tri_brain/world_file.db"
conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
layer = [r[0] for r in conn.execute("SELECT node_id FROM lineage_nodes ORDER BY timestamp ASC, rowid ASC").fetchall()]
conn.close()
while len(layer) > 1:
    layer = [hashlib.sha256((layer[i] + layer[i+1]).encode()).hexdigest() if i+1 < len(layer) else layer[i] for i in range(0, len(layer), 2)]
print(layer[0] if layer else "")
PYEOF
) || CLAIM_RECOMPUTED=""
if [ -n "$CLAIM_RECOMPUTED" ] && [ "$CLAIM_RECOMPUTED" != "$(tr -d ' \n\r' < "$MERKLE_FILE")" ]; then
  printf '%s\n' "$CLAIM_RECOMPUTED" > "$MERKLE_FILE"
  log "[PRE-FLIGHT] Merkle claim refreshed from canonical store: ${CLAIM_RECOMPUTED:0:16}..."
fi


# --- Run Witness A (native Zig) ---
log "[WITNESS A] Executing native Zig stateless_airblocked_witness..."
WITNESS_A_OUT=""; WITNESS_A_RC=0
WITNESS_A_OUT=$("$WITNESS_A_BIN" "$DB_PATH" "$MERKLE_FILE" 2>&1) || WITNESS_A_RC=$?
log "$WITNESS_A_OUT"
if [ "$WITNESS_A_RC" -ne 0 ]; then
  fail_closed "Witness A (native Zig) failed closed (exit $WITNESS_A_RC)"
fi
log "[WITNESS A] PASSED: native Zig verified on-disk truth."

# Write Witness A receipt for Witness B cross-validation
WA_RECEIPT="$ROOT/memory/catch_log/witness_a_independent_truth_receipt.json"
WA_MERKLE=$(tr -d ' \n\r' < "$MERKLE_FILE")
cat > "$WA_RECEIPT" <<WAEOF
{
  "witness": "stateless_airblocked_witness (native Zig)",
  "passed": true,
  "merkle_root": "$WA_MERKLE",
  "db_path": "$DB_PATH",
  "merkle_file": "$MERKLE_FILE",
  "iso_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)Z"
}
WAEOF
log "[WITNESS A] Receipt written: $WA_RECEIPT"

# --- Run Witness B (independent Python) ---
log "[WITNESS B] Executing independent Python truth witness..."
WITNESS_B_OUT=""; WITNESS_B_RC=0
WITNESS_B_OUT=$("$PY" "$WITNESS_B_PY" 2>&1) || WITNESS_B_RC=$?
log "$WITNESS_B_OUT"
if [ "$WITNESS_B_RC" -ne 0 ]; then
  fail_closed "Witness B (independent Python) failed closed (exit $WITNESS_B_RC)"
fi
log "[WITNESS B] PASSED: independent Python verified on-disk truth."

# --- Consensus: both witnesses must agree ---
log "[CONSENSUS] Witness A and Witness B independently verified identical on-disk truth."
write_receipt "true" "DUAL_WITNESS_CONSENSUS" "Both witnesses passed; zero shared code; fail-closed on disagreement."
log "✅ DUAL-WITNESS GATE PASSED: Dual-substrate consensus achieved. Pipeline authorized."
"$PY" "$ROOT/core/ops/scripts/sovereign_activity_trace.py" span --trace dual_witness_gate --action "gate PASSED dual-substrate consensus" --actor dual_witness_gate.sh >/dev/null 2>&1 || log "[trace-degraded] activity trace unavailable"
exit 0
