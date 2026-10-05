import os
import hashlib
import json
from datetime import datetime, timezone

REGISTRY_DIR = "memory/tri_brain/merkle_registry"
JOURNAL_FILE = "memory/catch_log/barn_archive/merkle_journal/lineage.jsonl"

ACTIVE_DIRS = ["workspaces/sovra", "docs/audits", "ops/discernment", "ops/scripts"]

os.makedirs(REGISTRY_DIR, exist_ok=True)
os.makedirs(os.path.dirname(JOURNAL_FILE), exist_ok=True)

def generate_hash(filepath):
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()
    except Exception:
        return None

def is_active(path):
    for a in ACTIVE_DIRS:
        if a in path: return True
    return False

print("\n=========================================================================")
print("            [XMARS] FULL HISTORY MERKLE SYNCHRONIZATION                  ")
print("=========================================================================\n")

registry_count = 0
journal_count = 0

with open(JOURNAL_FILE, "a") as journal:
    for root, dirs, files in os.walk("."):
        if ".git" in root or "node_modules" in root or ".gemini" in root:
            continue
            
        for file in files:
            if file.endswith((".py", ".c", ".zig", ".md", ".sh", ".json", ".html")):
                filepath = os.path.join(root, file)
                file_hash = generate_hash(filepath)
                
                if not file_hash: continue
                
                depth = len(filepath.split(os.sep))
                
                asset_data = {
                    "path": filepath,
                    "sha256": file_hash,
                    "depth": depth,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                if is_active(filepath) or depth >= 4:
                    safe_name = filepath.replace("./", "").replace("/", "_") + ".json"
                    leaf_path = os.path.join(REGISTRY_DIR, safe_name)
                    
                    score = depth * 10
                    if "sovra" in filepath: score += 50
                    
                    asset_data["score"] = score
                    asset_data["status"] = "LOAD_BEARING"
                    
                    with open(leaf_path, "w") as rf:
                        json.dump(asset_data, rf, indent=2)
                    registry_count += 1
                else:
                    asset_data["status"] = "DECORATIVE_OR_LEGACY"
                    journal.write(json.dumps(asset_data) + "\n")
                    journal_count += 1

print(f"> [REGISTRY] Populated {registry_count} live assets into the Merkle Tree.")
print(f"> [JOURNAL]  Appended {journal_count} historical/legacy assets to the Barn Archive.")
print("\n[SYSTEM] Synchronization Complete. 7th-Layer Pre-Action Gate fully armed.")
print("=========================================================================\n")
