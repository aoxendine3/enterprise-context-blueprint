#!/usr/bin/env python3
"""truth_verifier.py – Enhanced verifier with simple contradiction detection.

Input (stdin) JSON: {"question": "...", "answer": "..."}
Output (stdout) JSON: {
  "question": "...",
  "is_correct": true|false,
  "reason": "..."
}

The verifier:
1. Normalizes the question/answer (lower‑case, collapse whitespace).
2. Looks up the question in a tiny static KB (knowledge_base.json) using **exact‑match** after normalization.
3. If a match is found, it:
   * Checks whether the expected answer is contained in the provided answer (or vice‑versa).
   * Runs a **lightweight contradiction detector** that flags the answer if it mentions any **other known answer** from the KB in a contrasting clause (e.g., "but ... also").
   * Returns true only when containment succeeds **and** no contradiction is detected.
4. If the question is not in the KB, it returns false with reason "question not found in knowledge base".

This design stays minimal (no external services) while exposing the failure mode you asked for.
"""

import json, sys, pathlib, re

KB_PATH = pathlib.Path(__file__).with_name('knowledge_base.json')

def load_kb():
    if not KB_PATH.exists():
        print(json.dumps({"error": "knowledge base missing"}), file=sys.stderr)
        sys.exit(1)
    return json.load(KB_PATH.open())

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())

def detect_contradiction(provided: str, expected: str, kb_answers: set) -> bool:
    """Very lightweight rule‑based contradiction detector.
    * Flags if the answer contains a **different known answer** from the KB.
    * Also flags simple "but ... also" patterns where the second clause mentions a different known answer.
    """
    pnorm = normalize(provided)
    # Direct presence of a different known answer anywhere
    for ans in kb_answers:
        if ans != expected and ans in pnorm:
            return True
    # Contrast clause detection
    if " but " in pnorm:
        parts = [part.strip() for part in pnorm.split("but")]
        for part in parts:
            for ans in kb_answers:
                if ans != expected and ans in part:
                    return True
    return False

def verify(question: str, answer: str, kb) -> dict:
    # Build a set of all normalized answers in the KB for contradiction checks
    kb_answers = {normalize(entry.get('answer', '')) for entry in kb}
    qnorm = normalize(question)
    for entry in kb:
        if normalize(entry.get('question', '')) == qnorm:
            expected = normalize(entry.get('answer', ''))
            provided = normalize(answer)
            # Containment check (bidirectional)
            contains = expected in provided or provided in expected
            # Contradiction detection
            contradiction = detect_contradiction(answer, expected, kb_answers)
            if contains and not contradiction:
                return {"question": question, "is_correct": True, "reason": "exact match"}
            if contradiction:
                return {"question": question, "is_correct": False, "reason": "contradiction detected"}
            return {"question": question, "is_correct": False, "reason": "answer does not contain expected text"}
    return {"question": question, "is_correct": False, "reason": "question not found in knowledge base"}

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
