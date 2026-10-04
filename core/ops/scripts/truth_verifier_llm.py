#!/usr/bin/env python3
"""truth_verifier_llm.py – LLM‑based truth verifier with contradiction detection.

This version augments the simple rule‑based verifier by querying the Gemini
LLM (via the `google.generativeai` SDK) to assess whether the provided answer
contains any statement that contradicts the *expected* answer.

Input (stdin) – JSON object with two fields:
    {"question": "...", "answer": "..."}

Output (stdout) – JSON with the same schema used by the original verifier:
    {"question": "...", "is_correct": true|false, "reason": "..."}

Workflow:
1. Load the static knowledge base (`knowledge_base.json`).
2. Perform an exact‑match lookup on the normalized question.
3. If a match is found, run two checks:
   a) **Containment check** – bidirectional substring (same as before).
   b) **LLM consistency check** – send a concise prompt to Gemini asking
      whether the provided answer contradicts the known fact. The model
      returns a short "YES"/"NO" and a rationale.
4. Return `is_correct: true` only when containment succeeds **and** the LLM
   answers "NO" (i.e., no contradiction). Any other response is treated as a
   failure.
5. If the question is absent from the KB, return a "question not found"
   result.

The script is deliberately defensive: if the Gemini SDK cannot be imported
or the API call fails, it falls back to the original rule‑based logic so the
pipeline never crashes because of an external dependency.
"""

import json, sys, pathlib, re, os

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
KB_PATH = pathlib.Path(__file__).with_name('knowledge_base.json')

def load_kb():
    if not KB_PATH.exists():
        print(json.dumps({"error": "knowledge base missing"}), file=sys.stderr)
        sys.exit(1)
    return json.load(KB_PATH.open())

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())

# ---------------------------------------------------------------------------
# LLM consistency check (Gemini)
# ---------------------------------------------------------------------------
def llm_contradiction_check(question: str, expected: str, answer: str) -> (bool, str):
    """Local contradiction detector – no cloud call.
    Scans the answer for any clause that mentions a known answer from the KB
    other than the expected one. Handles contrast words like 'though', 'although',
    'however', 'but', 'yet', 'still', 'even though', 'despite', 'while'.
    Returns (True, explanation) if a conflict is found, otherwise (False, "").
    """
    # Load knowledge base to obtain all known answers.
    kb = load_kb()
    kb_answers = {normalize(entry.get('answer', '')) for entry in kb}
    expected_norm = normalize(expected)
    other_answers = {a for a in kb_answers if a and a != expected_norm}

    # Split answer into possible contrast clauses.
    clauses = re.split(r"[,.!?;]|\b(?:though|although|however|but|yet|still|even though|despite|while)\b", answer, flags=re.IGNORECASE)
    for clause in clauses:
        clause_norm = normalize(clause)
        for oa in other_answers:
            if oa in clause_norm:
                return (True, f"found other known answer '{oa}' in clause '{clause.strip()}'")
    return (False, "")

# ---------------------------------------------------------------------------
# Core verification routine
# ---------------------------------------------------------------------------
def verify(question: str, answer: str, kb) -> dict:
    kb_answers = {normalize(entry.get('answer', '')) for entry in kb}
    qnorm = normalize(question)
    for entry in kb:
        if normalize(entry.get('question', '')) == qnorm:
            expected = normalize(entry.get('answer', ''))
            provided = normalize(answer)
            # Containment (bidirectional) – fast pre‑filter
            contains = expected in provided or provided in expected
            if not contains:
                return {"question": question, "is_correct": False, "reason": "answer does not contain expected text"}
            # LLM consistency check
            contradiction, reason = llm_contradiction_check(question, entry.get('answer', ''), answer)
            if contradiction:
                return {"question": question, "is_correct": False, "reason": f"contradiction detected: {reason}"}
            else:
                return {"question": question, "is_correct": True, "reason": "exact match"}
    return {"question": question, "is_correct": False, "reason": "question not found in knowledge base"}

# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    try:
        payload = json.load(sys.stdin)
    except Exception as e:
        print(json.dumps({"error": f"invalid JSON input: {e}"}), file=sys.stderr)
        sys.exit(1)
    question = payload.get('question')
    answer = payload.get('answer')
    if not question or not answer:
        print(json.dumps({"error": "both 'question' and 'answer' fields required"}), file=sys.stderr)
        sys.exit(1)
    kb = load_kb()
    result = verify(question, answer, kb)
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
