"""
3D Tri-Brain Container Topology:
Container 1: Systems & Kernel Engineering (Maxx, Daxx) -> Catch 1
Container 2: Scientific Research & Physics / Formal Methods (Clara, Selene) -> Catch 2
Container 3: Sovereign Security, Falsification & Law (William Vance, John) -> Catch 3

Filtered by: 7th Layer Guard Membrane (Zero noise up, zero corruption down)
Synthesized by: Apex Council (Jarvis) into the 768-Vectored Holographic Memory Fabric
"""

import os
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional

from memory.tri_brain.manifold_12d import Dimension12Manifold
from memory.tri_brain.seventh_layer_guard import SeventhLayerGuard

TRI_BRAIN_ROOT = Path(__file__).resolve().parent

class TriBrainCluster:
    def __init__(self):
        self.manifold = Dimension12Manifold()
        self.guard = SeventhLayerGuard()
        self.containers = {
            1: {
                "name": "Kernel & Systems Engineering",
                "agents": ["Maxx", "Daxx"],
                "catch_file": TRI_BRAIN_ROOT / "container_1" / "CATCH_01.jsonl",
                "domain": "systems_kernel_remediation"
            },
            2: {
                "name": "Scientific Validation & Trajectory",
                "agents": ["Clara", "Selene"],
                "catch_file": TRI_BRAIN_ROOT / "container_2" / "CATCH_02.jsonl",
                "domain": "formal_methods_physics_narrative"
            },
            3: {
                "name": "Falsification & Secured Assurance",
                "agents": ["William Vance", "John"],
                "catch_file": TRI_BRAIN_ROOT / "container_3" / "CATCH_03.jsonl",
                "domain": "security_audit_adversarial_test"
            }
        }
        self.apex_catch_file = TRI_BRAIN_ROOT / "apex_synthesis" / "MASTER_CATCH.jsonl"
        self._init_storage()

    def _init_storage(self):
        for cid, meta in self.containers.items():
            meta["catch_file"].parent.mkdir(parents=True, exist_ok=True)
            if not meta["catch_file"].exists():
                with open(meta["catch_file"], "w", encoding="utf-8") as f:
                    pass
        self.apex_catch_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.apex_catch_file.exists():
            with open(self.apex_catch_file, "w", encoding="utf-8") as f:
                pass

    def emit_container_event(self, container_id: int, agent: str, claim: str, receipt: Dict[str, Any]) -> Dict[str, Any]:
        """Emits an event from one of the 3 isolated Tri-Brain containers."""
        if container_id not in self.containers:
            raise ValueError(f"Invalid Container ID: {container_id}")

        meta = self.containers[container_id]
        payload = {
            "container_id": container_id,
            "source_agent": agent,
            "domain": meta["domain"],
            "claim": claim,
            "receipt": receipt,
            "timestamp": time.time(),
            "sha256": hashlib.sha256(f"{agent}:{claim}:{time.time()}".encode()).hexdigest()[:16]
        }

        # 1. Append locally to Container's isolated Catch Log (Never shared sideways)
        with open(meta["catch_file"], "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")

        # 2. Filter through 7th-Layer Guard before rolling UP to Apex
        passed, msg = self.guard.screen_roll_up(container_id, payload)
        if not passed:
            return {"status": "BLOCKED_BY_7TH_LAYER", "reason": msg, "container_id": container_id}

        # 3. Project 24-dimensional raw signals into 12D Manifold
        raw_signals = [float(ord(c) % 10) for c in payload["sha256"]] + [container_id, time.time() % 100]
        self.manifold.project_24_to_12(raw_signals, target_layer=container_id)

        # 4. Synthesize into Apex Master Catch Log
        with open(self.apex_catch_file, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "apex_received": time.time(),
                "from_container": container_id,
                "verified_by_guard": True,
                "payload": payload,
                "merkle_root": self.manifold.merkle_root
            }) + "\n")

        return {
            "status": "ASSIMILATED",
            "container_id": container_id,
            "guard_receipt": msg,
            "merkle_root": self.manifold.merkle_root
        }

    def get_cluster_status(self) -> Dict[str, Any]:
        counts = {}
        for cid, meta in self.containers.items():
            if meta["catch_file"].exists():
                with open(meta["catch_file"], "r", encoding="utf-8") as f:
                    counts[f"container_{cid}"] = len(f.readlines())
            else:
                counts[f"container_{cid}"] = 0

        apex_count = 0
        if self.apex_catch_file.exists():
            with open(self.apex_catch_file, "r", encoding="utf-8") as f:
                apex_count = len(f.readlines())

        return {
            "architecture": "3D Tri-Brain 24-12-7-3-1 Pyramid",
            "containers": counts,
            "apex_events": apex_count,
            "guard_metrics": self.guard.get_metrics(),
            "manifold_12d": self.manifold.get_state()
        }

if __name__ == "__main__":
    cluster = TriBrainCluster()
    print("Initializing 3D Tri-Brain Verification Run...")
    res1 = cluster.emit_container_event(1, "Maxx", "Kernel memory refactored and aligned to 3,200 bytes", {"exit_code": 0, "verified": True})
    res2 = cluster.emit_container_event(2, "Clara", "Orbital trajectory Lyapunov stability proven delta V <= 0", {"theorem": "MTPO-2", "verified": True})
    res3 = cluster.emit_container_event(3, "William Vance", "AST and SAST mechanical gates falsified 500 edge cases with zero breach", {"falsified": True, "passed": 500})
    print("Cluster status:")
    print(json.dumps(cluster.get_cluster_status(), indent=2))
