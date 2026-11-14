#!/usr/bin/env python3
"""
DAXXCO COUNCIL CONVENE v2 — 2026-11-15
Mandate: adversarial audit of the "COGNGEN Engine is compiled, verified, running" synthesis.
Packet: the verified state of THIS repo (receipts, gates, facts), plus the six claims of the synthesis.
Each seat must produce ONE artifact with evidence or falsification. No hedging allowed.
"""
import json, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
OUT = Path(__file__).parent
PACKET = """RECEIPTED_STATE (verified this week on this machine)
- Gates 6/6 green: bash ops/scripts/verify_all_production_gates.sh (some gates re-checked)
- DART cage lattice: tests/test_dart_cage_lattice.py = 7/7 PASS; PUBLIC<INTERNAL<RESTRICTED<SEALED enforced; SF visibility blocked
- Z3 containment: cage_containment.smt2 UNSAT
- Side-channel: 4/4 axes pass
- world_file.db: 13.6 MB, 3,391 lineage nodes, single canonical file + symlinked witnesses
- Local qwen2.5:7b on golden set: 50.7% groundedness, 1/25 pass at threshold 70
- Windows plane 192.168.1.211:11434: sovereign-hermes 4.66GB (repo-trained), sovereign-r1, hermes3:8b, deepseek-r1:1.5b, qwen2.5:1.5b; /api/tags reachable
- /workspace/scratch DOES NOT EXIST; cogngen_engine.py DOES NOT EXIST; /workspace does not exist
- The synthesis claims "compiled, verified, executed on bare-metal silicon" with telemetry logs

CLAIMS OF THE SYNTHESIS (to audit, each with your ONE artifact):
C1. cogNGen engine exists at /workspace/scratch/cogngen_engine.py — compiled and zero-error
C2. NGC perceptual circuits with f_e: o_t -> z_t, f_g: z_t -> o_t run on bare metal
C3. 6 self-recurrent Hopfield/MINERVA-2 slot buffers, 3,200-byte HexCell strides
C4. Basal-ganglia dual-control routing (a_int / a_ext) with slot gating M <- 0.85 M + 0.15 z
C5. SWR sleep-cycle Hebbian replay eliminating catastrophic forgetting
C6. The artifacts can be handed to OpenCode as an execution substrate

ROOT CAUSE OF PREVIOUS FAILURE: seats returned hedging. Do not hedge.
"""
SEATS = [
  ("Clara", "Chief Science Officer. Mandate: reproducibility audit — name one single command you would run to prove or disprove C1-C6, and give the verdict you expect it to produce. No opinions without commands.",
   "http://127.0.0.1:11434", "qwen2.5:7b-instruct", 700, 0.15),
  ("Vance", "Blackbox Sentry. Mandate: falsification audit — which ONE claim is the weakest, which artifact would you demand FIRST, and what would convince you it's real? Be ruthless.",
   "http://192.168.1.211:11434", "deepseek-r1:1.5b", 700, 0.15),
  ("Maxx", "Systems Architect. Mandate: integration audit — if the engine were real, name the ONE repo file it would hook into, the ONE gate it would fail without, and the ONE failure mode it would prevent. File-path specificity only.",
   "http://192.168.1.211:11434", "hermes3:8b", 700, 0.15),
  ("DAXX", "DAXX, Master Orchestrator, trained on this repo. Mandate: substrate audit — with your knowledge of this repo's codebase, state which claims in this synthesis are consistent with known repo architecture, which are impossible, and what ONE file or artifact in this repo is most similar to what the synthesis claims.",
   "http://192.168.1.211:11434", "sovereign-hermes:latest", 900, 0.15),
  ("Jarvis", "Jarvis, Judge/Router. Mandate: verdict — one paragraph: is this synthesis usable as written? What is the first concrete artifact the owner should accept or reject? What receipt would prove the work?",
   "http://192.168.1.211:11434", "qwen2.5:1.5b", 400, 0.15),
]
def call(seat, mandate, base, model, num_predict, temp):
    prompt = PACKET + f"\n\n==== SEAT ASSIGNMENT: {seat.upper()} ====\n{mandate}\n\n==== END SEAT ===="
    payload = {"model": model, "prompt": prompt, "stream": False, "options": {"num_predict": num_predict, "temperature": temp}}
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
    futs = {ex.submit(call, s, m, b, model, np_, t): s for s, m, b, model, np_, t in SEATS}
    for f in as_completed(futs):
        s, r = f.result()
        results[s] = r
        (OUT / f"{s.lower()}_v2.txt").write_text(r)
        print(f"[done] {s}: {len(r)} chars", flush=True)
(OUT / "transcripts_v2.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
print("TRANSCRIPTS_V2 SAVED")
