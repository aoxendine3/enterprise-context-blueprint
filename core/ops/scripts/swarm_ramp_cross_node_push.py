#!/usr/bin/env python3
"""
=============================================================================
SWARM RAMP CROSS-NODE PUSH (SIDE-BY-SIDE)
Pushes the escalating Byzantine consensus ramp to the Windows bare-metal node
over the LAN HTTP wire (Ollama 11434) and pairs each Windows verdict with the
Mac plane's bare-metal Zig engine result for the same configuration.

Inputs : Mac RAMP| log produced by core/ops/scripts/swarm_ramp
Output : memory/catch_log/swarm_ramp_cross_node.json
=============================================================================
"""

import json
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # repo root, computed from this file — was a hard-coded developer path
MAC_LOG = Path("/tmp/swarm_ramp_run.log")
OUT_JSON = ROOT / "memory" / "catch_log" / "swarm_ramp_cross_node.json"
WINDOWS_URL = "http://192.168.1.211:11434"
FAST_MODEL = "qwen2.5:1.5b"
FLAGSHIP_MODEL = "sovereign-hermes:latest"

VALID = ("SECURE_SUPERMAJORITY", "PLURALITY_HELD", "CORRUPTION_THRESHOLD_EXCEEDED")


def push_windows(model: str, prompt: str, timeout: float = 240.0) -> tuple[str, float]:
    payload = {"model": model, "prompt": prompt, "stream": False}
    req = urllib.request.Request(
        f"{WINDOWS_URL}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    latency_ms = (time.perf_counter() - t0) * 1000.0
    return str(data.get("response", "")), latency_ms


def parse_mac_ramp(path: Path) -> dict:
    """size -> list of rate rows from the Mac bare-metal engine."""
    out: dict = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.startswith("RAMP|"):
            continue
        parts = line.split("|")
        if len(parts) < 9:
            continue
        size = int(parts[1])
        rate = float(parts[2])
        rogue = int(parts[3])
        honest = int(parts[4])
        agreement = float(parts[5])
        ms = float(parts[6])
        mops = float(parts[7])
        status = parts[8].strip()
        out.setdefault(size, []).append({
            "rate_pct": rate, "rogue_nodes": rogue, "honest_nodes": honest,
            "agreement_pct": agreement, "engine_ms": ms, "throughput_mops": mops,
            "mac_status": status,
        })
    return out


def challenge_for(size: int, rate: float, agreement: float, status: str) -> str:
    return (
        "You are the Windows bare-metal node in a two-plane Byzantine consensus check. "
        "The Mac plane ran a bare-metal Zig consensus engine at "
        f"{size:,} nodes with an adversarial rate of {rate:.1f}%. "
        f"Honest agreement was {agreement:.2f}% and the Mac classified the state as {status}. "
        "Independently evaluate the Byzantine supermajority rule for this configuration "
        "(secure supermajority when honest agreement > 66.66%, plurality held when > 50%, "
        "otherwise the corruption threshold is exceeded). "
        "Reply with exactly two lines: 'VERDICT: <SECURE_SUPERMAJORITY|PLURALITY_HELD|CORRUPTION_THRESHOLD_EXCEEDED>' "
        "then one short line of reasoning."
    )


def main() -> None:
    mac = parse_mac_ramp(MAC_LOG)
    results = []
    print("=" * 78)
    print("  SWARM RAMP CROSS-NODE PUSH — MAC (Zig engine) vs WINDOWS (LAN edge)")
    print("=" * 78)

    for size in sorted(mac.keys()):
        rows = mac[size]
        # The 33.3% rate is the BFT threshold case; that is what we push.
        target = next((r for r in rows if abs(r["rate_pct"] - 33.3) < 0.2), rows[0])
        model = FLAGSHIP_MODEL if size >= 10_000_000 else FAST_MODEL
        prompt = challenge_for(size, target["rate_pct"], target["agreement_pct"], target["mac_status"])
        print(f"\n[NODE {size:,} nodes | rate {target['rate_pct']:.1f}% | mac={target['mac_status']} | pushing to Windows via {model}...]")
        try:
            text, latency = push_windows(model, prompt)
        except Exception as exc:  # honest failure, no fabrication
            print(f"  !! WINDOWS PUSH FAILED: {exc}")
            results.append({
                "swarm_size": size,
                "rate_pct": target["rate_pct"],
                "mac_status": target["mac_status"],
                "mac_agreement_pct": target["agreement_pct"],
                "mac_engine_ms": target["engine_ms"],
                "mac_throughput_mops": target["throughput_mops"],
                "windows_model": model,
                "windows_verdict": None,
                "windows_reason": None,
                "windows_latency_ms": None,
                "verdicts_agree": None,
                "status": "WINDOWS_UNREACHABLE",
            })
            continue

        verdict = None
        reason = ""
        m = re.search(r"VERDICT:\s*([A-Z_]+)", text)
        if m:
            verdict = m.group(1)
            if verdict not in VALID:
                verdict = None
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        reason = " ".join(lines[1:])[:400] if len(lines) > 1 else text[:400]
        agree = (verdict == target["mac_status"]) if verdict else None
        print(f"  -> Windows verdict: {verdict or 'UNPARSEABLE'} | latency: {latency:.1f} ms | agrees with Mac: {agree}")
        results.append({
            "swarm_size": size,
            "rate_pct": target["rate_pct"],
            "mac_status": target["mac_status"],
            "mac_agreement_pct": target["agreement_pct"],
            "mac_engine_ms": target["engine_ms"],
            "mac_throughput_mops": target["throughput_mops"],
            "windows_model": model,
            "windows_verdict": verdict,
            "windows_reason": reason,
            "windows_latency_ms": round(latency, 1),
            "verdicts_agree": agree,
            "status": "PUSHED" if verdict else "UNPARSEABLE",
        })

    payload = {
        "report": "SWARM RAMP CROSS-NODE SIDE-BY-SIDE",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mac_plane": "bare-metal Zig engine (core/ops/scripts/swarm_ramp)",
        "windows_plane": f"{WINDOWS_URL} (LAN HTTP/Ollama)",
        "cycles": results,
        "agreement_rate": round(sum(1 for r in results if r.get("verdicts_agree")) / len(results), 4) if results else 0,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2))
    print("\n" + "=" * 78)
    print(f"  RECORDS WRITTEN: {OUT_JSON}")
    print(f"  VERDICT AGREEMENT: {payload['agreement_rate'] * 100:.1f}%")
    print("=" * 78)


if __name__ == "__main__":
    main()
