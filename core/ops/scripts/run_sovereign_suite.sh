#!/usr/bin/env bash
# Sovereign Verification Suite Turnkey Out-of-the-Box Entrypoint
# Executes pre-flight witness check, Red-Team gauntlet, Purple-Team PTEF loop, recovery engine, and compliance proofs.

set -e

# Security & PATH Sanitization Invariant
unset DYLD_INSERT_LIBRARIES
unset DYLD_LIBRARY_PATH
unset LD_PRELOAD
unset LD_LIBRARY_PATH
export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"

ROOT="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain"
MASTER_SUITE="$ROOT/ops/scripts/sovereign_verification_suite.py"

python3 "$MASTER_SUITE"
