"""
XORAS Systems LLC — Enterprise SIEM & Log Exporter
Formatted log exporter for Datadog, Splunk, Elastic, and Syslog JSON streams.
"""

import json
import logging
from dataclasses import asdict
from typing import Dict, Any, List, Optional
from ..signer import EvidenceReceipt

class SIEMExporter:
    def __init__(self, target_format: str = "datadog", stream_name: str = "xoras.agent.audit"):
        self.target_format = target_format.lower()
        self.stream_name = stream_name

    def format_receipt_for_siem(self, receipt: EvidenceReceipt) -> Dict[str, Any]:
        """Formats an EvidenceReceipt into SIEM-compatible log payload."""
        rec_dict = asdict(receipt)
        
        if self.target_format == "datadog":
            return {
                "ddsource": "xoras_agent_framework",
                "ddtags": f"env:production,agent:{receipt.agent_id},status:{receipt.status}",
                "hostname": "xoras-agent-node",
                "service": self.stream_name,
                "message": json.dumps(rec_dict),
                "timestamp": int(receipt.timestamp * 1000)
            }
        elif self.target_format == "splunk":
            return {
                "event": rec_dict,
                "sourcetype": "xoras:evidence:v1",
                "source": self.stream_name,
                "time": receipt.timestamp
            }
        elif self.target_format == "elastic":
            return {
                "@timestamp": pd_iso_format(receipt.timestamp),
                "event.kind": "event",
                "event.category": "iam",
                "event.type": "access",
                "xoras.agent_id": receipt.agent_id,
                "xoras.action": receipt.action,
                "xoras.status": receipt.status,
                "xoras.signature": receipt.signature,
                "xoras.payload_hash": receipt.payload_hash
            }
        else:
            # Standard JSON Syslog format
            return {
                "syslog_identifier": "XORAS_AGENT_AUDIT",
                "timestamp": receipt.timestamp,
                "receipt": rec_dict
            }

def pd_iso_format(ts: float) -> str:
    import datetime
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).isoformat()
