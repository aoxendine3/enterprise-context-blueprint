# Standard Template: Swarm Governance & Catch Log Receipt

Use this template for all automated remediation logs, catch log receipts, and Trinity Gate audit trails (`memory/catch_log/`).

## JSON Receipt Schema
```json
{
  "timestamp_utc": "2026-10-06T14:00:00Z",
  "agent_identity": "Maxx",
  "council_gate": "Trinity 2-of-3",
  "operation": "REMEDIATION_RECOVERY",
  "fault_code": "PLACEHOLDER_001",
  "patch_site": "core/ops/scripts/runner.py",
  "verification_gauntlet": "14-Gate Sovereign Blackbox PASS",
  "ed25519_signatures": {
    "maxx": "sig_hex...",
    "clara": "sig_hex...",
    "vance": "sig_hex..."
  },
  "merkle_dag_hash": "f42a86424456c63f809cafd41f01a9c71fc8cebccdeb3648d22e59ec6cb28337"
}
```
