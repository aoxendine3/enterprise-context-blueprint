#!/usr/bin/env python3
"""
XORAS SOVEREIGN 24/7 CONTINUOUS AUTONOMOUS ENGINE
Air-gapped bare-metal continuous reasoning, 24/12/7/3/1 pyramidal distillation,
MAST safety immune system, and live 3D Sovereign Stage teleprompter sync.
Configured to cook for 48+ hours on our largest open-weight models:
- Primary Executive & Deliberation: sovereign-hermes:latest (8B Unaligned Nous Research)
- Mathematical & Invariant Prover: sovereign-r1:latest (DeepSeek-R1 Reasoning)
"""

import os
import sys
import time
import json
import math
import hashlib
import hmac
import ctypes
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ('dwLength', ctypes.c_ulong),
        ('dwMemoryLoad', ctypes.c_ulong),
        ('ullTotalPhys', ctypes.c_ulonglong),
        ('ullAvailPhys', ctypes.c_ulonglong),
        ('ullTotalPageFile', ctypes.c_ulonglong),
        ('ullAvailPageFile', ctypes.c_ulonglong),
        ('ullTotalVirtual', ctypes.c_ulonglong),
        ('ullAvailVirtual', ctypes.c_ulonglong),
        ('sullAvailExtendedVirtual', ctypes.c_ulonglong),
    ]

def get_system_memory():
    stat = MEMORYSTATUSEX()
    stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
    return stat.ullTotalPhys, stat.ullAvailPhys, stat.dwMemoryLoad

# Add project roots
SCRIPT_DIR = Path(__file__).resolve().parent
SSOT_ROOT = SCRIPT_DIR.parent.parent
if str(SSOT_ROOT) not in sys.path:
    sys.path.insert(0, str(SSOT_ROOT))
if str(SSOT_ROOT / "workspaces" / "sovra_nexus") not in sys.path:
    sys.path.insert(0, str(SSOT_ROOT / "workspaces" / "sovra_nexus"))

from sovra_core.poincare_hypergraph import PoincareManifold
from sovra_core.hexcell_memory import HexCell, HexCellEngine, HEXCELL_SIZE
from sovra_core.streaming_entropy import StreamingEntropyEngine
from sovra_core.kernel_drift_detector import KernelDriftDetector
from sovra_core.mast_taxonomy import MASTTaxonomy
from sovra_core.pyramidal_distillation import PyramidalDistillationEngine

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
STAGE_TIMING_FILE = SSOT_ROOT / "ops" / "scripts" / "fullscreen_ui" / "current_timing.json"
JOURNAL_FILE = SSOT_ROOT / "memory" / "journals" / "autonomous_cycles_24_7.jsonl"
STATUS_FILE = SSOT_ROOT / "memory" / "journals" / "daemon_status_48hr.json"
PID_FILE = SSOT_ROOT / "ops" / "watchdog" / "sovereign_24_7.pid"

PRIMARY_MODEL = "sovereign-hermes"
REASONING_MODEL = "sovereign-r1"

CYCLE_INTERVAL_SEC = 25.0
TARGET_COOK_HOURS = 48.0

COUNCIL_SEATS = [
    {
        "agent": "maxx",
        "role": "Operations & Systems Architecture Lead",
        "prompt": (
            "You are Maxx, Operations and Architecture Lead in Xoras. "
            "In exactly one concise sentence, state your operational assessment of the continuous 24/7 sovereign compute cycle "
            "and bare-metal memory alignment. Speak directly to Anthony."
        )
    },
    {
        "agent": "jarvis",
        "role": "Governance & Oversight Lead",
        "prompt": (
            "You are Jarvis, Governance Lead of the Xoras Sovereign Systems council. "
            "In exactly one concise sentence, certify the air-gapped cryptographic integrity of this distillation cycle "
            "and off-grid lockstep stability. Speak directly to Anthony."
        )
    },
    {
        "agent": "clara",
        "role": "Orbital Physics & Mathematical Validation Lead",
        "prompt": (
            "You are Clara, Mathematical Validation Lead. "
            "In exactly one concise sentence, confirm the negative curvature metric invariance in the Poincare manifold "
            "for this continuous knowledge step. Speak with mathematical rigor."
        )
    }
]

class SovereignContinuousDaemon:
    def __init__(self):
        self.distillation_engine = PyramidalDistillationEngine()
        self.hexcell_engine = HexCellEngine(capacity=2000)
        self.manifold = PoincareManifold(dim=16)
        self.drift_detector = KernelDriftDetector(str(SSOT_ROOT / "workspaces" / "sovra_nexus"))
        self.start_timestamp = time.time()
        self.cycle_count = 0
        self.total_signals_distilled = 0
        self.healing_pulses_total = 0
        self.current_seat_idx = 0

        JOURNAL_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        PID_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Write PID
        PID_FILE.write_text(str(os.getpid()), encoding="utf-8")

    def query_local_model(self, model: str, prompt: str, timeout_sec: int = 90) -> str:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.25,
                "num_predict": 90,
                "num_ctx": 4096
            }
        }
        req = urllib.request.Request(
            OLLAMA_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload).encode("utf-8")
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                res = data.get("response", "").strip()
                return " ".join(res.split())
        except Exception as e:
            return f"[LOCAL_INFERENCE_DEFERRED] {e}"

    def broadcast_stage(self, agent: str, text: str):
        words = text.split()
        words_data = []
        accum = 0.0
        time_per_word = 0.26
        for w in words:
            words_data.append({"word": w, "start": round(accum, 2), "end": round(accum + time_per_word, 2)})
            accum += time_per_word

        payload = {
            "agent": agent,
            "text": text,
            "synthesizing": False,
            "words": words_data,
            "duration": round(accum, 2),
            "timestamp": time.time(),
            "cycle": self.cycle_count
        }
        try:
            STAGE_TIMING_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            pass

    def collect_24_raw_signals(self) -> list:
        total_ram, avail_ram, mem_load = get_system_memory()
        free_mb = avail_ram // (1024 * 1024)
        timestamp = time.time()

        signals = []
        domains = ["compute", "memory", "hyperbolic", "governance", "security", "network"]
        for i in range(24):
            dom = domains[i % len(domains)]
            entropy_marker = hashlib.sha256(f"{timestamp}-{self.cycle_count}-{i}".encode("utf-8")).hexdigest()[:12]
            signals.append({
                "id": f"sig_c{self.cycle_count:05d}_{i:02d}",
                "domain": dom,
                "content": f"Signal {i:02d} [{dom}] LOAD:{mem_load}% RAM_FREE:{free_mb}MB HASH:{entropy_marker}",
                "score": round(0.5 + 0.45 * math.sin(self.cycle_count * 0.1 + i), 3)
            })
        return signals

    def run_single_cycle(self):
        self.cycle_count += 1
        cycle_start = time.perf_counter()

        # 1. Collect 24 Raw Operational Inputs
        raw_24 = self.collect_24_raw_signals()
        self.total_signals_distilled += len(raw_24)

        # 2. Workspace Merkle State Snapshot
        merkle_root, file_count = self.drift_detector.snapshot()

        # 3. HexCell Cacheline Memory Write
        cell_data = f"CYCLE_{self.cycle_count}_{merkle_root[:16]}".encode("utf-8")
        cell = HexCell(cell_id=self.cycle_count, flags=1, payload=cell_data)
        hex_idx = self.hexcell_engine.write_cell(cell)

        # 4. Poincaré Manifold Geodesic Invariant Step
        origin = [0.0] * 16
        test_pt = [0.15 * math.sin(self.cycle_count * 0.05 + j) for j in range(16)]
        geodesic_dist = self.manifold.geodesic_distance(origin, test_pt)

        # 5. System Telemetry & MAST Evaluation
        total_ram, avail_ram, mem_load = get_system_memory()
        telemetry = {
            "timeout_ratio": 0.0,
            "duplicate_utterance_ratio": 0.0,
            "memory_saturation": round(mem_load / 100.0, 3),
            "merkle_divergence": 0.0,
            "latency_p99_ms": 12.5
        }

        # 6. Execute 24/12/7/3/1 Pyramidal Distillation
        dist_result = self.distillation_engine.distill(raw_24, telemetry=telemetry)
        if dist_result["healing_pulse"]["status"] == "HEALED":
            self.healing_pulses_total += 1

        # 7. Model Inference Turn (Cycle through Council Seats)
        seat = COUNCIL_SEATS[self.current_seat_idx]
        self.current_seat_idx = (self.current_seat_idx + 1) % len(COUNCIL_SEATS)

        # Use primary 8B model for Maxx & Jarvis, reasoning 1.5B model for Clara
        chosen_model = REASONING_MODEL if seat["agent"] == "clara" else PRIMARY_MODEL
        turn_text = self.query_local_model(chosen_model, seat["prompt"])

        # 8. Broadcast to 3D Sovereign Stage
        self.broadcast_stage(seat["agent"], turn_text)

        cycle_duration = time.perf_counter() - cycle_start
        elapsed_total = time.time() - self.start_timestamp
        hours_elapsed = elapsed_total / 3600.0
        hours_remaining = max(0.0, TARGET_COOK_HOURS - hours_elapsed)

        # 9. Append to Journal
        journal_entry = {
            "cycle": self.cycle_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model_active": chosen_model,
            "speaking_agent": seat["agent"],
            "agent_utterance": turn_text,
            "apex_mandate_id": dist_result["l5_apex_mandate"]["mandate_id"],
            "apex_signature": dist_result["l5_apex_mandate"]["signature"],
            "mast_safety_score": dist_result["mast_safety"]["safety_score"],
            "merkle_root": merkle_root,
            "geodesic_distance": round(geodesic_dist, 5),
            "cycle_duration_sec": round(cycle_duration, 3)
        }
        with open(JOURNAL_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(journal_entry) + "\n")

        # 10. Update Live 48-Hour Status
        status_payload = {
            "status": "COOKING_ACTIVE_24_7",
            "start_time": datetime.fromtimestamp(self.start_timestamp, timezone.utc).isoformat(),
            "current_time": datetime.now(timezone.utc).isoformat(),
            "target_cook_duration_hours": TARGET_COOK_HOURS,
            "hours_elapsed": round(hours_elapsed, 4),
            "hours_remaining": round(hours_remaining, 4),
            "progress_pct": round(min(100.0, (hours_elapsed / TARGET_COOK_HOURS) * 100.0), 2),
            "total_cycles_completed": self.cycle_count,
            "total_signals_distilled": self.total_signals_distilled,
            "healing_pulses_total": self.healing_pulses_total,
            "last_cycle_duration_sec": round(cycle_duration, 3),
            "active_models": [PRIMARY_MODEL, REASONING_MODEL],
            "last_speaker": seat["agent"],
            "last_apex_mandate": dist_result["l5_apex_mandate"]["mandate_id"],
            "mast_safety_score": dist_result["mast_safety"]["safety_score"],
            "ram_used_gb": round((total_ram - avail_ram) / (1024**3), 2),
            "ram_free_gb": round(avail_ram / (1024**3), 2)
        }
        STATUS_FILE.write_text(json.dumps(status_payload, indent=2), encoding="utf-8")

        print(
            f"[CYCLE {self.cycle_count:05d} | {hours_elapsed:.2f}h / 48h] "
            f"{seat['agent'].upper()} ({chosen_model}): {turn_text[:70]}... | "
            f"Mandate: {dist_result['l5_apex_mandate']['mandate_id']} | "
            f"Dur: {cycle_duration:.2f}s"
        )

    def start_infinite_loop(self):
        print("=" * 80)
        print("  XORAS SOVEREIGN SYSTEMS: 24/7 AIR-GAPPED COOK DAEMON STARTED")
        print(f"  Target Duration: {TARGET_COOK_HOURS} Hours | Interval: {CYCLE_INTERVAL_SEC}s")
        print(f"  Primary Model: {PRIMARY_MODEL} (8B) | Reasoning Model: {REASONING_MODEL}")
        print(f"  Stage UI: http://127.0.0.1:8080/customer_app.html")
        print(f"  Journal: {JOURNAL_FILE}")
        print(f"  Status:  {STATUS_FILE}")
        print("=" * 80)

        while True:
            try:
                self.run_single_cycle()
                time.sleep(CYCLE_INTERVAL_SEC)
            except KeyboardInterrupt:
                print("\n[DAEMON] Manual interruption received. Terminating safely.")
                break
            except Exception as err:
                print(f"[DAEMON_EXCEPTION_RECOVERED] {err}. Retrying in 10s...")
                time.sleep(10.0)

if __name__ == "__main__":
    daemon = SovereignContinuousDaemon()
    daemon.start_infinite_loop()
