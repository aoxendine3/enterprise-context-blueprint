# Enterprise Context Blueprint

**A blueprint and engineering workspace for governing context, coordination, containment, and evidence in autonomous AI systems.**

This repository brings together architecture documents, prototype components, experiments, and verification artifacts. Its unifying idea is that an agent's intent and context should be traceable, concurrent work should be coordinated, execution should be bounded, and claims about results should be backed by reproducible evidence.

> **Scope note:** The components in this repository are not necessarily one integrated, production-ready product. Read each component's documentation and current verification receipts before relying on a capability. “Risk-free” is an aspiration, not a guarantee.

## The architecture at a glance

| Concern | Component | Role in the overall model |
| --- | --- | --- |
| Intent and lineage | [REASONS](reasons/README.md) | Represents requirements, decisions, and context relationships as traceable graph data. |
| Concurrent work | [MTPO](mtpo/README.md) | Explores ordering and coordination rules for concurrent agent work. |
| Execution boundaries | [UPGP](core/products/upgp/) | Contains the sandbox and proving-ground work. See its local documentation and tests for scope. |
| Assurance and evidence | [Verification scripts and tests](ops/scripts/) · [test suite](tests/) · [falsification artifacts](dist/sovereign_falsification_suite/) | Provides checks and artifacts intended to make selected claims inspectable and repeatable. |

These are related concerns, not a promise that every component is wired together in every build. The broader product framing, **Agent Notary**, describes the goal of producing independently checkable evidence for agent actions; implementation status must be established from the relevant code and receipts, not from the name or a badge.

## How to navigate

- [`docs/`](docs/) — architecture, research, and paper drafts.
- [`mtpo/`](mtpo/) and [`reasons/`](reasons/) — component-specific descriptions and materials.
- [`core/products/upgp/`](core/products/upgp/) — UPGP product implementation.
- [`ops/scripts/`](ops/scripts/) and [`tests/`](tests/) — operational checks and tests.
- [`dist/sovereign_falsification_suite/`](dist/sovereign_falsification_suite/) — formal and reproducibility artifacts.
- [`memory/catch_log/`](memory/catch_log/) — recorded verification receipts, when present.

Start with the component README before running its tests. For repository-specific rules, see [`AGENTS.md`](AGENTS.md), and for contribution and security processes see [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`SECURITY.md`](SECURITY.md).

## Verification

The repository documents a consolidated gate:

```bash
bash ops/scripts/reality_gate.sh
```

You can also run the production-gate script directly:

```bash
bash ops/scripts/verify_all_production_gates.sh
```

Results depend on the current checkout and host prerequisites. Treat the command output and its generated receipt as the evidence for that run; do not infer current status from historical CI links, badges, or prose. Check the script's prerequisites and component documentation before interpreting a pass.

## Evidence and claims

When reporting a capability or benchmark, identify the implementation, the exact test or experiment, and the corresponding receipt (including date and environment where available). Clearly distinguish **design intent**, **implemented behavior**, and **independently verified results**. A passing test supports only the behavior it actually exercises; it is not proof of system-wide safety or correctness.

## License

See [`LICENSE`](LICENSE) and [`LICENSE_COMMERCIAL.md`](LICENSE_COMMERCIAL.md) for the applicable terms.
