#!/usr/bin/env python3
"""Pinned known-good manifest for the cockpit's critical source files.

Two modes:
  --emit    create/sign a manifest from current bytes (explicit maintenance only)
  --verify  recompute every digest and verify the detached signature; fail closed

This closes the ghost-intrusion gap: a process on the same host cannot alter a
critical source and have the build silently ship the poisoned version.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_evidence_bundle import canonical_bytes

SCHEMA = "xoras.known-good-sources.v1"

CRITICAL_PATHS = (
    "core/ops/tools/xoras_file_writer.py",
    "core/ops/scripts/verify_sovereign_file_writer.sh",
    "core/ops/scripts/reality_gate.sh",
    "core/ops/scripts/verify_cockpit.sh",
    "core/ops/scripts/blackbox_bbq_gauntlet.py",
    "memory/tri_brain/merkle_root.known_good",
    "workspaces/telemetry_cockpit/dist/index.html",
    "workspaces/telemetry_cockpit/dist/cockpit.css",
    "workspaces/telemetry_cockpit/src/crypto.js",
    "workspaces/telemetry_cockpit/src/drift.js",
    "workspaces/telemetry_cockpit/src/state-machine.js",
    "workspaces/telemetry_cockpit/src/evidence-adapter.js",
    "workspaces/telemetry_cockpit/src/app.js",
    "workspaces/telemetry_cockpit/tools/export_evidence_bundle.py",
    "workspaces/telemetry_cockpit/tools/verify_bundle.py",
    "workspaces/telemetry_cockpit/tools/verify_assets.py",
    "workspaces/telemetry_cockpit/tools/sign_bundle.py",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_public(path: str):
    key = serialization.load_pem_public_key(Path(path).read_bytes())
    if not isinstance(key, ed25519.Ed25519PublicKey):
        raise ValueError("public key is not Ed25519")
    return key


def build_manifest(repo: Path) -> dict:
    entries = []
    for relative in CRITICAL_PATHS:
        path = repo / relative
        if not path.is_file():
            raise FileNotFoundError(f"critical source missing: {relative}")
        data = path.read_bytes()
        entries.append({"path": relative, "sha256": digest(data), "bytes": len(data)})
    return {"schema_version": SCHEMA, "sources": entries}


def core_bytes(manifest: dict) -> bytes:
    return canonical_bytes({k: v for k, v in manifest.items() if k != "signature"})


def emit(repo: Path, out: Path, key_path: str) -> int:
    private = serialization.load_pem_private_key(Path(key_path).read_bytes(), password=None)
    if not isinstance(private, ed25519.Ed25519PrivateKey):
        raise ValueError("signing key is not Ed25519")
    manifest = build_manifest(repo)
    manifest["signature"] = private.sign(core_bytes(manifest)).hex()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(canonical_bytes(manifest) + b"\n")
    print(json.dumps({"status": "KNOWN_GOOD_EMITTED", "sources": len(manifest["sources"]), "out": str(out)}, indent=2))
    return 0


def verify(repo: Path, manifest_path: Path, pub_path: str) -> int:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != SCHEMA:
        print("KNOWN_GOOD_INVALID: schema", file=sys.stderr)
        return 1
    signature = manifest.get("signature")
    if not isinstance(signature, str) or len(signature) != 128:
        print("KNOWN_GOOD_INVALID: signature missing", file=sys.stderr)
        return 1
    try:
        load_public(pub_path).verify(bytes.fromhex(signature), core_bytes(manifest))
    except Exception as exc:
        print(f"KNOWN_GOOD_INVALID: signature: {exc}", file=sys.stderr)
        return 1

    expected = {e["path"]: e for e in manifest["sources"]}
    actual = {p: True for p in CRITICAL_PATHS}
    if set(expected) != set(actual):
        print("KNOWN_GOOD_DRIFT: source set changed", file=sys.stderr)
        return 1
    for relative, entry in expected.items():
        path = repo / relative
        if not path.is_file():
            print(f"KNOWN_GOOD_DRIFT: missing {relative}", file=sys.stderr)
            return 1
        data = path.read_bytes()
        if digest(data) != entry["sha256"] or len(data) != entry["bytes"]:
            print(f"KNOWN_GOOD_DRIFT: {relative}", file=sys.stderr)
            return 1
    print(json.dumps({"status": "KNOWN_GOOD_VERIFIED", "sources": len(expected)}, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--key", default=os.environ.get("XORAS_COCKPIT_SIGNING_KEY_PEM"))
    parser.add_argument("--public-key", default=os.environ.get("XORAS_COCKPIT_SIGNING_PUB_PEM"))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--emit", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    repo = Path(args.repo_root).resolve()
    if not args.public_key or not Path(args.public_key).is_file():
        print("ERROR: public key missing", file=sys.stderr)
        return 2
    try:
        if args.emit:
            if not args.key or not Path(args.key).is_file():
                print("ERROR: signing key missing", file=sys.stderr)
                return 2
            return emit(repo, Path(args.manifest), args.key)
        return verify(repo, Path(args.manifest), args.public_key)
    except Exception as exc:
        print(f"KNOWN_GOOD_ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
