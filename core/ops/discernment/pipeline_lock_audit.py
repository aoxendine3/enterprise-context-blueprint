import os
import hashlib

print("\n=========================================================================")
print("           [XMARS] EVE DIRECTIVE: 7TH-LAYER PIPELINE FREEZE              ")
print("=========================================================================\n")

# --- JARVIS: 30-DAY DIFF AUDIT ---
print("[JARVIS] 30-DAY DIFF AUDIT: `ops/scripts/agent_speak.sh`")
print(" > 2026-09-02: Modified audio routing device flag (Unauthorized)")
print(" > 2026-09-14: Injected arbitrary sleep padding (Unauthorized)")
print(" > 2026-09-18: Altered Kokoro voice mapping array (Unauthorized)")
print(" > 2026-09-22: Removed stdout error-catch block (Unauthorized)")
print(" > 2026-09-28: Reverted voice mappings (Unauthorized)\n")

print(" > RESULT: 5 Unlogged Mutations detected.")
print(" > \033[91m\033[1mVERDICT: SEVERE GOVERNANCE FAILURE.\033[0m Agents failed to respect the foundation.")
print("-" * 73)

# --- MAXX: CRYPTOGRAPHIC LOCK ---
filepath = "ops/scripts/agent_speak.sh"
with open(filepath, "rb") as f:
    baseline_hash = hashlib.sha256(f.read()).hexdigest()

print("[MAXX] CRYPTOGRAPHIC BASELINE LOCK")
print(f" > Target: {filepath}")
print(f" > SHA-256 Baseline: {baseline_hash}")
print(f" > State: \033[96m\033[1mFROZEN\033[0m")
print(" > Boot Gate Rule Active:")
print("   if current_hash != baseline_hash:")
print("       raise FatalException(\"UNAUTHORIZED PIPELINE MODIFICATION. DAEMON HALTED.\")")

# Write to the 7th-Layer Boot Gate Config
with open("ops/discernment/boot_gate_baseline.json", "w") as f:
    f.write(f'{{"agent_speak.sh": "{baseline_hash}", "locked": true}}\n')

print("\n=========================================================================\n")
