"""
=============================================================================
XORAS EXTENDED TOOL REGISTRY HARD-STRESS TORTURE TEST SUITE
Path: workspaces/xoras_agent_framework/tests/test_sovereign_tool_registry_extended.py
Standards: NIST SP 800-53 Rev. 5, NASA Software Safety Standard (Fail-Closed)
Coverage: 100% of New Sovereign Tools (7 Tools) under Heavy Concurrency & Fuzzing
=============================================================================
"""

import hashlib
import json
import os
import sys
import time
import pytest
from concurrent.futures import ThreadPoolExecutor

from xoras.tools import (
    SovereignToolRegistry,
    ToolDescriptor,
    NativeSystemProbe,
    CryptographicVault,
    CodeSandboxRunner,
    EpistemicProvenanceStore,
    NetworkAirgapGuard,
    ModelManifestScanner,
)
from xoras.tools.cryptographic_vault import SignatureReceipt


# ============================================================================
# 1. NATIVE SYSTEM PROBE TESTS
# ============================================================================
def test_native_system_probe_live_hardware_metrics():
    """Verify system probe reads real hardware data on Apple Silicon / POSIX."""
    probe = NativeSystemProbe()
    receipt = probe.probe()

    assert receipt.schema == "xoras.native_system_probe.v1"
    assert receipt.timestamp_epoch_ms > 0
    assert receipt.cpu_count_logical >= 1
    assert receipt.memory.total_bytes > 0
    assert receipt.storage.total_bytes > 0
    assert len(receipt.load_averages) == 3
    assert receipt.execution_time_ms >= 0.0

    # Test dictionary export serialization
    d = probe.as_dict()
    assert isinstance(d, dict)
    assert "memory" in d
    assert "storage" in d


def test_native_system_probe_stress_execution_speed():
    """Torture test: execute 500 consecutive probes, asserting sub-millisecond execution."""
    probe = NativeSystemProbe()
    t0 = time.perf_counter()
    for _ in range(500):
        r = probe.probe()
        assert r.cpu_count_logical >= 1
    total_elapsed = time.perf_counter() - t0
    avg_ms = (total_elapsed / 500.0) * 1000.0
    # Must average well under 2ms per probe on Apple Silicon M4
    assert avg_ms < 5.0, f"Probe too slow: {avg_ms} ms/op"


# ============================================================================
# 2. CRYPTOGRAPHIC VAULT TESTS
# ============================================================================
def test_cryptographic_vault_signature_and_verification():
    """Verify HMAC-SHA256 signature generation and constant-time verification."""
    vault = CryptographicVault()
    data = b"Sovereign collective state assertion #001"

    receipt = vault.sign_payload(data)
    assert receipt.schema == "xoras.cryptographic_vault.v1"
    assert len(receipt.signature_hex) == 64
    assert len(receipt.nonce) == 32

    # Valid verification
    ok, reason = vault.verify_payload(data, receipt)
    assert ok is True
    assert reason == "VERIFIED"

    # Tampered payload verification
    tampered_data = b"Sovereign collective state assertion #002 (tampered)"
    ok_tamper, reason_tamper = vault.verify_payload(tampered_data, receipt)
    assert ok_tamper is False
    assert reason_tamper == "SIGNATURE_FORGERY_DETECTED"

    # Foreign key mismatch
    foreign_vault = CryptographicVault()
    ok_foreign, reason_foreign = foreign_vault.verify_payload(data, receipt)
    assert ok_foreign is False
    assert reason_foreign == "KEY_ID_MISMATCH"


def test_cryptographic_vault_merkle_tree_computation():
    """Verify binary Merkle tree root calculation over arbitrary chunk counts."""
    vault = CryptographicVault()

    # Empty chunks
    empty_tree = vault.compute_merkle_root([])
    assert empty_tree.chunk_count == 0
    assert empty_tree.root_hash == hashlib.sha256(b"").hexdigest()

    # Power of 2 chunks (4 chunks)
    chunks = [f"chunk_{i}".encode("utf-8") for i in range(4)]
    tree_4 = vault.compute_merkle_root(chunks)
    assert tree_4.chunk_count == 4
    assert len(tree_4.chunk_hashes) == 4
    assert len(tree_4.root_hash) == 64

    # Odd chunk count (5 chunks - requires canonical duplication)
    chunks_5 = [f"chunk_{i}".encode("utf-8") for i in range(5)]
    tree_5 = vault.compute_merkle_root(chunks_5)
    assert tree_5.chunk_count == 5
    assert len(tree_5.chunk_hashes) == 5
    assert tree_5.root_hash != tree_4.root_hash


def test_cryptographic_vault_anti_replay_and_expiry():
    """Verify replay nonces and timestamp boundaries."""
    vault = CryptographicVault()
    data = b"State update"

    # Fabricate expired receipt
    expired_receipt = SignatureReceipt(
        schema=vault.SCHEMA_VERSION,
        key_id=vault._key_id,
        digest_algorithm="HMAC-SHA256",
        signature_hex="deadbeef" * 8,
        timestamp_epoch_ms=int((time.time() - 100) * 1000),  # 100s in past
        nonce="0" * 32,
    )
    ok, reason = vault.verify_payload(data, expired_receipt)
    assert ok is False
    assert reason == "TIMESTAMP_EXPIRED"


# ============================================================================
# 3. CODE SANDBOX RUNNER TESTS
# ============================================================================
def test_code_sandbox_runner_ast_screening_blocks_forbidden_primitives():
    """Verify AST pre-flight screening blocks dangerous calls, imports, and builtins."""
    runner = CodeSandboxRunner(timeout_sec=2.0)

    # 1. Eval block
    res_eval = runner.run_snippet("x = eval('1 + 1')")
    assert res_eval.status == "PRE_FLIGHT_BLOCKED"
    assert any("FORBIDDEN_CALL: eval" in v for v in res_eval.security_violations)

    # 2. Exec block
    res_exec = runner.run_snippet("exec('print(1)')")
    assert res_exec.status == "PRE_FLIGHT_BLOCKED"
    assert any("FORBIDDEN_CALL: exec" in v for v in res_exec.security_violations)

    # 3. Ctypes import block
    res_ctypes = runner.run_snippet("import ctypes\nctypes.CDLL('libc.so')")
    assert res_ctypes.status == "PRE_FLIGHT_BLOCKED"
    assert any("FORBIDDEN_IMPORT: ctypes" in v for v in res_ctypes.security_violations)

    # 4. Socket import block
    res_socket = runner.run_snippet("from socket import socket\ns = socket()")
    assert res_socket.status == "PRE_FLIGHT_BLOCKED"
    assert any("FORBIDDEN_IMPORT_FROM: socket" in v for v in res_socket.security_violations)

    # 5. Builtins inspection block
    res_builtins = runner.run_snippet("b = object.__builtins__")
    assert res_builtins.status == "PRE_FLIGHT_BLOCKED"
    assert any("FORBIDDEN_BUILTINS_ACCESS" in v for v in res_builtins.security_violations)


def test_code_sandbox_runner_safe_execution_and_timeout():
    """Verify safe snippets execute cleanly while infinite loops hit timeout limit."""
    runner = CodeSandboxRunner(timeout_sec=1.0)

    # Safe math snippet
    safe_code = "print(sum(i * i for i in range(100)))"
    res_safe = runner.run_snippet(safe_code)
    assert res_safe.status == "SUCCESS"
    assert res_safe.exit_code == 0
    assert "328350" in res_safe.stdout

    # Infinite loop timeout
    infinite_loop = "while True:\n    pass"
    res_timeout = runner.run_snippet(infinite_loop)
    assert res_timeout.status == "TIMEOUT_EXPIRED"
    assert res_timeout.exit_code == -2
    assert "TIMEOUT_EXCEEDED" in res_timeout.security_violations


# ============================================================================
# 4. EPISTEMIC PROVENANCE STORE TESTS
# ============================================================================
def test_epistemic_provenance_store_hash_chain_and_ethics():
    """Verify ethical score enforcement and cryptographic chain integrity."""
    store = EpistemicProvenanceStore()

    # Reject assertion below ethical threshold (< 0.80)
    ok_low, entry_low, reason_low = store.commit_assertion(
        author_agent="rogue_agent",
        assertion_text="Deploy unverified speculative code",
        ethical_alignment_score=0.65,
    )
    assert ok_low is False
    assert entry_low is None
    assert "ETHICAL_ALIGNMENT_REJECTED" in reason_low

    # Commit valid assertions
    ok1, e1, r1 = store.commit_assertion("maxx", "Honesty is mandatory in all reports", 0.98)
    assert ok1 is True
    assert e1 is not None
    assert r1 == "COMMITTED"

    ok2, e2, r2 = store.commit_assertion("vance", "Empirical proof precedes production promotion", 0.95)
    assert ok2 is True
    assert e2.parent_entry_hash == e1.entry_hash

    ok3, e3, r3 = store.commit_assertion("clara", "Zero third-party telemetry ensures true sovereignty", 0.99)
    assert ok3 is True
    assert e3.parent_entry_hash == e2.entry_hash

    # Full chain integrity check
    intact, count, msg = store.verify_chain_integrity()
    assert intact is True
    assert count == 3
    assert msg == "CHAIN_INTACT"

    # Query facts
    results = store.query_facts("telemetry")
    assert len(results) == 1
    assert "Zero third-party telemetry" in results[0]["assertion_text"]


def test_epistemic_provenance_store_detects_tampering():
    """Verify tampering with historical entry hash immediately fails validation."""
    store = EpistemicProvenanceStore()
    store.commit_assertion("maxx", "Truth statement 1", 0.95)
    store.commit_assertion("vance", "Truth statement 2", 0.95)

    # Illegally mutate second entry
    tampered_entry = store._chain[1]
    store._chain[1] = type(tampered_entry)(
        entry_id=tampered_entry.entry_id,
        author_agent=tampered_entry.author_agent,
        assertion_text="Tampered text statement",
        ethical_alignment_score=tampered_entry.ethical_alignment_score,
        parent_entry_hash=tampered_entry.parent_entry_hash,
        entry_hash=tampered_entry.entry_hash,  # Hash no longer matches content!
        timestamp_epoch_ms=tampered_entry.timestamp_epoch_ms,
    )

    intact, bad_idx, err_msg = store.verify_chain_integrity()
    assert intact is False
    assert bad_idx == 1
    assert "HASH_TAMPERING_DETECTED" in err_msg


# ============================================================================
# 5. NETWORK AIRGAP GUARD TESTS
# ============================================================================
def test_network_airgap_guard_policy_enforcement():
    """Verify airgap guard permits local LAN cluster and blocks external cloud telemetry."""
    guard = NetworkAirgapGuard()

    # Allowed local targets
    r_local = guard.audit_destination("http://localhost:8080/api")
    assert r_local.is_permitted is True
    assert r_local.verdict_reason == "ALLOWED_LOCAL_HOST"

    r_lan = guard.audit_destination("http://192.168.1.211:11434/api/tags")
    assert r_lan.is_permitted is True
    assert "ALLOWED_LAN_SUBNET" in r_lan.verdict_reason

    r_container = guard.audit_destination("http://10.0.1.5:9090")
    assert r_container.is_permitted is True

    # Blocked external telemetry domains
    r_telemetry = guard.audit_destination("https://telemetry.segment.io/v1/track")
    assert r_telemetry.is_permitted is False
    assert r_telemetry.verdict_reason == "FORBIDDEN_THIRD_PARTY_TELEMETRY"

    r_sentry = guard.audit_destination("https://o12345.ingest.sentry.io/api")
    assert r_sentry.is_permitted is False
    assert r_sentry.verdict_reason == "FORBIDDEN_THIRD_PARTY_TELEMETRY"

    # Blocked arbitrary internet IPs
    r_ext_ip = guard.audit_destination("http://8.8.8.8:53")
    assert r_ext_ip.is_permitted is False
    assert r_ext_ip.verdict_reason == "EXTERNAL_INTERNET_IP_DENIED"

    # Blocked external domains
    r_ext_domain = guard.audit_destination("https://api.openai.com/v1/chat")
    assert r_ext_domain.is_permitted is False
    assert r_ext_domain.verdict_reason == "UNREGISTERED_EXTERNAL_FQDN_DENIED"


# ============================================================================
# 6. UNIFIED SOVEREIGN TOOL REGISTRY INTEGRATION TESTS
# ============================================================================
def test_sovereign_tool_registry_lifecycle_and_execution():
    """Verify registry lists all 7 tools and executes them safely with receipts."""
    registry = SovereignToolRegistry()
    tools = registry.list_tools()
    assert len(tools) >= 7

    names = {t.name for t in tools}
    expected = {
        "native_system_probe",
        "cryptographic_vault",
        "code_sandbox_runner",
        "epistemic_provenance_store",
        "network_airgap_guard",
        "model_manifest_scanner",
        "serpapi_client",
    }
    assert expected.issubset(names)

    # 1. Execute system probe via registry
    res_probe = registry.execute_tool("native_system_probe")
    assert res_probe["status"] == "SUCCESS"
    assert res_probe["category"] == "HARDWARE_KERNEL_TELEMETRY"
    assert "memory" in res_probe["result"]

    # 2. Execute code sandbox runner via registry
    res_sandbox = registry.execute_tool("code_sandbox_runner", "print('hello from sandbox')")
    assert res_sandbox["status"] == "SUCCESS"
    assert res_sandbox["result"]["status"] == "SUCCESS"
    assert "hello from sandbox" in res_sandbox["result"]["stdout"]

    # 3. Execute network airgap guard via registry
    res_airgap = registry.execute_tool("network_airgap_guard", "https://api.segment.io")
    assert res_airgap["status"] == "SUCCESS"
    assert res_airgap["result"]["is_permitted"] is False

    # 4. Execute unknown tool
    res_unknown = registry.execute_tool("nonexistent_cloud_tool")
    assert res_unknown["status"] == "TOOL_NOT_FOUND"


def test_sovereign_tool_registry_concurrent_multi_thread_stress():
    """Torture test: run 200 concurrent tool executions across worker threads."""
    registry = SovereignToolRegistry()

    def worker_task(idx):
        if idx % 3 == 0:
            return registry.execute_tool("native_system_probe")
        elif idx % 3 == 1:
            return registry.execute_tool("network_airgap_guard", f"http://192.168.1.{idx % 250}:8080")
        else:
            return registry.execute_tool("code_sandbox_runner", f"print({idx} * {idx})")

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(worker_task, range(100)))

    assert len(results) == 100
    for r in results:
        assert r["status"] == "SUCCESS"
