#!/usr/bin/env python3
"""Structural verifier for an evidence bundle.

Checks schema shape and recomputes the manifest digest. It NEVER converts a
failing verdict into a build failure: a bad verdict is real data that the
cockpit must display. Exit 1 only for structural corruption or digest mismatch.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HEX64 = re.compile(r"^[0-9a-f]{64}$")
SCHEMA = "xoras.evidence-bundle.v1"


def _canon(value) -> str:
    """Must stay byte-identical to JS canonicalStringify and the exporter."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        import math
        from decimal import Decimal
        if not math.isfinite(value):
            raise ValueError("non-finite number cannot be canonicalized")
        if value.is_integer() and abs(value) < 1e21:
            return str(int(value))
        rendered = repr(value)
        if "e" in rendered or "E" in rendered:
            exponent = int(rendered.lower().split("e")[1])
            if -6 <= exponent < 21:
                rendered = format(Decimal(rendered), "f")
                if "." in rendered:
                    rendered = rendered.rstrip("0").rstrip(".")
        return rendered.replace("e-0", "e-").replace("e+0", "e+")
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_canon(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(
            json.dumps(key, ensure_ascii=False) + ":" + _canon(value[key])
            for key in sorted(value, key=lambda k: k.encode("utf-16-be"))
        ) + "}"
    raise TypeError("unsupported canonicalization type: " + type(value).__name__)


def canonical_bytes(obj) -> bytes:
    return _canon(obj).encode("utf-8")


def structural_check(bundle: dict) -> dict:
    problems = []
    if bundle.get("schema_version") != SCHEMA:
        problems.append("schema_version mismatch")
    manifest = bundle.get("manifest") or {}
    if manifest.get("algorithm") != "sha256":
        problems.append("manifest algorithm is not sha256")
    digest = manifest.get("digest", "")
    if not isinstance(digest, str) or not HEX64.match(digest):
        problems.append("manifest digest is not 64 lowercase hex")

    unsigned = dict(bundle)
    unsigned.pop("manifest", None)
    unsigned.pop("bundle_id", None)
    unsigned.pop("signature", None)
    computed = hashlib.sha256(canonical_bytes(unsigned)).hexdigest()
    if computed != digest:
        problems.append("manifest digest mismatch: expected " + digest + ", computed " + computed)

    source_ids = {s.get("source_id") for s in bundle.get("sources", [])}
    bad_refs = bad_ids = bad_backed = 0
    for r in bundle.get("records", []):
        if r.get("provenance", {}).get("source_id") not in source_ids:
            bad_refs += 1
        if not HEX64.match(str(r.get("evidence_id", ""))):
            bad_ids += 1
        if r.get("backed") is not True:
            bad_backed += 1
    if bad_refs:
        problems.append(str(bad_refs) + " records with unresolved source_id")
    if bad_ids:
        problems.append(str(bad_ids) + " records with invalid evidence_id")
    if bad_backed:
        problems.append(str(bad_backed) + " records not marked backed")

    kinds = {}
    for r in bundle.get("records", []):
        kind = r.get("kind", "UNKNOWN")
        kinds[kind] = kinds.get(kind, 0) + 1
    missing = sorted(set(bundle.get("required_slots", [])) - set(kinds))
    verdict_counts = {}
    for r in bundle.get("records", []):
        verdict = r.get("verdict", "UNKNOWN")
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1

    return {
        "structurally_valid": not problems,
        "problems": problems,
        "records": len(bundle.get("records", [])),
        "sources": len(bundle.get("sources", [])),
        "manifest_digest": digest,
        "computed_digest": computed,
        "required_slots_missing": missing,
        "verdict_counts": verdict_counts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", help="Path to evidence-bundle.json")
    args = parser.parse_args()
    try:
        bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(json.dumps({"structurally_valid": False, "problems": ["unreadable bundle: " + str(exc)]}, indent=2))
        return 1
    report = structural_check(bundle)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["structurally_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
