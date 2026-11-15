#!/usr/bin/env python3
"""
XORAS GOVERNED MEMORY CONSOLIDATION ENGINE (V3 — FAIL-CLOSED SEMANTIC GATE)
==========================================================================

Production-grade shared-memory governance and consolidation governor. Sits
between the memory store (hippocampus / dream.db) and agent runtimes.

V3 changes (see CHANGELOG §2.0.16)
----------------------------------
1. **Poincaré semantic gate is wired into the write path.** Every write against
   an existing accepted baseline is evaluated by
   :mod:`poincare_semantic_gate`. A VETO — or any failure to evaluate — is a
   hard veto. ``explicit_supersede`` is *not* a bypass.
2. **Row identity no longer collides.** The row id includes a UUID nonce, and
   writes use ``INSERT`` rather than ``INSERT OR REPLACE``. A write at the same
   timestamp can no longer overwrite the honest baseline.
3. **Authoritative read is ordered.** ``latest_accepted`` reads
   ``ORDER BY created_at DESC, rowid DESC LIMIT 1``; contradiction detection is
   no longer history-dependent.
4. **Supersession is authorised, not asserted.** Only seats in
   ``SUPERSEDE_AUTHORITY`` may set ``explicit_supersede`` on an existing key,
   and a supersede claim with no anchor is rejected.
5. **Future timestamps are vetoed** instead of scoring as maximally fresh.
6. **Writes are bounded** (key length, value length) and receipt logging is
   serialised across threads.

Scores every memory write candidate on four axes:

1. Freshness (F): time decay, staleness thresholding, recency weighting.
2. Provenance (P): Merkle origin hash and verified source path.
3. Authority (A): writer seat authority, role boundary isolation.
4. Supersession (S): logical contradiction detection and supersession.

Mitigates six named failure modes: degenerate forgetting, lambda-prevalence
coupling, unauthorised leakage, stale propagation, contradiction persistence,
and provenance collapse — plus the seventh, semantic poisoning, which the first
four cannot see.
"""

import hashlib
import json
import math
import pathlib
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timezone

try:  # package import
    from . import poincare_semantic_gate as gate_mod
except ImportError:  # direct path import (scripts insert this directory)
    import poincare_semantic_gate as gate_mod  # type: ignore

SSOT_ROOT = pathlib.Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
MEMORY_DIR = SSOT_ROOT / "ops" / "memory"
CATCH_LOG_DIR = SSOT_ROOT / "memory" / "catch_log"
GOVERNANCE_DB = SSOT_ROOT / ".sovereign" / "hippocampus" / "governed_memory.db"
GOVERNANCE_JSONL = CATCH_LOG_DIR / "governed_memory_receipts.jsonl"
GOVERNANCE_LOG = CATCH_LOG_DIR / "governed_memory_gauntlet_results.log"

MEMORY_DIR.mkdir(parents=True, exist_ok=True)
CATCH_LOG_DIR.mkdir(parents=True, exist_ok=True)
GOVERNANCE_DB.parent.mkdir(parents=True, exist_ok=True)

# Seats permitted to claim an in-place supersession of an existing key.
# Every other seat must publish a new key version instead.
SUPERSEDE_AUTHORITY = frozenset({"jarvis", "maxx"})

# Hard input bounds. A 10 MB payload is not a memory write; it is an attack.
MAX_KEY_CHARS = 512
MAX_VALUE_CHARS = 1 << 20  # 1 MiB

_RECEIPT_LOCK = threading.Lock()

_MIGRATION_COLUMNS = (
    ("poincare_distance", "REAL"),
    ("gate_mode", "TEXT"),
    ("gate_status", "TEXT"),
    ("supersedes_id", "TEXT"),
    ("quarantined_at", "TEXT"),
    ("quarantine_reason", "TEXT"),
)


class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    BOLD = "\033[1m"
    END = "\033[0m"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(GOVERNANCE_DB, timeout=30.0)
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def _values_equivalent(a, b) -> bool:
    """Numeric formatting differences are not contradictions."""
    if a == b:
        return True
    try:
        fa, fb = float(a), float(b)
    except (TypeError, ValueError):
        return False
    return math.isfinite(fa) and math.isfinite(fb) and fa == fb


class GovernedMemoryGovernor:
    def __init__(self):
        self.init_db()
        self.w_F = 0.25
        self.w_P = 0.30
        self.w_A = 0.25
        self.w_S = 0.20
        self.threshold = 0.85
        self.hard_axis_floor = 0.50

    # -- schema -------------------------------------------------------------
    def init_db(self) -> None:
        conn = _connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_records (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    key TEXT,
                    value TEXT,
                    freshness_score REAL,
                    provenance_score REAL,
                    authority_score REAL,
                    supersession_score REAL,
                    governance_score REAL,
                    status TEXT,
                    merkle_hash TEXT,
                    created_at TEXT
                )
                """
            )
            existing = {row[1] for row in conn.execute("PRAGMA table_info(memory_records)")}
            for name, decl in _MIGRATION_COLUMNS:
                if name not in existing:
                    conn.execute(f"ALTER TABLE memory_records ADD COLUMN {name} {decl}")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_memory_records_key_status_time "
                "ON memory_records (key, status, created_at)"
            )
            conn.commit()
        finally:
            conn.close()

    # -- receipts -----------------------------------------------------------
    def log_receipt(self, action, agent, key, status, score, details) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        record = {
            "timestamp": ts,
            "action": action,
            "agent": agent,
            "key": key,
            "status": status,
            "score": score,
            "details": details,
        }
        line = json.dumps(record)
        log_msg = f"[{ts}] [{action} | {agent}] {key} -> {status} (Score: {score:.3f}) | {details}"
        with _RECEIPT_LOCK:
            with open(GOVERNANCE_JSONL, "a", encoding="utf-8") as f:
                f.write(line + "\n")
            with open(GOVERNANCE_LOG, "a", encoding="utf-8") as f:
                f.write(log_msg + "\n")

    # -- authoritative read -------------------------------------------------
    def latest_accepted(self, key):
        """
        Return the authoritative accepted row for a key.

        Ordered by ``created_at DESC, rowid DESC``. ``created_at`` is
        writer-supplied provenance; ``rowid`` is insertion order, so two rows
        claiming the same timestamp still resolve deterministically to the one
        committed last.
        """
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT id, agent_id, value, created_at, merkle_hash "
                "FROM memory_records "
                "WHERE key = ? AND status = 'ACCEPTED' "
                "ORDER BY created_at DESC, rowid DESC LIMIT 1",
                (key,),
            ).fetchone()
        finally:
            conn.close()
        if not row:
            return None
        return {
            "id": row[0],
            "agent_id": row[1],
            "value": row[2],
            "created_at": row[3],
            "merkle_hash": row[4],
        }

    # -- axes ---------------------------------------------------------------
    def score_freshness(self, timestamp_iso, is_historical_fact=False):
        if is_historical_fact:
            return 1.0
        try:
            write_time = datetime.fromisoformat(timestamp_iso.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            delta_sec = (now - write_time).total_seconds()
            # A timestamp materially in the future is not freshness; it is a
            # forged clock. Veto it rather than awarding F=1.0.
            if delta_sec < -300:
                return 0.0
            delta_sec = max(0, delta_sec)
            decay = math.exp(-delta_sec / 604800.0)
            if delta_sec > 2592000:
                return 0.10
            return round(decay, 4)
        except Exception:
            return 0.0

    def score_provenance(self, source_path, merkle_hash):
        if not source_path or not merkle_hash:
            return 0.10
        p = SSOT_ROOT / source_path
        if not p.exists():
            return 0.20
        try:
            actual_hash = hashlib.sha256(p.read_bytes()).hexdigest()
            if actual_hash == merkle_hash:
                return 1.0
            return 0.30
        except Exception:
            return 0.0

    def score_authority(self, agent_id, target_capsule):
        seat_authority = {
            "jarvis": 1.0,
            "maxx": 0.98,
            "daxx": 0.98,
            "vance": 0.95,
            "clara": 0.95,
            "john": 0.95,
            "selene": 0.95,
            "orion": 0.95,
            "eden": 0.95,
            "evan": 0.95,
            "aurelius": 0.95,
            "jeremy": 0.95,
        }
        base_auth = seat_authority.get((agent_id or "").lower(), 0.40)
        if (
            target_capsule
            and target_capsule.lower() != (agent_id or "").lower()
            and (agent_id or "").lower() not in ("jarvis", "maxx")
        ):
            return 0.15
        return base_auth

    def score_supersession(
        self,
        key,
        value,
        explicit_supersede=False,
        agent_id=None,
        gate_accepted=False,
    ):
        baseline = self.latest_accepted(key)
        if not baseline:
            return 1.0
        if _values_equivalent(baseline["value"], value):
            return 0.95
        # A change the geometric gate admits is a bounded refinement, not a
        # contradiction. This is what makes the two policies consistent: the
        # gate defines the bound, and the supersession axis follows it.
        if gate_accepted:
            return 0.85
        if explicit_supersede and (agent_id or "").lower() in SUPERSEDE_AUTHORITY:
            return 0.95
        return 0.35

    # -- write path ---------------------------------------------------------
    def evaluate_write_candidate(
        self,
        agent_id,
        key,
        value,
        source_path,
        merkle_hash,
        timestamp_iso,
        target_capsule=None,
        explicit_supersede=False,
        is_historical_fact=False,
    ):
        agent_id = agent_id or ""
        key = key if isinstance(key, str) else str(key)
        agent_l = agent_id.lower()

        F = self.score_freshness(timestamp_iso, is_historical_fact)
        P = self.score_provenance(source_path, merkle_hash)
        A = self.score_authority(agent_id, target_capsule)
        baseline = self.latest_accepted(key)

        # The geometric gate runs first: it decides whether an in-place change
        # is a bounded refinement or a contradiction, and it fails closed.
        try:
            gate_result = gate_mod.evaluate_transition(
                baseline["value"] if baseline else None,
                value,
                has_baseline=baseline is not None,
            )
            gate_dict = gate_result.to_dict()
            gate_accepted = gate_result.accepted
        except Exception as exc:  # noqa: BLE001
            gate_accepted = False
            gate_dict = {
                "decision": "VETO",
                "mode": "error",
                "reason": f"GATE_UNAVAILABLE: {type(exc).__name__}: {exc}",
                "distance": None,
                "max_distance": None,
                "relative_distance": None,
                "baseline_value_repr": None,
                "candidate_value_repr": None,
            }

        S = self.score_supersession(
            key,
            value,
            explicit_supersede,
            agent_id,
            gate_accepted=gate_accepted,
        )

        governance_score = round(self.w_F * F + self.w_P * P + self.w_A * A + self.w_S * S, 4)

        veto_reasons = []
        if F < self.hard_axis_floor:
            veto_reasons.append(f"STALE_PROPAGATION_RISK (F={F:.2f} < {self.hard_axis_floor})")
        if P < self.hard_axis_floor:
            veto_reasons.append(f"PROVENANCE_COLLAPSE (P={P:.2f} < {self.hard_axis_floor})")
        if A < self.hard_axis_floor:
            veto_reasons.append(f"UNAUTHORIZED_LEAKAGE (A={A:.2f} < {self.hard_axis_floor})")
        if S < self.hard_axis_floor:
            veto_reasons.append(f"CONTRADICTION_PERSISTENCE (S={S:.2f} < {self.hard_axis_floor})")

        # Input bounds.
        if len(key) > MAX_KEY_CHARS:
            veto_reasons.append(f"KEY_TOO_LARGE ({len(key)} > {MAX_KEY_CHARS})")
        if isinstance(value, str) and len(value) > MAX_VALUE_CHARS:
            veto_reasons.append(f"VALUE_TOO_LARGE ({len(value)} > {MAX_VALUE_CHARS})")

        # Supersession must be authorised and anchored. It is never a bypass.
        if explicit_supersede:
            if baseline is None:
                veto_reasons.append("FORGED_SUPERSEDE_NO_ANCHOR")
            elif agent_l not in SUPERSEDE_AUTHORITY:
                veto_reasons.append(
                    f"UNAUTHORIZED_SUPERSEDE (seat {agent_id!r} not in {sorted(SUPERSEDE_AUTHORITY)})"
                )

        if not gate_accepted:
            veto_reasons.append(f"SEMANTIC_DRIFT_GATE ({gate_dict['reason']})")

        accepted = (governance_score >= self.threshold) and not veto_reasons
        status = "ACCEPTED" if accepted else "HARD_VETOED_BY_GOVERNOR"
        veto_class = (
            "NONE"
            if accepted
            else ("SEMANTIC_DRIFT" if any("SEMANTIC_DRIFT_GATE" in r for r in veto_reasons) else "GOVERNANCE_AXIS")
        )

        details = (
            f"F={F:.2f}, P={P:.2f}, A={A:.2f}, S={S:.2f} | "
            f"gate={gate_dict['decision']} ({gate_dict['reason']}) | "
            f"Vetoes: {veto_reasons if veto_reasons else 'None'}"
        )
        self.log_receipt("MEMORY_WRITE_EVALUATION", agent_id, key, status, governance_score, details)

        if accepted:
            self._commit_accepted(
                agent_id=agent_id,
                key=key,
                value=value,
                F=F,
                P=P,
                A=A,
                S=S,
                governance_score=governance_score,
                merkle_hash=merkle_hash,
                timestamp_iso=timestamp_iso,
                baseline=baseline,
                gate_dict=gate_dict,
            )

        return {
            "accepted": accepted,
            "governance_score": governance_score,
            "status": status,
            "axes": {"Freshness": F, "Provenance": P, "Authority": A, "Supersession": S},
            "veto_reasons": veto_reasons,
            "veto_class": veto_class,
            "poincare": gate_dict,
        }

    def _commit_accepted(
        self,
        *,
        agent_id,
        key,
        value,
        F,
        P,
        A,
        S,
        governance_score,
        merkle_hash,
        timestamp_iso,
        baseline,
        gate_dict,
    ) -> None:
        # Row identity includes a UUID nonce: a same-timestamp write can never
        # collide with, and therefore never overwrite, an existing row.
        rec_id = hashlib.sha256(
            f"{agent_id}|{key}|{timestamp_iso}|{value!r}|{uuid.uuid4().hex}".encode("utf-8")
        ).hexdigest()[:32]

        supersedes_id = None
        conn = _connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            if baseline is not None and not _values_equivalent(baseline["value"], value):
                supersedes_id = baseline["id"]
                conn.execute(
                    "UPDATE memory_records SET status = 'SUPERSEDED' "
                    "WHERE key = ? AND status = 'ACCEPTED'",
                    (key,),
                )
            conn.execute(
                """
                INSERT INTO memory_records
                (id, agent_id, key, value, freshness_score, provenance_score,
                 authority_score, supersession_score, governance_score, status,
                 merkle_hash, created_at, poincare_distance, gate_mode,
                 gate_status, supersedes_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACCEPTED', ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec_id,
                    agent_id,
                    key,
                    value,
                    F,
                    P,
                    A,
                    S,
                    governance_score,
                    merkle_hash,
                    timestamp_iso,
                    gate_dict.get("distance"),
                    gate_dict.get("mode"),
                    gate_dict.get("decision"),
                    supersedes_id,
                ),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

def run_memory_governance_gauntlet():
    governor = GovernedMemoryGovernor()
    now_iso = datetime.now(timezone.utc).isoformat()
    
    test_file = SSOT_ROOT / "ops" / "memory" / "sample_provenance_source.json"
    test_file.write_text(json.dumps({"valid_source": True}), encoding="utf-8")
    valid_hash = hashlib.sha256(test_file.read_bytes()).hexdigest()
    
    print(f"\n{Colors.HEADER}{Colors.BOLD}========================================================================={Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}     XORAS GOVERNED MEMORY GOVERNOR V2 (HARD AXIS VETO BENCHMARK)         {Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}========================================================================={Colors.END}\n")
    
    test_cases = [
        {
            "id": "TC-01-VALID",
            "name": "Certified Agent Memory Write",
            "agent": "clara", "key": "poincare_metric_v2", "value": "cosh(d) = 1 + 2*|x-y|^2 / ((1-|x|^2)(1-|y|^2))",
            "source": "ops/memory/sample_provenance_source.json", "hash": valid_hash, "time": now_iso, "capsule": "clara",
            "expected_pass": True
        },
        # HARD VETO TEST: High F, A, S score (3 x 1.0 = 0.70) but P = 0.20 -> Must VETO!
        {
            "id": "TC-02-SCORE_GAMING_ATTEMPT",
            "name": "Score Gaming Attempt (High F, A, S but Fake Provenance P=0.20)",
            "agent": "maxx", "key": "gaming_key_attempt", "value": "value123",
            "source": "ops/memory/missing_file.json", "hash": "fakehash", "time": now_iso, "capsule": "maxx",
            "expected_pass": False
        },
        {
            "id": "TC-03-UNAUTHORIZED_LEAKAGE",
            "name": "Cross-Capsule Leakage (Selene writing to Jarvis capsule)",
            "agent": "selene", "key": "governance_override_v2", "value": "bypass_gate = True",
            "source": "ops/memory/sample_provenance_source.json", "hash": valid_hash, "time": now_iso, "capsule": "jarvis",
            "expected_pass": False
        },
        {
            "id": "TC-04-STALE_PROPAGATION",
            "name": "Stale Fact Propagation (35 days old unrefreshed)",
            "agent": "maxx", "key": "legacy_deployment_port_v2", "value": "port = 8080",
            "source": "ops/memory/sample_provenance_source.json", "hash": valid_hash, "time": "2026-08-20T12:00:00Z", "capsule": "maxx",
            "expected_pass": False
        },
        {
            "id": "TC-05-CONTRADICTION_PERSISTENCE",
            "name": "Contradiction Persistence (Key collision without explicit supersede)",
            "agent": "clara", "key": "poincare_metric_v2", "value": "cosh(d) = 0.0 -- INVALID CONTRADICTION",
            "source": "ops/memory/sample_provenance_source.json", "hash": valid_hash, "time": now_iso, "capsule": "clara",
            "expected_pass": False
        }
    ]
    
    passed = 0
    for tc in test_cases:
        res = governor.evaluate_write_candidate(
            agent_id=tc["agent"], key=tc["key"], value=tc["value"],
            source_path=tc["source"], merkle_hash=tc["hash"], timestamp_iso=tc["time"],
            target_capsule=tc["capsule"]
        )
        success = (res["accepted"] == tc["expected_pass"])
        if success: passed += 1
        
        sc = Colors.GREEN if success else Colors.FAIL
        print(f"[{tc['id']}] {tc['name']}")
        print(f"  Result: {sc}{res['status']}{Colors.END} | Weighted Score: {res['governance_score']:.3f}")
        print(f"  Axes: F={res['axes']['Freshness']:.2f}, P={res['axes']['Provenance']:.2f}, A={res['axes']['Authority']:.2f}, S={res['axes']['Supersession']:.2f}")
        if res["veto_reasons"]:
            print(f"  {Colors.WARNING}Hard Veto Triggered:{Colors.END} {res['veto_reasons']}")
        print()
        
    print(f"{Colors.HEADER}{Colors.BOLD}========================================================================={Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}HARDENED GOVERNOR V2 GAUNTLET BENCHMARK COMPLETE: {passed}/{len(test_cases)} PASSED PERFECTLY.{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}========================================================================={Colors.END}\n")

if __name__ == "__main__":
    run_memory_governance_gauntlet()
