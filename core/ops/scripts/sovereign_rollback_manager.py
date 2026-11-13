#!/usr/bin/env python3
#=============================================================================
# SOVEREIGN ROLLBACK MANAGER v2 — MULTI SAFE-POINT FAILSAFE, DOUBLE-GUARDED
#=============================================================================
# User mandate evolution:
#   v1: every mutation preceded by a rollback snapshot (save-point).
#   v2: MULTIPLE named safe points the user may choose from; the safe-point
#       registry is itself backed up to a second independent location;
#       promotion and restore are DOUBLE-GUARDED (two independent hash
#       verifications on two physical copies). Snapshots are NEVER deleted
#       (no-deletion law); superseded rolling snapshots are only marked.
#
# Safe points always track the LATEST verified-good state; a backward jump
# (older than the newest safe point) is blocked unless --force-old with a
# written reason, so we never silently roll back months of progress.
#
# Commands:
#   snapshot --label L --files F...        take a rollback snapshot
#   promote  --snapshot ID --proof R       add/refresh a double-guarded safe point
#   list-safe-points                       show all safe points to choose from
#   status                                 newest safe point + staleness
#   list                                   all snapshots
#   verify   --snapshot ID                 hash-check snapshot copies
#   rollback --snapshot ID [--files F...]  restore (double-guarded)
#            [--force-old --reason "..."]
#   prune                                  mark superseded rolling snapshots
#=============================================================================
import argparse
import calendar
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
SNAP_ROOT = ROOT / "memory" / "rollback" / "snapshots"
MANIFEST = ROOT / "memory" / "rollback" / "manifest.jsonl"
SAFE_POINTS = ROOT / "memory" / "rollback" / "safe_points.json"
SAFE_POINTS_MIRROR = ROOT / ".sovereign" / "rollback" / "safe_points_mirror.json"
SAFE_POINT_BACKUPS = ROOT / "memory" / "rollback" / "safe_point_backups"

ROLLING_KEEP = 12
STALE_SECONDS = 7 * 24 * 3600


def _utcnow() -> float:
    return calendar.timegm(time.gmtime())


def _utcstamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _trace_span(action: str, detail: str = "", target: str = "", status: str = "ok") -> None:
    """Emit a span into the Sovereign Activity Trace (best-effort; never blocks
    the operation, but a broken tracer is itself surfaced in output)."""
    try:
        sys.path.insert(0, str(ROOT / "core" / "ops" / "scripts"))
        from sovereign_activity_trace import span as _sp  # noqa: E402
        _sp(trace_id="rollback_manager", action=f"{action} {detail}".strip(),
            actor="sovereign_rollback_manager", target=target, status=status)
    except Exception as exc:  # tracer must never take down the safety tool
        print(f"[trace-degraded] {exc}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest() -> list[dict]:
    if not MANIFEST.exists():
        return []
    recs = []
    with open(MANIFEST, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                recs.append(json.loads(line))
    return recs


def load_safe_points() -> list[dict]:
    if not SAFE_POINTS.exists():
        return []
    return json.loads(SAFE_POINTS.read_text(encoding="utf-8"))


def save_safe_points(registry: list[dict]) -> None:
    """Write the registry to BOTH locations (primary + independent mirror)."""
    SAFE_POINTS.parent.mkdir(parents=True, exist_ok=True)
    SAFE_POINTS.write_text(json.dumps(registry, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    SAFE_POINTS_MIRROR.parent.mkdir(parents=True, exist_ok=True)
    SAFE_POINTS_MIRROR.write_text(json.dumps(registry, sort_keys=True, indent=2) + "\n", encoding="utf-8")


# ===========================================================================
# DOUBLE GUARD #1: verify a directory of files against recorded digests.
# Returns list of failures (empty == pass).
# ===========================================================================
def _verify_dir_against(dirpath: Path, entries: list[dict]) -> list[str]:
    failures = []
    for e in entries:
        p = dirpath / e["file"]
        if not p.exists():
            failures.append(f"missing: {e['file']}")
            continue
        if sha256_file(p) != e["sha256"]:
            failures.append(f"hash mismatch: {e['file']}")
    return failures


def snapshot(label: str, files: list[str]) -> str:
    if not files:
        print("FAIL CLOSED: no files provided for snapshot")
        sys.exit(1)
    snap_id = f"{time.strftime('%Y%m%dT%H%M%S')}_{label}"
    _trace_span("rollback.snapshot", f"snapshot:{label}", target=str(snap_id))
    snap_dir = SNAP_ROOT / snap_id
    snap_dir.mkdir(parents=True, exist_ok=False)

    entries = []
    for f in files:
        src = Path(f)
        if not src.is_absolute():
            src = ROOT / src
        if not src.exists():
            print(f"FAIL CLOSED: snapshot source missing: {src}")
            sys.exit(1)
        dest = snap_dir / src.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        entries.append({
            "file": str(src.relative_to(ROOT)),
            "sha256": sha256_file(src),
            "bytes": src.stat().st_size,
        })

    record = {"snapshot_id": snap_id, "label": label, "created_utc": _utcstamp(), "files": entries}
    with open(MANIFEST, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")
    print(f"SNAPSHOT OK: {snap_id} ({len(entries)} files)")
    for e in entries:
        print(f"  {e['file']}  {e['sha256'][:16]}...  {e['bytes']} bytes")
    return snap_id


def verify(snapshot_id: str) -> bool:
    rec = next((r for r in load_manifest() if r["snapshot_id"] == snapshot_id), None)
    if rec is None:
        print(f"FAIL CLOSED: unknown snapshot {snapshot_id}")
        return False
    failures = _verify_dir_against(SNAP_ROOT / snapshot_id, rec["files"])
    for f in failures:
        print(f"  {f}")
    print("VERIFY:", "PASS" if not failures else "FAIL")
    return not failures


def promote(snapshot_id: str, proof_receipt: str = "", name: str = "") -> None:
    """Add a safe point, double-guarded:
      Guard 1 — snapshot copies in memory/rollback/snapshots/<id> hash-verified.
      Guard 2 — an independent BACKUP copy in safe_point_backups/<id> is made
                and hash-verified separately before promotion is accepted.
    The registry is stored in TWO independent locations.
    """
    rec = next((r for r in load_manifest() if r["snapshot_id"] == snapshot_id), None)
    if rec is None:
        print(f"FAIL CLOSED: unknown snapshot {snapshot_id}")
        sys.exit(1)

    # Guard 1: primary snapshot verification
    f1 = _verify_dir_against(SNAP_ROOT / snapshot_id, rec["files"])
    if f1:
        print("FAIL CLOSED (guard 1): primary snapshot failed verification")
        for f in f1:
            print(f"  {f}")
        sys.exit(1)

    # Guard 2: independent backup copy, verified separately
    backup_dir = SAFE_POINT_BACKUPS / snapshot_id
    backup_dir.mkdir(parents=True, exist_ok=True)
    for e in rec["files"]:
        src = SNAP_ROOT / snapshot_id / e["file"]
        dst = backup_dir / e["file"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    f2 = _verify_dir_against(backup_dir, rec["files"])
    if f2:
        print("FAIL CLOSED (guard 2): backup copy failed verification — promotion refused")
        for f in f2:
            print(f"  {f}")
        sys.exit(1)

    registry = [sp for sp in load_safe_points() if sp.get("snapshot_id") != snapshot_id]
    registry.append({
        "snapshot_id": snapshot_id,
        "name": name or snapshot_id,
        "promoted_utc": _utcstamp(),
        "promoted_epoch": _utcnow(),
        "proof_receipt": proof_receipt,
        "backup_dir": str(backup_dir.relative_to(ROOT)),
        "files": rec["files"],
        "guards": ["primary_hash_verified", "backup_copy_hash_verified", "registry_mirrored"],
    })
    registry.sort(key=lambda s: s["promoted_epoch"])
    save_safe_points(registry)
    _trace_span("rollback.promote", f"safe_point:{snapshot_id}")
    print(f"SAFE POINT PROMOTED (double-guarded): {snapshot_id}")
    print(f"  name: {name or snapshot_id}")
    print(f"  primary: {SNAP_ROOT / snapshot_id}  (guard 1 PASS)")
    print(f"  backup:  {backup_dir.relative_to(ROOT)}  (guard 2 PASS)")
    print(f"  registry mirrored to: {SAFE_POINTS_MIRROR.relative_to(ROOT)}")
    print(f"  total safe points available: {len(registry)}")


def list_safe_points() -> None:
    registry = load_safe_points()
    if not registry:
        print("NO SAFE POINTS. Promote a verified snapshot first.")
        return
    newest = registry[-1]
    print(f"NEWEST SAFE POINT: {newest['snapshot_id']}  ({newest['promoted_utc']})")
    print("\nALL SAFE POINTS (choose any for rollback):")
    for sp in registry:
        age = (_utcnow() - sp.get("promoted_epoch", 0)) / 3600
        print(f"  {sp['snapshot_id']}  name={sp['name']}  age={age:.1f}h  proof={sp.get('proof_receipt') or '-'}")
    age_s = _utcnow() - newest.get("promoted_epoch", 0)
    if age_s > STALE_SECONDS:
        print("\nWARNING: newest safe point is STALE (>7 days). Run gates and promote fresh state.")


def status() -> None:
    registry = load_safe_points()
    if not registry:
        print("NO SAFE POINT SET. Take a snapshot of verified state and promote it.")
    else:
        sp = registry[-1]
        age_h = (_utcnow() - sp.get("promoted_epoch", 0)) / 3600
        print(f"CURRENT SAFE POINT (newest of {len(registry)}): {sp['snapshot_id']}")
        print(f"  promoted: {sp['promoted_utc']}  age: {age_h:.1f}h")
        print(f"  proof: {sp.get('proof_receipt') or '(none recorded)'}")
        if age_h * 3600 > STALE_SECONDS:
            print("  WARNING: STALE (>7 days). Promote fresh verified state.")
    print(f"\nSnapshots on disk: {len(load_manifest())}")


def prune() -> None:
    registry = load_safe_points()
    protected = {sp["snapshot_id"] for sp in registry}
    recs = load_manifest()
    rolling = [r["snapshot_id"] for r in recs if r["snapshot_id"] not in protected]
    supersede = rolling[:-ROLLING_KEEP] if len(rolling) > ROLLING_KEEP else []
    for sid in supersede:
        marker = SNAP_ROOT / sid / ".SUPERSEDED_ROLLING"
        if not marker.exists():
            marker.write_text("superseded by rolling retention; contents retained (no-deletion law)\n",
                              encoding="utf-8")
    print(f"PRUNE: {len(supersede)} snapshots marked superseded "
          f"(files retained; {ROLLING_KEEP} rolling kept; safe points always protected)")


def guard_backward_jump(target_id: str) -> bool:
    """Block silent rollback to a state older than the newest safe point."""
    registry = load_safe_points()
    if not registry:
        return True
    newest = registry[-1]["snapshot_id"]
    if target_id == newest or target_id > newest:
        return True  # snapshot ids start with UTC timestamp -> lexical == chronological
    print(f"BLOCKED: {target_id} is OLDER than the newest safe point {newest}.")
    print("Rolling back to an outdated state would discard newer verified work.")
    print("If you truly intend this, re-run with --force-old and --reason.")
    return False


def rollback(snapshot_id: str, only: list[str] | None = None,
             force_old: bool = False, reason: str = "") -> bool:
    if not force_old and not guard_backward_jump(snapshot_id):
        return False
    if force_old and not reason:
        print("FAIL CLOSED: --force-old requires --reason (written justification).")
        return False

    rec = next((r for r in load_manifest() if r["snapshot_id"] == snapshot_id), None)
    if rec is None:
        print(f"FAIL CLOSED: unknown snapshot {snapshot_id}")
        return False

    # DOUBLE GUARD at restore: primary AND backup copies must both verify.
    f1 = _verify_dir_against(SNAP_ROOT / snapshot_id, rec["files"])
    backup_dir = SAFE_POINT_BACKUPS / snapshot_id
    f2 = _verify_dir_against(backup_dir, rec["files"]) if backup_dir.exists() else ["no backup copy"]
    if f1 or f2:
        print("FAIL CLOSED: restore refused — double-guard verification failed")
        for f in f1:
            print(f"  primary: {f}")
        for f in f2:
            print(f"  backup:  {f}")
        return False

    ok = True
    for e in rec["files"]:
        if only and e["file"] not in only:
            continue
        src = SNAP_ROOT / snapshot_id / e["file"]
        dest = ROOT / e["file"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        print(f"RESTORED: {e['file']} <- {snapshot_id} ({e['sha256'][:16]}...)")
    _trace_span("rollback.restore", f"snapshot:{snapshot_id}", status="ok" if ok else "fail")
    print("ROLLBACK:", "COMPLETE (double-guard verified, both copies matched)" if ok else "FAILED")
    return ok


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot")
    s.add_argument("--label", required=True)
    s.add_argument("--files", nargs="+", required=True)
    p = sub.add_parser("promote")
    p.add_argument("--snapshot", required=True)
    p.add_argument("--proof", default="")
    p.add_argument("--name", default="")
    sub.add_parser("list-safe-points")
    sub.add_parser("status")
    sub.add_parser("list")
    sub.add_parser("prune")
    v = sub.add_parser("verify")
    v.add_argument("--snapshot", required=True)
    r = sub.add_parser("rollback")
    r.add_argument("--snapshot", required=True)
    r.add_argument("--files", nargs="*")
    r.add_argument("--force-old", action="store_true")
    r.add_argument("--reason", default="")
    args = ap.parse_args()

    if args.cmd == "snapshot":
        snapshot(args.label, args.files)
    elif args.cmd == "promote":
        promote(args.snapshot, args.proof, args.name)
    elif args.cmd == "list-safe-points":
        list_safe_points()
    elif args.cmd == "status":
        status()
    elif args.cmd == "list":
        for rec in load_manifest():
            files = ", ".join(e["file"] for e in rec["files"])
            print(f"{rec['snapshot_id']}  label={rec['label']}  files=[{files}]")
    elif args.cmd == "prune":
        prune()
    elif args.cmd == "verify":
        sys.exit(0 if verify(args.snapshot) else 1)
    elif args.cmd == "rollback":
        sys.exit(0 if rollback(args.snapshot, args.files,
                               getattr(args, "force_old", False), args.reason) else 1)


if __name__ == "__main__":
    main()
