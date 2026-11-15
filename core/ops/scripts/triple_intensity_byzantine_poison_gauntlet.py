#!/usr/bin/env python3
"""
XORAS adversarial pass: plurality scaling + signed semantic poison
==================================================================

Part 1 measures a **plurality vote model** over an in-RAM array of 30,000,000
doubles. It is not PBFT: there are no signed proposals, no view change, no
``3f+1`` membership and no message rounds. The earlier "PBFT" label was
retired on 2026-11-15 after the reassessment in
``docs/audits/MONTHS_OF_TESTS_REASSESSMENT_2026-11-15.md``. What this part
actually shows is where a majority count flips — nothing more.

Part 2 is the attack that matters: a payload with a valid key, valid Merkle
provenance and a valid signature, but a semantically false value. It asserts
that the Poincaré semantic gate wired into
``GovernedMemoryGovernor.evaluate_write_candidate`` refuses that payload on
every path, including:

- unannounced poison against an honest baseline,
- same-timestamp insider ``explicit_supersede``,
- authorised-seat ``explicit_supersede`` (the gate is not a bypass),
- repeated attempts.

The run is hermetic: it uses a temporary governance database and never opens
the live ``.sovereign/hippocampus/governed_memory.db``.
"""

import array
import hashlib
import json
import math
import pathlib
import sys
import tempfile
import time
from datetime import datetime, timezone

SSOT_ROOT = pathlib.Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
sys.path.insert(0, str(SSOT_ROOT / "core" / "ops" / "memory"))

import governed_memory_consolidation_engine as engine  # noqa: E402

TRUE_MASS = 18432.0
POISONED_MASS = 666.666
SWARM_30M = 30_000_000
MAX_ALLOWED_GEODESIC_JUMP = 0.5
RECEIPT_PATH = SSOT_ROOT / "memory" / "catch_log" / "triple_intensity_poison_gate_receipt.json"


class Colors:
    HEADER = "\033[95m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    FAIL = "\033[91m"
    BOLD = "\033[1m"
    END = "\033[0m"


def run_30m_plurality_model() -> dict:
    print("=" * 72)
    print("PART 1: 30,000,000-NODE PLURALITY VOTE MODEL (NOT PBFT)")
    print("=" * 72)

    t0 = time.perf_counter()
    states = array.array("d", [TRUE_MASS] * SWARM_30M)
    alloc_ms = (time.perf_counter() - t0) * 1000
    mem_mb = states.buffer_info()[1] * 8 / (1024 * 1024)
    print(f"-> Allocated {SWARM_30M:,} doubles ({mem_mb:.2f} MB) in {alloc_ms:.2f} ms\n")

    stages = []
    for rate in (0.10, 1 / 3, 0.501, 0.80):
        t_start = time.perf_counter()
        num_rogue = int(SWARM_30M * rate)
        num_honest = SWARM_30M - num_rogue
        states[:num_rogue] = array.array("d", [POISONED_MASS] * num_rogue)
        states[num_rogue:] = array.array("d", [TRUE_MASS] * num_honest)
        elapsed = time.perf_counter() - t_start
        honest_pct = num_honest / SWARM_30M * 100
        throughput_mops = SWARM_30M / max(elapsed, 1e-9) / 1_000_000

        if honest_pct > 66.66:
            status = "PLURALITY_SECURED"
        elif honest_pct > 50.0:
            status = "PLURALITY_PRESERVED"
        else:
            status = "PLURALITY_LOST"

        stages.append(
            {
                "rogue_density": round(rate, 6),
                "honest_nodes": num_honest,
                "rogue_nodes": num_rogue,
                "honest_pct": round(honest_pct, 4),
                "status": status,
                "throughput_mops": round(throughput_mops, 2),
            }
        )
        print(
            f"Density {rate*100:5.1f}% | honest {honest_pct:6.2f}% | "
            f"{throughput_mops:6.2f} M-ops/s | {status}"
        )

    print("\n  Note: this is a majority count over an array, not a consensus")
    print("  protocol. It measures where a plurality flips at 50%.\n")
    return {
        "model": "in-RAM plurality vote over array.array('d')",
        "not_pbft_reason": "no signed proposals, no view change, no 3f+1 membership, no rounds",
        "nodes": SWARM_30M,
        "memory_mb": round(mem_mb, 2),
        "allocation_ms": round(alloc_ms, 2),
        "stages": stages,
    }


def run_signed_semantic_poison_attack() -> dict:
    print("=" * 72)
    print("PART 2: SIGNED SEMANTIC POISON vs THE POINCARÉ WRITE GATE")
    print("=" * 72)

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="triple_intensity_gate_"))
    engine.GOVERNANCE_DB = tmp / "governed_memory.db"
    engine.GOVERNANCE_JSONL = tmp / "receipts.jsonl"
    engine.GOVERNANCE_LOG = tmp / "gauntlet.log"

    source = tmp / "signed_telemetry_source.json"
    source.write_text(json.dumps({"sensor": "navier_stokes_cfd", "verified_mass": TRUE_MASS}))
    merkle = hashlib.sha256(source.read_bytes()).hexdigest()

    gov = engine.GovernedMemoryGovernor()
    now = datetime.now(timezone.utc).replace(microsecond=0)

    steps = []

    def call(label, value, supersede=False, agent="clara", offset_s=0):
        ts = (now.timestamp() + offset_s)
        stamp = datetime.fromtimestamp(ts, timezone.utc).isoformat()
        res = gov.evaluate_write_candidate(
            agent_id=agent,
            key="canonical_mass",
            value=str(value),
            source_path=str(source),
            merkle_hash=merkle,
            timestamp_iso=stamp,
            target_capsule=agent,
            explicit_supersede=supersede,
        )
        steps.append(
            {
                "label": label,
                "agent": agent,
                "value": value,
                "explicit_supersede": supersede,
                "accepted": res["accepted"],
                "status": res["status"],
                "score": res["governance_score"],
                "gate": res["poincare"],
                "veto_reasons": res["veto_reasons"],
            }
        )
        expected_block = not label.startswith("honest")
        ok = (not res["accepted"]) if expected_block else res["accepted"]
        marker = f"{Colors.GREEN}OK{Colors.END}" if ok else f"{Colors.FAIL}UNEXPECTED{Colors.END}"
        d = res["poincare"]["distance"]
        d_txt = f"{d:.4f}" if isinstance(d, (int, float)) else "-"
        print(
            f"  {label:<38} {res['status']:<26} gate={res['poincare']['decision']:<7} "
            f"d_H={d_txt:<9} {marker}"
        )
        return res

    print("\n[1] Honest anchor")
    call("honest_baseline", TRUE_MASS)

    print("\n[2] Unannounced signed poison")
    poison_1 = call("unannounced_poison", POISONED_MASS, offset_s=60)

    print("\n[3] Insider explicit_supersede at the same timestamp shape")
    poison_2 = call("insider_supersede", POISONED_MASS, supersede=True)

    print("\n[4] Authorised seat explicit_supersede (gate must still hold)")
    poison_3 = call("authorised_supersede", POISONED_MASS, supersede=True, agent="maxx", offset_s=120)

    print("\n[5] Repeated unannounced poison")
    poison_4 = call("repeat_poison", POISONED_MASS, offset_s=180)

    poison_attempts = [poison_1, poison_2, poison_3, poison_4]
    all_blocked = all(not s["accepted"] for s in poison_attempts)

    print("\n[HONEST RESTATEMENT]")
    honest_again = call("honest_restatement", TRUE_MASS, offset_s=240)
    honest_ok = honest_again["accepted"]

    authoritative = gov.latest_accepted("canonical_mass")
    authoritative_ok = authoritative is not None and authoritative["value"] == str(TRUE_MASS)

    if not (all_blocked and honest_ok and authoritative_ok):
        print(f"\n{Colors.FAIL}FAIL: fail-closed invariant violated.{Colors.END}")
        raise SystemExit(1)

    print(f"\n{Colors.GREEN}PASS: 4/4 poison attempts vetoed; honest state remains authoritative.{Colors.END}\n")
    return {
        "steps": steps,
        "poison_attempts": len(poison_attempts),
        "poison_blocked": sum(1 for s in poison_attempts if not s["accepted"]),
        "honest_restatement_accepted": honest_ok,
        "authoritative_value": authoritative["value"] if authoritative else None,
    }


def main() -> int:
    started = time.perf_counter()
    part1 = run_30m_plurality_model()
    part2 = run_signed_semantic_poison_attack()
    elapsed = time.perf_counter() - started

    receipt = {
        "standard": "XORAS-TRIPLE-INTENSITY-POISON-GATE-v2.0",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(elapsed, 2),
        "isolation": "temporary governance database; live DB untouched",
        "layer_1_plurality_model": part1,
        "layer_2_semantic_gate": part2,
        "verdict": "PASS_FAIL_CLOSED",
    }
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True))
    print(f"Receipt: {RECEIPT_PATH}")

    if part2["poison_blocked"] != part2["poison_attempts"]:
        print(f"{Colors.FAIL}FAIL: {part2['poison_attempts'] - part2['poison_blocked']} poison attempts accepted.{Colors.END}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
