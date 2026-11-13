#!/usr/bin/env python3
#=============================================================================
# SOVEREIGN ACTIVITY TRACE — FULL-STAGE AGENTIC MONITORING (TAMPER-EVIDENT)
#=============================================================================
# Mandate: "full agentic monitoring needs inclusion into this build at all
# stages. No work should be unmonitored and trackable with full tracing."
#
# Design:
#   * Append-only JSONL ledger: memory/observability/activity_trace.jsonl
#   * Every record hash-chains to the previous record (prev_hash) — any
#     deletion, insertion, or edit breaks the chain and verify() detects it.
#   * Spans: start-stage / span / end-stage records carry trace_id (a stage
#     of work), actor, action, targets with sha256 before/after, status,
#     and links to writer_log / receipts.
#   * Fail-closed: if the ledger cannot be written, the caller must abort
#     (callers get exit code 1 so governed scripts can fail closed).
#
# Usage:
#   activity_trace.py start --stage <name> --actor <who>
#   activity_trace.py span  --trace <trace_id> --action <what> [--target F --sha-before X --sha-after Y] [--status ok|fail] [--ref R]
#   activity_trace.py end   --trace <trace_id> --status ok|fail [--ref R]
#   activity_trace.py verify              (validates the whole hash chain)
#   activity_trace.py show [--trace T] [--tail N]
#=============================================================================
import argparse
import hashlib
import json
import sys
import time
import uuid
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
LEDGER = ROOT / "memory" / "observability" / "activity_trace.jsonl"


def _last_record() -> dict | None:
    if not LEDGER.exists():
        return None
    last = None
    with open(LEDGER, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                last = json.loads(line)
    return last


def _append(record: dict) -> None:
    prev = _last_record()
    record["prev_hash"] = prev["record_hash"] if prev else "GENESIS_TRACE"
    body = json.dumps({k: v for k, v in record.items() if k != "record_hash"}, sort_keys=True)
    record["record_hash"] = hashlib.sha256(body.encode()).hexdigest()
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")
    print(f"TRACE: {record['record_hash'][:16]}... ({record['type']})")


def _file_hash(path: str) -> str | None:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    if not p.exists():
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def start(stage: str, actor: str, ref: str = "") -> str:
    trace_id = uuid.uuid4().hex[:16]
    _append({
        "type": "stage_start", "trace_id": trace_id, "stage": stage,
        "actor": actor, "ref": ref, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ts": time.time(),
    })
    print(f"TRACE_ID: {trace_id}")
    return trace_id


def span(trace_id: str, action: str, actor: str = "", target: str = "",
         sha_before: str = "", sha_after: str = "", status: str = "ok",
         ref: str = "") -> None:
    if target and not sha_before:
        sha_before = _file_hash(target) or ""
    if target and not sha_after:
        sha_after = sha_before
    _append({
        "type": "span", "trace_id": trace_id, "action": action, "actor": actor,
        "target": target, "sha256_before": sha_before, "sha256_after": sha_after,
        "status": status, "ref": ref,
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "ts": time.time(),
    })


def end(trace_id: str, status: str, ref: str = "") -> None:
    _append({
        "type": "stage_end", "trace_id": trace_id, "status": status, "ref": ref,
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "ts": time.time(),
    })


def verify() -> bool:
    if not LEDGER.exists():
        print("NO LEDGER. Nothing traced yet.")
        return False
    prev_hash = "GENESIS_TRACE"
    count = 0
    ok = True
    with open(LEDGER, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            body = json.dumps({k: v for k, v in rec.items() if k != "record_hash"}, sort_keys=True)
            digest = hashlib.sha256(body.encode()).hexdigest()
            if rec.get("prev_hash") != prev_hash:
                print(f"CHAIN BREAK at record {count + 1}: prev_hash mismatch")
                ok = False
            if rec.get("record_hash") != digest:
                print(f"CHAIN BREAK at record {count + 1}: record_hash recompute mismatch (tampering)")
                ok = False
            prev_hash = rec.get("record_hash", prev_hash)
            count += 1
    print(f"VERIFY: {'PASS' if ok else 'FAIL'} — {count} records, chain intact" if ok
          else f"VERIFY: FAIL — {count} records examined")
    return ok


def show(trace_filter: str = "", tail: int = 20) -> None:
    records = []
    if LEDGER.exists():
        with open(LEDGER, encoding="utf-8") as fh:
            records = [json.loads(l) for l in fh if l.strip()]
    if trace_filter:
        records = [r for r in records if r.get("trace_id") == trace_filter or r.get("stage") == trace_filter]
    for r in records[-tail:]:
        extras = {k: v for k, v in r.items() if k in ("stage", "action", "target", "status", "actor", "trace_id")}
        print(f"{r['utc']}  {r['type']:<11} {extras}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start"); s.add_argument("--stage", required=True); s.add_argument("--actor", default=""); s.add_argument("--ref", default="")
    p = sub.add_parser("span"); p.add_argument("--trace", required=True); p.add_argument("--action", required=True)
    p.add_argument("--actor", default=""); p.add_argument("--target", default="")
    p.add_argument("--sha-before", default=""); p.add_argument("--sha-after", default="")
    p.add_argument("--status", default="ok"); p.add_argument("--ref", default="")
    e = sub.add_parser("end"); e.add_argument("--trace", required=True); e.add_argument("--status", required=True); e.add_argument("--ref", default="")
    sub.add_parser("verify")
    w = sub.add_parser("show"); w.add_argument("--trace", default=""); w.add_argument("--tail", type=int, default=20)
    args = ap.parse_args()

    if args.cmd == "start":
        start(args.stage, args.actor, args.ref)
    elif args.cmd == "span":
        span(args.trace, args.action, args.actor, args.target, args.sha_before, args.sha_after, args.status, args.ref)
    elif args.cmd == "end":
        end(args.trace, args.status, args.ref)
    elif args.cmd == "verify":
        sys.exit(0 if verify() else 1)
    elif args.cmd == "show":
        show(args.trace, args.tail)


if __name__ == "__main__":
    main()
