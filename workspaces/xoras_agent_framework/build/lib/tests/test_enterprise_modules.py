"""
Test suite for XORAS Enterprise Control Plane & Polyglot IPC Modules
"""

import os
import pytest
from xoras import (
    CryptographicSigner,
    SIEMExporter,
    PolyglotIPCBridge,
    SOC2ComplianceAuditor,
    XORASSerpAPIClient
)

def test_siem_exporter_datadog():
    signer = CryptographicSigner()
    receipt = signer.sign_receipt("Auditor", "ast_scan", {"target": "xoras/"}, "SUCCESS")
    exporter = SIEMExporter(target_format="datadog")
    payload = exporter.format_receipt_for_siem(receipt)
    assert payload["ddsource"] == "xoras_agent_framework"
    assert "Auditor" in payload["message"]

def test_siem_exporter_splunk():
    signer = CryptographicSigner()
    receipt = signer.sign_receipt("Auditor", "ast_scan", {"target": "xoras/"}, "SUCCESS")
    exporter = SIEMExporter(target_format="splunk")
    payload = exporter.format_receipt_for_siem(receipt)
    assert payload["sourcetype"] == "xoras:evidence:v1"

def test_polyglot_ipc_bridge_missing_file():
    bridge = PolyglotIPCBridge()
    res = bridge.execute_binary_ipc("non_existent_binary", ["--help"])
    assert res.success is False
    assert "not found" in res.stderr

def test_soc2_compliance_auditor():
    auditor = SOC2ComplianceAuditor()
    report = auditor.generate_audit_report("non_existent_traces.jsonl")
    assert report.compliance_verdict == "NON_COMPLIANT_MISSING_LOGS"

def test_serpapi_client_initialization():
    client = XORASSerpAPIClient()
    assert client.api_key is not None
