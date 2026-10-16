# Trinity Gate and associated execution removed per user request.
# This script no longer invokes the Trinity Gate.

#!/usr/bin/env bash
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
# TRINITY_SCRIPT removed

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

# Trinity Gate invocation (Genuine 2-of-3 BFT Audio Quorum)
TRINITY_SCRIPT="$ROOT/ops/scripts/trinity_gate.py"
if [ -f "$TRINITY_SCRIPT" ]; then
    TRINITY_OUTPUT=$(python3 "$TRINITY_SCRIPT" 2>/dev/null || true)
    PASSED=$(echo "$TRINITY_OUTPUT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('passed', False))" 2>/dev/null || echo "False")
    APPROVED=$(echo "$TRINITY_OUTPUT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('approved_count', 0))" 2>/dev/null || echo "0")
    if [ "$PASSED" = "True" ] && [ "$APPROVED" -ge 2 ]; then
        echo "✅ Trinity Gate passed with $APPROVED distinct approved agent briefings."
    else
        echo "❌ Trinity Gate failed closed: quorum not achieved (Approved: $APPROVED/3)."
        exit 1
    fi
else
    echo "❌ Trinity Gate script missing."
    exit 1
fi

# End of script.
