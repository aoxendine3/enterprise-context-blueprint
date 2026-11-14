# Contributing

XORAS is evidence-first. Every contribution must preserve three invariants:

1. **No artifact advances on trust alone.** Any claim of correctness must be backed  
   by a verifiable run — a gate, a test, a signed receipt.
2. **WORM is the law.** Nothing is deleted; broken work is quarantined in place and  
   receipted. If you break something, move it to `barn/archives/` with a receipt.
3. **Production gates must stay green.** Before committing, run:

   ```bash
   bash ops/scripts/verify_all_production_gates.sh
   ```
   This runs all 6/6 production gates, then the full test suite.

## How to propose a change

1. Open an issue describing the defect or the intent — not a spec, a problem.
2. Implement the fix with a matching test (`tests/`).
3. Run the full gate suite. Capture the canonical hash if any WORM artifact changed.
4. Submit as a pull request. We rebase, squash on merge, and sign the merge with Ed25519 tag `security-audit` for any change to the security posture.

## Code style

- Python: PEP 8, type hints, `mypy --strict` where applicable.
- Markdown: one sentence per line. No fluff, no hedging, no adjectives without evidence.
- Commits: `type(scope): subject` — e.g., `fix(witness): dual-substrate root recomputed from canonical store`.

## Questions

`platform@xoras.io` — or open an issue with the `question` label.
