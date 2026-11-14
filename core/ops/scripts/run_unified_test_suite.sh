#!/usr/bin/env bash
# ==============================================================================
# XORAS CITADEL: MASTER UNIFIED TEST & GATE RUNNER
# ==============================================================================
set -euo pipefail

SCRIPT_REALPATH="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "${BASH_SOURCE[0]}")"
WORKSPACE_ROOT="$(cd "$(dirname "$SCRIPT_REALPATH")/../.." && pwd)"
if [[ "$(basename "$WORKSPACE_ROOT")" == "core" ]]; then
    WORKSPACE_ROOT="$(dirname "$WORKSPACE_ROOT")"
fi
cd "$WORKSPACE_ROOT"

# Enforce speaker suppression during automated test execution per Anthony's Audio Hygiene Directive
export XORAS_SUPPRESS_SPEAKER_PLAYBACK=1

echo "================================================================================"
echo "  XORAS SYSTEMS: UNIFIED TEST & VERIFICATION SUITE"
echo "  Platform: Apple Silicon M4 | Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "================================================================================"

# 1. Run all Pytest Suites
echo "[STEP 1/3] Running Pytest Suites (Unit, Gate & Cross-Language Tests)..."
env PYTHONPATH="$WORKSPACE_ROOT" python3 -m pytest \
    tests/test_e2e_sovereign_gate.py \
    tests/test_m1_adversarial_stress_gauntlet.py \
    tests/test_m1_challenger1_audio_falsification.py \
    tests/test_m1_it2_challenger2_orion_lock_falsification.py \
    tests/test_sovra_deep_lock_cross_lang.py \
    tests/test_tier5_adversarial_hardening.py \
    tests/test_mtpo_scale_confluence.py \
    tests/test_empirical_language_compliance.py \
    tests/test_collective_voice_guard.py \
    -v --tb=short

# 2. Verify Telemetry Stream Monotonicity
echo ""
echo "[STEP 2/3] Verifying Telemetry Stream Integrity..."
python3 "$WORKSPACE_ROOT/core/ops/telemetry/daxx_telemetry_stream.py" --verify

# 3. Run all 6 Unified Production Gates
echo ""
echo "[STEP 3/3] Running Production Verification Gates (6 Gates)..."
bash "$WORKSPACE_ROOT/ops/scripts/verify_all_production_gates.sh"

echo ""
echo "================================================================================"
echo "  STATUS: ALL 164 PYTEST TESTS AND 6 PRODUCTION GATES PASSED"
echo "================================================================================"
exit 0
