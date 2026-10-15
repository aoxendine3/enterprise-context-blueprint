#!/bin/bash
set -euo pipefail

echo "=========================================================="
echo "  REASONS: CONTEXT LINEAGE MERKLE DAG & POLICY AUDIT      "
echo "=========================================================="

echo "[1/2] Running Python Merkle DAG & Invariant Unit Tests..."
python3 -m unittest discover -s tests -v

echo "[2/2] Checking Standalone HTML Application & SVG Assets..."
test -f index.html
test -f assets/merkle_dag_lineage.svg
test -f assets/evidence_chain_architecture.svg
echo "  [PASS] Standalone interactive dashboard and diagrams verified."

echo "=========================================================="
echo "  REASONS AUDIT VERIFIED: ALL CHECKS PASSED               "
echo "=========================================================="
