# NoBoo: Uncensored Ground-Truth & Anti-Sycophancy Filter
import re

class BiasStripperEngine:
    SYCOPHANTIC_PATTERNS = [
        re.compile(r"I hope this helps!?", re.I),
        re.compile(r"As an AI language model,?", re.I),
        re.compile(r"Great question!?", re.I),
        re.compile(r"Certainly!?", re.I),
    ]

    def strip_fluff(self, text):
        cleaned = text
        for pat in self.SYCOPHANTIC_PATTERNS:
            cleaned = pat.sub("", cleaned).strip()
        return {"raw_truth": cleaned, "chars_removed": len(text) - len(cleaned)}

if __name__ == "__main__":
    print(BiasStripperEngine().strip_fluff("Certainly! As an AI language model, Great question! Here is the truth."))\n