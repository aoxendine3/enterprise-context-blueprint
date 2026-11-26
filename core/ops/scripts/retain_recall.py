#!/usr/bin/env python3
"""
=============================================================================
XORAS RETAIN & RECALL — LOSSLESS ALPHA -> BETA -> GAMMA DISTILLATION
=============================================================================
Memory is re-indexed, never deleted.

  Alpha (short-term)  : a session's raw decisions are distilled into
                        KNOWLEDGE OBJECTS (decision, reason, verified artifact)
                        BEFORE the scratchpad is cleared — no silent drops.
  Beta  (mid-term)    : task checkpoints in memory/tri_brain/world_file.db.
                        Append-only, CAS-versioned: a new row must advance the
                        step and links to the previous row's signature.
  Gamma (long-term)   : the hash-chained knowledge-object journal
                        memory/agent_logs/knowledge_objects.jsonl. Append-only;
                        each record pins the hash of the one before it, so any
                        edit or deletion breaks the chain and is detected.

Honesty note: signatures here are SHA-256 hash chains. They prove tamper
evidence, not authorship; no ed25519 key is claimed or used.

Usage:
  retain_recall.py distill   --author maxx --session session.json
  retain_recall.py recall    "query terms" [--limit 5]
  retain_recall.py checkpoint --task T --step 2 --total 5 --status running [--payload '{}']
  retain_recall.py hydrate   [--limit 10]     # boot handshake: what do we know
  retain_recall.py verify                     # chain integrity (exit 0 / 1)
  retain_recall.py retract --author maxx --reason "why" KO-id [KO-id ...]
                                              # append-only retraction (nothing deleted)
  retain_recall.py --self-test
=============================================================================
"""
import argparse
import fcntl
import hashlib
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
JOURNAL = ROOT / "memory" / "agent_logs" / "knowledge_objects.jsonl"
WORLD_DB = ROOT / "memory" / "tri_brain" / "world_file.db"
GENESIS = "0" * 64


def _canon(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _tokens(text: str) -> list:
    return re.findall(r"[a-z0-9_]+", (text or "").lower())


# ---------------------------------------------------------------- Gamma ----
def read_journal(journal: Path = None) -> list:
    journal = journal or JOURNAL
    if not journal.exists():
        return []
    out = []
    with open(journal, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def verify_chain(journal: Path = None) -> tuple:
    """Return (ok, detail). Detects edits, reordering and deletions."""
    journal = journal or JOURNAL
    prev = GENESIS
    for n, rec in enumerate(read_journal(journal), 1):
        body = {k: v for k, v in rec.items() if k != "hash"}
        if rec.get("prev_hash") != prev:
            return False, f"record {n}: prev_hash broken (deletion or reorder)"
        if _sha(_canon(body)) != rec.get("hash"):
            return False, f"record {n}: content hash mismatch (edited)"
        prev = rec["hash"]
    return True, f"chain intact at head {prev[:16]}"


def _retraction_records(journal: Path = None) -> list:
    return [r for r in read_journal(journal) if r.get("kind") == "RETRACTION"]


def active_objects(journal: Path = None) -> list:
    """Knowledge objects not retracted. Retracted ones stay in the journal."""
    retracted = {i for r in _retraction_records(journal) for i in r.get("retracts", [])}
    return [r for r in read_journal(journal)
            if r.get("kind") == "KNOWLEDGE_OBJECT" and r["object_id"] not in retracted]


def retract(ids: list, reason: str, author: str, journal: Path = None) -> dict:
    """Append a retraction. The retracted objects are NOT deleted or edited."""
    journal = journal or JOURNAL
    with open(journal, "a+", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        fh.seek(0)
        existing = [json.loads(l) for l in fh.read().splitlines() if l.strip()]
        present = {r["object_id"] for r in existing if r.get("kind") == "KNOWLEDGE_OBJECT"}
        missing = [i for i in ids if i not in present]
        if missing or not reason.strip():
            return {"ok": False, "reason": f"unknown ids {missing}" if missing else "reason required"}
        prev = existing[-1]["hash"] if existing else GENESIS
        body = {
            "object_id": "RT-" + _sha(_canon([sorted(ids), reason]))[:16],
            "kind": "RETRACTION",
            "retracts": sorted(ids),
            "reason": reason.strip(),
            "author": author,
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "prev_hash": prev,
        }
        rec = dict(body, hash=_sha(_canon(body)))
        fh.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    return {"ok": True, "retracted": sorted(ids), "object_id": rec["object_id"]}


def _object_id(decision: str, reason: str, artifact: str) -> str:
    return "KO-" + _sha(_canon([decision, reason, artifact or ""]))[:16]


def distill(session: dict, author: str, journal: Path = None) -> dict:
    """Distill a session into knowledge objects. Idempotent; never drops."""
    journal = journal or JOURNAL
    decisions = session.get("decisions") or []
    journal.parent.mkdir(parents=True, exist_ok=True)
    retained, duplicates, rejected = [], [], []
    with open(journal, "a+", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        fh.seek(0)
        existing = [json.loads(l) for l in fh.read().splitlines() if l.strip()]
        known = {r["object_id"] for r in existing}
        prev = existing[-1]["hash"] if existing else GENESIS
        for d in decisions:
            decision, reason = (d.get("decision") or "").strip(), (d.get("reason") or "").strip()
            if not decision or not reason:
                # Surfaced, not silently dropped (errors-as-placeholders).
                rejected.append({"PLACEHOLDER_INCOMPLETE_KO": d})
                continue
            artifact = d.get("artifact") or ""
            oid = _object_id(decision, reason, artifact)
            if oid in known:
                duplicates.append(oid)
                continue
            art_hash = None
            if artifact and Path(artifact).is_file():
                art_hash = _sha(Path(artifact).read_bytes())
            body = {
                "object_id": oid,
                "kind": "KNOWLEDGE_OBJECT",
                "decision": decision,
                "reason": reason,
                "artifact": artifact,
                "artifact_sha256": art_hash,
                "tags": sorted({t.lower() for t in d.get("tags", [])}),
                "author": author,
                "session_id": session.get("session_id", "unspecified"),
                "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "prev_hash": prev,
            }
            rec = dict(body, hash=_sha(_canon(body)))
            fh.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
            fh.flush()
            known.add(oid)
            prev = rec["hash"]
            retained.append(oid)
    return {"retained": retained, "duplicates": duplicates, "rejected": rejected}


def recall(query: str, limit: int = 5, journal: Path = None) -> list:
    """Rank knowledge objects by term overlap (tags weigh double)."""
    q = set(_tokens(query))
    if not q:
        return []
    scored = []
    for rec in active_objects(journal):
        body = set(_tokens(" ".join([rec["decision"], rec["reason"], rec.get("artifact", "")])))
        tags = set(_tokens(" ".join(rec.get("tags", []))))
        score = len(q & body) + 2 * len(q & tags)
        if score:
            scored.append((score, rec["created_utc"], rec))
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [dict(r, score=s) for s, _, r in scored[:limit]]


# ----------------------------------------------------------------- Beta ----
def checkpoint(task_id: str, step: int, total: int, status: str, payload: dict,
               db: Path = None) -> dict:
    """Append a CAS-versioned checkpoint. Never overwrites history."""
    db = db or WORLD_DB
    conn = sqlite3.connect(str(db), timeout=30)
    try:
        conn.execute("BEGIN IMMEDIATE")  # single writer
        row = conn.execute(
            "SELECT step_completed, recovery_sig FROM task_checkpoints "
            "WHERE task_id=? ORDER BY rowid DESC LIMIT 1", (task_id,)).fetchone()
        prev_step = int(row[0]) if row else -1
        prev_sig = row[1] if row else GENESIS
        if step < prev_step:
            conn.execute("ROLLBACK")
            return {"ok": False, "reason": f"CAS_REJECT: step {step} < current {prev_step}"}
        payload_json = json.dumps(payload, sort_keys=True)
        sig = "sha256chain:" + _sha(f"{prev_sig}|{task_id}|{step}|{total}|{status}|{payload_json}".encode())
        conn.execute(
            "INSERT INTO task_checkpoints VALUES (?,?,?,?,?,?,?)",
            (task_id, str(step), str(total), payload_json, status,
             time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), sig))
        conn.commit()
        return {"ok": True, "task_id": task_id, "step": step, "recovery_sig": sig}
    finally:
        conn.close()


def latest_checkpoints(limit: int = 10, db: Path = None) -> list:
    db = db or WORLD_DB
    if not db.exists():
        return []
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            "SELECT task_id, step_completed, total_steps, status, updated_at "
            "FROM task_checkpoints ORDER BY rowid DESC LIMIT ?", (limit,)).fetchall()
    finally:
        conn.close()
    return [dict(zip(("task_id", "step", "total", "status", "updated_at"), r)) for r in rows]


# ------------------------------------------------------------ Handshake ----
def hydrate(limit: int = 10, journal: Path = None, db: Path = None) -> dict:
    """High-signal boot state: chain health, newest KOs, open checkpoints."""
    ok, detail = verify_chain(journal)
    active = active_objects(journal)
    recs = active[-limit:]
    return {
        "chain_ok": ok,
        "chain_detail": detail,
        "knowledge_objects_total": len(active),
        "retracted": len(read_journal(journal)) - len(active) - len(_retraction_records(journal)),
        "recent": [{"id": r["object_id"], "decision": r["decision"], "reason": r["reason"],
                    "artifact": r["artifact"]} for r in recs],
        "checkpoints": latest_checkpoints(limit, db),
    }


# ------------------------------------------------------------ Self test ----
def self_test() -> int:
    import tempfile
    fails = []
    with tempfile.TemporaryDirectory() as td:
        j, db = Path(td) / "ko.jsonl", Path(td) / "w.db"
        c = sqlite3.connect(db)
        c.execute("CREATE TABLE task_checkpoints (task_id TEXT, step_completed TEXT, total_steps TEXT, "
                  "payload_json TEXT, status TEXT, updated_at TEXT, recovery_sig TEXT)")
        c.commit(); c.close()
        s = {"session_id": "t", "decisions": [
            {"decision": "Lock ROOTS", "reason": "no self mutation", "tags": ["Identity"]},
            {"decision": "", "reason": "x"}]}
        r1, r2 = distill(s, "maxx", j), distill(s, "maxx", j)
        checks = [
            ("retain one, surface one rejection", len(r1["retained"]) == 1 and len(r1["rejected"]) == 1),
            ("idempotent re-distill", len(r2["retained"]) == 0 and len(r2["duplicates"]) == 1),
            ("recall finds it", bool(recall("identity lock", journal=j))),
            ("chain intact", verify_chain(j)[0]),
            ("checkpoint advances", checkpoint("T", 1, 3, "running", {}, db)["ok"]),
            ("CAS rejects regression", not checkpoint("T", 0, 3, "running", {}, db)["ok"]),
        ]
        lines = j.read_text().splitlines()
        j.write_text(lines[0].replace("Lock ROOTS", "Unlock ROOTS") + "\n")
        checks.append(("edit detected", not verify_chain(j)[0]))
        for name, ok in checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
            if not ok:
                fails.append(name)
    print("SELF TEST " + ("FAILED: " + ", ".join(fails) if fails else "PASSED"))
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="XORAS retain & recall")
    ap.add_argument("--self-test", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("distill"); p.add_argument("--author", required=True); p.add_argument("--session", required=True)
    p = sub.add_parser("recall"); p.add_argument("query"); p.add_argument("--limit", type=int, default=5)
    p = sub.add_parser("checkpoint")
    p.add_argument("--task", required=True); p.add_argument("--step", type=int, required=True)
    p.add_argument("--total", type=int, required=True); p.add_argument("--status", default="running")
    p.add_argument("--payload", default="{}")
    p = sub.add_parser("hydrate"); p.add_argument("--limit", type=int, default=10)
    p = sub.add_parser("retract"); p.add_argument("--author", required=True)
    p.add_argument("--reason", required=True); p.add_argument("ids", nargs="+")
    sub.add_parser("verify")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if a.cmd == "retract":
        out = retract(a.ids, a.reason, a.author)
    elif a.cmd == "distill":
        out = distill(json.loads(Path(a.session).read_text(encoding="utf-8")), a.author)
    elif a.cmd == "recall":
        out = recall(a.query, a.limit)
    elif a.cmd == "checkpoint":
        out = checkpoint(a.task, a.step, a.total, a.status, json.loads(a.payload))
    elif a.cmd == "hydrate":
        out = hydrate(a.limit)
    elif a.cmd == "verify":
        ok, detail = verify_chain()
        print(detail)
        return 0 if ok else 1
    else:
        ap.print_help()
        return 2
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if (not isinstance(out, dict) or out.get("ok", True)) else 1


if __name__ == "__main__":
    sys.exit(main())
