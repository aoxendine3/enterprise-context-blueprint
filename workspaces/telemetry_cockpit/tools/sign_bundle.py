#!/usr/bin/env python3
"""Detached Ed25519 signature for the cockpit evidence bundle.

Fails closed: missing/unreadable/wrong-type key, key mismatch, or a manifest
that does not match the unsigned payload all produce a non-zero exit. The
signature is a transport envelope and is excluded from the manifest digest.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_evidence_bundle import canonical_bytes, sha256_hex  # same canonicalizer

EXCLUDED = ("manifest", "bundle_id", "signature")


def unsigned_bytes(bundle: dict) -> bytes:
    return canonical_bytes({k: v for k, v in bundle.items() if k not in EXCLUDED})


def spki_b64(public_key) -> str:
    der = public_key.public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return base64.b64encode(der).decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--key", default=os.environ.get("XORAS_COCKPIT_SIGNING_KEY_PEM"))
    parser.add_argument("--public-key", default=os.environ.get("XORAS_COCKPIT_SIGNING_PUB_PEM"))
    args = parser.parse_args()

    if not args.key or not Path(args.key).is_file():
        print("ERROR: signing key missing; set XORAS_COCKPIT_SIGNING_KEY_PEM", file=sys.stderr)
        return 2
    try:
        private = serialization.load_pem_private_key(Path(args.key).read_bytes(), password=None)
        if not isinstance(private, ed25519.Ed25519PrivateKey):
            raise ValueError("signing key is not Ed25519")
        public = private.public_key()
        if args.public_key:
            declared = serialization.load_pem_public_key(Path(args.public_key).read_bytes())
            if declared.public_bytes(
                serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
            ) != public.public_bytes(
                serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
            ):
                raise ValueError("public key pin does not match signing key")
        bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
        data = unsigned_bytes(bundle)
        if sha256_hex(data) != bundle.get("manifest", {}).get("digest"):
            raise ValueError("manifest digest mismatch; refusing to sign")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    bundle["signature"] = {
        "algorithm": "Ed25519",
        "encoding": "raw64-hex",
        "value": private.sign(data).hex(),
    }
    Path(args.bundle).write_bytes(canonical_bytes(bundle) + b"\n")
    print(json.dumps({
        "status": "SIGNED",
        "signature_algorithm": "Ed25519",
        "signature_bytes": 64,
        "public_key_spki_b64": spki_b64(public),
        "bundle_id": bundle.get("bundle_id"),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
