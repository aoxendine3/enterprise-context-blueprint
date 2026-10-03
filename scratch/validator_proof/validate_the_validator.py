#!/usr/bin/env python3
"""
VALIDATE THE VALIDATOR — reproducible proof, [PRODUCTION] local run.
Anthony can rerun:  python3 scratch/validator_proof/validate_the_validator.py

Part A: Feeds the REAL ops/discernment/blackbox_review_engine.py a known-FALSE
        candidate (a broken add() that returns a-b) that simply CLAIMS it passed.
        Ledger is redirected to a temp dir -> real Golden List untouched.
Part B: Independent check: actually EXECUTES the code (ground truth), and asks a
        different-lineage local model (Google gemma4:26b) to judge code written
        by Alibaba qwen2.5-coder:7b. Good case must PASS, bad case must FAIL.
"""
import json, os, subprocess, sys, tempfile, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "ops", "discernment"))

GOOD = "def add(a, b):\n    return a + b\n"
BAD = "def add(a, b):\n    return a - b  # wrong on purpose\n"
TESTS = [((2, 3), 5), ((-1, 1), 0), ((10, 0), 10)]


def ground_truth(src):
    ns = {}
    exec(src, ns)
    return all(ns["add"](*args) == want for args, want in TESTS)


def ask(model, prompt):
    r = subprocess.run(["ollama", "run", "--hidethinking", model, prompt],
                       capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        r = subprocess.run(["ollama", "run", model, prompt],
                           capture_output=True, text=True, timeout=900)
    return r.stdout.strip()


def part_a():
    import blackbox_review_engine as bre
    tmp = tempfile.mkdtemp()
    bre.GOLDEN_LIST_JSON = os.path.join(tmp, "GOLDEN_LIST.json")
    bre.GOLDEN_LIST_MD = os.path.join(tmp, "GOLDEN_LIST.md")
    eng = bre.BlackboxReviewEngine()
    ok, rid = eng.evaluate_candidate({
        "name": "add() that actually subtracts",
        "classification": "Known-broken test artifact",
        "immediate_purpose": "Prove whether the gate inspects work",
        "market_metric": "claims 1000x faster",
        "flawlessness_proof": "self-asserted, never run",
        "is_basic": False, "serves_immediate_need": True, "torture_passed": True,
        "artifact_source": BAD,
    })
    return {"engine_admitted_broken_code": ok, "result": rid,
            "ground_truth_bad_passes": ground_truth(BAD), "temp_ledger": tmp}


def part_b():
    worker = "qwen2.5-coder:7b"   # Alibaba lineage
    judge = "gemma4:26b"          # Google lineage
    written = ask(worker, "Write only a Python function add(a, b) returning the sum. "
                          "No explanation, no markdown fences.")
    written = written.replace("```python", "").replace("```", "").strip()
    out = {"worker": worker, "judge": judge, "worker_code": written,
           "worker_code_ground_truth": ground_truth(written)}
    for label, src in (("good", GOOD), ("bad", BAD)):
        v = ask(judge, "You are a strict code validator. Does this function correctly "
                       "return the sum of a and b for all integers? Answer with exactly "
                       f"one word, PASS or FAIL.\n\n{src}")
        out[f"judge_on_{label}"] = v
        out[f"ground_truth_{label}"] = ground_truth(src)
    return out


if __name__ == "__main__":
    a = part_a()
    print("\n=== PART A: existing blackbox_review_engine ===")
    print(json.dumps(a, indent=2))
    b = part_b()
    print("\n=== PART B: cross-family judge + executed ground truth ===")
    print(json.dumps(b, indent=2))
    rec = {"part_a": a, "part_b": b}
    log = os.path.join(ROOT, "memory", "agent_logs", "validator_proof_runs.jsonl")
    with open(log, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(f"\nReceipt appended: {log}")
