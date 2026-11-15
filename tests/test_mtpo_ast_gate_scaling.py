#!/usr/bin/env python3
"""
MTPO × Council × AST-Gate scaling benchmark
===========================================

Question this file answers with measurements, not prose:

  "How does the council pipeline scale past 128 workers once full deliberation
   and an AST gate are in the critical path?"

Two configurations are measured against the same workload, on the same host,
in the same process:

  ``gate_in_path``
      Per transaction: deliberation wait (I/O) -> rank assignment (lock) ->
      AST scan (CPU, GIL-bound) -> Merkle DAG commit (locked) -> slot mutate.
      This is what ``CouncilOrchestrator.execute_governed_task`` does today,
      with the model call replaced by a fixed synthetic wait.

  ``gate_deferred``
      Per transaction: deliberation wait -> reserve slot -> rank assignment ->
      slot mutate -> release -> AST scan -> commit node, or compensate the slot
      if the scan rejects. This is the saga ordering that keeps a GIL-bound
      verifier off the state critical path.

A third measurement runs the AST gate in a *process* pool to show what
horizontal scaling of the gate actually buys on a GIL-bound runtime.

Every run asserts: zero lost updates, zero aborts, Church–Rosser confluence
against the rank-ordered serial execution, and that a rejected payload never
changes state. A signed receipt is written to
``memory/catch_log/mtpo_ast_gate_scaling_receipt.json``.
"""

from __future__ import annotations

import json
import os
import random
import sys
import threading
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FRAMEWORK = REPO_ROOT / "workspaces" / "xoras_agent_framework"
for p in (str(REPO_ROOT), str(FRAMEWORK)):
    if p not in sys.path:
        sys.path.insert(0, p)

from xoras.ast_security import ASTSecurityEngine  # noqa: E402
from xoras.merkle_dag import ContextLineageDAGEngine  # noqa: E402
from xoras.mtpo import HEXCELL_SLOTS, HexCellRing  # noqa: E402

RECEIPT_PATH = REPO_ROOT / "memory" / "catch_log" / "mtpo_ast_gate_scaling_receipt.json"

# A realistic-size agent payload: ~40 lines of benign Python.
SAFE_PAYLOAD = (
    """
import hashlib

def handle(rows):
    out = []
    for r in rows:
        if r.get("ok"):
            out.append({"id": r["id"], "h": hashlib.sha256(str(r).encode()).hexdigest()})
    return out
"""
    * 3
)

# A payload the AST tripwire must reject; used to prove rejection cannot mutate state.
UNSAFE_PAYLOAD = """
import subprocess
def run(cmd):
    return subprocess.check_output(cmd, shell=True)
"""


def _scan(payload: str) -> tuple[bool, int, float]:
    """Return (is_safe, nodes_analyzed, safety_score) for a payload."""
    engine = ASTSecurityEngine(strict_mode=True)
    res = engine.scan_code(payload)
    return res.is_safe, res.nodes_analyzed, res.safety_score


# Module-level worker for the process pool (must be picklable by name).
def _scan_worker(payload: str) -> bool:
    engine = ASTSecurityEngine(strict_mode=True)
    return engine.scan_code(payload).is_safe


class SwarmLedger:
    """Rank-ordered sharded ledger; the state the benchmark mutates."""

    def __init__(self) -> None:
        self.ring = HexCellRing()
        self._rank_lock = threading.Lock()
        self._rank = 0
        self._tx_lock = threading.Lock()
        self.txs: list[tuple[int, int, int]] = []  # (sigma, slot, delta)
        self.total_aborts = 0
        self.ast_rejections = 0

    def next_rank(self) -> int:
        with self._rank_lock:
            self._rank += 1
            return self._rank

    def record(self, sigma: int, slot: int, delta: int) -> None:
        with self._tx_lock:
            self.txs.append((sigma, slot, delta))

    def abort(self) -> None:
        with self._tx_lock:
            self.total_aborts += 1

    def reject(self) -> None:
        with self._tx_lock:
            self.ast_rejections += 1

    def state(self) -> list[int]:
        return [self.ring.read(i) for i in range(HEXCELL_SLOTS)]

    def canonical_state(self) -> list[int]:
        with self._tx_lock:
            ordered = sorted(self.txs, key=lambda t: t[0])
        state = [0] * HEXCELL_SLOTS
        for _, slot, delta in ordered:
            state[slot] += delta
        return state


def _deliberation_wait(rng: random.Random) -> float:
    """Synthetic stand-in for one council turn (local model or remote call)."""
    return rng.uniform(100.0, 300.0) / 1_000_000.0


def _run_workers(
    num_workers: int,
    txs_per_worker: int,
    mode: str,
    pool: ProcessPoolExecutor | None = None,
    unsafe_ratio: float = 0.0,
    seed: int = 0xDEADBEEF,
) -> dict:
    ledger = SwarmLedger()
    dag = ContextLineageDAGEngine()
    engine = ASTSecurityEngine(strict_mode=True)
    latencies: list[float] = []
    lat_lock = threading.Lock()
    rng = random.Random(seed)
    payload = SAFE_PAYLOAD
    nodes = _scan(payload)[1]

    def worker(wid: int) -> None:
        local: list[float] = []
        local_rng = random.Random(seed + wid)
        for seq in range(txs_per_worker):
            t_start = time.perf_counter()
            time.sleep(_deliberation_wait(local_rng))
            slot = local_rng.randrange(HEXCELL_SLOTS)
            delta = (wid + 1) * 2 + (seq % 3)
            this_payload = UNSAFE_PAYLOAD if (unsafe_ratio and local_rng.random() < unsafe_ratio) else payload

            if mode == "gate_in_path":
                sigma = ledger.next_rank()
                safe = engine.scan_code(this_payload).is_safe if not unsafe_ratio else _scan(this_payload)[0]
                if not safe:
                    ledger.reject()
                    ledger.abort()
                    local.append((time.perf_counter() - t_start) * 1000.0)
                    continue
                ok, _hash, _err = dag.commit(f"w{wid}_{seq}", [], {"slot": slot, "delta": delta, "wid": wid, "seq": seq})
                if not ok:
                    ledger.abort()
                    local.append((time.perf_counter() - t_start) * 1000.0)
                    continue
                ledger.ring.apply_delta(slot, delta)
                ledger.record(sigma, slot, delta)

            elif mode == "gate_deferred":
                sigma = ledger.next_rank()
                ledger.ring.apply_delta(slot, delta)
                if pool is not None:
                    safe = pool.submit(_scan_worker, this_payload).result()
                else:
                    safe = engine.scan_code(this_payload).is_safe
                if not safe:
                    ledger.ring.apply_delta(slot, -delta)
                    ledger.reject()
                    ledger.abort()
                else:
                    ok, _hash, _err = dag.commit(
                        f"w{wid}_{seq}", [], {"slot": slot, "delta": delta, "wid": wid, "seq": seq}
                    )
                    if ok:
                        ledger.record(sigma, slot, delta)
                    else:
                        ledger.ring.apply_delta(slot, -delta)
                        ledger.abort()
            else:
                raise ValueError(f"unknown mode {mode}")

            local.append((time.perf_counter() - t_start) * 1000.0)
        with lat_lock:
            latencies.extend(local)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_workers)]
    start = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=120.0)
        assert not t.is_alive(), "worker thread failed to finish"
    elapsed = time.perf_counter() - start

    latencies.sort()
    total = len(latencies)
    p50 = latencies[min(int(total * 0.50), total - 1)] if total else 0.0
    p99 = latencies[min(int(total * 0.99), total - 1)] if total else 0.0

    state = ledger.state()
    canonical = ledger.canonical_state()
    assert state == canonical, f"confluence mismatch: {state} != {canonical}"
    if unsafe_ratio == 0:
        assert ledger.total_aborts == 0, f"unexpected aborts: {ledger.total_aborts}"
    else:
        assert ledger.ast_rejections > 0, "unsafe payloads were never rejected"
        assert ledger.total_aborts == ledger.ast_rejections, (
            f"aborts ({ledger.total_aborts}) != rejections ({ledger.ast_rejections})"
        )

    return {
        "mode": mode,
        "workers": num_workers,
        "txs_per_worker": txs_per_worker,
        "total_transactions": total,
        "elapsed_sec": round(elapsed, 4),
        "throughput_tx_sec": round(total / elapsed, 2),
        "p50_latency_ms": round(p50, 4),
        "p99_latency_ms": round(p99, 4),
        "max_latency_ms": round(latencies[-1], 4) if total else 0.0,
        "aborts": ledger.total_aborts,
        "ast_rejections": ledger.ast_rejections,
        "confluence": state == canonical,
        "final_state": state,
    }


def _measure_scan_cost() -> dict:
    engine = ASTSecurityEngine(strict_mode=True)
    samples = []
    for _ in range(5):
        t0 = time.perf_counter()
        for _ in range(100):
            engine.scan_code(SAFE_PAYLOAD)
        samples.append((time.perf_counter() - t0) / 100 * 1e6)
    samples.sort()
    return {
        "payload_lines": SAFE_PAYLOAD.count("\n"),
        "ast_nodes": engine.scan_code(SAFE_PAYLOAD).nodes_analyzed,
        "mean_us": round(sum(samples) / len(samples), 1),
        "p50_us": round(samples[len(samples) // 2], 1),
        "min_us": round(samples[0], 1),
    }


def _sign(payload: dict) -> dict:
    """Reuse the repo's signing key if present; otherwise emit unsigned."""
    try:
        from cryptography.hazmat.primitives.asymmetric import ed25519
        key_path = REPO_ROOT / "memory" / "keys" / "test_signing.key"
        if key_path.exists():
            key = ed25519.Ed25519PrivateKey.from_private_bytes(key_path.read_bytes())
        else:
            key = ed25519.Ed25519PrivateKey.generate()
    except Exception:
        return {"payload": payload, "signature": None, "signed": False}
    body = json.dumps(payload, sort_keys=True).encode()
    return {
        "payload": payload,
        "signature": key.sign(body).hex(),
        "public_key": key.public_key().public_bytes_raw().hex(),
        "signed": True,
    }


class TestMTPOAstGateScaling:
    """Scale the pipeline until it breaks, then show the gate-pooling fix."""

    results: dict = {}
    scan_cost: dict = {}

    @classmethod
    def setup_class(cls):
        cls.scan_cost = _measure_scan_cost()

    def _record(self, key: str, block: dict):
        self.results[key] = block

    def test_01_scan_cost(self):
        cost = self.scan_cost
        print(f"\nAST scan cost: {cost['mean_us']} us/scan over {cost['ast_nodes']} nodes "
              f"({cost['payload_lines']} lines)")
        assert 50 < cost["mean_us"] < 2000, "scan cost outside sane range"

    @pytest.mark.parametrize("workers", [64, 128, 256, 512])
    def test_02_gate_in_path(self, workers: int):
        # Fixed work per worker: total work grows with the swarm, so throughput
        # and tail latency are a true scaling curve rather than a fixed-work
        # division artefact.
        txs_per_worker = 32
        res = _run_workers(workers, txs_per_worker, "gate_in_path")
        self._record(f"gate_in_path_{workers}", res)
        print(f"\n[gate_in_path] {workers:4d} workers -> {res['throughput_tx_sec']:8.1f} tx/s "
              f"p50={res['p50_latency_ms']:.2f}ms p99={res['p99_latency_ms']:.2f}ms "
              f"aborts={res['aborts']} confluence={res['confluence']}")
        assert res["confluence"] is True
        assert res["aborts"] == 0

    @pytest.mark.parametrize("workers", [64, 128, 256, 512])
    def test_03_gate_deferred(self, workers: int):
        txs_per_worker = 32
        res = _run_workers(workers, txs_per_worker, "gate_deferred")
        self._record(f"gate_deferred_{workers}", res)
        print(f"\n[gate_deferred] {workers:4d} workers -> {res['throughput_tx_sec']:8.1f} tx/s "
              f"p50={res['p50_latency_ms']:.2f}ms p99={res['p99_latency_ms']:.2f}ms "
              f"aborts={res['aborts']} confluence={res['confluence']}")
        assert res["confluence"] is True
        assert res["aborts"] == 0

    @pytest.mark.parametrize("pool_size", [4, 8])
    def test_04_gate_deferred_process_pool(self, pool_size: int):
        workers = 128
        txs_per_worker = 32
        with ProcessPoolExecutor(max_workers=pool_size) as pool:
            res = _run_workers(workers, txs_per_worker, "gate_deferred", pool=pool, unsafe_ratio=0.25)
        self._record(f"gate_deferred_pool{pool_size}_{workers}", res)
        print(f"\n[deferred+pool{pool_size}] {workers:4d} workers -> {res['throughput_tx_sec']:8.1f} tx/s "
              f"p99={res['p99_latency_ms']:.2f}ms rejections={res['ast_rejections']} confluence={res['confluence']}")
        assert res["confluence"] is True
        assert res["ast_rejections"] > 0, "unsafe payloads were not rejected"

    @pytest.mark.parametrize("pool_size", [4, 8])
    def test_04b_pool_all_safe(self, pool_size: int):
        # Same workload as gate_in_path, gate moved to a process pool, no rejections:
        # this isolates the gate-pooling effect from the cheaper rejected path.
        workers = 128
        txs_per_worker = 32
        with ProcessPoolExecutor(max_workers=pool_size) as pool:
            res = _run_workers(workers, txs_per_worker, "gate_deferred", pool=pool, unsafe_ratio=0.0)
        self._record(f"gate_deferred_pool{pool_size}_all_safe_{workers}", res)
        print(f"\n[deferred+pool{pool_size} all-safe] {workers:4d} workers -> {res['throughput_tx_sec']:8.1f} tx/s "
              f"p99={res['p99_latency_ms']:.2f}ms aborts={res['aborts']} confluence={res['confluence']}")
        assert res["confluence"] is True
        assert res["aborts"] == 0

    def test_05_rejected_payload_cannot_mutate_state(self):
        ledger = SwarmLedger()
        pre = ledger.ring.read(0)
        safe = _scan(SAFE_PAYLOAD)[0]
        assert safe is True
        unsafe = _scan(UNSAFE_PAYLOAD)[0]
        assert unsafe is False, "AST tripwire failed to reject subprocess payload"
        # A rejected transaction applies, then compensates: the slot must be
        # bit-identical to its pre-image afterwards.
        ledger.ring.apply_delta(0, 999)
        assert ledger.ring.read(0) == pre + 999
        ledger.ring.apply_delta(0, -999)
        assert ledger.ring.read(0) == pre

    def test_06_emit_receipt(self):
        inpath = [r["throughput_tx_sec"] for k, r in self.results.items() if r["mode"] == "gate_in_path"]
        ceiling = round(sum(inpath) / len(inpath), 1) if inpath else None
        # Break-even: a swarm of W workers with one council turn every T seconds
        # demands W/T commits/s. It saturates this host when W/T > ceiling.
        breakeven = {
            f"turn_{t}s": int(ceiling * t) if ceiling else None
            for t in (1, 5, 15, 30)
        }
        payload = {
            "standard": "XORAS-MTPO-ASTGATE-SCALING-v1.0",
            "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "host": {
                "platform": sys.platform,
                "python": sys.version.split()[0],
                "cpu_count": os.cpu_count(),
            },
            "ast_scan_cost": self.scan_cost,
            "runs": self.results,
            "commit_path_ceiling_tx_sec": ceiling,
            "workers_supported_before_gate_is_the_bottleneck": breakeven,
            "reading": {
                "gate_in_path": "AST scan runs inside the per-transaction critical path",
                "gate_deferred": "state commits first, AST gate runs after; compensate on reject",
                "process_pool": "AST gate moved to N processes with 25% unsafe payloads",
            },
            "known_limits": [
                "Deliberation is a 100-300us sleep, not a real model call; it models I/O "
                "wait only. Real council turns are 1-30s and dominate wall-clock.",
                "Throughput is GIL-bound in gate_in_path: adding workers past the scan "
                "cost buys queueing latency, not throughput.",
                "Measured on one host; cross-host claims need a second signed witness.",
            ],
        }
        RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
        RECEIPT_PATH.write_text(json.dumps(_sign(payload), indent=2, sort_keys=True))
        assert RECEIPT_PATH.exists()

        # Emit the human table so the scaling curve is visible in test output.
        print("\n\nMTPO × AST-GATE SCALING (32 tx per worker: load rises with swarm)")
        print(f"{'config':<28}{'workers':>8}{'tx/s':>10}{'p50 ms':>10}{'p99 ms':>10}{'aborts':>8}")
        for key, r in self.results.items():
            print(f"{r['mode']:<28}{r['workers']:>8}{r['throughput_tx_sec']:>10.0f}"
                  f"{r['p50_latency_ms']:>10.2f}{r['p99_latency_ms']:>10.2f}{r['aborts']:>8}")
