#!/usr/bin/env bash
# ops/scripts/daxx_saga.sh
# Continuous DAXX saga – generates gap matrices, assembles proposal, runs gauntlet, and includes full rollback.
# The script aborts on any failure, restores previous state from backups, and logs all actions.

set -euo pipefail

ROOT="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain"
TAXONOMY_MD="$ROOT/docs/plans/research_gap_taxonomy.md"
TEMPLATE_MD="$ROOT/docs/plans/research_proposal_template.md"
MATRIX_BUILDER="$ROOT/benchmarks/gap_matrix_builder.py"
PROPOSALS_DIR="$ROOT/docs/plans/generated_proposals"
MASTER_PROP="$PROPOSALS_DIR/master_research_proposal.md"
GAUNTLET_PY="$ROOT/core/ops/discernment/fourteen_gate_blackbox_gauntlet.py"
RECEIPT_JSON="$ROOT/docs/audits/HALLUCINATION_GAUNTLET_RECEIPT.json"
LOG="$ROOT/memory/catch_log/daxx_saga.log"
BACKUP_DIR="$ROOT/.backup/daxx_saga_$(date +%Y%m%d%H%M%S)"

mkdir -p "${PROPOSALS_DIR}" "${BACKUP_DIR}" "${LOG%/*}"

log() {
  echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] $*" | tee -a "$LOG"
}

rollback() {
  log "*** Rolling back to previous state ***"
  # Restore backups if they exist
  if [[ -d "$BACKUP_DIR/proposals" ]]; then
    rm -rf "$PROPOSALS_DIR"
    cp -r "$BACKUP_DIR/proposals" "$PROPOSALS_DIR"
    log "Restored proposal directory from backup."
  fi
  if [[ -f "$BACKUP_DIR/receipt.json" ]]; then
    cp "$BACKUP_DIR/receipt.json" "$RECEIPT_JSON"
    log "Restored gauntlet receipt from backup."
  fi
  log "Rollback completed."
}

# Ensure we always clean up on error
trap 'log "ERROR encountered. Initiating rollback..."; rollback; exit 1' ERR

log "=== DAXX Saga start ==="

# 1. Verify prerequisite files
if [[ ! -f "$TAXONOMY_MD" ]]; then log "ERROR: Taxonomy missing"; exit 1; fi
if [[ ! -f "$TEMPLATE_MD" ]]; then log "ERROR: Proposal template missing"; exit 1; fi
if [[ ! -f "$MATRIX_BUILDER" ]]; then log "ERROR: Matrix builder missing"; exit 1; fi
log "Prerequisites verified."

# 2. Backup current state before making changes
log "Creating backup of current proposals and receipt (if present)."
if [[ -d "$PROPOSALS_DIR" ]]; then cp -r "$PROPOSALS_DIR" "$BACKUP_DIR/proposals"; fi
if [[ -f "$RECEIPT_JSON" ]]; then cp "$RECEIPT_JSON" "$BACKUP_DIR/receipt.json"; fi

# 3. Generate FINER/PICOT matrices for each gap
log "Generating FINER/PICOT matrices..."
while IFS= read -r line; do
  if [[ "$line" =~ ^\|[[:space:]]*([0-9]+)\️⃣[[:space:]]*\|[[:space:]]*\*\*([^*]+)\*\* ]]; then
    GAP_NAME="${BASH_REMATCH[2]}"
    CLEAN_NAME=$(echo "$GAP_NAME" | xargs | tr ' ' '_')
    OUTFILE="$PROPOSALS_DIR/${CLEAN_NAME}_matrix.md"
    log "Generating matrix for gap: $GAP_NAME -> $OUTFILE"
    python3 "$MATRIX_BUILDER" --gap "$GAP_NAME" > "$OUTFILE"
  fi
done < "$TAXONOMY_MD"
log "All matrices generated."

# 4. Assemble master proposal
log "Assembling master proposal at $MASTER_PROP"
cat "$TEMPLATE_MD" > "$MASTER_PROP"
for matrix in "$PROPOSALS_DIR"/*_matrix.md; do
  echo -e "\n---\n" >> "$MASTER_PROP"
  cat "$matrix" >> "$MASTER_PROP"
done
log "Master proposal assembled."

# 5. Run the 14‑gate gauntlet
log "Running the 14‑gate gauntlet..."
python3 "$GAUNTLET_PY" > "$ROOT/memory/catch_log/gauntlet_run.log" 2>&1
log "Gauntlet execution finished."

# 6. Validate receipt
if [[ ! -f "$RECEIPT_JSON" ]]; then
  log "ERROR: Gauntlet receipt missing."
  exit 1
fi
PASS=$(jq '.gauntlet_pass' "$RECEIPT_JSON")
if [[ "$PASS" != "true" ]]; then
  log "Gauntlet reported FAILURE. Reasons: $(jq -r '.failure_reasons[]' "$RECEIPT_JSON")"
  exit 1
fi
log "Gauntlet PASS – all thresholds met."

log "=== DAXX Saga completed successfully ==="
exit 0
