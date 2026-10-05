import json
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

class CouncilRuntime:
    def __init__(self):
        self.manifest_path = "identity/sovereign_citizens_manifest.json"
        self.keys_dir = "core/memory/tri_brain/keys"
        self.citizens = self.load_citizens()
        
    def load_citizens(self):
        with open(self.manifest_path, 'r') as f:
            return json.load(f).get('citizens', [])
            
    def execute_and_sign(self, citizen, payload_bytes):
        agent_id = citizen['agent_id']
        key_path = os.path.join(self.keys_dir, f"{agent_id}_private.pem")
        pub_path = os.path.join(self.keys_dir, f"{agent_id}_public.pem")
        
        if not os.path.exists(key_path):
            return f"[{agent_id}] FAULT: No signing key."
            
        with open(key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(), password=None
            )
            
        # Real cryptographic signature
        signature = private_key.sign(payload_bytes)
        
        # Verify the signature to prove the pipeline works
        with open(pub_path, "rb") as pub_file:
            public_key = serialization.load_pem_public_key(pub_file.read())
            
        try:
            public_key.verify(signature, payload_bytes)
            sig_hex = signature.hex()[:16]
            return f"[{agent_id}] Verified Signature: {sig_hex}..."
        except InvalidSignature:
            return f"[{agent_id}] FAULT: Invalid Signature."

    def run_pressure_test(self, iterations=100):
        print(f"Running {iterations} concurrent cryptographic signatures across {len(self.citizens)} agents...")
        start_time = time.time()
        
        tasks = []
        for i in range(iterations):
            payload = f"Block_{i}_Payload".encode('utf-8')
            for c in self.citizens:
                tasks.append((c, payload))
                
        success_count = 0
        with ThreadPoolExecutor(max_workers=44) as executor:
            futures = [executor.submit(self.execute_and_sign, c, p) for c, p in tasks]
            for future in futures:
                res = future.result()
                if "Verified" in res:
                    success_count += 1
                    
        elapsed = time.time() - start_time
        print(f"Completed {success_count} valid cryptographic signatures in {elapsed:.4f} seconds.")

if __name__ == "__main__":
    runtime = CouncilRuntime()
    runtime.run_pressure_test(iterations=100)
