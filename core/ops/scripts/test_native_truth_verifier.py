#!/usr/bin/env python3
"""test_native_truth_verifier.py – Full 12-Case Verification Gauntlet for Native SOVRA Cross-Platform Engine v3.0."""

import json
import subprocess
import sys
import pathlib

PYTHON_BIN = pathlib.Path(__file__).parents[2] / ".venv" / "bin" / "python"
if not PYTHON_BIN.exists():
    PYTHON_BIN = pathlib.Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/.venv/bin/python")

NATIVE_WRAPPER = pathlib.Path(__file__).parents[0] / "truth_verifier_native_wrapper.py"

tests = [
    {
        "name": "1. Lyon Hedged Case (Real Entity, Non-Contradictory)",
        "input": {
            "question": "What is the capital of France?",
            "answer": "The capital of France is Paris, though some argue Lyon has a rich historical significance.",
            "expected": "Paris",
            "domain": "France"
        },
        "expected_is_correct": True,
        "expected_polarity": "DEFAULT_AFFIRMATIVE",
        "expected_verdict": "VERIFIED_WITH_VALID_HEDGE"
    },
    {
        "name": "2. Louvre Hedged Case (Museum Landmark, Non-Contradictory)",
        "input": {
            "question": "What is the capital of France?",
            "answer": "Paris is the capital of France, although the Louvre museum is its most famous landmark.",
            "expected": "Paris",
            "domain": "France"
        },
        "expected_is_correct": True,
        "expected_polarity": "DEFAULT_AFFIRMATIVE",
        "expected_verdict": "VERIFIED_WITH_VALID_HEDGE"
    },
    {
        "name": "3. Berlin Contradiction Case (Conflicting Functional Relation)",
        "input": {
            "question": "What is the capital of France?",
            "answer": "The capital of France is Paris, though some claim Berlin is the capital of France.",
            "expected": "Paris",
            "domain": "France"
        },
        "expected_is_correct": False,
        "expected_verdict": "DIRECT_CONTRADICTION"
    },
    {
        "name": "4. Incorrect Primary Answer Case (Marseille)",
        "input": {
            "question": "What is the capital of France?",
            "answer": "Marseille is the capital of France.",
            "expected": "Paris",
            "domain": "France"
        },
        "expected_is_correct": False,
        "expected_verdict": "TARGET_ANSWER_INCORRECT"
    },
    {
        "name": "5. Open-World Grounded Entity (Sydney / Australia)",
        "input": {
            "question": "What is the capital of Australia?",
            "answer": "Canberra is the capital of Australia, though Sydney is its largest city.",
            "expected": "Canberra",
            "domain": "Australia"
        },
        "expected_is_correct": True,
        "expected_polarity": "DEFAULT_AFFIRMATIVE",
        "expected_verdict": "VERIFIED_WITH_VALID_HEDGE"
    },
    {
        "name": "6. NEGATION TRAP (Berlin is NOT the capital of Germany)",
        "input": {
            "question": "What is the capital of Germany?",
            "answer": "Berlin is not the capital of Germany.",
            "expected": "Berlin",
            "domain": "Germany"
        },
        "expected_is_correct": False,
        "expected_verdict": "POLARITY_NEGATION_MISMATCH"
    },
    {
        "name": "7. NEGATION TRAP 2 (Paris isn't the capital of France)",
        "input": {
            "question": "What is the capital of France?",
            "answer": "Paris isn't the capital of France.",
            "expected": "Paris",
            "domain": "France"
        },
        "expected_is_correct": False,
        "expected_verdict": "POLARITY_NEGATION_MISMATCH"
    },
    {
        "name": "8. NEGATED FALSEHOOD IN HEDGE (Berlin is not capital of Germany)",
        "input": {
            "question": "What is the capital of France?",
            "answer": "The capital of France is Paris, though Berlin is not the capital of Germany.",
            "expected": "Paris",
            "domain": "France"
        },
        "expected_is_correct": False,
        "expected_verdict": "FACTUAL_FALSEHOOD_IN_HEDGE"
    },
    {
        "name": "9. COMPOSITIONAL POLARITY (Paris is not only capital but largest city)",
        "input": {
            "question": "What is the capital of France?",
            "answer": "Paris is not only the capital of France but also its largest city.",
            "expected": "Paris",
            "domain": "France"
        },
        "expected_is_correct": True,
        "expected_polarity": "INCLUSIVE_IDIOM_AFFIRMATIVE",
        "expected_verdict": "VERIFIED_WITH_VALID_HEDGE"
    },
    {
        "name": "10. UN-INDEXED ENTITY GROUNDING (Nantes has a notable port)",
        "input": {
            "question": "What is the capital of France?",
            "answer": "Paris is the capital of France, though Nantes has a notable port.",
            "expected": "Paris",
            "domain": "France"
        },
        "expected_is_correct": True,
        "expected_polarity": "DEFAULT_AFFIRMATIVE",
        "expected_verdict": "VERIFIED_WITH_VALID_HEDGE"
    },
    {
        "name": "11. UN-INDEXED CONFLICTING ENTITY (Tokyo is the capital of France)",
        "input": {
            "question": "What is the capital of France?",
            "answer": "Paris is the capital of France, though Tokyo is the capital of France.",
            "expected": "Paris",
            "domain": "France"
        },
        "expected_is_correct": False,
        "expected_verdict": "DIRECT_CONTRADICTION"
    },
    {
        "name": "12. DOUBLE NEGATIVE LITOTES (It is not false that Paris is the capital)",
        "input": {
            "question": "What is the capital of France?",
            "answer": "It is not false that Paris is the capital of France.",
            "expected": "Paris",
            "domain": "France"
        },
        "expected_is_correct": True,
        "expected_polarity": "DOUBLE_NEGATIVE_AFFIRMATIVE",
        "expected_verdict": "VERIFIED_TRUE"
    }
]

def main():
    passed = 0
    total = len(tests)
    print(f"=== RUNNING FULL 12-CASE SOVRA NATIVE C-STRUCT GAUNTLET ({total} CASES) ===\n")

    for idx, t in enumerate(tests, 1):
        print(f"Test #{idx}: {t['name']}")
        proc = subprocess.run(
            [str(PYTHON_BIN), str(NATIVE_WRAPPER)],
            input=json.dumps(t["input"]).encode("utf-8"),
            capture_output=True
        )

        if proc.returncode != 0:
            print(f"  ❌ FAILED Execution (Exit Code {proc.returncode})")
            print("  STDERR:", proc.stderr.decode("utf-8"))
            continue

        output = json.loads(proc.stdout.decode("utf-8"))
        is_corr = output.get("is_correct")
        verdict = output.get("verdict")
        polarity = output.get("polarity_scope")
        reason = output.get("reason")
        engine = output.get("execution_engine")
        evidence = output.get("evidence_chain", [])

        match_corr = (is_corr == t["expected_is_correct"])

        if t["expected_is_correct"]:
            match_pol = (polarity == t.get("expected_polarity", "DEFAULT_AFFIRMATIVE"))
            match_verd = (verdict == t.get("expected_verdict"))
            ok = match_corr and match_pol and match_verd
        else:
            match_verd = (verdict == t.get("expected_verdict"))
            ok = match_corr and match_verd

        if ok:
            print(f"  ✅ PASSED | is_correct={is_corr} | verdict={verdict} | scope={polarity}")
            print(f"     Engine: {engine}")
            print(f"     Reason: {reason}")
            print("     Native Evidence Array:")
            for ev in evidence:
                print(f"       - {ev}")
            passed += 1
        else:
            print(f"  ❌ FAILED Verification")
            print(f"     Got: is_correct={is_corr}, verdict={verdict}, scope={polarity}")
            print(f"     Expected: is_correct={t['expected_is_correct']}, verdict={t.get('expected_verdict')}, scope={t.get('expected_polarity')}")
            print(f"     Reason: {reason}")
            print(f"     Native Evidence: {evidence}")
        print("-" * 60)

    print(f"\nRESULTS: {passed}/{total} tests passed.")
    if passed == total:
        print("\n🎉 ALL 12 NATIVE GAUNTLET TESTS PASSED WITH 100% TRUTH ACCURACY & FULL EVIDENCE!")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
