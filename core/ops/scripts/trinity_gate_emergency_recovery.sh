#!/usr/bin/env bash
# Trinity Gate Emergency Recovery & Auto-Remediation Protocol
# Restores system state alignment when the front witness gate enters a fail-closed hard halt.

set -e

# Security & PATH Sanitization Invariant
unset DYLD_INSERT_LIBRARIES
unset DYLD_LIBRARY_PATH
unset LD_PRELOAD
unset LD_LIBRARY_PATH
export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"

ROOT="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain"
REMEDIATION_SCRIPT="$ROOT/ops/scripts/fail_closed_remediation.py"

echo "=========================================================================="
echo "  TRINITY GATE EMERGENCY RECOVERY PROTOCOL"
echo "=========================================================================="

if [ ! -f "$REMEDIATION_SCRIPT" ]; then
    echo "❌ CRITICAL RECOVERY FAILURE: Remediation script missing at $REMEDIATION_SCRIPT"
    exit 1
fi

python3 "$REMEDIATION_SCRIPT"

echo "✅ EMERGENCY RECOVERY PROCEDURE COMPLETED SUCCESSFULLY."
