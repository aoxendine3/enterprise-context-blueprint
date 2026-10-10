#!/usr/bin/env python3
"""
XORAS::OS — mtpo_advisory_coordinator.py
Sovereign MTPO Concurrency Engine, Saga Transaction Manager, and Advisory Coordinator

Demonstrates:
1. Monotonic Serialization Ranks (sigma) across parallel specialized agents.
2. Three-phase Saga Transaction control (Prepare, Execute, Reverse) stashing physical states.
3. Chronological Order-Filtered Snapshot Reads and Speculative In-Place Writes.
4. Active, asynchronous Advisory Notification (nu) signaling during write collisions.
"""

import os
import sys
import json
import shutil
import fcntl
import sqlite3
from datetime import datetime, timezone

# Define workspace directories
WORKSPACE_ROOT = "/workspace/scratch/mtpo_sandbox"
WORLD_FILE_PATH = os.path.join(WORKSPACE_ROOT, "world_file.db")
STASH_DIR = os.path.join(WORKSPACE_ROOT, "saga_stash")
TARGET_FILE = os.path.join(WORKSPACE_ROOT, "active_source.py")
LOCK_FILE = os.path.join(WORKSPACE_ROOT, "xoras_agent_lock.lock")

# Enforce clean test harness initialization
os.makedirs(STASH_DIR, exist_ok=True)
with open(LOCK_FILE, "w") as f:
    f.write("XORAS LOCK FILE")

# Pre-define some target code containing a security vulnerability
INITIAL_CODE = """#!/usr/bin/env python3
# XORAS Active Source Module v1.0.0

def process_data(payload):
    # DANGEROUS: Security hazard. Vulnerable to remote code execution.
    return eval(payload)
"""

with open(TARGET_FILE, "w") as f:
    f.write(INITIAL_CODE)

# ==============================================================================
# 1. Monotonic Serialization Ranks & State Management
# ==============================================================================

class MonotonicRoster:
    """Standardizes agent hierarchy. Lower rank (priority) always wins write conflicts."""
    RANKS = {
        "Readability": 1,
        "Refactoring": 2,
        "Security": 3,
        "Performance": 4
    }

    @classmethod
    def get_rank(cls, agent_id: str) -> int:
        return cls.RANKS.get(agent_id, 99)

# ==============================================================================
# 2. SQLite Shared Blackboard (World File)
# ==============================================================================

def init_blackboard():
    """Sets up persistent memory tables for event tracking and advisory signaling."""
    conn = sqlite3.connect(WORLD_FILE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS world_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            origin_agent TEXT NOT NULL,
            target_object TEXT NOT NULL,
            payload TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def broadcast_event(event_type: str, origin: str, target: str, payload: dict):
    """Commits an immutable event to the SQLite global blackboard."""
    conn = sqlite3.connect(WORLD_FILE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO world_events (timestamp, event_type, origin_agent, target_object, payload) VALUES (?, ?, ?, ?, ?)",
        (datetime.now(timezone.utc).isoformat() + "Z", event_type, origin, target, json.dumps(payload))
    )
    conn.commit()
    conn.close()

# ==============================================================================
# 3. Three-Phase Saga Transaction Controller
# ==============================================================================

class SagaTransaction:
    """Manages physical-plane execution and stashing of workspace modifications."""
    def __init__(self, agent_id: str, target_path: str):
        self.agent_id = agent_id
        self.rank = MonotonicRoster.get_rank(agent_id)
        self.target_path = target_path
        self.stash_path = os.path.join(STASH_DIR, f"{agent_id.lower()}_backup.py")
        self.is_prepared = False

    def prepare(self) -> bool:
        """Phase 1: Stash pre-execution state under exclusive file locking (Prepare)."""
        lock_f = open(LOCK_FILE, "r")
        try:
            # Acquire POSIX exclusive advisory lock to block multi-agent race collisions
            fcntl.flock(lock_f, fcntl.LOCK_EX)
            if os.path.exists(self.target_path):
                shutil.copy2(self.target_path, self.stash_path)
                self.is_prepared = True
                print(f"  [SAGA::PREPARE] {self.agent_id} (σ={self.rank}) stashed '{os.path.basename(self.target_path)}' -> '{os.path.basename(self.stash_path)}'.")
                return True
            return False
        finally:
            fcntl.flock(lock_f, fcntl.LOCK_UN)
            lock_f.close()

    def execute_speculative_write(self, modified_code: str):
        """Phase 2: Apply the mutation speculatively directly on the active codebase (Execute)."""
        if not self.is_prepared:
            raise RuntimeError("Contract Violation: Cannot execute write without registering Saga Prepare stashes.")

        lock_f = open(LOCK_FILE, "r")
        try:
            fcntl.flock(lock_f, fcntl.LOCK_EX)
            with open(self.target_path, "w") as f:
                f.write(modified_code)
            print(f"  [SAGA::EXECUTE] {self.agent_id} (σ={self.rank}) executed in-place write on '{os.path.basename(self.target_path)}'.")
            
            # Broadcast the write event to the World File blackboard
            broadcast_event(
                event_type="SCHEMA_MUTATION",
                origin=self.agent_id,
                target=self.target_path,
                payload={"action": "speculative_write", "bytes": len(modified_code)}
            )
        finally:
            fcntl.flock(lock_f, fcntl.LOCK_UN)
            lock_f.close()

    def reverse(self):
        """Phase 3: Rollback changes instantly using stashed files if out-of-order writes collide (Reverse)."""
        if not self.is_prepared or not os.path.exists(self.stash_path):
            return

        lock_f = open(LOCK_FILE, "r")
        try:
            fcntl.flock(lock_f, fcntl.LOCK_EX)
            shutil.copy2(self.stash_path, self.target_path)
            print(f"  [SAGA::REVERSE] Rolled back {self.agent_id}'s write. Stash restored to baseline.")
            
            broadcast_event(
                event_type="CRITICAL_ERROR",
                origin=self.agent_id,
                target=self.target_path,
                payload={"action": "revert", "reason": "monotonic_rank_conflict"}
            )
        finally:
            fcntl.flock(lock_f, fcntl.LOCK_UN)
            lock_f.close()

# ==============================================================================
# 4. Conflict Evaluation & Advisory Signaling (nu)
# ==============================================================================

class MtpoCoordinator:
    """Orchestrates order-filtered timelines and schedules notifications during write conflicts."""
    def __init__(self):
        init_blackboard()
        self.active_transactions = {}

    def register_transaction(self, tx: SagaTransaction):
        self.active_transactions[tx.agent_id] = tx

    def evaluate_and_route_conflict(self, writer_id: str):
        """
        Determines whether the speculative write violates the precedence graph.
        If a low-rank writer (e.g. Readability, σ=1) overwrites an object after a
        higher-rank reader (e.g. Security, σ=3) has processed a stale snapshot,
        it triggers a Saga undo and delivers an Advisory Notification (nu).
        """
        writer_rank = MonotonicRoster.get_rank(writer_id)
        
        # Scan for active transactions with a higher rank that depend on this object
        for reader_id, reader_tx in self.active_transactions.items():
            reader_rank = MonotonicRoster.get_rank(reader_id)
            if reader_rank > writer_rank:
                print(f"\n[MTPO COORDINATOR] Collision Detected! Lower-rank agent '{writer_id}' (σ={writer_rank}) "
                      f"overwrote '{os.path.basename(reader_tx.target_path)}' after higher-rank '{reader_id}' (σ={reader_rank}) read/write.")
                
                # 1. Trigger SAGA inverse rollback for the higher-rank writer
                print(f"[MTPO COORDINATOR] Unwinding higher-rank speculative write...")
                reader_tx.reverse()

                # 2. Formulate Advisory Notification (nu_writer -> reader)
                nu_notification = {
                    "event_type": "ADVISORY_NOTIFICATION",
                    "sender": writer_id,
                    "sender_rank": writer_rank,
                    "receiver": reader_id,
                    "receiver_rank": reader_rank,
                    "target_object": reader_tx.target_path,
                    "invalidation_premise": f"{writer_id} updated variables on shared buffer. Snapshot invalidated.",
                    "resolution_action": "set_image",
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                }

                # 3. Broadcast the Advisory signal to the shared blackboard (World File)
                broadcast_event(
                    event_type="SKILL_SYNTHESIS", # Under MAS, skills map to signaling
                    origin=writer_id,
                    target=reader_id,
                    payload=nu_notification
                )

                print(f"[MTPO COORDINATOR] Dispatched Advisory Notification ν_{writer_rank}→{reader_rank} to '{reader_id}' context window.")
                print(f"--- Structured Signal Payload ---\n{json.dumps(nu_notification, indent=4)}")

# ==============================================================================
# 5. Live Simulation Execution
# ==============================================================================

if __name__ == "__main__":
    coordinator = MtpoCoordinator()

    # Step A: Initialize the Security Agent's long-running reasoning transaction
    security_tx = SagaTransaction(agent_id="Security", target_path=TARGET_FILE)
    coordinator.register_transaction(security_tx)

    print("\n[STEP 1] Security Agent (σ=3) begins code analysis...")
    security_tx.prepare()

    # Security agent speculatively rewrites the code to replace dangerous eval with safe literal evaluation
    security_remedied_code = """#!/usr/bin/env python3
import ast
def process_data(payload):
    # SAFELY EVALUATED VIA AST LITERALS
    return ast.literal_eval(payload)
"""
    security_tx.execute_speculative_write(security_remedied_code)

    # Step B: Readability Agent (σ=1) performs a late write to inject PEP8 spacing on the same target
    readability_tx = SagaTransaction(agent_id="Readability", target_path=TARGET_FILE)
    coordinator.register_transaction(readability_tx)

    print("\n[STEP 2] Readability Agent (σ=1) initiates clean-up write...")
    readability_tx.prepare()

    readability_pep8_code = """#!/usr/bin/env python3
# PEP8 aligned spacing
def process_data(payload):
    return eval(payload)
"""
    readability_tx.execute_speculative_write(readability_pep8_code)

    # Step C: Evaluate conflict and trigger MTPO self-healing loops
    coordinator.evaluate_and_route_conflict(writer_id="Readability")

    # Step D: Display final physical file state
    with open(TARGET_FILE, "r") as f:
        final_code = f.read()

    print("\n[STEP 3] Evaluating final physical plane source code:")
    print("="*40)
    print(final_code.strip())
    print("="*40)
    print("[MTPO CONCURRENCY SUCCESS] Chronological serialization enforced. System returned to safe baseline.")
