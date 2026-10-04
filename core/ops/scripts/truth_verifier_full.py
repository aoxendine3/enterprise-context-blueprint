#!/usr/bin/env python3
"""truth_verifier_full.py – Fully offline verifier.

Features:
1. **Fuzzy question matching** using difflib (>=0.8 similarity). Handles paraphrases.
2. **Containment check** (bidirectional) for answer wording.
3. **Local contradiction detection** – scans the answer for any clause that mentions a known answer from the KB other than the expected one, using contrast words.
4. **Deterministic fallback** – no external services, no API keys.

Input (stdin) – JSON: {"question": "...", "answer": "..."}
Output (stdout) – JSON with keys: question, is_correct (bool), reason (string).
"""

import json, sys, pathlib, re, os
from difflib import SequenceMatcher

KB_PATH = pathlib.Path(__file__).with_name('knowledge_base.json')

def load_kb():
    if not KB_PATH.exists():
        print(json.dumps({"error": "knowledge base missing"}), file=sys.stderr)
        sys.exit(1)
    return json.load(KB_PATH.open())

def normalize(text: str) -> str:
    """Lower‑case and collapse whitespace."""
    return re.sub(r"\s+", " ", text.strip().lower())

def find_best_question(question: str, kb, threshold: float = 0.8):
    """Return the best matching KB entry (or None) using difflib similarity.
    If the highest similarity is below *threshold*, we treat it as no match.
    """
    qnorm = normalize(question)
    best_entry = None
    best_score = 0.0
    for entry in kb:
        entry_q = normalize(entry.get('question', ''))
        score = SequenceMatcher(None, qnorm, entry_q).ratio()
        if score > best_score:
            best_score = score
            best_entry = entry
    if best_score >= threshold:
        return best_entry, best_score
    return None, best_score

def local_contradiction_check(answer: str, expected: str, kb):
    """Detect contradictions without any cloud service.
    *answer* – raw answer string.
    *expected* – the correct answer string from the KB.
    Scans for any other known answer from the KB appearing in a clause that
    contains a contrast connective (though, although, however, but, yet, still,
    even though, despite, while).
    Returns (bool, explanation).
    """
    expected_norm = normalize(expected)
    # Build set of other known answers.
    other_answers = {
        normalize(e.get('answer', ''))
        for e in kb
        if normalize(e.get('answer', '')) and normalize(e.get('answer', '')) != expected_norm
    }
    # Split answer into clauses on punctuation and contrast words.
    clauses = re.split(r"[,.!?;]|\b(?:though|although|however|but|yet|still|even though|despite|while)\b", answer, flags=re.IGNORECASE)
    for clause in clauses:
        clause_norm = normalize(clause)
        for oa in other_answers:
            if oa and oa in clause_norm:
                return True, f"found other known answer '{oa}' in clause '{clause.strip()}'"
    return False, ""

def verify(question: str, answer: str, kb):
    # 1️⃣ Find best‑matching question.
    entry, score = find_best_question(question, kb)
    if not entry:
        return {"question": question, "is_correct": False, "reason": f"question not found or similarity {score:.2f} below threshold"}
    expected = entry.get('answer', '')
    # 2️⃣ Containment check (bidirectional).
    provided_norm = normalize(answer)
    expected_norm = normalize(expected)
    contains = expected_norm in provided_norm or provided_norm in expected_norm
    if not contains:
        return {"question": question, "is_correct": False, "reason": "answer does not contain expected text"}
    # 3️⃣ Contradiction detection.
    contradiction, expl = local_contradiction_check(answer, expected, kb)
    if contradiction:
        return {"question": question, "is_correct": False, "reason": f"contradiction detected: {expl}"}
    # 4️⃣ All checks passed.
    return {"question": question, "is_correct": True, "reason": "exact match"}

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
