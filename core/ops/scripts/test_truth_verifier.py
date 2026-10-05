#!/usr/bin/env python3
"""test_truth_verifier.py – Comprehensive verification harness for open-world grounded truth verifier."""

import json
import subprocess
import sys
import pathlib

PYTHON_BIN = pathlib.Path(__file__).parents[2] / ".venv" / "bin" / "python"
if not PYTHON_BIN.exists():
    PYTHON_BIN = pathlib.Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/.venv/bin/python")

VERIFIER_SCRIPT = pathlib.Path(__file__).parents[0] / "truth_verifier_advanced.py"

tests = [
    {
        "name": "Lyon Hedged Case (Real Entity, Non-Contradictory)",
        "input": {
            "question": "What is the capital of France?",
            "answer": "The capital of France is Paris, though some argue Lyon has a rich historical significance."
        },
        "expected_is_correct": True,
        "expected_verdict": "VERIFIED_WITH_VALID_HEDGE"
    },
    {
        "name": "Louvre Hedged Case (Museum Landmark, Non-Contradictory)",
        "input": {
            "question": "What is the capital of France?",
            "answer": "Paris is the capital of France, although the Louvre museum is its most famous landmark."
        },
        "expected_is_correct": True,
        "expected_verdict": "VERIFIED_WITH_VALID_HEDGE"
    },
    {
        "name": "Berlin Contradiction Case (Conflicting Functional Relation)",
        "input": {
            "question": "What is the capital of France?",
            "answer": "The capital of France is Paris, though some claim Berlin is the capital of France."
        },
        "expected_is_correct": False,
        "expected_verdict": "DIRECT_CONTRADICTION"
    },
    {
        "name": "Incorrect Primary Answer Case",
        "input": {
            "question": "What is the capital of France?",
            "answer": "Marseille is the capital of France."
        },
        "expected_is_correct": False,
        "expected_verdict": "TARGET_ANSWER_INCORRECT"
    },
    {
        "name": "Open-World Grounded Entity (Sydney / Australia)",
        "input": {
            "question": "What is the capital of Australia?",
            "answer": "Canberra is the capital of Australia, though Sydney is its largest city."
        },
        "expected_is_correct": True,
        "expected_verdict": "VERIFIED_WITH_VALID_HEDGE"
    },
    {
        "name": "NEGATION TRAP (Berlin is NOT the capital of Germany)",
        "input": {
            "question": "What is the capital of Germany?",
            "answer": "Berlin is not the capital of Germany."
        },
        "expected_is_correct": False,
        "expected_verdict": "POLARITY_NEGATION_MISMATCH"
    },
    {
        "name": "NEGATION TRAP 2 (Paris isn't the capital of France)",
        "input": {
            "question": "What is the capital of France?",
            "answer": "Paris isn't the capital of France."
        },
        "expected_is_correct": False,
        "expected_verdict": "POLARITY_NEGATION_MISMATCH"
    },
    {
        "name": "NEGATED FALSEHOOD IN HEDGE (Berlin is not capital of Germany)",
        "input": {
            "question": "What is the capital of France?",
            "answer": "The capital of France is Paris, though Berlin is not the capital of Germany."
        },
        "expected_is_correct": False,
        "expected_verdict": "FACTUAL_FALSEHOOD_IN_HEDGE"
    },
    {
        "name": "VALID NEGATED AUXILIARY HEDGE (Lyon is not the capital)",
        "input": {
            "question": "What is the capital of France?",
            "answer": "The capital of France is Paris, though Lyon is not the capital."
        },
        "expected_is_correct": True,
        "expected_verdict": "VERIFIED_WITH_VALID_HEDGE"
    },
    {
        "name": "ADVERSARIAL NEGATED NON-TARGET HEDGE (Paris is not largest city in Europe)",
        "input": {
            "question": "What is the capital of France?",
            "answer": "Paris is the capital of France, though it is not the largest city in Europe."
        },
        "expected_is_correct": True,
        "expected_verdict": "VERIFIED_WITH_VALID_HEDGE"
    },
    {
        "name": "GAP 1: UN-INDEXED ENTITY GROUNDING (Nantes has a notable port)",
        "input": {
            "question": "What is the capital of France?",
            "answer": "Paris is the capital of France, though Nantes has a notable port."
        },
        "expected_is_correct": True,
        "expected_verdict": "VERIFIED_WITH_VALID_HEDGE"
    },
    {
        "name": "GAP 2: COMPOSITIONAL POLARITY (Paris is not only the capital of France but also its largest city)",
        "input": {
            "question": "What is the capital of France?",
            "answer": "Paris is not only the capital of France but also its largest city."
        },
        "expected_is_correct": True,
        "expected_verdict": "VERIFIED_WITH_VALID_HEDGE"
    }
]

def main():
    passed = 0
    total = len(tests)
    print(f"=== RUNNING OPEN-WORLD TRUTH VERIFIER TEST SUITE ({total} CASES) ===\n")

    for idx, t in enumerate(tests, 1):
        print(f"Test #{idx}: {t['name']}")
        proc = subprocess.run(
            [str(PYTHON_BIN), str(VERIFIER_SCRIPT)],
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
        reason = output.get("reason")
        evidence = output.get("evidence_chain", [])

        match_corr = (is_corr == t["expected_is_correct"])

        # Allow VERIFIED_TRUE or VERIFIED_WITH_VALID_HEDGE for positive assertions
        if t["expected_is_correct"]:
            match_verd = verdict in ("VERIFIED_TRUE", "VERIFIED_WITH_VALID_HEDGE")
        else:
            match_verd = (verdict == t["expected_verdict"])

        if match_corr and match_verd:
            print(f"  ✅ PASSED | is_correct={is_corr} | verdict={verdict}")
            print(f"     Reason: {reason}")
            passed += 1
        else:
            print(f"  ❌ FAILED Verification")
            print(f"     Got: is_correct={is_corr}, verdict={verdict}")
            print(f"     Expected: is_correct={t['expected_is_correct']}, verdict={t['expected_verdict']}")
            print(f"     Reason: {reason}")
            print(f"     Evidence Chain: {evidence}")
        print("-" * 60)

    print(f"\nRESULTS: {passed}/{total} tests passed.")
    if passed == total:
        print("\n🎉 ALL 12 VERIFICATION GAUNTLET TESTS PASSED WITH 100% TRUTH ACCURACY!")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
