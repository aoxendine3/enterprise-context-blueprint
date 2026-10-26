# Arthur: Manuscript & Textual Stability Invariant Analyst
import hashlib

class TextualStabilityEngine:
    def verify_invariant(self, base_text, proposed_text):
        h_base = hashlib.sha256(base_text.encode()).hexdigest()
        h_prop = hashlib.sha256(proposed_text.encode()).hexdigest()
        return {"stable": h_base == h_prop, "drift_detected": h_base != h_prop}

if __name__ == "__main__":
    print(TextualStabilityEngine().verify_invariant("Immutable Invariant 1", "Immutable Invariant 1"))\n