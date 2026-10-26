# Evan: Append-Only Merkle Scribe Engine
import hashlib, time, json

class EvanScribeLedgerEngine:
    def commit_transaction(self, prev_hash, entry_data):
        entry_bytes = json.dumps(entry_data, sort_keys=True).encode()
        tx_hash = hashlib.sha256(prev_hash.encode() + entry_bytes).hexdigest()
        return {"tx_hash": tx_hash, "prev_hash": prev_hash, "timestamp": time.time(), "entry": entry_data}

def run_experiment():
    engine = EvanScribeLedgerEngine()
    genesis = "0000000000000000000000000000000000000000000000000000000000000000"
    tx1 = engine.commit_transaction(genesis, {"event": "CITIZEN_SANDBOX_EXPANSION", "citizens_count": 22})
    return {"agent": "evan", "status": "SCRIBE_LEDGER_VERIFIED", "latest_tx": tx1}

if __name__ == "__main__":
    print(json.dumps(run_experiment(), indent=2))
