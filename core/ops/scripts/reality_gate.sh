#!/usr/bin/env bash
# XORAS REALITY GATE — the pre-flight that nothing skips.
# Runs all nine gates in order and aggregates failures (fail-closed);
# writes memory/catch_log/REALITY_GATE_RECEIPT.json; exits non-zero unless everything passes.
# The six production gates keep their own 6/6 runner and semantics unchanged.
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

PRODUCTION_STATUS="FAIL"
if run_gate "production gates (6/6)" bash ops/scripts/verify_all_production_gates.sh; then
  PRODUCTION_STATUS="PASS"
fi
run_gate "side-channel 4/4" node --expose-gc core/ops/scripts/test_side_channel_verification.cjs || true
run_gate "DART cage lattice 7/7" python3 tests/test_dart_cage_lattice.py || true
run_gate "Z3 cage_containment UNSAT" z3 -smt2 -T:30 core/ops/security/cage_containment.smt2 || true

WRITER_STATUS="FAIL"
if run_gate "sovereign writer verification" bash ops/scripts/verify_sovereign_file_writer.sh; then
  WRITER_STATUS="PASS"
fi

COCKPIT_STATUS="FAIL"
if run_gate "cockpit structural + asset lock + coverage" bash ops/scripts/verify_cockpit.sh; then
  COCKPIT_STATUS="PASS"
fi

CI_SURFACE_STATUS="FAIL"
if run_gate "CI surface (WASM + doc-sync gates)" bash ops/scripts/verify_ci_surface.sh; then
  CI_SURFACE_STATUS="PASS"
fi

GOLDEN_STATUS="FAIL"
if run_gate "golden groundedness (floor metric)" python3 core/ops/scripts/verify_golden_groundedness.py; then
  GOLDEN_STATUS="PASS"
fi

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

cat > memory/catch_log/REALITY_GATE_RECEIPT.json <<RECEIPT || { note "[FAIL] receipt write failed"; exit 1; }
{
  "gate": "reality_gate.sh",
  "verdict": "${VERDICT}",
  "timestamp_utc": "${TIMESTAMP}",
  "gates_passed": ${PASSED},
  "gates_failed": ${FAILED},
  "gates_total": 9,
  "first_failure": "${FAIL_AT}",
  "production_gates": "$( [ "$PRODUCTION_STATUS" = "PASS" ] && echo '6/6' || echo 'FAILED' )",
  "sovereign_writer_verification": "${WRITER_STATUS}",
  "cockpit_verification": "${COCKPIT_STATUS}",
  "ci_surface_verification": "${CI_SURFACE_STATUS}",
  "golden_groundedness": "${GOLDEN_STATUS}",
  "world_file_lineage_nodes": "${LINEAGE}"
}
RECEIPT

note "verdict: ${VERDICT}  passed=${PASSED} failed=${FAILED}  first_failure=${FAIL_AT:-none}"
[ "$FAILED" -eq 0 ]
