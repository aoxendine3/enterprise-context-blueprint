# Standard Template: Polyglot Research Paper & Evidence Package

Use this template when publishing academic whitepapers backed by empirical benchmark evidence.

## Directory Structure
```text
<research_paper_package>/
├── README.md                        # Technical overview & abstract
├── paper/
│   ├── paper.tex                    # Two-column IEEE/ACM/Kaggle LaTeX source
│   ├── references.bib               # Bibliography file
│   └── figures/                     # Vector graphics & rendered plots
├── scripts/
│   ├── generate_plots.py            # Matplotlib / Seaborn benchmark plot generator
│   └── run_experiments.py          # Empirical benchmark data collector
└── data/
    ├── raw_telemetry.csv            # Raw experimental measurements
    └── GAUNTLET_RECEIPT.json        # Immutable verification receipt
```
