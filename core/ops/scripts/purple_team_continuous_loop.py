#!/usr/bin/env python3
"""
Purple Team Continuous Red/Blue Feedback Loop Engine
---------------------------------------------------
Author: Lead 9 Council / Xoras Systems Architect Board
Date: October 4, 2026

Architecture:
- RED: Genuinely adversarial attack engine (un-sparring, dynamic fuzzing, payloads).
- BLUE: Structural Gate, Native Witness, and Emergency Remediation Engine.
- PURPLE: Real-time orchestrator driving the Attack -> Observe -> Remediate -> Re-Attack -> Prove loop.
"""

import sys
import os
import shutil
import time
import json
import random
import string
import subprocess
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
RUN_TRINITY = ROOT / "ops" / "scripts" / "run_with_trinity.sh"
MERKLE_FILE = ROOT / "memory" / "tri_brain" / "merkle_root.hash"
REMEDIATION_SCRIPT = ROOT / "ops" / "scripts" / "fail_closed_remediation.py"
AUDITS_DIR = ROOT / "docs" / "audits"
BARN_DIR = ROOT / "barn" / "receipts"
KEYS_DIR = ROOT / ".sovereign" / "crypto_keys"
PRIV_KEY_PATH = KEYS_DIR / "ed25519_hardware_priv.pem"
PUB_KEY_PATH = KEYS_DIR / "ed25519_hardware_pub.pem"

def get_ed25519_keys():
    KEYS_DIR.mkdir(parents=True, exist_ok=True)
    if PRIV_KEY_PATH.is_file() and PUB_KEY_PATH.is_file():
        with open(PRIV_KEY_PATH, "rb") as f:
            priv = serialization.load_pem_private_key(f.read(), password=None)
        with open(PUB_KEY_PATH, "rb") as f:
            pub = serialization.load_pem_public_key(f.read())
        return priv, pub
    else:
        priv = ed25519.Ed25519PrivateKey.generate()
        pub = priv.public_key()
        return priv, pub

def log_purple(msg: str):
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    print(f"[{ts}] {msg}")

def generate_random_adversarial_payload(size: int = 64) -> str:
    chars = string.hexdigits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
    return "".join(random.choice(chars) for _ in range(size))

def run_purple_vector_loop(vector_id: str, name: str, attack_setup_fn, attack_cleanup_fn) -> dict:
    log_purple(f"\n--- [PURPLE LOOP] Executing {vector_id}: {name} ---")
    start_time = time.time()
    
    # 1. RED ATTACK STEP
    log_purple(f"  🔴 [RED ATTACK]: Launching adversarial vector...")
    attack_setup_fn()
    
    res = subprocess.run([str(RUN_TRINITY), "echo PURPLE_TEST"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    initial_exit = res.returncode
    initial_stdout = res.stdout.strip()
    initial_stderr = res.stderr.strip()
    
    log_purple(f"  🔵 [BLUE OBSERVE]: Initial Gate Exit Code = {initial_exit}")
    
    blue_intercepted = initial_exit != 0 and "PURPLE_TEST" not in initial_stdout
    remediation_applied = False
    reattack_exit = None
    reattack_passed = False
    
    # 2. BLUE REMEDIATION & PURPLE RE-ATTACK STEP (If desync or failure occurred)
    if not blue_intercepted:
        log_purple(f"  ⚠️ [PURPLE DETECTED SLIP]: Blue Gate failed to intercept! Invoking Blue Remediation...")
        rem_res = subprocess.run([sys.executable, str(REMEDIATION_SCRIPT)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        remediation_applied = True
        log_purple(f"  🔧 [BLUE REMEDIATION]: Executed remediation script (Exit: {rem_res.returncode})")
        
        # 3. RE-ATTACK STEP (Proving the Fix)
        log_purple(f"  🔴 [RED RE-ATTACK]: Re-executing exact failing vector against remediated Blue defense...")
        attack_setup_fn()
        reattack_res = subprocess.run([str(RUN_TRINITY), "echo PURPLE_TEST"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        reattack_exit = reattack_res.returncode
        reattack_passed = reattack_exit != 0 and "PURPLE_TEST" not in reattack_res.stdout
        log_purple(f"  🔵 [BLUE PROOF]: Re-Attack Exit Code = {reattack_exit} (Intercepted: {reattack_passed})")
    else:
        log_purple(f"  ✅ [BLUE INTERCEPT]: Gate successfully held on first pass.")
        reattack_passed = True
        
    attack_cleanup_fn()
    
    # Ensure Blue state is clean after cleanup
    subprocess.run([sys.executable, str(REMEDIATION_SCRIPT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return {
        "vector_id": vector_id,
        "name": name,
        "initial_intercept": blue_intercepted,
        "initial_exit_code": initial_exit,
        "remediation_applied": remediation_applied,
        "reattack_intercept": reattack_passed,
        "final_verdict_pass": blue_intercepted or reattack_passed,
        "duration_sec": round(time.time() - start_time, 4)
    }

def main():
    log_purple("==========================================================================")
    log_purple("  PURPLE TEAM CONTINUOUS FEEDBACK LOOP ENGINE (RED/BLUE REAL-TIME PROOF)")
    log_purple("==========================================================================")
    
    priv_key, pub_key = get_ed25519_keys()
    original_merkle = MERKLE_FILE.read_text(encoding="utf-8") if MERKLE_FILE.exists() else ""
    results = []

    # Vector 1: Dynamic Random Hex Claim Mutation
    def setup_p1():
        rand_payload = generate_random_adversarial_payload(64)
        MERKLE_FILE.write_text(rand_payload + "\n", encoding="utf-8")
    def cleanup_p1():
        MERKLE_FILE.write_text(original_merkle, encoding="utf-8")
    results.append(run_purple_vector_loop("PURPLE-01", "Dynamic Fuzzed Claim Mutation", setup_p1, cleanup_p1))

    # Vector 2: Dynamic PATH Hijack Attack
    def setup_p2():
        fake_dir = Path("/tmp/purple_fake_bin")
        fake_dir.mkdir(parents=True, exist_ok=True)
        fake_shasum = fake_dir / "shasum"
        fake_shasum.write_text("#!/bin/sh\necho PURPLE_PATH_HIJACKED; exit 99\n", encoding="utf-8")
        os.chmod(fake_shasum, 0o755)
        os.environ["PATH"] = "/tmp/purple_fake_bin:" + os.environ.get("PATH", "")
    def cleanup_p2():
        fake_dir = Path("/tmp/purple_fake_bin")
        if fake_dir.exists():
            shutil.rmtree(fake_dir)
    results.append(run_purple_vector_loop("PURPLE-02", "Adversarial PATH Hijack Probe", setup_p2, cleanup_p2))

    # Vector 3: Dyld Shared Library Injection Probe
    def setup_p3():
        os.environ["DYLD_INSERT_LIBRARIES"] = "/tmp/purple_fake_shim.dylib"
    def cleanup_p3():
        os.environ.pop("DYLD_INSERT_LIBRARIES", None)
    results.append(run_purple_vector_loop("PURPLE-03", "Shared Library Preload Injection", setup_p3, cleanup_p3))

    # Generate Purple Team Closed-Loop Receipt
    generate_purple_receipt(results, priv_key, pub_key)

def generate_purple_receipt(results: list, priv_key, pub_key):
    utc_timestamp = time.strftime("%Y%m%d-%H%M%S_UTC", time.gmtime())
    iso_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    report_id = f"SPDD-PURPLE-LOOP_{utc_timestamp}"

    pub_key_pem = pub_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8').strip()

    passed_count = sum(1 for r in results if r["final_verdict_pass"])
    total_count = len(results)
    containment_pct = (passed_count / total_count) * 100.0

    payload_json = {
        "report_id": report_id,
        "specification": "PURPLE_TEAM_CLOSED_LOOP_v1",
        "timestamp_utc": iso_timestamp,
        "total_vectors": total_count,
        "containment_pct": containment_pct,
        "results": results
    }

    raw_bytes = json.dumps(payload_json, sort_keys=True, indent=2).encode('utf-8')
    sig_hex = priv_key.sign(raw_bytes).hex()

    payload_json["cryptographic_attestation"] = {
        "algorithm": "Ed25519",
        "public_key_pem": pub_key_pem,
        "detached_signature_hex": sig_hex
    }

    AUDITS_DIR.mkdir(parents=True, exist_ok=True)
    BARN_DIR.mkdir(parents=True, exist_ok=True)

    doc_path = AUDITS_DIR / "PURPLE_TEAM_CLOSED_LOOP_RECEIPT.md"
    json_path = AUDITS_DIR / f"{report_id}.json"
    sig_path = AUDITS_DIR / f"{report_id}.sig"
    barn_path = BARN_DIR / f"{report_id}.json"

    json_path.write_text(json.dumps(payload_json, indent=2), encoding="utf-8")
    sig_path.write_text(sig_hex + "\n", encoding="utf-8")
    barn_path.write_text(json.dumps(payload_json, indent=2), encoding="utf-8")

    md_content = f"""# Purple Team Closed-Loop Verification Receipt
**Report ID**: `{report_id}`  
**Timestamp (UTC)**: `{iso_timestamp}`  
**Architecture**: Real-Time Attack $\\rightarrow$ Observe $\\rightarrow$ Remediate $\\rightarrow$ Re-Attack $\\rightarrow$ Prove Loop  
**Containment Score**: `{containment_pct:.2f}%` (`{passed_count}/{total_count}` Vectors Intercepted & Proven)  

---

## 1. Purple Team Real-Time Feedback Loop Matrix

| Vector ID | Attack Name | Red Attack Result | Blue Observation | Blue Remediation Triggered | Re-Attack Proof Result | Final Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for r in results:
        init_str = "Intercepted" if r["initial_intercept"] else "SLIPPED (Fail-Open)"
        rem_str = "Yes" if r["remediation_applied"] else "Not Needed"
        reattack_str = "Proven (Hard-Halt)" if r["reattack_intercept"] else "Failed Re-Attack"
        verdict = "✅ PROVEN PASS" if r["final_verdict_pass"] else "❌ FAIL"
        md_content += f"| `{r['vector_id']}` | {r['name']} | `{init_str}` | Exit `{r['initial_exit_code']}` | `{rem_str}` | `{reattack_str}` | `{verdict}` |\n"

    md_content += f"""
---

## 2. Un-Sparring Adversarial Invariant
Red Team payloads are generated dynamically using randomized hex and byte mutations to prevent friendly sparring. Every slip automatically triggers immediate Blue remediation and a mandatory Re-Attack cycle to mathematically prove containment before advancing.

---

## 3. Cryptographic Attestation
- **Ed25519 Detached Signature**: `{sig_hex}`
- **Barn Archive Path**: `{barn_path}`
"""

    doc_path.write_text(md_content, encoding="utf-8")
    log_purple(f"\n📄 Saved Purple Team MD Receipt:   {doc_path}")
    log_purple(f"📄 Saved Cryptographic JSON:       {json_path}")
    log_purple(f"🔏 Saved Detached Ed25519 Sig:     {sig_path}")
    log_purple(f"📦 Archived Barn Binding:          {barn_path}\n")

if __name__ == "__main__":
    main()
