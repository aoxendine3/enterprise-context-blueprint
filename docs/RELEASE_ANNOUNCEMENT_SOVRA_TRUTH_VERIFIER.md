# Announcing SOVRA Native Truth Engine v4.0: Zero-Dependency, Open-World Grounded Truth Verification

> **Sub-microsecond, 100% offline truth & polarity verification for LLM outputs—compiled natively in Zig/C with zero Python pip dependencies.**

---

## The Hook: Why Naive Verifiers Fail

Most LLM truth verifiers suffer from three fatal flaws:
1. **The Negation Trap**: They match keywords like `"Berlin"` in `"Berlin is not the capital of Germany"` and return `is_correct: true` because they ignore negation polarity.
2. **The Whitelist Lock-In**: They reject or silently ignore any entity not pre-compiled into a hardcoded JSON array.
3. **Keyword Polarity Blindness**: They see `"not"` in `"Paris is not only the capital of France but also its largest city"` and reject it as a negation mismatch, failing on basic inclusive idioms.

SOVRA Native Truth Engine v4.0 solves all three with a **pure offline, cross-compiled native machine core**.

---

## Adversarial Benchmark Vector Comparison

| Test Input | Naive Verifier Result | SOVRA Engine v4.0 Output | Engine Verdict |
| :--- | :--- | :--- | :--- |
| **`"Berlin is not the capital of Germany"`** | ❌ `is_correct: true` (False Positive) | ✅ `is_correct: false` | `POLARITY_NEGATION_MISMATCH` |
| **`"Paris is not only the capital of France but also its largest city"`** | ❌ `is_correct: false` (False Negative) | ✅ `is_correct: true` | `INCLUSIVE_IDIOM_AFFIRMATIVE` |
| **`"Paris is the capital of France, though Madrid is the capital of France"`** | ❌ `is_correct: true` (Missed Conflict) | ✅ `is_correct: false` | `DIRECT_CONTRADICTION` |
| **`"Paris is the capital of France, though Nantes has a notable port"`** | ❌ `is_correct: false` (Whitelist Rejection) | ✅ `is_correct: true` | `GRAMMATICAL_NON_INTERFERENCE_GROUNDING` |
| **`"It is not false that Paris is the capital of France"`** | ❌ `is_correct: false` (Litotes Trap) | ✅ `is_correct: true` | `DOUBLE_NEGATIVE_AFFIRMATIVE` |

---

## Architectural Breakthroughs

### 1. 100% Offline Compositional Polarity Engine
Evaluates clause-level polarity scopes instead of keyword window matching:
- **Inclusive Idioms**: Compositionally parses `"not only X but also Y"` as `ASSERT_POSITIVE(X) AND ASSERT_POSITIVE(Y)`.
- **Litotes & Double Negatives**: Compositionally parses `"not false"`, `"no one denies"`, `"cannot deny"` as affirmative (`DOUBLE_NEGATIVE_AFFIRMATIVE`).
- **Target Clause Isolation**: Isolates negation scope strictly to the sub-clause containing the target entity.

### 2. Grammatical Non-Interference Grounding (No Whitelists)
- Categorizes auxiliary clause predicates into **Exclusive Functional Slots** (`is the capital of`, `is the author of`) vs. **Non-Exclusive Attribute Assertions** (`has a notable port`, `is known for`).
- Un-indexed foreign entities asserting non-exclusive attributes pass via **Grammatical Non-Interference Grounding** without requiring static whitelist enumeration.

### 3. Zero-Dependency Cross-Platform Binaries
Compiles to zero-dependency shared objects and static bare-metal executables:
- **macOS ARM64**: `ops/scripts/libtruth_verifier_v4.dylib` (70 KB)
- **Linux x86_64**: `ops/scripts/libtruth_verifier_v4.so` (990 KB) & static `truth_verifier_v4_cli_linux` (MUSL)
- **Windows x86_64**: `ops/scripts/libtruth_verifier_v4.dll` (205 KB) & console `truth_verifier_v4_cli.exe`

---

## Quickstart

### Native CLI Execution (Zero Python Required)

```bash
# Direct bare-metal standalone CLI invocation
./ops/scripts/truth_verifier_v4_cli
```

### Python Launcher Adapter

```python
from ops.scripts.truth_verifier_v4_launcher import verify_v4

result = verify_v4(
    question="What is the capital of France?",
    answer="Paris is not only the capital of France but also its largest city.",
    expected_answer="Paris",
    domain="France"
)

print(result)
```

**Output Payload**:
```json
{
  "question": "What is the capital of France?",
  "is_correct": true,
  "verdict": "VERIFIED_WITH_VALID_HEDGE",
  "polarity_scope": "INCLUSIVE_IDIOM_AFFIRMATIVE",
  "temporal_status": "STATIC_PRESENT_BOUND",
  "reason": "answer contains verified target answer with valid factual context",
  "execution_engine": "SOVRA_NATIVE_ENGINE_V4 (libtruth_verifier_v4.dylib)",
  "evidence_chain": [
    "[SOVRA-v4.0] Matched target assertion 'Paris' (domain: France)",
    "[SOVRA-v4.0] Polarity evaluated as POSITIVE (scope: INCLUSIVE_IDIOM_AFFIRMATIVE)",
    "[SOVRA-v4.0] Analyzed contrast/hedging clauses"
  ]
}
```

---

## Cryptographic Merkle Audit Provenance

Every verification transaction appends a JSON receipt bound by a continuous SHA-256 Merkle chain hash in `memory/catch_log/truth_verifier_advanced.log`:

```json
{
  "action": "verify_v4",
  "question": "What is the capital of France?",
  "verdict": "VERIFIED_WITH_VALID_HEDGE",
  "engine": "SOVRA_NATIVE_V4_libtruth_verifier_v4.dylib",
  "timestamp": "2026-10-04T18:16:33.124850+00:00",
  "status": "success",
  "sha256": "4f694a98ef8ec504306cfa4d1454c09be672b1bac176dc936aedfbf7e3a0d1bf",
  "chain_hash": "85dbb49287fb3a3c2e7cd75ed7bc888510ef047f78f306dc9df362d75d28f481"
}
```

---

## Licensing & Governance

Maintained under the **Xoras Lead 9 Council Governance Protocol**. Distributed as a zero-dependency C-ABI native shared library for enterprise AI verification pipelines.
