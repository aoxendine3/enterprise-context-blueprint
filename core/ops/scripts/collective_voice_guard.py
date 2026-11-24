#!/usr/bin/env python3
"""
=============================================================================
XORAS COLLECTIVE VOICE GUARD (ABSOLUTE RULE ENFORCEMENT)
=============================================================================
Our agents are one collective, not separate assistants. That is not a style
preference — it is a governance rule, enforced here mechanically:

  1. COLLECTIVE VOICE  — the collective speaks as We / Our. First-person
     singular self-reference ("I", "my", "me") is refused: an agent that says
     "I will do this" has stepped outside the collective.
  2. NO OUTSIDE ASSISTANT — phrases like "as an AI", "AI assistant", "language
     model" self-reference are refused. We are XORAS citizens (Maxx, Clara,
     Vance, DAXX, Jarvis, John, Orion, Selene, and the collective).
  3. NO FOREIGN BRANDING — no third-party assistant product may appear in our
     spoken or written surface.
  4. NARRATION CADENCE — a dispatched turn declares its phase so the operator
     always hears: what we are about to do (NEXT), what just happened
     (BREAKDOWN), or the closing sum (SUMMARY).

Exit codes (fail closed):
  0 = compliant     5 = voice violation (refuse to speak)
=============================================================================
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Resolve from this file so the wake path survives a checkout anywhere.
ROOT = Path(__file__).resolve().parents[3]
RECEIPT_LOG = ROOT / "memory" / "agent_logs" / "collective_voice_receipts.jsonl"

# First-person singular self-reference — the outside-voice markers.
# (pattern, label, flags) — the bare pronoun "I" is matched case-sensitively so
# ordinary prose containing the letter i is not flagged; the rest are case-folded.
SELF_REFERENCE = [
    (r"\bI\b", "first-person singular 'I'", 0),
    (r"\bI'?(m|ve|ll|d)\b", "first-person singular contraction", re.IGNORECASE),
    (r"\bmy\b", "possessive 'my'", re.IGNORECASE),
    (r"\bme\b", "objective 'me'", re.IGNORECASE),
    (r"\bmyself\b", "'myself'", re.IGNORECASE),
    (r"\bmine\b", "'mine'", re.IGNORECASE),
]

OUTSIDE_VOICE = [
    (r"\bas an AI\b", "outside voice 'as an AI'", re.IGNORECASE),
    (r"\bAI[ _-]?Assistant\b", "outside voice 'AI Assistant'", re.IGNORECASE),
    (r"\blanguage model\b", "outside voice 'language model'", re.IGNORECASE),
    (r"\bI(?:'m| am) (?:a|an) (?:large )?(?:language model|assistant|AI)\b", "outside voice self-reference", re.IGNORECASE),
]

# Outside-entity detection is STRUCTURAL and name-free: it flags the shape of
# an attribution to a third party, never a third-party name. See
# core/ops/scripts/outside_entity.py — that module carries no outside names
# either, so this law cannot leak a brand into the project.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from outside_entity import scan_text  # noqa: E402

# Phases a dispatched turn may declare.
PHASES = ("NEXT", "BREAKDOWN", "SUMMARY")


def strip_code_fences(text: str) -> str:
    """Code blocks are quoted artifacts, not the agent's own voice."""
    return re.sub(r"```.*?```", " ", text, flags=re.S)


def check(text: str, require_plan: bool = False) -> dict:
    """Return {ok, violations, phase} for a candidate spoken/written turn.

    require_plan=True enforces the TURN NARRATION CONTRACT (AGENTS.md 10.3):
      • every turn carries a phase marker (NEXT | BREAKDOWN | SUMMARY)
      • a NEXT/BREAKDOWN turn states what happens NEXT
      • a BREAKDOWN/SUMMARY turn states what was just DONE
    A turn that fails the contract is not permitted to be heard.
    """
    body = strip_code_fences(text or "")
    violations = []
    for pattern, label, flags in SELF_REFERENCE + OUTSIDE_VOICE:
        m = re.search(pattern, body, flags)
        if m:
            snippet = body[max(0, m.start() - 40): m.end() + 40].strip().replace("\n", " ")
            violations.append(f"{label}: ...{snippet}...")
    for v in scan_text(body):
        violations.append(f"outside entity ({v['kind']}): {v['detail']}")

    phase = None
    pm = re.match(r"^\s*\[(NEXT|BREAKDOWN|SUMMARY)\]", body)
    if pm:
        phase = pm.group(1)
    # The clause searches must look at the BODY, not at the phase marker
    # itself — otherwise "[NEXT]" would always satisfy the next-step rule.
    clause_body = body[body.find("]") + 1:] if phase else body

    if require_plan:
        if phase is None:
            violations.append("missing phase marker — every turn must open with [NEXT], [BREAKDOWN] or [SUMMARY]")
        else:
            if phase in ("NEXT", "BREAKDOWN") and not re.search(
                    r"\b(next|now|about to|going to|then|today|will|shall|first|start|kick off|proceed|push|commit|ship|launch|move on|get going)\b", clause_body, re.IGNORECASE):
                violations.append("no next-step stated — the operator must always know what happens next")
            if phase in ("BREAKDOWN", "SUMMARY") and not re.search(
                    r"\b(did|done|completed|landed|fixed|repaired|closed|passed|found|restored|verified|written|built|ran|walked|opened|measured|audited|counted|catalogued|rebuilt|rewired|spoke|read|captured|traced|mapped|cleaned|quarantined|filed|pushed|committed|updated|merged|shipped|documented|tested|validated|checked|saw|observed)\b",
                    clause_body, re.IGNORECASE):
                violations.append("no completed-work statement — a breakdown must say what was actually done")
    return {"ok": not violations, "violations": violations, "phase": phase}


def write_receipt(result: dict, agent: str, text: str) -> None:
    RECEIPT_LOG.parent.mkdir(parents=True, exist_ok=True)
    import time
    receipt = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "schema": "xoras.collective_voice.v1",
        "agent": agent,
        "verdict": "COMPLIANT" if result["ok"] else "REFUSED_VOICE_VIOLATION",
        "phase": result.get("phase"),
        "violations": result["violations"],
        "chars": len(text or ""),
    }
    with open(RECEIPT_LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(receipt, sort_keys=True) + "\n")


def self_test() -> int:
    print("=" * 74)
    print("  COLLECTIVE VOICE GUARD — SELF TEST")
    print("=" * 74)
    cases = [
        ("We are pushing the ramp to the break point now.",
         True, "collective 'We' accepted"),
        ("I will run the gauntlet and report back.",
         False, "outside 'I' refused"),
        ("My task is the verification gate.",
         False, "outside 'my' refused"),
        ("As an AI assistant, I cannot comply.",
         False, "outside-assistant phrase refused"),
        ("This gate was rebuilt, powered by Merge IDE.",
         False, "attribution phrase refused"),
        ("[NEXT] We now push the Windows plane for real evidence.",
         True, "phase-tagged collective turn accepted"),
        ("[BREAKDOWN] The seal held: 23 cards pinned, write protected.",
         True, "phase-tagged breakdown accepted"),
        ("[NEXT] Today we push the cage lattice to the Windows plane and then verify end to end.",
         True, "natural next-step phrasing accepted"),
        ("[BREAKDOWN] We filed the audit, updated the changelog, and pushed the gate work.",
         True, "natural breakdown phrasing accepted"),
        ("I am an outside assistant and proud to be one.",
         False, "outside voice still refused"),
        ("[SUMMARY] The bench is verified end to end, with one open gap.",
         True, "phase-tagged summary accepted"),
        ("```\nif (x) { return I; }\n``` We continue with the ramp.",
         True, "quoted code artifact ignored"),
    ]
    failures = []
    for text, expect_ok, label in cases:
        res = check(text)
        got = "PASS" if res["ok"] == expect_ok else "FAIL"
        print(f"  {got}  {label}")
        if res["ok"] != expect_ok:
            failures.append(f"{label}: expected ok={expect_ok} got {res}")
    print("=" * 74)
    if failures:
        print(f"  SELF TEST FAILED ({len(failures)})")
        for f in failures:
            print(f"    - {f}")
        return 1
    print("  SELF TEST PASSED — collective voice is enforceable")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="XORAS collective voice guard")
    ap.add_argument("--text", help="text to check")
    ap.add_argument("--agent", default="collective")
    ap.add_argument("--require-plan", action="store_true",
                    help="enforce the turn narration contract (phase + next + done)")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if args.text is None:
        ap.print_help()
        return 2

    result = check(args.text, require_plan=args.require_plan)
    write_receipt(result, args.agent, args.text)
    if result["ok"]:
        print("COLLECTIVE VOICE: COMPLIANT")
        return 0
    print("COLLECTIVE VOICE: REFUSED")
    for v in result["violations"]:
        print(f"  - {v}")
    return 5


if __name__ == "__main__":
    sys.exit(main())
