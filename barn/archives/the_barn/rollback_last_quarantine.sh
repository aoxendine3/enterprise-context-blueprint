#!/usr/bin/env bash
# =============================================================================
# XORAS SYSTEM: AUTOMATED ROLLBACK FOR BARN QUARANTINE
# =============================================================================
set -euo pipefail

ROOT="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain"

echo "Rolling back last quarantine from the Barn..."

# Restore ELITE_BOW
if [ -d "$ROOT/archives/the_barn/ELITE_BOW_Legacy" ] && [ "$(ls -A "$ROOT/archives/the_barn/ELITE_BOW_Legacy" 2>/dev/null)" ]; then
    mkdir -p "$ROOT/ELITE_BOW"
    mv "$ROOT/archives/the_barn/ELITE_BOW_Legacy"/* "$ROOT/ELITE_BOW/" 2>/dev/null || true
    echo "[✓] ELITE_BOW restored."
fi

# Restore scratch files
if [ -d "$ROOT/archives/the_barn/scratch_legacy" ] && [ "$(ls -A "$ROOT/archives/the_barn/scratch_legacy" 2>/dev/null)" ]; then
    mkdir -p "$ROOT/scratch"
    mv "$ROOT/archives/the_barn/scratch_legacy"/* "$ROOT/scratch/" 2>/dev/null || true
    echo "[✓] Scratch files restored."
fi

# Restore ops scripts
if [ -d "$ROOT/archives/the_barn/ops_legacy" ] && [ "$(ls -A "$ROOT/archives/the_barn/ops_legacy" 2>/dev/null)" ]; then
    mkdir -p "$ROOT/ops/scripts"
    mv "$ROOT/archives/the_barn/ops_legacy"/* "$ROOT/ops/scripts/" 2>/dev/null || true
    echo "[✓] Ops scripts restored."
fi

echo "Rollback complete."
