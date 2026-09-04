#!/usr/bin/env python3
"""
=============================================================================
XORAS DOJO EMPIRICAL DATASET HARVESTER
Extracts empirical agent combat, consensus, and state transitions
into offline JSONL training datasets for local Ollama fine-tuning.
Zero data loss, zero cloud tethers.
=============================================================================
"""

import os, sqlite3, json, hashlib

SSOT_ROOT = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain"
DOJO_DB = os.path.join(SSOT_ROOT, "data_center/products/upgp_dojo_proving_ground/upgp_state.db")
OUTPUT_JSONL = os.path.join(SSOT_ROOT, "data_center/research/dojo_empirical_training_dataset.jsonl")

def harvest():
    print("=================================================================")
    print("🌾 HARVESTING DOJO EMPIRICAL TESTING DATA FOR LOCAL TRAINING")
    print("=================================================================")
    
    if not os.path.exists(DOJO_DB):
        print("[-] Dojo database not found:", DOJO_DB)
        return
        
    conn = sqlite3.connect(DOJO_DB)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"[1/3] Found {len(tables)} tables in Dojo state DB: {tables}")
    
    total_records = 0
    with open(OUTPUT_JSONL, "w") as out_f:
        for t in tables:
            cursor.execute(f"PRAGMA table_info({t});")
            cols = [c[1] for c in cursor.fetchall()]
            
            cursor.execute(f"SELECT * FROM {t};")
            rows = cursor.fetchall()
            print(f"  Table '{t}': extracting {len(rows)} records...")
            
            for row in rows:
                record = {
                    "source_table": t,
                    "data": dict(zip(cols, [str(v) if isinstance(v, (bytes, bytearray)) else v for v in row]))
                }
                out_f.write(json.dumps(record) + "\n")
                total_records += 1
                
    conn.close()
    
    h = hashlib.sha256()
    with open(OUTPUT_JSONL, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
            
    print(f"[2/3] Extraction complete: {total_records} empirical records harvested.")
    print(f"[3/3] SHA-256 Digest: {h.hexdigest()} ({OUTPUT_JSONL})")
    print("[✓] Empirical research data secured for local model training.")

if __name__ == "__main__":
    harvest()
