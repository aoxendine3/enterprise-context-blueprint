# Arthur: Manuscript & Textual Stability Analyst
import difflib, time, json

class ArthurTextualStabilityEngine:
    def calculate_drift_and_stability(self, text_a, text_b):
        matcher = difflib.SequenceMatcher(None, text_a, text_b)
        ratio = matcher.ratio()
        return {
            "similarity_ratio": round(ratio, 4),
            "textual_drift_pct": round((1.0 - ratio) * 100, 2),
            "is_stable": ratio >= 0.95
        }

def run_experiment():
    engine = ArthurTextualStabilityEngine()
    t1 = "The Sovereign Council deliberates with zero latency on Apple Silicon M4 unified memory."
    t2 = "The Sovereign Council deliberates with low latency on Apple Silicon M4 unified memory."
    res = engine.calculate_drift_and_stability(t1, t2)
    return {"agent": "arthur", "status": "TEXTUAL_STABILITY_VERIFIED", "analysis": res}

if __name__ == "__main__":
    print(json.dumps(run_experiment(), indent=2))
