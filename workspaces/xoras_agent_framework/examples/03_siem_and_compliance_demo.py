"""
XORAS Enterprise Control Plane Example: SIEM Exporting & SOC2 Audit Reporting
"""

from xoras import XORASAgentEnvironment, SIEMExporter, SOC2ComplianceAuditor

def main():
    print("=== 1. INITIALIZING XORAS AGENT ENVIRONMENT ===")
    env = XORASAgentEnvironment()

    # Execute safe agent tool call
    res = env.execute_tool("Engineer", "file_write", {
        "path": "artifacts/enterprise_status.json",
        "content": '{"status": "XORAS Enterprise Governance Active", "audited": true}'
    })
    print("Execution Result:", res)

    print("\n=== 2. SIEM LOG EXPORTER DEMONSTRATION ===")
    siem = SIEMExporter(target_format="datadog")
    signer = env.signer
    receipt = signer.sign_receipt("Engineer", "file_write", {"path": "artifacts/enterprise_status.json"}, "SUCCESS")
    
    datadog_payload = siem.format_receipt_for_siem(receipt)
    print("Datadog Formatted Log Payload:\n", datadog_payload)

    print("\n=== 3. AUTOMATED SOC2 & ISO 27001 COMPLIANCE AUDITOR ===")
    auditor = SOC2ComplianceAuditor(organization="XORAS Systems LLC")
    report = auditor.generate_audit_report(env.trace_file)
    print(f"Compliance Verdict: {report.compliance_verdict}")
    print(f"Audit Summary: {report.audit_summary}")
    print("Evaluated Controls:", report.controls_evaluated)

if __name__ == "__main__":
    main()
