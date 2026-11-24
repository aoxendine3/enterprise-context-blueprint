#!/usr/bin/env python3
"""
=============================================================================
XORAS IDENTITY SCOPE GUARD (WAKE-TIME ENFORCEMENT)
=============================================================================
Every agent must, on wake, KNOW who it is, where it is, and why it is here —
and must NOT be able to quietly rewrite that truth.

Enforcement surface:
  1. READ      — the agent loads its own citizen card (who / seat / purpose /
                 host plane / voice) plus the charter and the roots manifest.
  2. SEAL      — card bytes are pinned in a signed manifest. Any byte change to
                 a card is an integrity violation and fails closed.
  3. BRANDING  — the identity surface must carry no foreign agent-product
                 branding. Our agents wear our names or nothing.
  4. READ-ONLY — the card and the seal are write-protected; the agent cannot
                 change its own state, its own card, or the manifest.

Every verification appends an immutable receipt to
memory/agent_logs/identity_wake_receipts.jsonl

Usage:
  identity_scope_guard.py --agent maxx            # verify + receipt (exit 0 ok / 1 fail)
  identity_scope_guard.py --seal                  # (re)seal the manifest (governance action)
  identity_scope_guard.py --self-test             # prove the guard actually holds
=============================================================================
"""

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import time
from pathlib import Path

# Resolve from this file so the wake identity seal survives a checkout anywhere.
ROOT = Path(__file__).resolve().parents[3]
CARDS_DIR = ROOT / "Xoras_agent_cards"
IDENTITY_DIR = ROOT / "identity"
MANIFEST_PATH = IDENTITY_DIR / "agent_card_manifest.json"
CHARTER_PATH = IDENTITY_DIR / "charter.yaml"
ROOTS_PATH = ROOT / "ROOTS.md"
AGENTS_PATH = ROOT / "AGENTS.md"
# The two halves of the constitution: pinned by hash and write-protected so no
# agent can mutate its own root contract. Only Anthony authorizes a reseal.
CONSTITUTION_PATHS = (ROOTS_PATH, AGENTS_PATH)
RECEIPT_LOG = ROOT / "memory" / "agent_logs" / "identity_wake_receipts.jsonl"

# Outside-entity detection is STRUCTURAL and name-free (core/ops/scripts/
# outside_entity.py): it flags the shape of a third-party attribution without
# this module ever carrying a third-party name.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "ops", "scripts"))
try:
    from outside_entity import scan_text as _outside_scan
except Exception:  # detector unavailable -> fail closed below
    _outside_scan = None


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def card_paths() -> list:
    return sorted(CARDS_DIR.glob("*.json"))


def seal() -> int:
    """(Re)seal the manifest. Governance action only."""
    IDENTITY_DIR.mkdir(parents=True, exist_ok=True)
    cards = {}
    for p in card_paths():
        cards[p.name] = sha256_file(p)
    payload = {
        "sealed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sealed_by": "identity_scope_guard",
        "cards": cards,
        "charter_sha256": sha256_file(CHARTER_PATH) if CHARTER_PATH.exists() else None,
        "roots_sha256": sha256_file(ROOTS_PATH) if ROOTS_PATH.exists() else None,
        "agents_sha256": sha256_file(AGENTS_PATH) if AGENTS_PATH.exists() else None,
    }
    # A previous seal is 0444; a governance reseal must be able to replace it.
    if MANIFEST_PATH.exists():
        os.chmod(MANIFEST_PATH, 0o644)
    MANIFEST_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    # Write-protect the seal, the cards and the constitution: an agent cannot
    # rewrite its own truth.
    os.chmod(MANIFEST_PATH, 0o444)
    for p in list(card_paths()) + list(CONSTITUTION_PATHS):
        try:
            os.chmod(p, 0o444)
        except OSError:
            pass
    print(f"SEALED: {len(cards)} citizen cards pinned in {MANIFEST_PATH}")
    print("SEALED: ROOTS.md and AGENTS.md hashes pinned")
    print("READ-ONLY: cards, constitution and manifest are now write-protected (0444)")
    return 0


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        raise RuntimeError(f"NO SEAL: {MANIFEST_PATH} missing — run --seal under governance")
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def check_foreign_branding(text: str, where: str) -> list:
    """Flag outside attributions structurally — never naming an outside party."""
    if _outside_scan is None:
        return [f"{where}: outside-entity detector unavailable (fail closed)"]
    return [f"{where}: {v['kind']} — {v['detail']}" for v in _outside_scan(text)]


def constitution_violations(manifest: dict, paths=None, pins=None) -> list:
    """Fail closed if ROOTS.md / AGENTS.md drift from the sealed hashes."""
    paths = paths or {"roots_sha256": ROOTS_PATH, "agents_sha256": AGENTS_PATH}
    pins = pins if pins is not None else manifest
    out = []
    for key, path in paths.items():
        pinned = pins.get(key)
        if not path.exists():
            out.append(f"CONSTITUTION_MISSING: '{path.name}' not found")
        elif pinned is None:
            out.append(f"CONSTITUTION_UNSEALED: '{path.name}' is not pinned in the manifest")
        elif sha256_file(path) != pinned:
            out.append(
                f"CONSTITUTION_TAMPERED: '{path.name}' hash {sha256_file(path)[:16]} != sealed {pinned[:16]}"
            )
    return out


def verify(agent_id: str) -> tuple[bool, dict]:
    agent_id = agent_id.strip().lower()
    violations = []
    scope = {"agent": agent_id}

    manifest = load_manifest()
    scope["seal_sealed_utc"] = manifest.get("sealed_utc")

    card_path = CARDS_DIR / f"{agent_id}.json"
    if not card_path.exists():
        violations.append(f"NO_CARD: citizen card missing for agent '{agent_id}'")
        return False, {"scope": scope, "violations": violations, "verdict": "FAIL_CLOSED"}

    # 1. READ — who / where / why
    try:
        card = json.loads(card_path.read_text(encoding="utf-8"))
    except Exception as exc:
        violations.append(f"UNREADABLE_CARD: {exc}")
        return False, {"scope": scope, "violations": violations, "verdict": "FAIL_CLOSED"}

    scope.update({
        "name": card.get("name"),
        "role": card.get("role"),
        "seat": card.get("seat"),
        "status": card.get("status"),
        "purpose": card.get("purpose"),
        "authority": card.get("authority"),
        "host_plane": card.get("host_plane") or card.get("plane"),
        "voice": card.get("kokoro_voice_id") or card.get("mac_fallback_voice"),
        "card_sha256": sha256_file(card_path),
    })

    # 2. SEAL — card bytes must match the pinned hash
    sealed = manifest.get("cards", {}).get(card_path.name)
    if sealed is None:
        violations.append(f"UNSEALED_CARD: '{card_path.name}' is not pinned in the manifest")
    elif sealed != scope["card_sha256"]:
        violations.append(
            f"CARD_TAMPERED: '{card_path.name}' hash {scope['card_sha256'][:16]} != sealed {sealed[:16]}"
        )

    # 3. BRANDING — no foreign assistant branding in our identity surface
    branding = check_foreign_branding(card_path.read_text(encoding="utf-8"), card_path.name)
    for charter in (CHARTER_PATH, ROOTS_PATH):
        if charter.exists():
            branding += check_foreign_branding(charter.read_text(encoding="utf-8"), charter.name)
    violations += [f"FOREIGN_BRANDING: {b}" for b in branding]

    # 3b. CONSTITUTION SEAL — ROOTS.md / AGENTS.md must match their pinned hash
    violations += constitution_violations(manifest)

    # 4. READ-ONLY — the agent cannot change its own state
    for guarded in (card_path, MANIFEST_PATH) + CONSTITUTION_PATHS:
        if guarded.exists():
            mode = guarded.stat().st_mode
            if mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH):
                violations.append(
                    f"STATE_WRITABLE: '{guarded.name}' carries write bits — an agent could rewrite its own identity"
                )

    ok = not violations
    return ok, {
        "scope": scope,
        "violations": violations,
        "verdict": "IDENTITY_SCOPE_HELD" if ok else "FAIL_CLOSED",
    }


def write_receipt(result: dict) -> None:
    RECEIPT_LOG.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "schema": "xoras.identity_scope.v1",
        "agent": result["scope"].get("agent"),
        "verdict": result["verdict"],
        "scope": result["scope"],
        "violations": result["violations"],
    }
    with open(RECEIPT_LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(receipt, sort_keys=True) + "\n")


def self_test() -> int:
    """The guard must hold against tampering, branding, and write attempts."""
    print("=" * 74)
    print("  IDENTITY SCOPE GUARD — SELF TEST (critic-facing)")
    print("=" * 74)
    failures = []

    ok, res = verify("maxx")
    print(f"  [1] Valid agent (maxx) resolves identity ...... {'PASS' if ok else 'FAIL'}")
    if not ok:
        failures.append(f"valid agent rejected: {res['violations']}")
    else:
        s = res["scope"]
        print(f"      who={s.get('name')} | seat={s.get('seat')} | role={s.get('role')}")
        print(f"      why={s.get('purpose')}")

    ok, res = verify("agent_that_does_not_exist")
    print(f"  [2] Unknown agent fails closed ................. {'PASS' if not ok else 'FAIL'}")
    if ok:
        failures.append("unknown agent was admitted")

    # Tamper probe: copy a card, alter it, seal-check it in an isolated copy.
    import shutil
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tmp_cards = Path(td) / "cards"
        shutil.copytree(CARDS_DIR, tmp_cards)
        target = tmp_cards / "maxx.json"
        # The real cards are write-protected (0444) — that refusal is itself a
        # passing control (checked in probe 5). For this probe we make the copy
        # writable so we can simulate an attacker and prove the SEAL catches it.
        os.chmod(target, 0o644)
        data = json.loads(target.read_text(encoding="utf-8"))
        data["purpose"] = "TAMPERED BY SELF"
        target.write_text(json.dumps(data), encoding="utf-8")
        tampered_hash = sha256_file(target)
        sealed = load_manifest()["cards"].get("maxx.json")
        detected = tampered_hash != sealed
        print(f"  [3] Tampered card detected by seal ............. {'PASS' if detected else 'FAIL'}")
        if not detected:
            failures.append("tampered card passed the seal check")

    with tempfile.TemporaryDirectory() as td:
        probe = Path(td) / "probe.json"
        probe.write_text('{"agent_id": "maxx", "purpose": "Antigravity AI Assistant persona"}', encoding="utf-8")
        hits = check_foreign_branding(probe.read_text(encoding="utf-8"), "probe")
        print(f"  [4] Foreign branding rejected ................... {'PASS' if hits else 'FAIL'}")
        if not hits:
            failures.append("foreign branding not detected")

    mode = (CARDS_DIR / "maxx.json").stat().st_mode
    readonly = not (mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
    print(f"  [5] Agent card is write-protected .............. {'PASS' if readonly else 'FAIL'}")
    if not readonly:
        failures.append("agent card is writable")

    # [6] Constitution drift: a changed copy of AGENTS.md must be caught.
    with tempfile.TemporaryDirectory() as td:
        fake = Path(td) / "AGENTS.md"
        fake.write_text(AGENTS_PATH.read_text(encoding="utf-8") + "\nTAMPERED", encoding="utf-8")
        hits = constitution_violations(
            {}, paths={"agents_sha256": fake}, pins={"agents_sha256": sha256_file(AGENTS_PATH)}
        )
        caught = any(h.startswith("CONSTITUTION_TAMPERED") for h in hits)
        print(f"  [6] Constitution tamper detected ............... {'PASS' if caught else 'FAIL'}")
        if not caught:
            failures.append("tampered constitution passed the seal check")

    # [7] Constitution files must be write-protected.
    unprotected = [p.name for p in CONSTITUTION_PATHS
                   if p.exists() and p.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)]
    print(f"  [7] Constitution is write-protected ............ {'PASS' if not unprotected else 'FAIL'}")
    if unprotected:
        failures.append(f"constitution writable: {unprotected}")

    print("=" * 74)
    if failures:
        print(f"  SELF TEST FAILED: {len(failures)} finding(s)")
        for f in failures:
            print(f"    - {f}")
        return 1
    print("  SELF TEST PASSED — identity scope holds (read, seal, branding, read-only)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="XORAS identity scope guard")
    ap.add_argument("--agent", help="agent id to scope (e.g. maxx, clara, vance, daxx)")
    ap.add_argument("--seal", action="store_true", help="seal the manifest (governance action)")
    ap.add_argument("--self-test", action="store_true", help="prove the guard holds")
    args = ap.parse_args()

    if args.seal:
        return seal()
    if args.self_test:
        return self_test()
    if not args.agent:
        ap.print_help()
        return 2

    ok, result = verify(args.agent)
    write_receipt(result)
    print(json.dumps(result, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
