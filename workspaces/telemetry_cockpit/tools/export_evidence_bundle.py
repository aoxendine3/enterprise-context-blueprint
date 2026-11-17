#!/usr/bin/env python3
"""XORAS Cockpit - deterministic evidence bundle exporter.

Reads the repository's real SSOT (receipt files, world_file.db, JSONL sidecars),
canonicalizes them, and emits ONE manifest-hashed evidence bundle. The cockpit
renderer consumes only this bundle. No value is invented by this tool: every
record carries a locator to the real source and an observed SHA-256 of the raw
bytes read at export time.

Usage:
    python3 tools/export_evidence_bundle.py --repo-root .. --out dist/evidence-bundle.json

Exit is non-zero only on a structural/IO failure, never because the evidence
reports a failing verdict. A failing verdict is data, and must reach the UI.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path

SCHEMA = "xoras.evidence-bundle.v1"
VERSION = "1.0.0"
HEX64 = re.compile(r"^[0-9a-f]{64}$")

# Explicit vocabulary. Order matters: FAIL is evaluated before PASS so that
# e.g. "FAIL_CLOSED_RESTORED" is not mistaken for a success.
PASS_RE = re.compile(
    r"(APPROVED|PASS|VERIFIED|CERTIFIED|GREEN|COMPLETE|SUCCESS|SEALED|"
    r"CAPTURED|NEUTRALIZED|CONFIRMED|ACCOMPLISHED|CONVERGENCE|PROVEN|"
    r"RECONCILED|ZERO_|ALL_|ELITE_|BLIND_|TRINITY_|UPGP_|SWARM_)",
    re.IGNORECASE,
)
FAIL_RE = re.compile(
    r"(FAIL|MISMATCH|VIOLATION|DIVERGED|ERROR|REJECTED|CIRCUIT_BREAKER|"
    r"DEGRADED|TIMEOUT|PARTIAL|INVALID|PARSE_ERROR|UNREADABLE|0xBEAF)",
    re.IGNORECASE,
)
MAX_RECEIPT_FILES = 500
MAX_RECEIPT_BYTES = 5 * 1024 * 1024

# DART clearance lattice: PUBLIC(0) < INTERNAL(1) < RESTRICTED(2) < SEALED(3).
CLEARANCE_BY_SOURCE_TYPE = {
    "artifact": 0,
    "receipt_json": 1,
    "db_table": 1,
    "jsonl": 1,
}
EGRESS_CLEARANCE = 1

SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(sk-[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,})\b"),
    re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key|access[_-]?token)\s*[:=]\s*\S+"),
)


def redact_claims(claims):
    """Never ship a claim that looks like a credential to a downstream consumer."""
    cleaned = []
    count = 0
    for claim in claims or []:
        item = dict(claim)
        value = item.get("value")
        if isinstance(value, str):
            for pattern in SECRET_PATTERNS:
                value, hits = pattern.subn("[REDACTED]", value)
                count += hits
            item["value"] = value
        cleaned.append(item)
    return cleaned, count

REQUIRED_SLOTS = (
    "REALITY_GATE",
    "DART_CAGE_LATTICE",
    "MERKLE_CHECKPOINT",
    "ROOT_MANIFEST",
    "GOLDEN_CHECKPOINT",
    "HASH_ASSERT",
    "DRIFT_VECTORS",
    "LINEAGE_VERIFIED",
)


def _canon(value) -> str:
    """Language-neutral canonical JSON: byte-identical to JS canonicalStringify.

    Python writes integral floats as "0.0" while JavaScript writes "0"; both
    must agree or the manifest digest cannot be recomputed in the browser.
    """
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
            # JavaScript prints decimals for exponents in [-6, 21); Python
            # switches to scientific much earlier. Normalize to JS form.
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


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def display_verdict(value) -> str:
    """Classify without lying: positive evidence is PASS, negatives are FAIL,
    and anything else is UNRECOGNIZED (a distinct fail-closed halt reason).

    Mislabeling 'APPROVED' as FAIL is itself a fabrication of assurance.
    """
    if not isinstance(value, str) or not value.strip():
        return "UNKNOWN"
    v = value.strip()
    if FAIL_RE.search(v):
        return "FAIL"
    if PASS_RE.search(v):
        return "PASS"
    return "UNRECOGNIZED"


def as_iso(value) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    return ""


def make_record(source_id, locator, captured_at, raw_bytes, kind, subject,
                claims, checks=None, verdict=None, digests=None, attestation="ATTESTED_BY_EXPORTER"):
    observed = sha256_hex(raw_bytes)
    evidence_id = sha256_hex(
        canonical_bytes({
            "source_id": source_id,
            "locator": locator,
            "observed_sha256": observed,
        })
    )
    record = {
        "evidence_id": evidence_id,
        "kind": kind,
        "subject": str(subject),
        "claims": claims,
        "verdict_raw": verdict,
        "verdict": display_verdict(verdict),
        "provenance": {
            "source_id": source_id,
            "locator": locator,
            "captured_at": as_iso(captured_at),
            "observed_sha256": observed,
            "attestation": attestation,
        },
        "raw_ref": locator,
        "backed": True,
    }
    if checks is not None:
        record["checks"] = checks
    if digests:
        record["digests"] = digests
    return record


def add_source(sources, source_id, source_type, locator, raw_bytes, captured_at=""):
    sources.append({
        "source_id": source_id,
        "type": source_type,
        "locator": locator,
        "captured_at": as_iso(captured_at),
        "observed_sha256": sha256_hex(raw_bytes),
        "byte_count": len(raw_bytes),
    })


def receipt_kind(filename: str) -> str:
    name = filename.upper()
    if "REALITY_GATE" in name:
        return "REALITY_GATE"
    if "DART_CAGE" in name:
        return "DART_CAGE_LATTICE"
    if "GOLDEN" in name:
        return "GOLDEN_CHECKPOINT"
    if "GATE" in name or "GAUNTLET" in name:
        return "GATE_RESULT"
    return "RECEIPT"


def collect_receipts(repo: Path, sources, records):
    directory = repo / "memory" / "catch_log"
    if not directory.is_dir():
        return
    receipt_paths = sorted(directory.glob("*_RECEIPT.json"))
    if len(receipt_paths) > MAX_RECEIPT_FILES:
        raise ValueError(
            f"receipt count {len(receipt_paths)} exceeds cap {MAX_RECEIPT_FILES}; "
            "refusing unbounded ingestion"
        )
    for path in receipt_paths:
        if path.stat().st_size > MAX_RECEIPT_BYTES:
            raise ValueError(f"receipt {path.name} exceeds {MAX_RECEIPT_BYTES} byte cap")
        raw = path.read_bytes()
        rel = path.relative_to(repo).as_posix()
        sid = "receipt:" + path.stem
        try:
            doc = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            add_source(sources, sid, "receipt_json", rel, raw)
            records.append(make_record(
                sid, rel, "", raw, "RECEIPT", path.stem,
                [{"key": "parse", "value": "INVALID_JSON"}],
                verdict="RECEIPT_PARSE_ERROR",
            ))
            continue

        verdict = doc.get("verdict") or doc.get("status") or doc.get("audit_status") or ""
        captured = (doc.get("timestamp_utc") or doc.get("iso_timestamp")
                    or doc.get("timestamp") or doc.get("timestamp_iso") or "")
        checks = doc.get("checks") if isinstance(doc.get("checks"), dict) else None
        digests = {}
        for key in ("sha256", "hash", "merkle_root", "final_merkle_root", "signature"):
            val = doc.get(key)
            if isinstance(val, str) and HEX64.match(val.lower()):
                digests[key] = val.lower()

        claims = []
        for key in ("gates_passed", "gates_failed", "passes", "pass_rate",
                    "world_file_lineage_nodes", "questions_evaluated",
                    "mean_groundedness", "first_failure", "epistemic_confidence_score"):
            if key in doc and isinstance(doc[key], (str, int, float, bool)):
                claims.append({"key": key, "value": doc[key]})

        # Layer 1 drift vectors, only when a real receipt supplies them.
        drift_kind = None
        for key in ("goal_vector", "thought_vector"):
            val = doc.get(key)
            if isinstance(val, list) and val and all(isinstance(n, (int, float)) for n in val):
                claims.append({"key": key, "value": val})
                drift_kind = "DRIFT_VECTORS"

        add_source(sources, sid, "receipt_json", rel, raw, captured)
        records.append(make_record(
            sid, rel, captured, raw, drift_kind or receipt_kind(path.name), path.stem,
            claims, checks=checks, verdict=str(verdict), digests=digests,
        ))


def verify_lineage(conn) -> dict:
    """Fail closed on a corrupt database or a broken lineage parent link."""
    row = conn.execute("PRAGMA integrity_check").fetchone()
    if not row or row[0] != "ok":
        raise ValueError("world_file.db integrity_check failed: " + str(row))
    rows = list(conn.execute(
        "SELECT seq_num, node_id, parent_hash FROM lineage_nodes "
        "ORDER BY seq_num DESC LIMIT 300"
    ))
    if not rows:
        raise ValueError("lineage_nodes is empty; refusing to export")
    by_seq = {}
    for seq, node_id, parent in rows:
        by_seq.setdefault(seq, set()).add(node_id)
    broken = 0
    for seq, node_id, parent in rows:
        if seq - 1 in by_seq and parent not in by_seq[seq - 1]:
            broken += 1
    if broken:
        raise ValueError(f"lineage parent linkage broken in {broken} rows")
    return {"integrity": "ok", "rows_checked": len(rows), "broken_parents": broken}


def collect_db(repo: Path, sources, records):
    db_path = repo / "memory" / "tri_brain" / "world_file.db"
    if not db_path.is_file():
        return
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    rel_db = db_path.relative_to(repo).as_posix()
    lineage_report = verify_lineage(conn)

    specs = (
        ("master_merkle_checkpoints", None, 20, "MERKLE_CHECKPOINT"),
        ("world_file_manifest_pointers", None, 20, "ROOT_MANIFEST"),
        ("global_evidence_registry", None, 100, "HASH_ASSERT"),
        ("lineage_nodes", "seq_num", 300, "TRACE_STEP"),
        ("knowledge_objects", None, 100, "HASH_ASSERT"),
        ("daxx_worker_receipts", None, 50, "HASH_ASSERT"),
    )
    try:
        for table, order_col, limit, kind in specs:
            try:
                cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
            except sqlite3.Error:
                continue
            if not cols:
                continue
            order = f" ORDER BY {order_col} DESC" if order_col else " ORDER BY rowid DESC"
            try:
                rows = list(conn.execute(
                    f"SELECT rowid AS _locator_rowid, * FROM {table}{order} LIMIT ?", (limit,)))
            except sqlite3.Error:
                rows = list(conn.execute(f"SELECT * FROM {table}{order} LIMIT ?", (limit,)))
            for idx, row in enumerate(rows):
                row_data = dict(row)
                data = {c: row_data[c] for c in cols}
                for k, v in list(data.items()):
                    if isinstance(v, bytes):
                        data[k] = v.hex()
                raw = canonical_bytes(data)
                row_id = row_data.get("_locator_rowid", idx)
                locator = f"{rel_db}#{table}#rowid={row_id}"
                sid = f"db:{table}:{row_id}"
                digests = {}
                for key in ("sha256_hash", "merkle_root", "parent_hash", "payload_hash",
                            "evidence_hash", "evidence_digest", "signature", "merkle_root_hash"):
                    val = data.get(key)
                    if isinstance(val, str) and HEX64.match(val.lower()):
                        digests[key] = val.lower()
                claims = [{"key": k, "value": data[k]} for k in cols
                          if isinstance(data[k], (str, int, float, bool)) and data[k] != ""]
                add_source(sources, sid, "db_table", locator, raw,
                           data.get("timestamp_utc") or data.get("timestamp") or "")
                records.append(make_record(
                    sid, locator, data.get("timestamp_utc") or data.get("timestamp") or "",
                    raw, kind, f"{table}#{idx}", claims,
                    verdict=str(data.get("verdict") or data.get("status") or ""),
                    digests=digests,
                ))
    finally:
        conn.close()
    return lineage_report


JSONL_SLOTS = (
    ("trinity_hashes.jsonl", "HASH_ASSERT"),
    ("signed_root_manifests.jsonl", "MERKLE_CHECKPOINT"),
    ("merkle_asset_registry.jsonl", "HASH_ASSERT"),
    ("golden_checkpoints.jsonl", "GOLDEN_CHECKPOINT"),
)


def collect_jsonl(repo: Path, sources, records):
    base = repo / "memory" / "tri_brain"
    for filename, kind in JSONL_SLOTS:
        path = base / filename
        if not path.is_file():
            continue
        all_lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        start = max(0, len(all_lines) - 200)
        for line_no in range(start, len(all_lines)):
            line = all_lines[line_no]
            if not line.strip():
                continue
            raw = line.encode("utf-8")
            rel = path.relative_to(repo).as_posix() + f"#line={line_no}"
            sid = f"jsonl:{filename}:{line_no}"
            try:
                doc = json.loads(line)
            except ValueError:
                doc = {}
            digests = {}
            for key in ("hash", "merkle_root_hash", "receipt_sha256", "readme_sha256", "merkle_root_sha256"):
                val = doc.get(key)
                if isinstance(val, str) and HEX64.match(val.lower()):
                    digests[key] = val.lower()
            claims = [{"key": k, "value": v} for k, v in doc.items()
                      if isinstance(v, (str, int, float, bool))]
            captured = doc.get("timestamp_utc") or doc.get("timestamp") or ""
            add_source(sources, sid, "jsonl", rel, raw, captured)
            records.append(make_record(
                sid, rel, captured, raw, kind, f"{filename}#{line_no}", claims,
                verdict=str(doc.get("status") or doc.get("verdict") or doc.get("gauntlet_status") or ""),
                digests=digests,
            ))


def git_commit(repo: Path) -> str:
    try:
        import subprocess
        out = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5, check=False,
        )
        return out.stdout.strip() if out.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def collect_browser_artifact(repo: Path, sources, records, artifacts):
    """Bundle one real, fixed artifact so in-browser SHA-256 recomputation is live."""
    css = repo / "workspaces" / "telemetry_cockpit" / "dist" / "cockpit.css"
    if not css.is_file():
        return
    raw = css.read_bytes()
    rel = css.relative_to(repo).as_posix()
    digest = sha256_hex(raw)
    sid = "artifact:cockpit-css"
    add_source(sources, sid, "artifact", rel, raw)
    artifacts.append({
        "artifact_id": sid,
        "path": rel,
        "bytes_b64": base64.b64encode(raw).decode("ascii"),
        "sha256_at_export": digest,
    })
    records.append(make_record(
        sid, rel, "", raw, "HASH_ASSERT", rel,
        [{"key": "bytes", "value": len(raw)}],
        digests={"sha256": digest},
        attestation="RECOMPUTED_IN_BROWSER",
    ))


def build_bundle(repo: Path, build_seq: int = 0) -> dict:
    sources, records, artifacts = [], [], []
    collect_receipts(repo, sources, records)
    lineage_report = collect_db(repo, sources, records)
    collect_jsonl(repo, sources, records)
    if lineage_report:
        sid = "db:lineage_verification"
        locator = "memory/tri_brain/world_file.db#lineage_verification"
        raw = canonical_bytes(lineage_report)
        add_source(sources, sid, "db_table", locator, raw)
        records.append(make_record(
            sid, locator, "", raw, "LINEAGE_VERIFIED", "lineage_nodes",
            [{"key": k, "value": v} for k, v in lineage_report.items()],
            verdict="PASS",
        ))
    collect_browser_artifact(repo, sources, records, artifacts)

    source_types = {s["source_id"]: s["type"] for s in sources}
    for record in records:
        stype = source_types.get(record["provenance"]["source_id"], "receipt_json")
        record["clearance"] = CLEARANCE_BY_SOURCE_TYPE.get(stype, 1)
        record["claims"], record["redactions"] = redact_claims(record.get("claims"))

    # Deterministic generated_at: max observed source timestamp, else epoch.
    stamps = sorted({r["provenance"]["captured_at"] for r in records if r["provenance"]["captured_at"]})
    generated_at = stamps[-1] if stamps else "1970-01-01T00:00:00Z"

    payload = {
        "schema_version": SCHEMA,
        "generated_at": generated_at,
        "build_seq": build_seq,
        "egress_clearance": EGRESS_CLEARANCE,
        "generator": {
            "tool": "cockpit/tools/export_evidence_bundle.py",
            "version": VERSION,
            "repo_commit": git_commit(repo),
        },
        "sources": sources,
        "records": records,
        "artifacts": artifacts,
        "required_slots": list(REQUIRED_SLOTS),
    }
    raw = canonical_bytes(payload)
    payload["bundle_id"] = sha256_hex(raw)
    payload["manifest"] = {
        "algorithm": "sha256",
        "digest": payload["bundle_id"],
        "byte_count": len(raw),
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, help="Repository root (SSOT source)")
    parser.add_argument("--out", required=True, help="Output bundle JSON path")
    parser.add_argument("--build-seq", type=int, default=0,
                        help="Monotonic build sequence from the external high-water mark")
    parser.add_argument("--known-good", default=None,
                        help="Signed known-good source manifest to verify before export")
    parser.add_argument("--known-good-public-key", default=None,
                        help="Public key for the known-good manifest")
    args = parser.parse_args()
    if args.build_seq < 0:
        print("ERROR: build sequence must be non-negative", file=sys.stderr)
        return 2
    if bool(args.known_good) != bool(args.known_good_public_key):
        print("ERROR: --known-good and --known-good-public-key must be supplied together", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    if not repo.is_dir():
        print(f"ERROR: repo root does not exist: {repo}", file=sys.stderr)
        return 2

    if args.known_good:
        import known_good_sources
        result = known_good_sources.verify(
            repo, Path(args.known_good), args.known_good_public_key
        )
        if result != 0:
            print("ERROR: known-good source verification failed; refusing to export", file=sys.stderr)
            return 1

    bundle = build_bundle(repo, args.build_seq)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(canonical_bytes(bundle) + b"\n")

    kinds = {}
    for record in bundle["records"]:
        kinds[record["kind"]] = kinds.get(record["kind"], 0) + 1
    print(json.dumps({
        "status": "EXPORTED",
        "schema_version": SCHEMA,
        "bundle_id": bundle["bundle_id"],
        "byte_count": bundle["manifest"]["byte_count"],
        "sources": len(bundle["sources"]),
        "records": len(bundle["records"]),
        "kinds": kinds,
        "required_slots_present": sorted(set(bundle["required_slots"]) & set(kinds)),
        "required_slots_missing": sorted(set(bundle["required_slots"]) - set(kinds)),
        "out": str(out),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
