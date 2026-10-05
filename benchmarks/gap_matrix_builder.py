#!/usr/bin/env python3
"""gap_matrix_builder.py – Generate a FINER/PICOT matrix for a chosen research‑gap type.

Usage:
    python3 benchmarks/gap_matrix_builder.py --gap "Population Gap" > output.md

The script reads the taxonomy markdown file, validates the requested gap name,
and emits a markdown matrix that can be pasted directly into a proposal.
"""

import argparse
import pathlib
import sys
import textwrap

# Absolute path to the taxonomy markdown – keep in sync with saga.
TAXONOMY_PATH = pathlib.Path(
    "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/docs/plans/research_gap_taxonomy.md"
)

def load_taxonomy():
    """Parse the markdown table and return a dict mapping gap names to rank strings."""
    gaps = {}
    for line in TAXONOMY_PATH.read_text().splitlines():
        if line.startswith("|") and "Gap Type" not in line:
            parts = [p.strip() for p in line.strip("|").split("|")]
            if len(parts) >= 3:
                # parts[1] contains the **Gap Name** with markdown bold
                name = parts[1].replace("**", "")
                gaps[name.lower()] = parts[0]  # rank cell
    return gaps

def generate_matrix(gap_name: str) -> str:
    finers = textwrap.dedent("""
        | Criterion | Assessment (Yes/No) | Rationale |
        |-----------|--------------------|-----------|
        | **Feasibility** | | |
        | **Interest**    | | |
        | **Novelty**     | | |
        | **Ethics**      | | |
        | **Relevance**   | | |
    """)
    picot = textwrap.dedent("""
        | Element | Definition |
        |---------|------------|
        | **Population** | |
        | **Intervention** | |
        | **Comparison**   | |
        | **Outcome**      | |
        | **Timing**       | |
    """)
    return f"# FINER & PICOT Matrix – {gap_name}\n\n## FINER Criteria\n{finers}\n## PICOT Elements\n{picot}\n"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gap", required=True, help="Exact gap name as appears in the taxonomy (e.g., 'Population Gap')")
    args = parser.parse_args()

    taxonomy = load_taxonomy()
    key = args.gap.lower()
    if key not in taxonomy:
        sys.stderr.write(f"Error: Gap '{args.gap}' not found in taxonomy.\n")
        sys.exit(1)

    sys.stdout.write(generate_matrix(args.gap))

if __name__ == "__main__":
    main()
