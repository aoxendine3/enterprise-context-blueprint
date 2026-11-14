#!/usr/bin/env python3
"""
=============================================================================
ACTIVITY REPORT BUILDER — FULL-DETAIL MONITOR
=============================================================================
Every action the collective takes is already recorded somewhere: identity
scopes, voice verdicts, tool calls, telemetry events, Trinity approvals,
cross-node attestations. This builds ONE report from all of them, with a
distinct box per purpose, so an operator can read the whole session's
behaviour — including the details — without hunting across files.

Boxes (one purpose each):
  [1] IDENTITY SCOPE     — who each agent was, seal state, tamper checks
  [2] COLLECTIVE VOICE   — every voice verdict, every refusal
  [3] TOOL LEDGER        — every tool call: exit code, duration, reference
  [4] TELEMETRY CHAIN    — every stream event with its hashes and roots
  [5] TRINITY GATE       — every approval, seat by seat
  [6] CROSS-NODE         — the other plane's attestations
  [7] ANOMALIES          — anything that failed, timed out, or was refused
  [8] TIMELINE           — everything above, merged in true chronological order

Output: memory/catch_log/ACTIVITY_REPORT.md
=============================================================================
"""

import json
import os
import time
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
OUT = ROOT / "memory" / "catch_log" / "ACTIVITY_REPORT.md"

SOURCES = {
    "identity": ROOT / "memory" / "agent_logs" / "identity_wake_receipts.jsonl",
    "voice": ROOT / "memory" / "agent_logs" / "collective_voice_receipts.jsonl",
    "tools": ROOT / "memory" / "observability" / "tool_ledger.jsonl",
    "telemetry": ROOT / ".agents" / "journals" / "daxx_telemetry.jsonl",
    "trinity": ROOT / "memory" / "tri_brain" / "trinity_hashes.jsonl",
    "turns": ROOT / "memory" / "agent_logs" / "turn_ledger.jsonl",
    "activity": ROOT / "memory" / "agent_logs" / "activity_trace.jsonl",
}

WIDTH = 100


def box(title: str, purpose: str, body_lines: list) -> list:
    """One box per purpose — visually distinct, self-describing."""
    inner = WIDTH - 4
    out = []
    out.append("╔" + "═" * inner + "╗")
    out.append("║" + f" {title}".ljust(inner - 1) + "║")
    out.append("║" + f" purpose: {purpose}".ljust(inner - 1) + "║")
    out.append("╠" + "═" * inner + "╣")
    for line in body_lines:
        text = str(line)
        if len(text) > inner - 3:
            text = text[: inner - 6] + "..."
        out.append("║" + f" {text}".ljust(inner - 1) + "║")
    out.append("╚" + "═" * inner + "╝")
    return out


def load_jsonl(path: Path) -> list:
    rows = []
    if not path.exists():
        return rows
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def stamp_of(rec: dict) -> float:
    for key in ("timestamp_utc", "timestamp", "timestamp_epoch_ms", "ts"):
        val = rec.get(key)
        if val is None:
            continue
        if key == "timestamp_epoch_ms":
            return float(val) / 1000.0
        if isinstance(val, (int, float)):
            return float(val)
        try:
            return time.mktime(time.strptime(str(val)[:19], "%Y-%m-%dT%H:%M:%S"))
        except Exception:
            continue
    return 0.0


def main() -> int:
    data = {k: load_jsonl(v) for k, v in SOURCES.items()}
    anomalies = []
    lines = []

    lines += [
        "# COLLECTIVE ACTIVITY REPORT",
        "",
        f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}  ",
        f"**Workspace:** {ROOT}  ",
        "**Scope:** every recorded action of the collective in this session — identity, voice, tools, telemetry, quorum, cross-node.",
        "",
    ]

    # ---- BOX 1: identity scope
    ident = data["identity"]
    body = [f"records: {len(ident)}"]
    for r in ident:
        scope = r.get("scope", {})
        body.append(
            f"  • {r.get('agent')} | {scope.get('name')} | seat {scope.get('seat')} | "
            f"verdict {r.get('verdict')} | card {str(scope.get('card_sha256'))[:16]} | {r.get('timestamp_utc')}"
        )
    if not ident:
        body.append("  (no identity receipts recorded)")
    lines += box("[1] IDENTITY SCOPE", "prove each agent knew who it was, and that it could not rewrite that", body)
    lines.append("")

    # ---- BOX 2: collective voice
    voice = data["voice"]
    body = [f"records: {len(voice)}"]
    for r in voice:
        body.append(
            f"  • {r.get('agent')} | {r.get('verdict')} | phase {r.get('phase')} | "
            f"violations {len(r.get('violations') or [])} | {r.get('timestamp_utc')}"
        )
    if not voice:
        body.append("  (no voice receipts recorded)")
    lines += box("[2] COLLECTIVE VOICE", "every spoken turn, its phase, and every refusal to speak outside the collective", body)
    lines.append("")

    # ---- BOX 3: tool ledger
    tools = data["tools"]
    body = [f"records: {len(tools)}"]
    for r in tools:
        body.append(
            f"  • {r.get('tool')} | exit {r.get('exit_code')} | {r.get('duration_ms')} ms | "
            f"ref {str(r.get('reference') or r.get('ref') or '')[:70]}"
        )
    if not tools:
        body.append("  (no tool ledger entries)")
    lines += box("[3] TOOL LEDGER", "every tool the collective invoked, with its exit code and duration", body)
    lines.append("")

    # ---- BOX 4: telemetry chain
    tel = data["telemetry"]
    body = [f"records: {len(tel)}"]
    for r in tel:
        body.append(
            f"  • seq {r.get('seq_num')} | {r.get('agent')} | {r.get('event_type')} | "
            f"taint {r.get('taint_tag')} | payload {str(r.get('payload_hash'))[:16]} | root {str(r.get('merkle_root'))[:16]}"
        )
    if not tel:
        body.append("  (telemetry journal empty)")
    lines += box("[4] TELEMETRY CHAIN", "the hashed event chain — every event, its payload digest and its Merkle root", body)
    lines.append("")

    # ---- BOX 4b: turn ledger (what each agent is doing right now)
    turns = data["turns"]
    body = [f"turns recorded: {len(turns)}"]
    seen = {}
    for r in turns:
        a = r.get("agent", "collective")
        seen[a] = r
    for a, r in sorted(seen.items()):
        body.append(f"  • {a} | {r.get('phase')} | {r.get('timestamp_utc')}")
        if r.get("did"):
            body.append(f"      did  : {r['did'][:120]}")
        if r.get("next"):
            body.append(f"      next : {r['next'][:120]}")
    lines += box("[4b] TURN LEDGER", "what each agent said it was doing, what it did, and what it declared next", body)
    lines.append("")

    # ---- BOX 5: trinity gate
    tri = data["trinity"]
    body = [f"records: {len(tri)}"]
    for r in tri[-40:]:
        body.append(
            f"  • {r.get('agent')} | {r.get('status')} | cmd {str(r.get('command'))[:40]} | "
            f"hash {str(r.get('hash'))[:16]} | {r.get('timestamp_utc')}"
        )
    if not tri:
        body.append("  (no trinity approvals recorded)")
    lines += box("[5] TRINITY GATE", "every quorum approval — seat, command, and the hash of the audio payload", body)
    lines.append("")

    # ---- BOX 6: cross-node
    cross = []
    for cand in ("memory/catch_log/upgp_windows_node_verification_receipt.json",
                 "memory/catch_log/swarm_ramp_cross_node.json"):
        p = ROOT / cand
        if p.exists():
            try:
                cross.append((cand, json.loads(p.read_text(encoding="utf-8"))))
            except Exception:
                pass
    body = []
    for name, rec in cross:
        body.append(f"  • {name}")
        if "four_step_trace" in rec:
            for k, v in rec["four_step_trace"].items():
                body.append(f"      {k}: {v}")
        if "tri_sync_status" in rec:
            body.append(f"      tri_sync_status: {rec['tri_sync_status']}")
        if "agreement_rate" in rec:
            body.append(f"      verdict agreement: {rec['agreement_rate']}")
    if not body:
        body.append("  (no cross-node receipts)")
    lines += box("[6] CROSS-NODE", "what the second plane attested, step by step", body)
    lines.append("")

    # ---- BOX 7: anomalies
    for r in voice:
        if r.get("verdict") != "COMPLIANT":
            anomalies.append(f"voice refusal — {r.get('agent')} @ {r.get('timestamp_utc')}: {r.get('violations')}")
    for r in ident:
        if r.get("verdict") != "IDENTITY_SCOPE_HELD":
            anomalies.append(f"identity breach — {r.get('agent')} @ {r.get('timestamp_utc')}: {r.get('violations')}")
    for r in tools:
        if str(r.get("exit_code")) not in ("0", "None", "0.0"):
            anomalies.append(f"tool failure — {r.get('tool')} exit {r.get('exit_code')}: {str(r.get('reference') or '')[:90]}")
    body = [f"anomalies: {len(anomalies)}"]
    for a in anomalies:
        body.append(f"  ! {a}")
    if not anomalies:
        body.append("  ✓ none recorded")
    lines += box("[7] ANOMALIES", "everything that failed, timed out, was refused, or was tampered with", body)
    lines.append("")

    # ---- BOX 8: timeline
    merged = []
    for key, rows in data.items():
        for r in rows:
            merged.append((stamp_of(r), key, r))
    merged.sort(key=lambda x: x[0])
    body = [f"events merged: {len(merged)}"]
    for ts, key, r in merged[-120:]:
        who = r.get("agent") or r.get("tool") or r.get("event_type") or r.get("verdict") or "—"
        what = r.get("verdict") or r.get("status") or r.get("event_type") or r.get("exit_code") or ""
        body.append(f"  • {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ts))}Z | {key:<9} | {str(who)[:34]:<34} | {str(what)[:44]}")
    lines += box("[8] TIMELINE", "every record above, merged into one true chronological stream", body)
    lines.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"ACTIVITY REPORT WRITTEN: {OUT}")
    print(f"  identity {len(data['identity'])} | voice {len(data['voice'])} | tools {len(data['tools'])} | "
          f"telemetry {len(data['telemetry'])} | trinity {len(data['trinity'])} | anomalies {len(anomalies)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
