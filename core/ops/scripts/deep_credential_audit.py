#!/usr/bin/env python3
"""
DEEP CREDENTIAL AUDIT — read-only, no secret values printed.
Triggered by owner challenge that the prior audit was shallow (missed home dotfiles).

Scans:
  A) canonical repo dirs for credential-like LITERALS (multi-pattern, not just
     AIzaSy / BEGIN PRIVATE KEY) — reports file:line + pattern class, REDACTED.
  B) home dotfiles for credential FILES — reports name/mode/size/VAR NAMES only.
  C) fail-closed behavior of live consumers with credentials ABSENT (no revoke).

Writes memory/catch_log/DEEP_CREDENTIAL_AUDIT.json.
"""
import json, os, re, time, subprocess, importlib.util
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
HOME = Path("/Users/ajoxendine68")
OUT = ROOT / "memory/catch_log/DEEP_CREDENTIAL_AUDIT.json"

# pattern -> redacted detector. Values are NEVER emitted.
PATTERNS = {
    "cloudflare_token": re.compile(r"cfut_[A-Za-z0-9]{20,}"),
    "openai_key": re.compile(r"sk-[A-Za-z0-9]{20,}"),
    "hf_token": re.compile(r"hf_[A-Za-z0-9]{20,}"),
    "github_pat": re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    "google_api_key": re.compile(r"AIza[A-Za-z0-9_-]{30,}"),
    "aws_access": re.compile(r"AKIA[0-9A-Z]{16}"),
    "private_key_block": re.compile(r"BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY"),
}

EXCLUDE_PARTS = {"node_modules", "misc", "__pycache__", ".git", "target",
                 "zsh_sessions", "Caches", ".Trash"}
SCAN_DIRS = [ROOT / "core", ROOT / "ops", ROOT / "code", ROOT / "identity",
             ROOT / "Xoras_agent_cards"]

def redact(kind):
    return f"<{kind}:REDACTED>"

def scan_repo():
    findings = []
    for base in SCAN_DIRS:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix not in (".py", ".sh", ".js", ".cjs", ".mjs", ".json", ".ts", ".env", ".yaml", ".yml"):
                continue
            if any(x in p.parts for x in EXCLUDE_PARTS):
                continue
            try:
                text = p.read_text(errors="ignore")
            except Exception:
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                for kind, pat in PATTERNS.items():
                    if pat.search(line):
                        findings.append({
                            "file": str(p.relative_to(ROOT)),
                            "line": lineno,
                            "pattern": kind,
                            "evidence": redact(kind),
                            "is_default_literal": bool(re.search(r'getenv\([^)]*,\s*["\']', line)) or bool(re.search(r'=\s*["\']' + pat.pattern.split('{')[0], line)),
                        })
    return findings

def scan_home():
    names = [".env", ".xoras_env", ".github_token", ".github_token_extra", ".netrc",
             ".npmrc", ".git-credentials", ".claude.json", ".mcp-auth",
             ".sovereign/cloud_credentials.env", ".sovereign/credentials.json",
             ".config/xoras/cockpit_bundle_signing/ed25519_priv.pem",
             ".config/xoras/cockpit_bundle_signing/ed25519_pub.pem"]
    out = []
    for rel in names:
        p = HOME / rel
        if not p.exists():
            continue
        try:
            st = p.stat()
            mode = oct(st.st_mode & 0o777)
            var_names = []
            if p.suffix in (".env", "") and st.st_size < 5000:
                txt = p.read_text(errors="ignore")
                var_names = re.findall(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=", txt, re.M)
                # token files with no '=' → label as RAW_TOKEN
                if not var_names and any(c in txt for c in "_-"):
                    var_names = ["<RAW_TOKEN_VALUE_PRESENT>"]
            out.append({"file": "~/" + rel, "bytes": st.st_size, "mode": mode,
                        "var_names_or_shape": var_names})
        except Exception as e:
            out.append({"file": "~/" + rel, "error": str(e)})
    return out

def fail_closed_probe():
    """Probe live consumers with credentials ABSENT — no files mutated, no revoke."""
    probes = []
    # 1. cloudflare_r2_client with no env/no file creds -> does upload pretend success?
    saved = {k: os.environ.get(k) for k in ("R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")}
    for k in saved:
        os.environ.pop(k, None)
    try:
        spec = importlib.util.spec_from_file_location(
            "r2probe", ROOT / "core/ops/cloud/cloudflare_r2_client.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        c = mod.SovereignCloudflareR2Client()
        probes.append({"consumer": "cloudflare_r2_client",
                       "access_key_present": bool(c.access_key),
                       "secret_key_present": bool(c.secret_key),
                       "note": "CREDENTIALS_FILE fallback still applies; env-only probe"})
    except Exception as e:
        probes.append({"consumer": "cloudflare_r2_client", "error": type(e).__name__ + ": " + str(e)[:120]})
    finally:
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v
    return probes

repo = scan_repo()
home = scan_home()
probes = fail_closed_probe()
payload = {
    "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "verdict": "DEEP_AUDIT_COMPLETE",
    "owner_challenge": "prior audit was shallow; home dotfiles never scanned",
    "repo_literal_findings": repo,
    "home_credential_files": home,
    "fail_closed_probes": probes,
    "note": "No secret values are stored in this receipt. No credentials revoked.",
}
OUT.write_text(json.dumps(payload, indent=2))
print(json.dumps({
    "verdict": payload["verdict"],
    "repo_literal_findings": len(repo),
    "by_pattern": {k: sum(1 for f in repo if f["pattern"] == k) for k in PATTERNS},
    "home_credential_files": len(home),
    "fail_closed_probes": probes,
    "receipt": str(OUT),
}, indent=2))
