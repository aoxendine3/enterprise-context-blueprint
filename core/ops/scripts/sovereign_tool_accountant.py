#!/usr/bin/env python3
#=============================================================================
# SOVEREIGN TOOL ACCOUNTANT — PERFORMANCE & STABILITY LEDGER OF THE TOOLCHAIN
#=============================================================================
# Mandate: "my agent is still tracking and their performance... I like to keep
# track of the tool accountant to performance and how stable they are over the
# working process of utilizing several tools... monitoring, stability,
# structure, sovereignty, autonomy, sync."
#
# What it is:
#   The accountant of record for the sovereign toolchain. Every governed
#   tool run is timed, judged, and written into an append-only, hash-chained
#   ledger INSIDE the project. Per-tool stability is scored over a rolling
#   window so degradation surfaces as a number before it becomes an incident.
#
# Subcommands:
#   run -- <tool> [args...]   execute a tool under accounting (times it,
#                             records exit code, writes ledger + writer-log ref)
#   record --tool T --ms N --exit C [--ref R]
#                             record a run performed outside the wrapper
#   report [--window N] [--tool T]
#                             per-tool stability report (success rate, latency
#                             profile, stability score, classification)
#   verify                    validate the ledger hash chain (fail-closed)
#
# Ledger design (tamper-evident, project-internal):
#   memory/observability/tool_ledger.jsonl   append-only, hash-chained
#   Every entry carries:
#     utc start/end + epoch (timestamp integrity), duration_ms, exit_code,
#     status, prev_hash/record_hash chain, prev_trace_hash (cross-link to
#     the activity trace chain), writer_log_ref (sha256 of the line appended
#     to memory/catch_log/writer_log.jsonl for this run).
#
# Stability score (per tool, rolling window):
#   score = 100 * success_rate * (1 - min(cv, 1))
#     cv = coefficient of variation of duration_ms (consistency)
#   classification: >=85 STABLE | >=60 WATCH | else UNSTABLE | <3 runs INSUFFICIENT
#=============================================================================
import argparse
import hashlib
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
LEDGER = ROOT / "memory" / "observability" / "tool_ledger.jsonl"
TRACE = ROOT / "memory" / "observability" / "activity_trace.jsonl"
WRITER_LOG = ROOT / "memory" / "catch_log" / "writer_log.jsonl"
REPORT = ROOT / "memory" / "intelligence" / "tool_stability_report.json"


def _last_record(path: Path) -> dict | None:
    if not path.exists():
        return None
    last = None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                last = json.loads(line)
    return last


def _last_trace_hash() -> str:
    last = _last_record(TRACE)
    return last["record_hash"] if last else "NO_TRACE_YET"


def _writer_log_ref(entry: dict) -> str:
    """Append a provenance line to the writer log; return its sha256 ref."""
    WRITER_LOG.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps({
        "utc": entry["utc_start"],
        "kind": "tool_accounting",
        "tool": entry["tool"],
        "ledger_record_hash": entry["record_hash"],
        "exit_code": entry["exit_code"],
    }, sort_keys=True)
    with open(WRITER_LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    return hashlib.sha256(line.encode()).hexdigest()


def append_entry(entry: dict) -> dict:
    prev = _last_record(LEDGER)
    entry["prev_hash"] = prev["record_hash"] if prev else "GENESIS_TOOL_LEDGER"
    entry["prev_trace_hash"] = _last_trace_hash()
    body = json.dumps({k: v for k, v in entry.items() if k != "record_hash"}, sort_keys=True)
    entry["record_hash"] = hashlib.sha256(body.encode()).hexdigest()
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")
    entry["writer_log_ref"] = _writer_log_ref(entry)
    # rewrite final line with the writer_log_ref included (chain covers the
    # pre-ref body; ref is additive provenance, verified separately)
    with open(LEDGER, encoding="utf-8") as fh:
        lines = fh.readlines()
    lines[-1] = json.dumps(entry, sort_keys=True) + "\n"
    with open(LEDGER, "w", encoding="utf-8") as fh:
        fh.writelines(lines)
    print(f"ACCOUNTED: {entry['tool']} exit={entry['exit_code']} "
          f"{entry['duration_ms']}ms hash={entry['record_hash'][:16]}...")
    return entry


# ---------------------------------------------------------------- run
INTERPRETERS = {"python", "python3", "python3.14", "bash", "sh", "zsh", "node", "uv"}


def _tool_name(argv: list[str]) -> str:
    """Resolve the accountable tool name: the script behind the interpreter."""
    name = Path(argv[0]).name
    if name in INTERPRETERS:
        for a in argv[1:]:
            if a.startswith("-"):
                continue
            base = Path(a).name
            if base in INTERPRETERS:
                continue
            return base
    return name


def cmd_run(args) -> int:
    argv = list(args.cmd)
    while argv and argv[0] == "--":
        argv.pop(0)
    if not argv:
        print("run requires -- <tool> [args...]", file=sys.stderr)
        return 2
    args.cmd = argv
    tool = _tool_name(argv)
    t0 = time.time()
    try:
        proc = subprocess.run(args.cmd, capture_output=True, text=True, timeout=args.timeout)
        exit_code, out_tail, err_tail = proc.returncode, proc.stdout[-400:], proc.stderr[-400:]
    except subprocess.TimeoutExpired as e:
        exit_code, out_tail, err_tail = 124, (e.stdout or b"")[-400:] if isinstance(e.stdout, bytes) else str(e.stdout or "")[-400:], "TIMEOUT"
    dur_ms = int((time.time() - t0) * 1000)
    entry = {
        "type": "tool_run",
        "utc_start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0)),
        "epoch_start": t0,
        "utc_end": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tool": tool,
        "argv": args.cmd,
        "duration_ms": dur_ms,
        "exit_code": exit_code,
        "status": "ok" if exit_code == 0 else "fail",
        "stdout_tail": out_tail,
        "stderr_tail": err_tail if exit_code else "",
    }
    append_entry(entry)
    if args.pass_through and exit_code:
        sys.stderr.write(err_tail)
    return 0 if args.pass_through else (0 if exit_code == 0 else 1)


# ---------------------------------------------------------------- record
def cmd_record(args) -> int:
    entry = {
        "type": "tool_run",
        "utc_start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "epoch_start": time.time(),
        "utc_end": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tool": args.tool,
        "argv": [args.tool],
        "duration_ms": args.ms,
        "exit_code": args.exit,
        "status": "ok" if args.exit == 0 else "fail",
        "stdout_tail": "",
        "stderr_tail": "",
        "note": args.ref or "recorded_outside_wrapper",
    }
    append_entry(entry)
    return 0


# ---------------------------------------------------------------- report
def load_entries() -> list[dict]:
    if not LEDGER.exists():
        return []
    out = []
    with open(LEDGER, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                out.append(json.loads(line))
    return out


def classify(score: float | None, runs: int) -> str:
    if runs < 3:
        return "INSUFFICIENT"
    if score is None:
        return "INSUFFICIENT"
    if score >= 85:
        return "STABLE"
    if score >= 60:
        return "WATCH"
    return "UNSTABLE"


def cmd_report(args) -> int:
    entries = load_entries()
    window = args.window
    by_tool: dict[str, list[dict]] = {}
    for e in entries:
        by_tool.setdefault(e["tool"], []).append(e)

    tools_report = {}
    for tool, runs in sorted(by_tool.items()):
        recent = runs[-window:]
        n = len(recent)
        durs = [e["duration_ms"] for e in recent if isinstance(e.get("duration_ms"), int)]
        ok = [e for e in recent if e["status"] == "ok"]
        success_rate = len(ok) / n if n else 0.0
        score = None
        cv = None
        if durs and n >= 3:
            mean = statistics.mean(durs)
            if mean > 0 and len(durs) >= 2:
                cv = statistics.pstdev(durs) / mean
            score = round(100 * success_rate * (1 - min(cv or 0, 1)), 1)
        tools_report[tool] = {
            "runs_total": len(runs),
            "runs_window": n,
            "success_rate": round(success_rate, 3),
            "latency_ms": {
                "avg": round(statistics.mean(durs)) if durs else None,
                "p95": round(sorted(durs)[int(0.95 * (len(durs) - 1))]) if durs else None,
                "max": max(durs) if durs else None,
            },
            "latency_cv": round(cv, 3) if cv is not None else None,
            "stability_score": score,
            "classification": classify(score, n),
            "last_run_utc": recent[-1]["utc_end"],
            "last_writer_log_ref": recent[-1].get("writer_log_ref"),
        }

    chain_ok = verify_chain(silent=True)
    report = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ledger": str(LEDGER.relative_to(ROOT)),
        "ledger_entries": len(entries),
        "ledger_chain_verified": chain_ok,
        "window": window,
        "tools": tools_report,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    print(f"TOOL ACCOUNTANT REPORT ({len(entries)} entries, chain {'OK' if chain_ok else 'BROKEN'})")
    for tool, t in tools_report.items():
        lat = t["latency_ms"]
        lat_s = f"{lat['avg'] or '-'}ms avg / {lat['p95'] or '-'}ms p95"
        print(f"  {tool:<44} {t['classification']:<12} score={t['stability_score']} "
              f"success={t['success_rate']*100:.0f}% {lat_s} (n={t['runs_window']})")
    print(f"  report filed: {REPORT.relative_to(ROOT)}")
    return 0 if chain_ok else 1


# ---------------------------------------------------------------- verify
def verify_chain(silent: bool = False) -> bool:
    prev = "GENESIS_TOOL_LEDGER"
    ok = True
    entries = load_entries()
    for i, e in enumerate(entries):
        body = json.dumps({k: v for k, v in e.items()
                           if k not in ("record_hash", "writer_log_ref")}, sort_keys=True)
        # entries before writer_log_ref propagation have plain bodies
        if e.get("prev_hash") != prev:
            ok = False
        if e.get("record_hash") != hashlib.sha256(body.encode()).hexdigest():
            ok = False
        prev = e.get("record_hash")
    if not silent:
        print("TOOL LEDGER CHAIN: VALID" if ok else "TOOL LEDGER CHAIN: BROKEN")
    return ok


def cmd_verify(_args) -> int:
    return 0 if verify_chain() else 1


def main() -> None:
    ap = argparse.ArgumentParser(prog="sovereign_tool_accountant")
    sub = ap.add_subparsers(dest="mode", required=True)

    p_run = sub.add_parser("run")
    p_run.add_argument("cmd", nargs=argparse.REMAINDER)
    p_run.add_argument("--timeout", type=int, default=600)
    p_run.add_argument("--pass-through", action="store_true")
    p_run.set_defaults(func=cmd_run)

    p_rec = sub.add_parser("record")
    p_rec.add_argument("--tool", required=True)
    p_rec.add_argument("--ms", type=int, required=True)
    p_rec.add_argument("--exit", type=int, default=0)
    p_rec.add_argument("--ref")
    p_rec.set_defaults(func=cmd_record)

    p_rep = sub.add_parser("report")
    p_rep.add_argument("--window", type=int, default=20)
    p_rep.set_defaults(func=cmd_report)

    p_ver = sub.add_parser("verify")
    p_ver.set_defaults(func=cmd_verify)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
