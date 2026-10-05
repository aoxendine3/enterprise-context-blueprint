#!/usr/bin/env python3
import os
import shutil

desktop = "/Users/ajoxendine68/Desktop"
barn_archive = "/Users/ajoxendine68/Projects/the-barn/misc/desktop_archive"
os.makedirs(barn_archive, exist_ok=True)
os.makedirs(os.path.join(barn_archive, "screenshots"), exist_ok=True)

# 1. Clean desktop items
items_to_move = [
    (".agents", "dot_agents"),
    (".cursor", "dot_cursor"),
    (".zed", "dot_zed"),
    ("Launch_Sovereign_Dashboard.command", "Launch_Sovereign_Dashboard.command"),
    ("Xoras_Workspace", "Xoras_Workspace"),
    ("Projects", "Projects")
]

for src_name, dst_name in items_to_move:
    src = os.path.join(desktop, src_name)
    dst = os.path.join(barn_archive, dst_name)
    if os.path.exists(src):
        if os.path.exists(dst):
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            else:
                os.remove(dst)
        shutil.move(src, dst)
        print(f"Archived to barn: {src_name} -> {dst}")

# 2. Screenshots
for f in os.listdir(desktop):
    if f.startswith("Screenshot"):
        src = os.path.join(desktop, f)
        dst = os.path.join(barn_archive, "screenshots", f)
        shutil.move(src, dst)
        print(f"Archived screenshot: {f}")

# 3. Clean cache
pytest_cache = os.path.join(desktop, ".pytest_cache")
if os.path.exists(pytest_cache):
    shutil.rmtree(pytest_cache)
    print("Cleaned .pytest_cache")

print("\n--- Desktop Clean Summary ---")
for item in os.listdir(desktop):
    print("Remaining on Desktop:", item)
