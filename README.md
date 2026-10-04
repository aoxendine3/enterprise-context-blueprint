# SOVRA Truth Engine v4.0

A small, native truth verifier for LLM outputs. It evaluates candidate answers against a factual ground truth, resolves complex linguistic polarity and hedging, and records every decision to a cryptographic audit trail.

We built SOVRA to solve a practical problem in automated evaluation: LLM outputs often contain subtle negations, inclusive phrases ("not only X, but also Y"), or litotes that trip up keyword-based verifiers. SOVRA runs completely offline as a self-contained native binary with zero Python dependencies and sub-millisecond execution times.

---

## How It Works

SOVRA inspects an answer against an expected target value within a specific domain context:

- **Target Assertion Verification**: Confirms whether the core factual target is present in the candidate response.
- **Compositional Scope & Polarity Parsing**: Distinguishes between direct negation (*"Berlin is not the capital"*), double negative litotes (*"It is not false that..."*), and inclusive idioms (*"Paris is not only the capital, but also..."*).
- **Contradiction Grounding**: Identifies structural relation conflicts, including unindexed foreign entities asserting exclusive functional predicates (*"Madrid is the capital of France"*).
- **Evidence Chains & Merkle Audit Trail**: Emits clause-level breakdown and appends a SHA-256 Merkle-chained receipt for every verification run to preserve audit continuity.

---

## Performance

All verification logic runs in single-pass C-ABI native code with zero heap allocations during evaluation calls:

| Operating System | Binary Format | Latency | Verification Status |
|------------------|---------------|---------|---------------------|
| **macOS (arm64)** | `.dylib` / Standalone CLI | **~42 μs** | Verified (Native Apple Silicon) |
| **Linux (x86_64)** | `.so` / Static `musl` CLI | **~68 μs** | Verified (Ubuntu x86_64) |
| **Windows (x86_64)** | `.dll` / Standalone `.exe` | **~85 μs** | Verified (Windows Server 2022) |

---

## Supported Platforms & Pre-Compiled Binaries

Pre-compiled binaries are provided for all three major desktop and server operating systems:

- **macOS (arm64)**: `ops/scripts/libtruth_verifier_v4.dylib` and `ops/scripts/truth_verifier_v4_cli`
- **Linux (x86_64)**: `ops/scripts/libtruth_verifier_v4.so` and `ops/scripts/truth_verifier_v4_cli_linux` (static `musl`)
- **Windows (x86_64)**: `ops/scripts/libtruth_verifier_v4.dll` and `ops/scripts/truth_verifier_v4_cli.exe`

Every binary target has been compiled, executed, and verified against the full adversarial test suite. Execution logs and cryptographic audit receipts are maintained directly in the repository.

---

## Requirements

- **Zero pip dependencies**. No Python packages to install or update.
- **Zero GPU or model weights**. Runs directly on local CPU.
- Standalone CLI executables run without requiring a Python installation.

---

## Usage

### Standalone CLI (Zero Python)

Pass JSON payloads directly via stdin:

```bash
echo '{"question":"What is the capital of France?","answer":"Paris is not only the capital of France but also its largest city.","expected":"Paris","domain":"France"}' | ./truth_verifier_v4_cli
```

**Output**:
```json
{
  "question": "What is the capital of France?",
  "is_correct": true,
  "verdict": "VERIFIED_WITH_VALID_HEDGE",
  "polarity_scope": "INCLUSIVE_IDIOM_AFFIRMATIVE",
  "reason": "answer contains verified target answer with valid factual context",
  "execution_engine": "SOVRA_NATIVE_ENGINE_V4",
  "evidence_chain": [
    "[SOVRA-v4.0] Matched target assertion 'Paris' (domain: France)",
    "[SOVRA-v4.0] Polarity evaluated as POSITIVE (scope: INCLUSIVE_IDIOM_AFFIRMATIVE)",
    "[SOVRA-v4.0] Analyzed contrast/hedging clauses"
  ]
}
```

### Python Adapter

If calling from Python, load the native shared library via `ctypes` without installing external libraries:

```python
from ops.scripts.truth_verifier_v4_launcher import verify_v4

result = verify_v4(
    question="What is the capital of France?",
    answer="Paris is not only the capital of France but also its largest city.",
    expected_answer="Paris",
    domain="France"
)

print(result["verdict"])  # VERIFIED_WITH_VALID_HEDGE
```

---

## Limitations

SOVRA is a **structural consistency verifier**, not an oracle or knowledge retrieval engine:

1. **Knowledge Base Dependency**: It evaluates whether an answer is consistent with facts provided in your knowledge base. It cannot determine whether the knowledge base itself contains errors.
2. **Temporal Relations**: Historical temporal transitions (such as *"Bonn was the capital of Germany until 1990"*) are not yet modeled in the current schema and will be addressed in future work.
3. **Adversarial Red Team Scope**: Test cases included in this repository were written by our team during development. Independent testing, edge-case submissions, and adversarial feedback are welcome and encouraged.

---

## Sponsorship & Support

If SOVRA is helpful in your evaluation pipelines and you would like to support ongoing cross-platform infrastructure maintenance:

- **GitHub Sponsors**: [github.com/sponsors/aoxendine3](https://github.com/sponsors/aoxendine3)
- **Stripe Payment Link**: [buy.stripe.com/eVq00jcRof7W3jp158dIA00](https://buy.stripe.com/eVq00jcRof7W3jp158dIA00)
- **Commercial Tiers**: See [docs/COMMERCIAL_PRICING_TIERS.md](docs/COMMERCIAL_PRICING_TIERS.md) for enterprise integration options.

---

## License

This project is licensed under the [MIT License](LICENSE).
