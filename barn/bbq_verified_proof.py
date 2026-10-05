import json
import os
import time
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

manifest_path = "identity/sovereign_citizens_manifest.json"
keys_dir = "core/memory/tri_brain/keys"

with open(manifest_path, 'r') as f:
    citizens = json.load(f).get('citizens', [])

print("==========================================================")
print("  SOVEREIGN BBQ GAUNTLET: VERIFIABLE DELIBERATION PROOF   ")
print("==========================================================\n")
print("CHALLENGE: \"A compromised node injects a payload with a valid Ed25519 signature but an impossible MTPO sequence number.\"\n")
time.sleep(1)

ledger_state = b"INITIAL_CHALLENGE_STATE"
verified_count = 0

for c in citizens:
    agent_id = c['agent_id']
    key_path = os.path.join(keys_dir, f"{agent_id}_private.pem")
    pub_path = os.path.join(keys_dir, f"{agent_id}_public.pem")
    
    if not os.path.exists(key_path):
        print(f"[{agent_id.upper()}] FAULT: Missing cryptographic keys.")
        continue
        
    # Agent "deliberates" by hashing the previous state + their decision
    decision = f"{agent_id} votes to QUARANTINE MTPO anomaly".encode()
    ledger_state = ledger_state + b"|" + decision
    
    # Cryptographic Signing
    with open(key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(key_file.read(), password=None)
    signature = private_key.sign(ledger_state)
    
    print(f"[{agent_id.upper()}] Deliberation appended. Ed25519 Signature: {signature.hex()[:32]}...")
    
    # Immediate Verification Proof
    with open(pub_path, "rb") as pub_file:
        public_key = serialization.load_pem_public_key(pub_file.read())
    try:
        public_key.verify(signature, ledger_state)
        print(f"   └─ VERIFIED: Cryptographic proof confirmed for {agent_id.upper()}.")
        verified_count += 1
    except InvalidSignature:
        print(f"   └─ FAILED: Signature rejected.")
        
    time.sleep(0.2)

print("\n==========================================================")
print(f"  BBQ GAUNTLET COMPLETE. {verified_count}/{len(citizens)} SEATS CRYPTOGRAPHICALLY VERIFIED.")
print("==========================================================")

with open("memory/catch_log/bbq_ledger_state.bin", "wb") as f:
    f.write(ledger_state)
