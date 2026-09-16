import os
import json
import hashlib
from pathlib import Path

DESKTOP_PATH = r"C:\Users\admin\Desktop"
OUTPUT_JSON = r"C:\Users\admin\Desktop\SSOT_Agentic_Brain\ops\inventory_data.json"

def compute_sha256(filepath):
    try:
        if os.path.getsize(filepath) > 50 * 1024 * 1024:  # skip >50MB for speed
            return "SKIPPED_LARGE_FILE"
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        return f"ERROR: {str(e)}"

def scan_desktop():
    inventory = []
    print(f"Scanning {DESKTOP_PATH}...")
    for root, dirs, files in os.walk(DESKTOP_PATH):
        # Prune node_modules, .git objects, cache
        if 'node_modules' in dirs:
            dirs.remove('node_modules')
        if '.git' in dirs:
            dirs.remove('.git')
        if 'Cache' in dirs:
            dirs.remove('Cache')
        if 'ShaderCache' in dirs:
            dirs.remove('ShaderCache')
                
        rel_root = os.path.relpath(root, DESKTOP_PATH)
        top_folder = rel_root.split(os.sep)[0] if rel_root != '.' else 'Desktop_Root'
        
        for file in files:
            full_path = os.path.join(root, file)
            try:
                stat = os.stat(full_path)
                item = {
                    "top_folder": top_folder,
                    "rel_path": os.path.relpath(full_path, DESKTOP_PATH),
                    "full_path": full_path,
                    "size_bytes": stat.st_size,
                    "extension": os.path.splitext(file)[1].lower(),
                    "sha256": compute_sha256(full_path)
                }
                inventory.append(item)
            except Exception as e:
                print(f"Error reading {full_path}: {e}")
                
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(inventory, f, indent=2)
    print(f"Inventory completed. Total files indexed: {len(inventory)}")

if __name__ == "__main__":
    scan_desktop()
