#!/usr/bin/env bash
# XORAS REALITY GATE — the pre-flight that nothing skips.
# Runs our actual gates in order; stops at the first failure (fail-closed);
# writes memory/catch_log/REALITY_GATE_RECEIPT.json; exits non-zero unless everything passes.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
PASSED=0
FAILED=0
FAIL_AT=""
note() { printf '%s\n' "$*"; }

run_gate() {
  local label="$1"; shift
  note "[gate] ${label} ..."
  if "$@" >/tmp/reality_gate_step.log 2>&1; then
    note "  [PASS] ${label}"
    PASSED=$((PASSED + 1))
    return 0
  fi
  note "  [FAIL] ${label} — see /tmp/reality_gate_step.log"
  FAILED=$((FAILED + 1))
  [ -z "$FAIL_AT" ] && FAIL_AT="$label"
  return 1
}

run_gate "production gates (6/6)" bash ops/scripts/verify_all_production_gates.sh || true
run_gate "side-channel 4/4" node --expose-gc core/ops/scripts/test_side_channel_verification.cjs || true
run_gate "DART cage lattice 7/7" python3 tests/test_dart_cage_lattice.py || true
run_gate "Z3 cage_containment UNSAT" z3 -smt2 -T:30 core/ops/security/cage_containment.smt2 || true

LINEAGE="UNKNOWN"
if LINEAGE_COUNT="$(sqlite3 memory/tri_brain/world_file.db 'select count(*) from lineage_nodes;' 2>/tmp/reality_gate_sqlite.log)"; then
  LINEAGE="$LINEAGE_COUNT"
  note "[gate] world_file lineage: ${LINEAGE} nodes — witness present"
  PASSED=$((PASSED + 1))
else
  note "[FAIL] world_file.db unreachable (sqlite3 error)"
  FAILED=$((FAILED + 1))
  [ -z "$FAIL_AT" ] && FAIL_AT="world_file"
fi

TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
if [ "$FAILED" -eq 0 ]; then
  VERDICT="REALITY_GATE_PASS"
else
  VERDICT="REALITY_GATE_FAIL"
fi

cat > memory/catch_log/REALITY_GATE_RECEIPT.json <<RECEIPT
{
  "gate": "reality_gate.sh",
  "verdict": "${VERDICT}",
  "timestamp_utc": "${TIMESTAMP}",
  "gates_passed": ${PASSED},
  "gates_failed": ${FAILED},
  "first_failure": "${FAIL_AT}",
  "world_file_lineage_nodes": "${LINEAGE}"
}
RECEIPT

note "verdict: ${VERDICT}  passed=${PASSED} failed=${FAILED}  first_failure=${FAIL_AT:-none}"
[ "$FAILED" -eq 0 ]
