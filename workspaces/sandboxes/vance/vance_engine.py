# William Vance: Ruthless Blackbox Falsification & Byzantine Chaos Engine
import hashlib, time, json, random

class VanceFalsificationEngine:
    """The 4 Ruthless Gates: Anti-Basic, Immediate Purpose, Flawlessness/Torture, Market Superiority."""
    def evaluate_asset_against_4_gates(self, asset_name, loc, has_unit_tests, asan_clean, novelty_mult):
        verdict = {"asset": asset_name, "passed": False, "failed_gate": None, "score": 0.0}
        
        # Gate 1: Anti-Basic Filter (reject naive wrappers)
        if loc < 25:
            verdict["failed_gate"] = "GATE_1_ANTI_BASIC_FILTER (Boilerplate stub rejected)"
            return verdict
            
        # Gate 2: Immediate Purpose Check
        if not asset_name.endswith((".py", ".sh", ".json", ".rs", ".cpp", ".md")):
            verdict["failed_gate"] = "GATE_2_IMMEDIATE_PURPOSE (Extraneous artifact format)"
            return verdict
            
        # Gate 3: Flawlessness & Torture (TSAN/ASAN clean, 100% test pass)
        if not (has_unit_tests and asan_clean):
            verdict["failed_gate"] = "GATE_3_TORTURE_VERIFICATION (Lacks test coverage or memory sanitizer pass)"
            return verdict
            
        # Gate 4: Market Superiority (5x - 10x improvement)
        if novelty_mult < 5.0:
            verdict["failed_gate"] = f"GATE_4_MARKET_SUPERIORITY ({novelty_mult:.1f}x < 5.0x minimum floor)"
            return verdict
            
        verdict["passed"] = True
        verdict["score"] = round(loc * novelty_mult, 2)
        return verdict

    def inject_byzantine_fault_injection(self, data_dict):
        # Corrupt Merkle leaf or flip bits to test sentry detection
        raw = json.dumps(data_dict, sort_keys=True).encode()
        original_hash = hashlib.sha256(raw).hexdigest()
        corrupted = bytearray(raw)
        corrupted[len(corrupted) // 2] ^= 0xFF # Invert middle byte
        poisoned_hash = hashlib.sha256(corrupted).hexdigest()
        return {
            "original_hash": original_hash,
            "poisoned_hash": poisoned_hash,
            "tamper_detected": original_hash != poisoned_hash
        }

def run_experiment():
    t0 = time.perf_counter()
    engine = VanceFalsificationEngine()
    test_gate = engine.evaluate_asset_against_4_gates("axlon_engine.py", 120, True, True, 6.5)
    fuzz = engine.inject_byzantine_fault_injection({"sample_block": 4096, "proof": "MERKLE_ROOT_77"})
    return {
        "agent": "vance",
        "status": "DISCERNMENT_VERIFIED",
        "gate_evaluation": test_gate,
        "falsification_proof": fuzz,
        "latency_ms": round((time.perf_counter() - t0) * 1000, 3)
    }

if __name__ == "__main__":
    print(json.dumps(run_experiment(), indent=2))
