#!/usr/bin/env python3
"""
=============================================================================
XORAS UPSTREAM CLAIM GATE (RETRIEVAL-GATED + SCHEMA-ENFORCED + ABSTENTION)
=============================================================================
Moves verification UPSTREAM of emission:
  1. Span Indexer   : indexes retrieved authoritative sources into hash-pinned
                      Evidence Spans (SPAN-01 .. SPAN-N). No span, no claim.
  2. Schema Gate    : requires structured JSON output:
                        {"abstain": bool, "reason": str,
                         "claims": [{"claim": str, "span_id": str, "quote": str}]}
  3. Upstream Check : BEFORE any claim is emitted downstream (0xDEAD0000 -> 0xBEAF0000):
                        - span_id must exist in retrieved spans
                        - quote must be a verbatim normalized substring of that span
                        - claim's rare tokens must be grounded in the quoted span
                        - any code/path/symbol argument feature must exist in the
                          retrieved span or pass repo verification
  4. Abstention     : if insufficient evidence or all claims are rejected,
                      emits explicit ABSTAIN_INSUFFICIENT_EVIDENCE (never guesses).
  5. Notary Receipt : logs every promoted/blocked/abstained decision to
                      memory/catch_log/UPSTREAM_CLAIM_GATE_RECEIPT.jsonl.
=============================================================================
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[3]
RECEIPT_LOG = ROOT / "memory" / "catch_log" / "UPSTREAM_CLAIM_GATE_RECEIPT.jsonl"
TOOLCHAIN = set(
    "git cargo npm node python3 python z3 zig make grep sed awk curl nc jq "
    "sha256sum go rustc gcc ld cmake sqlite3 say swiftc".split()
)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _rare_tokens(text: str, min_len: int = 5) -> set:
    stop = {
        "about", "after", "always", "before", "being", "could", "every",
        "never", "other", "should", "their", "there", "these", "those",
        "under", "where", "which", "while", "would",
    }
    return {
        t for t in re.findall(r"[a-z0-9_./-]{%d,}" % min_len, (text or "").lower())
        if t not in stop
    }


def extract_argument_features(text: str) -> List[str]:
    feats = []
    for m in re.findall(r"`([^`\n]+)`", text or ""):
        feats.append(m.strip())
    for m in re.findall(r"(?:^|[\s|;>])((?:\./|/|\.\./)[\w./-]+)", text or ""):
        feats.append(m.strip())
    for m in re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]{2,})\s*\(", text or ""):
        feats.append(m.strip() + "()")
    return feats


def verify_repo_feature(feat: str, span_text: str) -> Tuple[bool, str]:
    """Verify a code/path/command feature against the retrieved span or repo."""
    if _norm(feat.rstrip("()")) in _norm(span_text):
        return True, "span_grounded"
    if feat.startswith(("./", "/", "../")) or ("/" in feat and not feat.endswith("()")):
        p = (ROOT / feat).resolve() if not feat.startswith("/") else Path(feat)
        try:
            return p.exists(), "repo_path"
        except OSError:
            return False, "repo_path"
    if feat.endswith("()"):
        name = feat[:-2]
        try:
            out = subprocess.run(
                ["grep", "-rF", "-l", name, "--include=*.py", "--include=*.rs",
                 "--include=*.zig", "--include=*.ts", "--include=*.c", "core", "ops", "tests"],
                cwd=ROOT, capture_output=True, timeout=8, text=True,
            )
            return bool(out.stdout.strip()), "repo_symbol"
        except Exception:
            return False, "repo_symbol"
    tok = feat.split()[0] if feat.split() else feat
    return tok in TOOLCHAIN, "toolchain"


@dataclass
class EvidenceSpan:
    span_id: str
    source: str
    text: str
    sha256: str


def index_spans(sources: List[Tuple[str, str]]) -> Dict[str, EvidenceSpan]:
    """Index retrieved (source_label, text) pairs into deterministic EvidenceSpans."""
    spans: Dict[str, EvidenceSpan] = {}
    for idx, (label, text) in enumerate(sources, 1):
        clean = (text or "").strip()
        if not clean:
            continue
        sid = f"SPAN-{idx:02d}"
        spans[sid] = EvidenceSpan(
            span_id=sid,
            source=label,
            text=clean,
            sha256=hashlib.sha256(clean.encode("utf-8")).hexdigest(),
        )
    return spans


def validate_structured_response(
    raw_json: Dict[str, Any],
    spans: Dict[str, EvidenceSpan],
    min_token_overlap: float = 0.5,
) -> Dict[str, Any]:
    """
    Upstream pre-emission gate:
    Promotes ONLY claims backed by a valid span_id, verbatim quote, lexical
    grounding, and verified argument features. Forces explicit abstention if
    no valid claims survive or if the model abstained.
    """
    if not isinstance(raw_json, dict):
        return {
            "status": "ABSTAIN_INVALID_SCHEMA",
            "taint": "0xBEAF0000",
            "abstained": True,
            "promoted_claims": [],
            "rejected_claims": [{"reason": "RESPONSE_NOT_JSON_OBJECT"}],
            "emitted_text": "ABSTAIN: INSUFFICIENT_EVIDENCE",
        }

    if raw_json.get("abstain") is True or not spans:
        return {
            "status": "ABSTAIN_INSUFFICIENT_EVIDENCE",
            "taint": "0xBEAF0000",
            "abstained": True,
            "reason": str(raw_json.get("reason") or "INSUFFICIENT_EVIDENCE"),
            "promoted_claims": [],
            "rejected_claims": [],
            "emitted_text": "ABSTAIN: INSUFFICIENT_EVIDENCE",
        }

    claims_in = raw_json.get("claims")
    if not isinstance(claims_in, list):
        return {
            "status": "ABSTAIN_INVALID_SCHEMA",
            "taint": "0xBEAF0000",
            "abstained": True,
            "promoted_claims": [],
            "rejected_claims": [{"reason": "CLAIMS_NOT_LIST"}],
            "emitted_text": "ABSTAIN: INSUFFICIENT_EVIDENCE",
        }

    promoted = []
    rejected = []
    for item in claims_in:
        if not isinstance(item, dict):
            rejected.append({"item": item, "reason": "CLAIM_NOT_OBJECT"})
            continue
        sid = str(item.get("span_id") or "").strip()
        quote = str(item.get("quote") or "").strip()
        claim = str(item.get("claim") or "").strip()

        if sid not in spans:
            rejected.append({"claim": claim, "span_id": sid, "reason": "UNKNOWN_SPAN_ID"})
            continue
        span = spans[sid]
        if not quote or _norm(quote) not in _norm(span.text):
            rejected.append({"claim": claim, "span_id": sid, "reason": "QUOTE_NOT_IN_SPAN"})
            continue

        claim_toks = _rare_tokens(claim)
        span_toks = _rare_tokens(span.text)
        if claim_toks:
            overlap = len(claim_toks & span_toks) / len(claim_toks)
            if overlap < min_token_overlap:
                rejected.append({
                    "claim": claim,
                    "span_id": sid,
                    "reason": f"UNGROUNDED_CLAIM_TOKENS ({overlap:.2f} < {min_token_overlap})",
                })
                continue

        bad_feats = []
        for f in extract_argument_features(claim):
            ok, kind = verify_repo_feature(f, span.text)
            if not ok:
                bad_feats.append({"feature": f, "kind": kind})
        if bad_feats:
            rejected.append({
                "claim": claim,
                "span_id": sid,
                "reason": "UNVERIFIED_ARGUMENT_FEATURE",
                "details": bad_feats,
            })
            continue

        promoted.append({
            "claim": claim,
            "span_id": sid,
            "span_sha256": span.sha256,
            "quote": quote,
        })

    if not promoted:
        return {
            "status": "ABSTAIN_ALL_CLAIMS_REJECTED",
            "taint": "0xBEAF0000",
            "abstained": True,
            "promoted_claims": [],
            "rejected_claims": rejected,
            "emitted_text": "ABSTAIN: INSUFFICIENT_EVIDENCE",
        }

    return {
        "status": "PROMOTED_GROUNDED",
        "taint": "0xBEAF0000",
        "abstained": False,
        "promoted_claims": promoted,
        "rejected_claims": rejected,
        "emitted_text": " ".join(c["claim"] for c in promoted),
    }


def query_ollama_constrained(
    question: str,
    spans: Dict[str, EvidenceSpan],
    model: str = "xoras-golden:latest",
    endpoint: str = "http://127.0.0.1:11434/api/generate",
    timeout_s: float = 90.0,
) -> Dict[str, Any]:
    """Ask a local Ollama model with JSON-schema constraint, then gate upstream."""
    span_block = "\n".join(f"[{s.span_id}] ({s.source}): {s.text}" for s in spans.values())
    prompt = (
        "Answer ONLY using the retrieved spans below. Output a JSON object matching:\n"
        '{"abstain": boolean, "reason": string, "claims": [{"claim": string, "span_id": string, "quote": string}]}\n'
        "Rules: If the spans do not support an answer, set abstain=true and claims=[]. "
        "Otherwise every claim MUST cite a valid span_id and include an exact verbatim quote from that span.\n\n"
        f"RETRIEVED SPANS:\n{span_block or '(none)'}\n\nQUESTION: {question}\nJSON:"
    )
    payload = {
        "model": model,
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 320},
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        outer = json.loads(resp.read().decode("utf-8"))
    raw_text = (outer.get("response") or "").strip()
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        parsed = {"abstain": True, "reason": "NON_JSON_OUTPUT", "claims": []}
    verdict = validate_structured_response(parsed, spans)
    log_receipt(question, verdict)
    return verdict


def log_receipt(question: str, verdict: Dict[str, Any], receipt_path: Path = None) -> None:
    path = receipt_path or RECEIPT_LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "question_sha256": hashlib.sha256(question.encode("utf-8")).hexdigest()[:16],
        "status": verdict.get("status"),
        "abstained": verdict.get("abstained"),
        "promoted_count": len(verdict.get("promoted_claims", [])),
        "rejected_count": len(verdict.get("rejected_claims", [])),
        "taint": verdict.get("taint"),
    }
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")
