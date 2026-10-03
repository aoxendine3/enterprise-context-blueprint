import sqlite3
import os
import json

DB_PATH = os.path.expanduser("~/Desktop/SSOT_Agentic_Brain/.sovereign/provenance/lineage_dag.db")

def dump_db():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Sort by timestamp to get the absolute latest entries regardless of session sequence
    cursor.execute("SELECT * FROM lineage_nodes ORDER BY timestamp DESC LIMIT 10")
    rows = cursor.fetchall()
    
    markdown = "# 7th-Layer Sovereign MerkleDB (lineage_dag.db)\n\n"
    markdown += "| Seq | Session ID | Agent | Step Type | Payload Hash | Merkle Root (Node ID) |\n"
    markdown += "|---|---|---|---|---|---|\n"
    
    for row in rows:
        d = dict(row)
        seq = d.get("seq_num", "?")
        session = d.get("session_id", "?")
        agent = d.get("agent_id", "?")
        step_type = d.get("step_type", "?")
        payload_hash = d.get("payload_hash", "?")[:16] + "..."
        merkle_root = d.get("node_id", "?")[:16] + "..."
        
        markdown += f"| {seq} | `{session}` | **{agent}** | `{step_type}` | `{payload_hash}` | `{merkle_root}` |\n"
        
    markdown += "\n### Latest Raw Payload Data (From Your Current Session)\n"
    if rows:
        latest = dict(rows[0])
        payload = latest.get('payload_data') or latest.get('payload') or "{}"
        try:
            parsed = json.loads(payload)
            markdown += f"```json\n{json.dumps(parsed, indent=2)}\n```\n"
        except:
            markdown += f"```json\n{payload}\n```\n"
        
    with open("/Users/ajoxendine68/.gemini/antigravity/brain/bd892285-cca1-43cd-bb8b-d1c3128f05ca/MERKLE_DB_DUMP.md", "w") as f:
        f.write(markdown)
        
    print("MerkleDB dumped to UI.")

if __name__ == "__main__":
    dump_db()
