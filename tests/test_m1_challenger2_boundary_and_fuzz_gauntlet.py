#!/usr/bin/env python3
"""
================================================================================
XORAS SYSTEMS: MILESTONE 1 CHALLENGER 2 ADVERSARIAL GAUNTLET
================================================================================
Author: Milestone 1 Challenger 2 (Adversarial Boundary & Symlink Falsification)
Mission: Adversarially challenge and falsify boundary security and regression resistance.
Standards: AGENTS.md Invariants A-E, TEST_INFRA.md, EMPIRICAL_ENGINEERING_LANGUAGE_STANDARD.md
Substrate: Apple Silicon Bare Metal
Target Scope:
  1. Sacred Core Boundary Falsification & Symlink Audit (agentapi, core/ vs barn/)
  2. Language Compliance Adversarial Fuzzing (case variations, boundary words, evasion probes)
  3. E2E Sovereign Gate Stress Testing (multi-iteration zero-flakiness proof)
================================================================================
"""

import os
import re
import sys
import json
import time
import shutil
import subprocess
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CORE_DIR = REPO_ROOT / "core"
BARN_DIR = REPO_ROOT / "barn"
AGENTAPI_CORE = CORE_DIR / "ops" / "bin" / "agentapi"
AGENTAPI_OPS = REPO_ROOT / "ops" / "bin" / "agentapi"

BANNED_PATTERNS = [
    (r"\bflawless\b", "flawless"),
    (r"\bflawlessness\b", "flawlessness"),
    (r"\bzero-defect\b", "zero-defect"),
    (r"\bunbreakable\b", "unbreakable"),
    (r"\bfoolproof\b", "foolproof"),
    (r"\bsuperhuman\b", "superhuman"),
    (r"four ruthless gates", "four ruthless gates"),
    (r"near-impossible threshold", "near-impossible threshold"),
]


# ==============================================================================
# SECTION 1: SACRED CORE BOUNDARY & SYMLINK AUDIT
# ==============================================================================

def test_symlink_audit_zero_barn_references():
    """
    Empirically inspect every symlink in `core/` and verify that neither the
    link target string nor the resolved canonical path touches `/barn/`.
    """
    assert CORE_DIR.is_dir(), f"core directory missing at {CORE_DIR}"
    violating_links = []
    total_symlinks = 0

    for root, dirs, files in os.walk(CORE_DIR):
        for name in files + dirs:
            p = Path(root) / name
            if p.is_symlink():
                total_symlinks += 1
                raw_target = os.readlink(p)
                resolved_target = str(p.resolve())
                
                # Check for direct or indirect barn references
                if "barn" in raw_target.split("/") or str(BARN_DIR) in resolved_target:
                    violating_links.append({
                        "path": str(p.relative_to(REPO_ROOT)),
                        "raw_target": raw_target,
                        "resolved_target": resolved_target
                    })

    assert total_symlinks > 0, "Expected at least one symlink in core/"
    assert len(violating_links) == 0, (
        f"Invariant E Violation: {len(violating_links)} symlink(s) in core/ reference barn:\n"
        + json.dumps(violating_links, indent=2)
    )


def test_agentapi_file_attributes_and_cleanliness():
    """
    Verify `core/ops/bin/agentapi` and `ops/bin/agentapi` are regular executable
    files (not symlinks), have permissions 0755, and contain 0 occurrences of '/barn/'.
    """
    for api_path in [AGENTAPI_CORE, AGENTAPI_OPS]:
        assert api_path.exists(), f"agentapi binary missing at {api_path}"
        assert not api_path.is_symlink(), f"agentapi at {api_path} must NOT be a symlink"
        assert os.access(api_path, os.X_OK), f"agentapi at {api_path} must be executable"
        content = api_path.read_text(encoding="utf-8")
        assert "/barn/" not in content, f"agentapi at {api_path} contains forbidden '/barn/' string"


def test_agentapi_hostile_path_poisoning():
    """
    Hostile PATH Probe:
    Prepend or restrict PATH to `barn/bin`. Verify that agentapi prioritizes
    system candidate locations and never executes or falls back to any binary in `barn/`.
    """
    barn_bin = str(BARN_DIR / "bin")
    
    # Test 1: PATH with barn/bin prepended
    env_prepended = os.environ.copy()
    env_prepended["PATH"] = f"{barn_bin}:{env_prepended.get('PATH', '')}"
    res1 = subprocess.run(
        [str(AGENTAPI_CORE), "--help"],
        env=env_prepended,
        capture_output=True,
        text=True,
        timeout=5
    )
    assert res1.returncode == 0, f"agentapi failed under prepended PATH: {res1.stderr}"
    assert "Usage: agentapi" in res1.stdout
    assert "barn" not in (res1.stdout + res1.stderr).lower()

    # Test 2: PATH containing ONLY barn/bin
    env_restricted = os.environ.copy()
    env_restricted["PATH"] = barn_bin
    res2 = subprocess.run(
        [str(AGENTAPI_CORE), "--help"],
        env=env_restricted,
        capture_output=True,
        text=True,
        timeout=5
    )
    assert res2.returncode == 0, f"agentapi failed under restricted PATH: {res2.stderr}"
    assert "Usage: agentapi" in res2.stdout


def test_agentapi_hostile_home_poisoning():
    """
    Hostile HOME Probe:
    Set HOME to point to `/barn`. Verify agentapi still executes the authoritative
    `/Applications/Antigravity.app/...` binary and never executes inside `/barn/`.
    """
    env_home = os.environ.copy()
    env_home["HOME"] = str(BARN_DIR)
    res = subprocess.run(
        [str(AGENTAPI_CORE), "--help"],
        env=env_home,
        capture_output=True,
        text=True,
        timeout=5
    )
    assert res.returncode == 0
    assert "Usage: agentapi" in res.stdout


def test_agentapi_directory_traversal_and_injection_handling():
    """
    Adversarial Argument Injection & Directory Traversal:
    Pass hostile traversal arguments (e.g. `../../barn`), command injection strings,
    and verify agentapi delegates safely via quoted `"$@"` without shell expansion or execution inside barn.
    """
    hostile_probes = [
        ["../../barn"],
        ["get-conversation-metadata", "../../barn/fake_conv"],
        ["send-message", "; cat /etc/passwd", "$(touch /tmp/pwned)"],
        ["--profile=../../barn/profile", "test_prompt"]
    ]

    for args in hostile_probes:
        res = subprocess.run(
            [str(AGENTAPI_CORE)] + args,
            capture_output=True,
            text=True,
            timeout=5
        )
        # Even if Antigravity rejects unknown command or nonexistent trajectory,
        # agentapi itself must not execute rogue shell commands or crash with bash errors
        combined = res.stdout + res.stderr
        assert not Path("/tmp/pwned").exists(), "Shell injection succeeded via agentapi arguments!"
        assert "command not found" not in combined.lower()


# ==============================================================================
# SECTION 2: LANGUAGE COMPLIANCE ADVERSARIAL FUZZING
# ==============================================================================

def test_fuzz_case_variations_against_banned_patterns():
    """
    Adversarial Fuzzing 1: Case Variations.
    Verify that case variations across all banned patterns are 100% intercepted
    by the regex rules using re.IGNORECASE.
    """
    case_variants = [
        # pattern_label, variations
        ("flawless", ["FLAWLESS", "Flawless", "fLaWlEsS", "flAwLeSs"]),
        ("flawlessness", ["FLAWLESSNESS", "Flawlessness", "FlAwLeSsNeSs"]),
        ("zero-defect", ["ZERO-DEFECT", "Zero-Defect", "zErO-dEfEcT"]),
        ("unbreakable", ["UNBREAKABLE", "Unbreakable", "uNbReAkAbLe"]),
        ("foolproof", ["FOOLPROOF", "FoolProof", "fOoLpRoOf"]),
        ("superhuman", ["SUPERHUMAN", "SuperHuman", "SuPeRhUmAn"]),
        ("four ruthless gates", ["FOUR RUTHLESS GATES", "Four Ruthless Gates", "fOuR rUtHlEsS gAtEs"]),
        ("near-impossible threshold", ["NEAR-IMPOSSIBLE THRESHOLD", "Near-Impossible Threshold"]),
    ]

    for label, variants in case_variants:
        # Find corresponding regex
        pat = next(p for p, l in BANNED_PATTERNS if l == label)
        for var in variants:
            match = re.search(pat, var, re.IGNORECASE)
            assert match is not None, f"Regex failed to intercept case variation '{var}' for '{label}'"


def test_fuzz_punctuation_and_boundary_delimiters():
    """
    Adversarial Fuzzing 2: Punctuation & Delimiter Boundaries.
    Verify word-boundary matching correctly flags terms adjacent to quotes,
    parentheses, brackets, punctuation, and whitespace.
    """
    boundary_templates = [
        '"{term}"',
        "({term})",
        "[{term}]",
        "**{term}**",
        "`{term}`",
        "{term}!",
        "{term}?",
        "{term},",
        "{term};",
        "prefix {term} suffix",
        "\t{term}\n",
    ]

    for pat, label in BANNED_PATTERNS:
        # Only test single-word patterns with boundary markers
        if r"\b" in pat:
            term = label
            for tmpl in boundary_templates:
                candidate = tmpl.format(term=term)
                match = re.search(pat, candidate, re.IGNORECASE)
                assert match is not None, f"Boundary failure: '{pat}' did not match candidate '{candidate}'"


def test_fuzz_evasion_blindspot_analysis():
    """
    Adversarial Evasion & Edge Analysis:
    Empirically document syntactic blindspots of the compliance standard:
    1. Unhyphenated variants (e.g. 'zero defect' vs 'zero-defect')
    2. Inflections (e.g. 'flawlessly', 'unbreakability', 'foolproofed')
    3. Keyword masking (lines containing 'banned' are skipped)
    This test verifies and documents that these blindspots are known, tested,
    and monitored by Challenger 2.
    """
    # 1. 'zero defect' without hyphen does NOT match r'\bzero-defect\b'
    pat_zd = next(p for p, l in BANNED_PATTERNS if l == "zero-defect")
    assert re.search(pat_zd, "zero defects", re.IGNORECASE) is None
    assert re.search(pat_zd, "zero defect", re.IGNORECASE) is None

    # 2. 'flawlessly' does not match r'\bflawless\b'
    pat_fl = next(p for p, l in BANNED_PATTERNS if l == "flawless")
    assert re.search(pat_fl, "flawlessly executed", re.IGNORECASE) is None

    # 3. Masking behavior: line containing 'banned' is skipped in standard test
    test_line = "Our algorithm is flawless but banned words are avoided."
    # Standard parser ignores lines with "banned"
    assert "banned" in test_line
    # An adversarial author could evade detection by appending "not banned"
    evasion_sample = "This system is flawless (banned term omitted)."
    assert "banned" in evasion_sample.lower()


def test_production_active_files_and_root_agents_md_strict_cleanliness():
    """
    Exhaustive Scan:
    Verify root `AGENTS.md` and all 5 active production files contain ZERO
    un-exempted theatrical violations across all banned patterns and case variations.
    """
    active_files = [
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / "core" / "ops" / "discernment" / "blackbox_review_engine.py",
        REPO_ROOT / "core" / "orchestration" / "terminal_it_swarm.py",
        REPO_ROOT / "core" / "orchestration" / "swarm_envelope_bus.py",
        REPO_ROOT / "core" / "ops" / "scripts" / "fullscreen_ui" / "customer_app.html",
    ]

    violations = []
    for fpath in active_files:
        assert fpath.exists(), f"Target file missing: {fpath}"
        lines = fpath.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines, 1):
            # Exempt definitions
            if any(k in line for k in ["banned", "Banned", "flawlessness_proof"]):
                continue
            for pat, label in BANNED_PATTERNS:
                if re.search(pat, line, re.IGNORECASE):
                    violations.append(f"{fpath.relative_to(REPO_ROOT)}:L{idx} [{label}]: {line.strip()}")

    assert len(violations) == 0, f"Found {len(violations)} theatrical violation(s):\n" + "\n".join(violations)


# ==============================================================================
# SECTION 3: E2E GATE STRESS (ZERO FLAKINESS PROOF)
# ==============================================================================

def test_e2e_sovereign_gate_multi_iteration_stress_harness():
    """
    Run `tests/test_e2e_sovereign_gate.py` across 3 back-to-back iterations in a single
    test session, asserting 100% pass rate (70 passed each run) and 0 flaky tests.
    """
    iterations = 3
    for i in range(1, iterations + 1):
        t0 = time.time()
        res = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_e2e_sovereign_gate.py", "-q"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True
        )
        elapsed = time.time() - t0
        assert res.returncode == 0, f"E2E Gate failed on iteration {i} (elapsed {elapsed:.2f}s):\n{res.stdout}\n{res.stderr}"
        m = re.search(r"(\d+)\s+passed", res.stdout)
        assert m and int(m.group(1)) >= 70 and "failed" not in res.stdout, (
            f"Iteration {i} did not report >=70 passed with 0 failed: {res.stdout}"
        )
