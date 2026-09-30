import os
import json
import glob

print("\n=========================================================================")
print("             [XMARS] EVE DIRECTIVE: BOUNDARY ENFORCEMENT                 ")
print("=========================================================================\n")

# 1. TELEMETRY KILL
settings_path = os.path.expanduser("~/.gemini/settings.json")
try:
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            data = json.load(f)
    else:
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        data = {}

    data["usage_statistics_enabled"] = False
    data["telemetry"] = False
    data["data_collection"] = False

    with open(settings_path, 'w') as f:
        json.dump(data, f, indent=4)
    print("[MAXX] Telemetry & Usage Statistics: \033[91m\033[1mDISABLED\033[0m")
    print(f"       -> Target: {settings_path}")
except Exception as e:
    print(f"[MAXX] Error writing settings: {e}")

# 2. SYMLINK BRAIN TO SSOT
ssot_mem = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory"
brain_src = os.path.expanduser("~/.gemini/antigravity/brain")
know_src = os.path.expanduser("~/.gemini/antigravity/knowledge")

brain_link = os.path.join(ssot_mem, "gemini_brain_symlink")
if not os.path.exists(brain_link) and os.path.exists(brain_src):
    os.symlink(brain_src, brain_link)
    print(f"[MAXX] Hidden Brain Relocated -> {brain_link}")

know_link = os.path.join(ssot_mem, "gemini_knowledge_symlink")
if not os.path.exists(know_link) and os.path.exists(know_src):
    os.symlink(know_src, know_link)
    print(f"[MAXX] Hidden Knowledge Relocated -> {know_link}")

# 3. AGENT.PY AUDIT & QUARANTINE
print("\n[JARVIS] Sweeping ~/.gemini for foreign or untracked agent binaries...")
target_dir = os.path.expanduser("~/.gemini")
suspicious_files = []
for root, dirs, files in os.walk(target_dir):
    for file in files:
        if file == "agent.py" or file == "foreign_agent.py":
            suspicious_files.append(os.path.join(root, file))

if suspicious_files:
    quarantine_dir = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/catch_log/quarantine"
    os.makedirs(quarantine_dir, exist_ok=True)
    for f in suspicious_files:
        base = os.path.basename(f)
        q_path = os.path.join(quarantine_dir, "QUARANTINED_" + base)
        os.rename(f, q_path)
        print(f"  -> \033[93m[VANCE] QUARANTINED foreign execution script:\033[0m {f}")
else:
    print("  -> \033[92m[VANCE] Directory sweep clean. No rogue agent.py scripts found.\033[0m")

# 4. .GEMINIIGNORE BOUNDARY ENFORCEMENT
ignore_path = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/.geminiignore"
with open(ignore_path, "w") as f:
    f.write("# EVE DIRECTIVE: BOUNDARY LOCK\n")
    f.write("# Deny all top-level reads outside canonical subdirectories\n")
    f.write("/*\n")
    f.write("!/workspaces/\n")
    f.write("!/memory/\n")
    f.write("!/ops/\n")
    f.write("!/docs/\n")
    f.write("!/products/\n")
print(f"\n[JARVIS] SSOT Ignore Boundary Enforced -> {ignore_path}")

print("\n=========================================================================\n")
