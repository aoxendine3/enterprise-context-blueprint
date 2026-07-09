import sqlite3
import json
import time
import os
import hashlib
from typing import Dict, Any, Optional

# Path to the ledger database (default location can be overridden via env var)
_DB_PATH = os.getenv('INTENT_LEDGER_PATH', '/tmp/intent_ledger.db')

def _init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS intents (
            intent_id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            intent_json TEXT NOT NULL,
            signature TEXT NOT NULL,
            timestamp INTEGER NOT NULL
        )
    ''')
    conn.commit()
    return conn

_conn = _init_db()

def _hash_intent(intent: Dict[str, Any]) -> str:
    """Create a deterministic hash of the intent JSON for signing/verification."""
    intent_bytes = json.dumps(intent, sort_keys=True).encode('utf-8')
    return hashlib.sha256(intent_bytes).hexdigest()

def add_intent(agent_id: str, intent: Dict[str, Any], signature: str) -> bool:
    """Add a new intent to the ledger.

    Args:
        agent_id: Unique identifier of the agent submitting the intent.
        intent: The intent payload (must be JSON‑serialisable).
        signature: Cryptographic signature of the intent hash (placeholder).

    Returns:
        True if insertion succeeded, False otherwise (e.g., duplicate).
    """
    intent_id = _hash_intent(intent)
    ts = int(time.time())
    try:
        _conn.execute(
            'INSERT INTO intents (intent_id, agent_id, intent_json, signature, timestamp) VALUES (?,?,?,?,?)',
            (intent_id, agent_id, json.dumps(intent), signature, ts)
        )
        _conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def get_intent(intent_id: str) -> Optional[Dict[str, Any]]:
    cur = _conn.execute('SELECT intent_json FROM intents WHERE intent_id=?', (intent_id,))
    row = cur.fetchone()
    return json.loads(row[0]) if row else None

def verify_intent(intent: Dict[str, Any], signature: str, public_key: str) -> bool:
    """Placeholder verification using a simple hash comparison.
    In a real system this would employ asymmetric crypto (e.g., Ed25519).
    """
    expected_hash = _hash_intent(intent)
    return signature == f"{expected_hash}:{public_key}"

def list_intents() -> list:
    cur = _conn.execute('SELECT intent_id, agent_id, timestamp FROM intents')
    return [{'intent_id': r[0], 'agent_id': r[1], 'timestamp': r[2]} for r in cur.fetchall()]

# Example usage (removed for production; keep as reference)
# if __name__ == '__main__':
#     sample_intent = {'goal': 'process_data', 'priority': 5}
#     sig = f"{_hash_intent(sample_intent)}:dummy_pub_key"
#     add_intent('agent_001', sample_intent, sig)
