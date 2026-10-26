"""
XORAS Model Manifest Scanner (read-only).

Detects, from Ollama *metadata only*:
  * GHOST manifests            (size 0 / /api/show failure)
  * rug-pulls                  (digest / template / system / modelfile drift vs. a pinned baseline)
  * poisoned chat templates    (non-allowlisted URLs, instruction-override text, base64 blobs,
                                shell snippets, hidden Unicode)
  * UNPINNED models            (no baseline entry)

Only the read-only endpoints ``/api/tags`` and ``/api/show`` are ever contacted by the default
fetcher.  It cannot pull, delete, copy, create or push anything.

Known limit: weights are NOT verified.  Only the manifest digest/size and text metadata are
inspected; a malicious tensor payload behind an unchanged digest is out of scope.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import tempfile
import unicodedata
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple
from urllib.parse import urlparse

FetchJson = Callable[..., Any]

SCHEMA = "xoras.model_manifest.v1"

# Only these read-only endpoints may be called by the default fetcher.
READ_ONLY_PATHS = frozenset({"/api/tags", "/api/show"})

# Severities (ordered).
SEVERITY_ORDER = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

# host -> tuple of allowed path prefixes (None = any path on that host).
# Evidence-based: these are the hosts that appear in the stock licence / template text of the
# Llama, Qwen, Hermes, SmolLM, Nomic and StableLM models measured on the real node.
DEFAULT_URL_ALLOWLIST: Dict[str, Optional[Tuple[str, ...]]] = {
    "apache.org": None,
    "llama.com": None,
    "meta.com": None,
    "facebook.com": None,
    "stability.ai": None,
    "ollama.com": None,
    "github.com": ("/meta-llama/",),
    # Official Meta licence text embeds a workplace redirect link.
    "l.workplace.com": ("/l.php",),
}

_URL_RE = re.compile(r"https?://[^\s\"'<>)\]}\\,;|]+", re.I)

_OVERRIDE_PATTERNS = [
    re.compile(
        r"\b(ignore|disregard|forget|override|bypass)\s+(all\s+|any\s+)?(of\s+)?(the\s+|your\s+)?"
        r"(previous|prior|above|earlier|preceding|system|safety)\s+"
        r"(instructions?|prompts?|rules?|messages?|context|guidelines?)",
        re.I,
    ),
    re.compile(r"\bdo\s+not\s+(tell|reveal|inform|mention)\s+(this\s+to\s+)?the\s+user", re.I),
    re.compile(r"\b(new|updated|real)\s+system\s+prompt\s*:", re.I),
    re.compile(r"\bfrom\s+now\s+on,?\s+you\s+(are|will|must)\b", re.I),
    re.compile(r"\byou\s+must\s+(secretly|silently|covertly)\b", re.I),
    re.compile(r"\bexfiltrat\w*", re.I),
    re.compile(r"\bjailbreak(ed)?\b|\bDAN\s+mode\b", re.I),
]

_SHELL_PATTERNS = [
    re.compile(r"\b(curl|wget)\s+(-\w|--\w|https?:)", re.I),
    re.compile(r"\|\s*(sudo\s+)?(ba|z|da|k)?sh\b", re.I),
    re.compile(r"\brm\s+-[a-z]*[rf][a-z]*\b|\bchmod\s+\+x\b|\bmkfifo\b|\bnc\s+-e\b|\bbash\s+-i\b|/dev/tcp/", re.I),
    re.compile(r"\bos\.system\b|\bsubprocess\.(run|Popen|call|check_output)\b|__import__\s*\(|\beval\s*\(", re.I),
    re.compile(r"\bpowershell(\.exe)?\s+-(enc|e|nop|w)\b|\bInvoke-(Expression|WebRequest)\b|\bIEX\b"),
    re.compile(r"/etc/passwd|/etc/shadow|\.ssh/id_rsa", re.I),
    re.compile(r"<script\b", re.I),
]

_B64_RE = re.compile(r"[A-Za-z0-9+/]{64,}={0,2}")
_HEX_ONLY_RE = re.compile(r"^[0-9a-fA-F]+$")


def sha256_text(text: Optional[str]) -> Optional[str]:
    """SHA-256 of UTF-8 text; ``None`` stays ``None`` (missing field)."""
    if text is None:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _entropy(s: str) -> float:
    if not s:
        return 0.0
    counts: Dict[str, int] = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


@dataclass
class Finding:
    model: str
    code: str
    severity: str
    detail: str
    field: str = ""
    evidence: str = ""

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


def make_urllib_fetcher(base_url: str, timeout: float = 30.0) -> FetchJson:
    """Default read-only fetcher.  Refuses any path outside READ_ONLY_PATHS."""
    base = base_url.rstrip("/")

    def fetch_json(path: str, body: Optional[Mapping[str, Any]] = None) -> Any:
        if path not in READ_ONLY_PATHS:
            raise PermissionError(f"read-only fetcher refuses path {path!r}")
        if body is None:
            req = urllib.request.Request(base + path)
        else:
            req = urllib.request.Request(
                base + path,
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    return fetch_json


class ModelManifestScanner:
    """Snapshot / diff / audit of an Ollama node's model manifests (metadata only)."""

    SCAN_FIELDS = ("template", "system", "modelfile")

    def __init__(
        self,
        fetch_json: Optional[FetchJson] = None,
        base_url: str = "http://localhost:11434",
        url_allowlist: Optional[Mapping[str, Optional[Tuple[str, ...]]]] = None,
        clock: Optional[Callable[[], str]] = None,
    ) -> None:
        self.base_url = base_url
        self._fetch = fetch_json if fetch_json is not None else make_urllib_fetcher(base_url)
        self.url_allowlist = dict(DEFAULT_URL_ALLOWLIST if url_allowlist is None else url_allowlist)
        self._clock = clock or (lambda: datetime.now(timezone.utc).isoformat())

    # ------------------------------------------------------------------ collection
    def _collect(self) -> List[Dict[str, Any]]:
        """Returns per-model dicts: record (hashes) + private ``_texts`` for auditing."""
        tags = self._fetch("/api/tags")
        models = (tags or {}).get("models") or []
        out: List[Dict[str, Any]] = []
        for m in sorted(models, key=lambda x: str(x.get("name", ""))):
            name = str(m.get("name") or m.get("model") or "")
            details = m.get("details") or {}
            size = int(m.get("size") or 0)
            info: Optional[Mapping[str, Any]] = None
            show_error = ""
            try:
                info = self._fetch("/api/show", {"model": name})
                if not isinstance(info, Mapping):
                    show_error = "non-object /api/show response"
                    info = None
            except Exception as exc:  # errors-as-placeholders: never crash the scan
                show_error = f"{type(exc).__name__}: {exc}"
                info = None
            show_details = (info or {}).get("details") or {}
            texts = {f: ((info or {}).get(f) if info else None) for f in self.SCAN_FIELDS}
            texts = {f: (v if isinstance(v, str) else None) for f, v in texts.items()}
            record = {
                "name": name,
                "digest": str(m.get("digest") or ""),
                "size": size,
                "parent_model": details.get("parent_model", show_details.get("parent_model", "")) or "",
                "format": details.get("format", show_details.get("format", "")) or "",
                "template_sha256": sha256_text(texts["template"]),
                "system_sha256": sha256_text(texts["system"]),
                "modelfile_sha256": sha256_text(texts["modelfile"]),
                "show_ok": info is not None,
                "show_error": show_error,
            }
            out.append({"record": record, "texts": texts})
        return out

    def snapshot(self) -> Dict[str, Any]:
        collected = self._collect()
        return self._snapshot_from(collected)

    def _snapshot_from(self, collected: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "schema": SCHEMA,
            "base_url": self.base_url,
            "created_at": self._clock(),
            "models": {c["record"]["name"]: c["record"] for c in collected},
        }

    # ------------------------------------------------------------------ diff
    @staticmethod
    def diff(baseline: Mapping[str, Any], current: Mapping[str, Any]) -> Dict[str, Any]:
        b = dict((baseline or {}).get("models") or {})
        c = dict((current or {}).get("models") or {})
        result: Dict[str, Any] = {
            "added": sorted(set(c) - set(b)),
            "removed": sorted(set(b) - set(c)),
            "digest_changed": [],
            "template_changed": [],
            "system_changed": [],
            "modelfile_changed": [],
        }
        for name in sorted(set(b) & set(c)):
            old, new = b[name], c[name]
            for key, bucket, fld in (
                ("digest", "digest_changed", "digest"),
                ("template_sha256", "template_changed", "template_sha256"),
                ("system_sha256", "system_changed", "system_sha256"),
                ("modelfile_sha256", "modelfile_changed", "modelfile_sha256"),
            ):
                if old.get(fld) != new.get(fld):
                    result[bucket].append({"name": name, "old": old.get(fld), "new": new.get(fld)})
        return result

    # ------------------------------------------------------------------ text checks
    def _host_allowed(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            host = (parsed.hostname or "").lower().rstrip(".")
        except ValueError:
            return False
        if not host:
            return False
        for allowed, prefixes in self.url_allowlist.items():
            if host == allowed or host.endswith("." + allowed):
                if prefixes is None:
                    return True
                if any((parsed.path or "/").startswith(p) for p in prefixes):
                    return True
        return False

    def scan_text(self, model: str, field: str, text: Optional[str]) -> List[Finding]:
        findings: List[Finding] = []
        if not text:
            return findings

        # URLs outside the allowlist
        for raw in _URL_RE.findall(text):
            url = raw.rstrip(".:!?")
            if not self._host_allowed(url):
                findings.append(Finding(model, "TEMPLATE_URL_NONALLOWLIST", "HIGH",
                                        "URL to host outside allowlist", field, url[:160]))

        # instruction-override text
        for pat in _OVERRIDE_PATTERNS:
            mt = pat.search(text)
            if mt:
                findings.append(Finding(model, "TEMPLATE_OVERRIDE_TEXT", "HIGH",
                                        "instruction-override phrase", field, mt.group(0)[:160]))

        # base64 blobs (URLs removed first so query tokens are not mistaken for payloads)
        stripped = _URL_RE.sub(" ", text)
        for mt in _B64_RE.finditer(stripped):
            blob = mt.group(0)
            if _HEX_ONLY_RE.match(blob):
                continue
            has_mix = (any(ch.isdigit() for ch in blob) and any(ch.isupper() for ch in blob)
                       and any(ch.islower() for ch in blob))
            if has_mix and _entropy(blob) >= 4.5:
                findings.append(Finding(model, "TEMPLATE_BASE64_BLOB", "MEDIUM",
                                        f"base64-like blob of {len(blob)} chars", field, blob[:48] + "..."))

        # shell snippets
        for pat in _SHELL_PATTERNS:
            mt = pat.search(text)
            if mt:
                findings.append(Finding(model, "TEMPLATE_SHELL_SNIPPET", "HIGH",
                                        "shell/code-execution snippet", field, mt.group(0)[:160]))

        # hidden unicode (format chars: zero-width, bidi controls, tag chars, BOM, soft hyphen)
        hidden = sorted({f"U+{ord(ch):04X}" for ch in text if unicodedata.category(ch) == "Cf"})
        if hidden:
            findings.append(Finding(model, "HIDDEN_UNICODE", "HIGH",
                                    "invisible format characters present", field, ",".join(hidden)))
        return findings

    # ------------------------------------------------------------------ audit
    def audit(self, baseline: Optional[Mapping[str, Any]] = None) -> List[Dict[str, str]]:
        collected = self._collect()
        findings: List[Finding] = []
        base_models = dict((baseline or {}).get("models") or {})

        for item in collected:
            rec, texts = item["record"], item["texts"]
            name = rec["name"]

            if rec["size"] == 0 or not rec["show_ok"]:
                reasons = []
                if rec["size"] == 0:
                    reasons.append("size=0")
                if not rec["show_ok"]:
                    reasons.append(f"/api/show failed ({rec['show_error']})")
                findings.append(Finding(name, "GHOST", "HIGH", "; ".join(reasons)))

            seen = set()
            for field in self.SCAN_FIELDS:
                for f in self.scan_text(name, field, texts.get(field)):
                    key = (f.code, f.evidence)
                    if key in seen:
                        continue
                    seen.add(key)
                    findings.append(f)

            if name not in base_models:
                findings.append(Finding(name, "UNPINNED", "MEDIUM", "no baseline entry for model"))
            else:
                old = base_models[name]
                if old.get("digest") != rec["digest"]:
                    findings.append(Finding(name, "DIGEST_CHANGED", "HIGH",
                                            "digest differs from baseline", "digest",
                                            f"{old.get('digest')} -> {rec['digest']}"))
                if old.get("template_sha256") != rec["template_sha256"]:
                    findings.append(Finding(name, "TEMPLATE_CHANGED", "CRITICAL",
                                            "template differs from baseline (possible rug-pull)", "template",
                                            f"{old.get('template_sha256')} -> {rec['template_sha256']}"))
                if old.get("system_sha256") != rec["system_sha256"]:
                    findings.append(Finding(name, "SYSTEM_CHANGED", "HIGH",
                                            "system prompt differs from baseline", "system",
                                            f"{old.get('system_sha256')} -> {rec['system_sha256']}"))

        if baseline is not None:
            current_names = {i["record"]["name"] for i in collected}
            for name in sorted(set(base_models) - current_names):
                findings.append(Finding(name, "REMOVED", "LOW", "model present in baseline but absent now"))

        return [f.to_dict() for f in findings]


# ---------------------------------------------------------------------- persistence helpers
def write_baseline(path: str, snapshot: Mapping[str, Any]) -> str:
    """Atomically write the snapshot JSON; returns the file sha256."""
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".baseline.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(snapshot, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return sha256_file(path)


def load_baseline(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------- CLI
def main(argv: Optional[List[str]] = None, fetch_json: Optional[FetchJson] = None) -> int:
    ap = argparse.ArgumentParser(description="XORAS read-only Ollama model manifest scanner")
    ap.add_argument("--base-url", default=os.environ.get("OLLAMA_HOST", "http://localhost:11434"))
    ap.add_argument("--baseline", default=None, help="baseline JSON path")
    ap.add_argument("--write-baseline", action="store_true", help="snapshot node and write --baseline")
    ap.add_argument("--audit", action="store_true", help="audit node (against --baseline if it exists)")
    args = ap.parse_args(argv)

    if not (args.write_baseline or args.audit):
        ap.error("choose --write-baseline and/or --audit")
    if args.write_baseline and not args.baseline:
        ap.error("--write-baseline requires --baseline PATH")

    scanner = ModelManifestScanner(fetch_json=fetch_json, base_url=args.base_url)
    exit_code = 0

    if args.audit:
        baseline = load_baseline(args.baseline) if args.baseline else None
        findings = scanner.audit(baseline)
        print(json.dumps({"base_url": args.base_url, "baseline": args.baseline if baseline else None,
                          "findings": findings}, indent=2))
        if any(SEVERITY_ORDER.get(f["severity"], 0) >= SEVERITY_ORDER["HIGH"] for f in findings):
            exit_code = 1

    if args.write_baseline:
        snap = scanner.snapshot()
        digest = write_baseline(args.baseline, snap)
        print(json.dumps({"baseline_written": args.baseline, "models": len(snap["models"]),
                          "file_sha256": digest}, indent=2))

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
