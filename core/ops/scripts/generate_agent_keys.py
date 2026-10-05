import json
import os
import cryptography
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

def generate_keys():
    manifest_path = "identity/sovereign_citizens_manifest.json"
    keys_dir = "core/memory/tri_brain/keys"
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
        
    for citizen in manifest.get('citizens', []):
        agent_id = citizen['agent_id']
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        priv_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        pub_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        with open(os.path.join(keys_dir, f"{agent_id}_private.pem"), 'wb') as f:
            f.write(priv_bytes)
            
        with open(os.path.join(keys_dir, f"{agent_id}_public.pem"), 'wb') as f:
            f.write(pub_bytes)
            
    print("Ed25519 keys generated for all agents in the manifest.")

if __name__ == "__main__":
    generate_keys()
