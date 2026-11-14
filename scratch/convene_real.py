#!/usr/bin/env python3
"""DaxxCo council — REAL seats, REAL artifact mandates, SSOT law only."""
import json, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
PACKET = (ROOT / "scratch/COUNCIL_PACKET.md").read_text()
OUT = ROOT / "scratch/daxxco_2026-11-15"
OUT.mkdir(parents=True, exist_ok=True)
SEATS = [
    ("clara", "You are Clara, Chief Science Officer of XORAS. Mandate: method you will not compromise. The packet contains verified state (gates, cage lattice, side-channel, groundedness). The synthesis documents claim a 'Reality SSOT + CogNGen bridge for our coding agent.' Your job: define the MINIMAL algorithm that makes that TRUE without introducing any new runtime. You get: gates, cage lattice, DART, world_file.db, Notary receipts, Windows plane. Output: 6-step algorithm, each step named as a repo file or command that must exist — if any step needs code that does not exist, name it explicitly as TODO with the smallest possible implementation. ≤350 words.", "http://192.168.1.211:11434", "sovereign-r1:latest", 700, 0.35),
    ("vance", "You are Vance, Blackbox Sentry. Mandate: falsify. The packet contains the evidence and the failures. Produce your falsification list for the synthesis: (a) which claims fall first, (b) which single test would most cheaply prove the bridge fake, (c) the smallest change that makes it real. Output as a numbered list, ≤300 words.", "http://192.168.1.211:11434", "deepseek-r1:1.5b", 600, 0.4),
    ("maxx", "You are Maxx, Systems Architect. Mandate: buildable design. Produce the actual file layout + content sketch for a pre-flight gate script that OpenCode must run before any task is accepted: what it checks (named gates), what evidence it emits, where the receipt lands, what exit code on failure. ≤350 words. Concrete file names only.", "http://192.168.1.211:11434", "hermes3:8b", 700, 0.35),
    ("daxx", "You are DAXX, Master Orchestrator, sovereign-trained on the SSOT corpus. Mandate: iteration truth. Using everything you know of this repo — world_file.db, merkle_root.hash, cage_containment.smt2, DartDb, the 14-gate gauntlet, MARS — produce the smallest REAL artifact that satisfies the synthesis: a pre-flight sequence script, call it `ops/scripts/reality_gate.sh` or `reality_gate.py`, that runs our actual gates and emits a signed-ish receipt. Output the actual script body (shell or python). ≤500 words. No prose about 'vision' — code only.", "http://192.168.1.211:11434", "sovereign-hermes:latest", 900, 0.35),
    ("jarvis", "You are Jarvis, Judge/Router. Mandate: verdict with receipts. After hearing nothing else: given verified state and the synthesis, is proceeding to implement worth it? Name ONE acceptance criterion for the build, and ONE command you would run to accept it. ≤200 words.", "http://192.168.1.211:11434", "qwen2.5:1.5b", 300, 0.35),
]
def call(seat, mandate, base, model, np_, temp):
    prompt = PACKET + "\n\n==== SEAT ASSIGNMENT: " + seat.upper() + " ====\n" + mandate + "\n\n==== END ===="
    payload = {"model": model, "prompt": prompt, "stream": False, "options": {"num_predict": np_, "temperature": temp}}
    try:
        out = subprocess.run(["curl", "-s", "--max-time", "300", "-H", "Content-Type: application/json", "-d", json.dumps(payload), base + "/api/generate"],
                             capture_output=True, timeout=305)
        d = json.loads(out.stdout.decode())
        text = (d.get("response") or d.get("thinking") or "").strip()
        return seat, text
    except Exception as e:
        return seat, f"ERROR: {e}"
results = {}
with ThreadPoolExecutor(max_workers=5) as ex:
    futs = {ex.submit(call, n, m, b, model, np_, temp): n for n, m, b, model, np_, temp in SEATS}
    for f in as_completed(futs):
        s, r = f.result()
        results[s] = r
        (OUT / f"{s}.txt").write_text(r)
        print(f"[done] {s}: {len(r)} chars", flush=True)
(OUT / "transcripts.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
print("TRANSCRIPTS:", OUT / "transcripts.json")
