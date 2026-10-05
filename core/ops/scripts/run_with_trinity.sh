#!/usr/bin/env bash
# Sovereign 3-Stage Order of Protection Pipeline
# STAGE 1: Policy Engine (Intent Filter)
# STAGE 2: Gate Control (Execution Filter & Trinity Tribunal)
# STAGE 3: Native Witness (Verification Layer & Receipt-as-Node)

set -e

# Security & PATH Sanitization Invariant
unset DYLD_INSERT_LIBRARIES
unset DYLD_LIBRARY_PATH
unset LD_PRELOAD
unset LD_LIBRARY_PATH
export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"

ROOT="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain"
POLICY_ENGINE="$ROOT/ops/scripts/sovereign_policy_engine.py"
FRONT_WITNESS_GATE="$ROOT/ops/scripts/discernment_front_witness_gate.sh"
TRINITY_SCRIPT="$ROOT/ops/scripts/trinity_gate.py"

# STAGE 1: Policy Engine (Intent Filter - Sits in FRONT of everything)
if [ -f "$POLICY_ENGINE" ]; then
    python3 "$POLICY_ENGINE" "$@"
fi

# STAGE 2: Physical Structural Gate Intercept (Execution Filter)
if [ ! -f "$FRONT_WITNESS_GATE" ]; then
    echo "❌ STRUCTURAL CONTROL FAIL CLOSED: Front-gate witness script missing."
    exit 1
fi
/bin/bash "$FRONT_WITNESS_GATE"

# STAGE 2 (Cont.): Multi-Agent Trinity Tribunal Cross-Examination
if [ ! -f "$TRINITY_SCRIPT" ]; then
    echo "❌ STRUCTURAL CONTROL FAIL CLOSED: Trinity Gate script missing."
    exit 1
fi
python3 "$TRINITY_SCRIPT" "$@"
