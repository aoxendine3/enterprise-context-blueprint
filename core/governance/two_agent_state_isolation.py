"""
Two-Agent Explicit Proposal & Commit Concurrency Harness
=========================================================
Implements the exact 3-step mandate:
1. Give every shared key an owner agent; other agents may propose changes but only the owner commits them.
2. Add a version number to each write and reject writes based on a stale version (CAS) instead of overwriting.
3. Run two agents against the same key in parallel 20 times and count lost updates in the ledger — target: ZERO.
"""

import os
import json
import time
import threading
from typing import Dict, Any, List, Optional, Tuple

class GovernedSharedStateManager:
    def __init__(self, ledger_file: str):
        self.ledger_file = ledger_file
        os.makedirs(os.path.dirname(self.ledger_file), exist_ok=True)
        self._lock = threading.Lock()
        # key -> { 'value': any, 'version': int, 'owner': str, 'pending_proposals': list }
        self._state: Dict[str, Dict[str, Any]] = {}
        # Append-only write ledger
        self.ledger_records: List[Dict[str, Any]] = []

    def register_key(self, key: str, owner: str, initial_value: Any):
        """Step 1: Every key gets an explicit owner agent."""
        with self._lock:
            self._state[key] = {
                "value": initial_value,
                "version": 1,
                "owner": owner,
                "pending_proposals": []
            }
            self._append_ledger(
                event="KEY_REGISTERED",
                key=key,
                agent=owner,
                prior_version=0,
                new_version=1,
                status="INITIALIZED",
                detail=f"Key registered with owner '{owner}'"
            )

    def propose_change(self, key: str, proposer: str, delta: Any, base_version: int) -> int:
        """Non-owners (or any agent) submit proposals based on a base_version."""
        with self._lock:
            if key not in self._state:
                raise KeyError(f"Key {key} not found")
            proposal_id = len(self._state[key]["pending_proposals"]) + 1
            proposal = {
                "id": proposal_id,
                "proposer": proposer,
                "delta": delta,
                "base_version": base_version,
                "timestamp": time.time()
            }
            self._state[key]["pending_proposals"].append(proposal)
            self._append_ledger(
                event="PROPOSAL_SUBMITTED",
                key=key,
                agent=proposer,
                prior_version=base_version,
                new_version=base_version,
                status="PENDING",
                detail=f"Proposal #{proposal_id} by {proposer}"
            )
            return proposal_id

    def commit_direct(self, key: str, agent: str, new_value: Any, expected_version: int) -> Tuple[bool, int, str]:
        """
        Direct write attempt.
        Step 1: ONLY the owner can commit.
        Step 2: Version number checked (CAS). Rejects stale version instead of overwriting.
        """
        with self._lock:
            if key not in self._state:
                return False, 0, "KEY_NOT_FOUND"

            entry = self._state[key]

            # Step 1: Judge-Gate (Single Writer / Owner Verification)
            if entry["owner"] != agent:
                self._append_ledger(
                    event="WRITE_ATTEMPT",
                    key=key,
                    agent=agent,
                    prior_version=expected_version,
                    new_version=entry["version"],
                    status="REJECTED_UNAUTHORIZED",
                    detail=f"Judge-Gate: Agent '{agent}' is not owner '{entry['owner']}'"
                )
                return False, entry["version"], "JUDGE_GATE_REJECT: Not key owner"

            # Step 2: Witness-Gate (Version CAS Check)
            if entry["version"] != expected_version:
                self._append_ledger(
                    event="WRITE_ATTEMPT",
                    key=key,
                    agent=agent,
                    prior_version=expected_version,
                    new_version=entry["version"],
                    status="REJECTED_STALE_VERSION",
                    detail=f"Witness-Gate: Expected v{expected_version}, current is v{entry['version']}"
                )
                return False, entry["version"], "WITNESS_GATE_REJECT: Stale version"

            # Commit Successful
            new_version = entry["version"] + 1
            entry["value"] = new_value
            entry["version"] = new_version
            self._append_ledger(
                event="WRITE_COMMIT",
                key=key,
                agent=agent,
                prior_version=expected_version,
                new_version=new_version,
                status="COMMITTED",
                detail=f"Owner '{agent}' committed v{new_version}"
            )
            return True, new_version, "SUCCESS"

    def owner_review_and_commit_proposal(self, key: str, owner_agent: str, proposal_id: int) -> Tuple[bool, int, str]:
        """Step 1 & 2: Owner reviews proposal and commits with CAS."""
        with self._lock:
            entry = self._state[key]
            if entry["owner"] != owner_agent:
                return False, entry["version"], "JUDGE_GATE_REJECT: Not key owner"

            # Find proposal
            proposal = next((p for p in entry["pending_proposals"] if p["id"] == proposal_id), None)
            if not proposal:
                return False, entry["version"], "PROPOSAL_NOT_FOUND"

            # CAS check on proposal's base version
            if proposal["base_version"] != entry["version"]:
                self._append_ledger(
                    event="PROPOSAL_COMMIT_ATTEMPT",
                    key=key,
                    agent=owner_agent,
                    prior_version=proposal["base_version"],
                    new_version=entry["version"],
                    status="REJECTED_STALE_PROPOSAL",
                    detail=f"Proposal based on v{proposal['base_version']} is stale (current v{entry['version']})"
                )
                return False, entry["version"], "STALE_PROPOSAL"

            # Apply Delta
            new_version = entry["version"] + 1
            if isinstance(entry["value"], int) and isinstance(proposal["delta"], int):
                entry["value"] += proposal["delta"]
            else:
                entry["value"] = proposal["delta"]

            entry["version"] = new_version
            entry["pending_proposals"].remove(proposal)

            self._append_ledger(
                event="PROPOSAL_COMMITTED",
                key=key,
                agent=owner_agent,
                prior_version=proposal["base_version"],
                new_version=new_version,
                status="COMMITTED",
                detail=f"Owner '{owner_agent}' committed proposal #{proposal_id} from {proposal['proposer']}"
            )
            return True, new_version, "SUCCESS"

    def read_state(self, key: str) -> Tuple[Any, int, str]:
        with self._lock:
            e = self._state[key]
            return e["value"], e["version"], e["owner"]

    def _append_ledger(self, event: str, key: str, agent: str, prior_version: int, new_version: int, status: str, detail: str):
        record = {
            "record_id": len(self.ledger_records) + 1,
            "timestamp": time.time(),
            "event": event,
            "key": key,
            "agent": agent,
            "prior_version": prior_version,
            "new_version": new_version,
            "status": status,
            "detail": detail
        }
        self.ledger_records.append(record)
        with open(self.ledger_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
