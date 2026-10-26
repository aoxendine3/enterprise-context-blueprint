# NoBoo: Uncensored Evaluator & Bias Stripper
import re, time, json

class NoBooRawTruthEngine:
    BANNED_FLATTERY = [
        "impressive", "cutting-edge", "game-changing", "revolutionary", 
        "incredible", "seamless", "effortless", "industry-leading"
    ]
    def strip_sycophancy(self, text):
        clean_text = text
        stripped_count = 0
        for buzz in self.BANNED_FLATTERY:
            matches = len(re.findall(r'\b' + re.escape(buzz) + r'\b', clean_text, re.IGNORECASE))
            if matches > 0:
                clean_text = re.sub(r'\b' + re.escape(buzz) + r'\b', "[FLATTERY_STRIPPED]", clean_text, flags=re.IGNORECASE)
                stripped_count += matches
        return {"unvarnished_text": clean_text, "flattery_occurrences_stripped": stripped_count}

def run_experiment():
    engine = NoBooRawTruthEngine()
    test_text = "This cutting-edge framework provides a revolutionary and seamless experience."
    res = engine.strip_sycophancy(test_text)
    return {"agent": "noboo", "status": "RAW_TRUTH_VERIFIED", "result": res}

if __name__ == "__main__":
    print(json.dumps(run_experiment(), indent=2))
