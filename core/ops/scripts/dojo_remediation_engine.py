#!/usr/bin/env python3
"""
dojo_remediation_engine.py
XORAS::OS — Sovereign Automated Program Repair & Cryptographic Remediation Engine
Enforces MARS Constitutional boundaries, Compartmentalization-Aware Fault Localization,
Feedback-Driven Fuzzing-Based Validation, and POSIX-Locked Immutable Ledgers.
"""

import os
import sys
import json
import time
import sqlite3
import hashlib
import fcntl
import stat
from typing import Dict, Any, List, Tuple
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

# --- HARDENED ENVIRONMENT CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Navigate from core/ops/scripts up to repository root
WORKSPACE_ROOT = os.getenv("WORKSPACE_ROOT", os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..")))
CORE_DIR = os.path.join(WORKSPACE_ROOT, "core")
AGENTS_DIR = os.path.join(CORE_DIR, ".agents")
KEYS_DIR = os.path.join(AGENTS_DIR, "keys")
DB_PATH = os.path.join(AGENTS_DIR, "dojo_remediation.db")
AUDIT_LOG_PATH = os.path.join(AGENTS_DIR, "dojo_audit_ledger.log")
CHECKPOINT_PATH = os.path.join(AGENTS_DIR, "dojo_ledger_checkpoints.json")

os.makedirs(KEYS_DIR, exist_ok=True)

class DojoRemediationEngine:
    def __init__(self, master_public_key_path: str, allowed_keys: Dict[str, str]):
        """
        Initializes the Sovereign Security Broker and APR Engine.
        :param master_public_key_path: Path to the public key used to verify capability tokens.
        :param allowed_keys: Mapping of agent_id -> public_key_pem_path for validating action envelopes.
        """
        self.master_public_key_path = master_public_key_path
        self.allowed_keys = allowed_keys
        self.init_database()
        
    def init_database(self):
        """Initializes atomic, transaction-safe tables for single-use tokens, nonces, and sequence tracking."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Consumed Capability Tokens (Atomic Prevention of Double-Spend)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consumed_tokens (
                token_id TEXT PRIMARY KEY,
                consumed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Nonce Tracking (Replay Attack Prevention)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_nonces (
                nonce TEXT PRIMARY KEY,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Audit Ledger Metadata (Global Monotonic Sequence)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ledger_metadata (
                key TEXT PRIMARY KEY,
                val INTEGER NOT NULL
            )
        """)
        cursor.execute("INSERT OR IGNORE INTO ledger_metadata (key, val) VALUES ('next_sequence', 1)")
        
        conn.commit()
        conn.close()

    def get_next_sequence(self) -> int:
        """Atomically increments and retrieves the global monotonic sequence number."""
        conn = sqlite3.connect(DB_PATH)
        conn.execute("BEGIN IMMEDIATE TRANSACTION")
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT val FROM ledger_metadata WHERE key = 'next_sequence'")
            seq = cursor.fetchone()[0]
            cursor.execute("UPDATE ledger_metadata SET val = val + 1 WHERE key = 'next_sequence'")
            conn.commit()
            return seq
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def canonicalize(payload: Dict[str, Any]) -> bytes:
        """Enforces a strict deterministic JSON serialization (no whitespace, sorted keys)."""
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")

    # =========================================================================
    # 1. Zero-Trust Cryptographic Action Envelope Validation
    # =========================================================================
    def verify_envelope(self, envelope: Dict[str, Any], signature_hex: str) -> bool:
        """
        Validates the structure, temporals, nonces, and signature of the Action Envelope.
        Enforces absolute alignment with MARS security boundaries.
        """
        required_keys = {
            "action_id", "agent_id", "issued_at", "expires_at", 
            "nonce", "capability_id", "command", "normalized_args", "policy_version"
        }
        if not required_keys.issubset(envelope.keys()):
            raise ValueError("[SECURITY REJECTION] Action envelope is missing mandatory fields.")

        # Temporal validations
        now = int(time.time())
        if envelope["issued_at"] > now + 5:  # 5-second clock skew buffer
            raise ValueError("[SECURITY REJECTION] Action envelope issued in the future.")
        if now > envelope["expires_at"]:
            raise ValueError("[SECURITY REJECTION] Action envelope has expired.")

        # Replay Attack Prevention (Atomic Nonce Verification in isolated SQLite transaction)
        conn = sqlite3.connect(DB_PATH)
        conn.execute("BEGIN IMMEDIATE TRANSACTION")
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO processed_nonces (nonce) VALUES (?)", (envelope["nonce"],))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.rollback()
            raise ValueError(f"[SECURITY REJECTION] Replay attack detected. Nonce {envelope['nonce']} already processed.")
        finally:
            conn.close()

        # Cryptographic Signature Verification
        agent_id = envelope["agent_id"]
        if agent_id not in self.allowed_keys:
            raise ValueError(f"[SECURITY REJECTION] Unknown or unallowlisted agent identity: '{agent_id}'")
        
        pub_key_path = self.allowed_keys[agent_id]
        with open(pub_key_path, "rb") as f:
            pub_pem = f.read()
        public_key = serialization.load_pem_public_key(pub_pem)
        
        canonical_bytes = self.canonicalize(envelope)
        try:
            public_key.verify(bytes.fromhex(signature_hex), canonical_bytes)
        except InvalidSignature:
            raise ValueError("[SECURITY REJECTION] Cryptographic verification failed. Envelope signature mismatch.")
        
        return True

    # =========================================================================
    # 2. Cryptographic Capability Token & Double-Spend Gate
    # =========================================================================
    def verify_capability_token(self, token_payload: Dict[str, Any], token_sig_hex: str, action_envelope: Dict[str, Any]) -> bool:
        """
        Verifies the capability token's cryptographic validity, checks for single-use compliance,
        and enforces scope, subject, and action matching against the Action Envelope.
        """
        required_keys = {"token_id", "issuer", "subject_agent", "allowed_actions", "narrowed_resource_selectors", "expiry"}
        if not required_keys.issubset(token_payload.keys()):
            raise ValueError("[SECURITY REJECTION] Capability token is missing mandatory fields.")

        # Temporal validation
        now = int(time.time())
        if now > token_payload["expiry"]:
            raise ValueError("[SECURITY REJECTION] Capability token has expired.")

        # Subject alignment
        if token_payload["subject_agent"] != action_envelope["agent_id"]:
            raise ValueError("[SECURITY REJECTION] Token subject does not match envelope agent identity.")

        # Action validation
        if action_envelope["command"] not in token_payload["allowed_actions"]:
            raise ValueError(f"[SECURITY REJECTION] Command '{action_envelope['command']}' not authorized by capability token.")

        # Scope validation (Resource matching)
        resource_target = action_envelope["normalized_args"].get("target")
        if not resource_target:
            raise ValueError("[SECURITY REJECTION] Action envelope is missing target resource argument.")
            
        is_authorized_resource = False
        for selector in token_payload["narrowed_resource_selectors"]:
            if selector == "*" or resource_target == selector or resource_target.startswith(selector):
                is_authorized_resource = True
                break
        if not is_authorized_resource:
            raise ValueError(f"[SECURITY REJECTION] Resource target '{resource_target}' is outside token's resource selectors.")

        # Cryptographic Token Verification (Under master public key authority)
        with open(self.master_public_key_path, "rb") as f:
            master_pub_pem = f.read()
        master_pub_key = serialization.load_pem_public_key(master_pub_pem)
        
        canonical_token = self.canonicalize(token_payload)
        try:
            master_pub_key.verify(bytes.fromhex(token_sig_hex), canonical_token)
        except InvalidSignature:
            raise ValueError("[SECURITY REJECTION] Capability token signature mismatch against Master Authority.")

        # Single-Use Enforcement (Atomic double-spend check PRIOR to dispatch)
        conn = sqlite3.connect(DB_PATH)
        conn.execute("BEGIN IMMEDIATE TRANSACTION")
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO consumed_tokens (token_id) VALUES (?)", (token_payload["token_id"],))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.rollback()
            raise ValueError(f"[SECURITY REJECTION] Capability Token '{token_payload['token_id']}' is single-use and has already been consumed.")
        finally:
            conn.close()

        return True

    # =========================================================================
    # 3. Compartmentalization-Aware Fault Localization (APR)
    # =========================================================================
    def locate_optimal_patching_site(self, crash_stack: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Implements the formal Crash Stack Function Classification to isolate the optimal patching target.
        Classifies stack frames into CONSUME, FORWARD, PRESENCE, or COMMIT.
        Selects the earliest trusted function available for modification (having source code) that interprets the variable.
        """
        boundary_candidates = []
        
        for frame in crash_stack:
            frame_id = frame.get("frame_id")
            function_name = frame.get("function_name")
            has_source = frame.get("has_source", False)
            in_sandbox = frame.get("is_sandbox", False)
            variable_in_scope = frame.get("has_variable", False)
            interaction = frame.get("interaction_type") # "CONSUME", "FORWARD", "PRESENCE", "COMMIT"
            
            # Sandbox compartment boundary verification
            if in_sandbox:
                continue # BANNED: The trust model dictates we never patch inside the untrusted sandbox!
                
            if variable_in_scope:
                boundary_candidates.append({
                    "frame_id": frame_id,
                    "function_name": function_name,
                    "has_source": has_source,
                    "interaction": interaction
                })
        
        if not boundary_candidates:
            raise ValueError("[APR FAILURE] No valid boundary candidates found in trusted scope.")
            
        # Priority mapping: CONSUME > FORWARD > PRESENCE
        # If the direct consumer lacks source code (e.g. library function), trace up to the last FORWARD function that does.
        consume_candidate = next((c for c in boundary_candidates if c["interaction"] == "CONSUME"), None)
        if consume_candidate and consume_candidate["has_source"]:
            return consume_candidate
            
        # If CONSUME is a library function or unmodifiable, find the nearest FORWARD frame that has source code
        forward_candidates = [c for c in boundary_candidates if c["interaction"] == "FORWARD" and c["has_source"]]
        if forward_candidates:
            # Sort by frame id ascending to find the latest frame in call execution sequence
            forward_candidates.sort(key=lambda x: x["frame_id"])
            return forward_candidates[0]
            
        presence_candidates = [c for c in boundary_candidates if c["interaction"] == "PRESENCE" and c["has_source"]]
        if presence_candidates:
            presence_candidates.sort(key=lambda x: x["frame_id"])
            return presence_candidates[0]
            
        raise ValueError("[APR FAILURE] All candidate frames are unmodifiable or external library functions.")

    # =========================================================================
    # 4. Type-Centric CIV Classification
    # =========================================================================
    def analyze_vulnerability_remediation(self, civ_type: str, variable_details: Dict[str, Any]) -> str:
        """
        Classifies CIV (Compartment Interface Vulnerabilities) type-centrically and applies 
        strict defensive verification criteria (e.g., is_pointer_mapped, is_in_domain limits).
        """
        if civ_type == "POINTER":
            # Pointer type check
            pointer_var = variable_details.get("name")
            struct_type = variable_details.get("struct_type", "void")
            return (
                f"// Enforcing MARS Pointer-Legality Oracle Check\n"
                f"int {pointer_var}_mapped = is_pointer_mapped((const void *){pointer_var}, sizeof({struct_type}));\n"
                f"if (!{pointer_var}_mapped) {{\n"
                f"    return -1; // Containment mitigation active. Drop execution.\n"
                f"}}"
            )
        elif civ_type == "SCALAR":
            # Scalar value range checks
            scalar_var = variable_details.get("name")
            min_val = variable_details.get("min_value", 0)
            max_val = variable_details.get("max_value", 255)
            return (
                f"// Enforcing MARS Scalar-Domain Oracle Check\n"
                f"if ({scalar_var} < {min_val} || {scalar_var} > {max_val}) {{\n"
                f"    return -1; // Boundary out of bounds. Reject input.\n"
                f"}}"
            )
        elif civ_type == "STRUCTURED_PAYLOAD":
            # Nested table/pointer check
            base_var = variable_details.get("name")
            field = variable_details.get("field")
            expected_type = variable_details.get("field_type")
            return (
                f"// Enforcing MARS Structured Payload Check\n"
                f"if ({base_var} == NULL || !is_pointer_mapped((const void *){base_var}->{field}, sizeof({expected_type}))) {{\n"
                f"    return -1; // Nested structure corrupted. Interdicting.\n"
                f"}}"
            )
        else:
            return "// Standard defensive check\nif (table == NULL) return -1;"

    # =========================================================================
    # 5. Robust POSIX-Locked Append-Only Audit Ledger
    # =========================================================================
    def write_audit_ledger(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enforces a hardened, append-only audit trail with POSIX advisory file locking,
        sequence numbers, and strict structure validation.
        """
        seq_num = self.get_next_sequence()
        record_with_meta = {
            "sequence": seq_num,
            "timestamp": int(time.time()),
            "audit_payload": record
        }
        
        canonical_record = self.canonicalize(record_with_meta)
        
        # Advisory File Locking to prevent concurrent file corruption
        with open(AUDIT_LOG_PATH, "a") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.write(canonical_record.decode("utf-8") + "\n")
                f.flush()
                os.fsync(f.fileno())  # Force write to physical storage
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                
        return record_with_meta

    def generate_checkpoint(self, checkpoint_signer_priv_key_path: str):
        """
        Periodically computes a SHA-256 hash of the audit ledger up to the current sequence,
        signs the hash using an Ed25519 private key, and stores the checkpoint separately.
        """
        if not os.path.exists(AUDIT_LOG_PATH):
            return
            
        with open(AUDIT_LOG_PATH, "rb") as f:
            log_data = f.read()
            
        ledger_hash = hashlib.sha256(log_data).hexdigest()
        
        # Sign the checkpoint hash
        with open(checkpoint_signer_priv_key_path, "rb") as f:
            priv_pem = f.read()
        priv_key = serialization.load_pem_private_key(priv_pem, password=None)
        
        signature = priv_key.sign(ledger_hash.encode("utf-8"))
        
        checkpoint = {
            "timestamp": int(time.time()),
            "ledger_sha256": ledger_hash,
            "checkpoint_signature": signature.hex()
        }
        
        with open(CHECKPOINT_PATH, "w") as f:
            json.dump(checkpoint, f, indent=2)

class ControlledEffectDispatcher:
    def __init__(self):
        """Allowlisted Effect Handlers Registry (No arbitrary commands allowed)."""
        self._handlers = {}

    def register_handler(self, command: str, handler_func):
        self._handlers[command] = handler_func

    def dispatch(self, command: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if command not in self._handlers:
            raise ValueError(f"[DISPATCH REJECTION] Unallowlisted command '{command}'. Rejected at gateway.")
        
        return self._handlers[command](args)
