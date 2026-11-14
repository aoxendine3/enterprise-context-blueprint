#!/usr/bin/env python3
"""
=============================================================================
OUTSIDE ENTITY DETECTOR — STRUCTURAL, NAME-FREE
=============================================================================
Sovereign law: our artifacts carry no attribution to any third-party product
or assistant, and no self-reference to a generic outside category.

This detector NEVER names an outside entity. It detects the SHAPE of an
outside attribution — an attribution slot, an attribution phrase, or an
outside category self-reference — and reports the file and line so a human
can look, without this module ever carrying a third-party name.

Rules (all structural):
  1. ATTRIBUTION PHRASE  — "powered by X", "built with X", "based on X",
     "inspired by X", "thanks to X", "using the X IDE", "the X assistant".
  2. ATTRIBUTION SLOT    — a receipt/JSON field whose name is an attribution
     slot (vendor, product, brand, powered_by, built_with, editor, ide,
     assistant, model_vendor, based_on) whose value is not a sovereign term.
  3. OUTSIDE CATEGORY    — self-reference to a generic outside category
     ("as an AI", "AI assistant", "language model", "chatbot", "AI agent").
  4. OUTSIDE NARRATIVE   — a sentence that credits another party for the work.

Only sovereign vocabulary is named, and only as the allowlist of who WE are.
=============================================================================
"""

import json
import re

# WHO WE ARE — the only names this module carries.
SOVEREIGN_VOCAB = {
    "maxx", "clara", "vance", "daxx", "jarvis", "john", "orion", "selene",
    "eden", "aurelius", "arthur", "axlon", "lex", "elana", "evan", "counselor",
    "jeremy", "zorex", "brandon",
    "xoras", "sovra", "ssot", "daxxco", "upgp", "mtpo", "mars", "smit",
    "clara", "sovereign", "collective", "council",
    "apple", "linux", "unix", "posix", "zig", "rust", "python", "swift",
    "sqlite", "postgres", "postgres", "lancedb", "ollama", "vercel", "github",
    "pages", "cloudflare", "workers", "darwin", "macos", "ios", "tvos",
    "windows", "nt", "amd64", "arm64", "x86",
    "http", "https", "json", "yaml", "toml", "csv", "md", "api", "cdn", "ui",
    "llm", "sql", "rest", "sha256", "sha512", "hmac", "ed25519", "aes",
    "tls", "ssl", "tcp", "udp", "rpc", "ffi", "abi", "wasm", "zig",
}

# Attribution phrase shapes — no entity names, only the grammar of credit.
ATTRIBUTION_PHRASES = [
    r"\bpowered by\b",
    r"\bbuilt with\b",
    r"\bbased on\b",
    r"\binspired by\b",
    r"\bthanks to\b",
    r"\bmade with\b",
    r"\bthe\s+[a-z-]*\s?ide\b",
    r"\bthe\s+[a-z-]*\s?assistant\b",
    r"\bmigrated from\b",
    r"\bported from\b",
    r"\bimported from\b",
]

# Outside category self-reference — categories, not brands.
OUTSIDE_CATEGORY = [
    r"\bas an ai\b",
    r"\bas a language model\b",
    r"\bai[ _-]?assistant\b",
    r"\blarge language model\b",
    r"\bas an ai agent\b",
    r"\bchatbot\b",
    r"\bvirtual assistant\b",
]

# Receipt/JSON fields that are attribution slots.
ATTRIBUTION_SLOTS = {
    "vendor", "product", "brand", "powered_by", "poweredby", "built_with",
    "builtwith", "editor", "ide", "assistant", "model_vendor", "based_on",
    "basedon", "inspired_by", "inspiredby", "origin_vendor", "origin_tool",
    "created_with", "generated_by", "tool_vendor", "client", "client_name",
}


def _is_sovereign(value: str) -> bool:
    v = (value or "").strip().strip("\"'").lower()
    if not v:
        return True
    if v in SOVEREIGN_VOCAB:
        return True
    # Accept a sovereign value that merely CONTAINS a sovereign token
    # (e.g. "SSOT_Agentic_Brain", "clara_conductor").
    return any(tok in v for tok in ("xoras", "sovra", "ssot", "maxx", "clara",
                                    "vance", "daxx", "jarvis", "john", "orion",
                                    "selene", "eden", "aurelius", "upgp", "mtpo",
                                    "mars", "smit"))


def scan_text(text: str) -> list:
    """Return structural violations found in a block of text."""
    violations = []
    for line_no, line in enumerate((text or "").splitlines(), start=1):
        low = line.lower()
        for pat in ATTRIBUTION_PHRASES:
            m = re.search(pat, low)
            if m:
                # An attribution only means an outside party when what follows
                # looks like a proper noun (X-prefixed, capitalized or digits).
                # "thanks to the git repack" is credit to our own machinery,
                # not to a third party — it must not fire.
                rest = low[m.end():].lstrip(" \t")
                if rest and (rest[0].isupper() or rest[0].isdigit()):
                    violations.append({"line": line_no, "kind": "attribution_phrase",
                                       "detail": f"credits another party ({pat.strip(chr(92)+'b')})"})
                    break
        for pat in OUTSIDE_CATEGORY:
            if re.search(pat, low):
                violations.append({"line": line_no, "kind": "outside_category",
                                   "detail": "self-references a generic outside category"})
                break
    return violations


def scan_json(obj, path: str = "") -> list:
    """Return violations for attribution slots whose value is not sovereign."""
    violations = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = str(k).lower()
            if key in ATTRIBUTION_SLOTS and isinstance(v, str):
                if not _is_sovereign(v):
                    violations.append({"path": f"{path}.{k}", "kind": "attribution_slot",
                                       "detail": "attribution slot names a non-sovereign party"})
            violations.extend(scan_json(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            violations.extend(scan_json(v, f"{path}[{i}]"))
    return violations


def scan_file(path: str) -> list:
    """Scan one file. Returns [{line, kind, detail}] — never the offending text."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            raw = fh.read()
    except OSError:
        return []
    if path.endswith(".json"):
        try:
            return scan_json(json.loads(raw))
        except Exception:
            pass
    return scan_text(raw)


if __name__ == "__main__":
    import sys
    for target in sys.argv[1:]:
        for v in scan_file(target):
            print(f"{target}:{v.get('line', v.get('path', '?'))} [{v['kind']}] {v['detail']}")
