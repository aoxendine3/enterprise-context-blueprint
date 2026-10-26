"""
=============================================================================
XORAS HIGH-ASSURANCE NETWORK AIRGAP GUARD TOOL
Path: workspaces/xoras_agent_framework/xoras/tools/network_airgap_guard.py
Standards: NIST SP 800-53 Rev. 5 (AC-4 Information Flow Enforcement, SC-7 Boundary Protection)
Capabilities: Local-First Outbound Gating, Subnet Validation, Fail-Closed Aborts,
Zero Cloud Leakage Invariant.
=============================================================================
"""

from __future__ import annotations

import ipaddress
import re
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse


@dataclass(frozen=True)
class NetworkAuditReceipt:
    schema: str
    target_destination: str
    destination_ip_or_host: str
    is_permitted: bool
    verdict_reason: str
    timestamp_epoch_ms: int


class NetworkAirgapGuard:
    """
    Sovereignty enforcement tool that audits destination hosts, IPs, and URLs,
    strictly blocking external third-party telemetry, metrics uploaders, or
    unauthorized cloud traffic while permitting verified local LAN cluster nodes.
    """
    SCHEMA_VERSION = "xoras.network_airgap_guard.v1"

    # Strictly allowed local hostnames
    ALLOWED_HOSTNAMES = frozenset({"localhost", "127.0.0.1", "::1", "sovereign.xoras.local"})

    # Strictly allowed subnets (Loopback and Home LAN subnet for physical Windows node)
    ALLOWED_NETWORKS = (
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("192.168.1.0/24"),  # Physical LAN cluster
        ipaddress.ip_network("10.0.0.0/8"),      # Optional isolated container mesh
    )

    # Disallowed external third-party telemetry patterns
    FORBIDDEN_EXTERNAL_PATTERNS = (
        re.compile(r".*telemetry.*", re.IGNORECASE),
        re.compile(r".*analytics.*", re.IGNORECASE),
        re.compile(r".*segment\.io.*", re.IGNORECASE),
        re.compile(r".*sentry\.io.*", re.IGNORECASE),
        re.compile(r".*datadoghq\.com.*", re.IGNORECASE),
        re.compile(r".*posthog\.com.*", re.IGNORECASE),
    )

    def audit_destination(self, target_url_or_host: str) -> NetworkAuditReceipt:
        """Audit target destination against sovereign airgap policies."""
        ts_ms = int(time.time() * 1000)
        cleaned = target_url_or_host.strip()
        
        # Check forbidden telemetry patterns immediately
        for pat in self.FORBIDDEN_EXTERNAL_PATTERNS:
            if pat.search(cleaned):
                return NetworkAuditReceipt(
                    schema=self.SCHEMA_VERSION,
                    target_destination=cleaned,
                    destination_ip_or_host=cleaned,
                    is_permitted=False,
                    verdict_reason="FORBIDDEN_THIRD_PARTY_TELEMETRY",
                    timestamp_epoch_ms=ts_ms,
                )

        # Parse host
        parsed = urlparse(cleaned)
        host = parsed.hostname or cleaned.split(":")[0]

        if not host:
            return NetworkAuditReceipt(
                schema=self.SCHEMA_VERSION,
                target_destination=cleaned,
                destination_ip_or_host="UNKNOWN",
                is_permitted=False,
                verdict_reason="MALFORMED_DESTINATION",
                timestamp_epoch_ms=ts_ms,
            )

        # Check allowed literal hostnames
        if host.lower() in self.ALLOWED_HOSTNAMES:
            return NetworkAuditReceipt(
                schema=self.SCHEMA_VERSION,
                target_destination=cleaned,
                destination_ip_or_host=host,
                is_permitted=True,
                verdict_reason="ALLOWED_LOCAL_HOST",
                timestamp_epoch_ms=ts_ms,
            )

        # Check IP network allowances
        try:
            ip_obj = ipaddress.ip_address(host)
            for net in self.ALLOWED_NETWORKS:
                if ip_obj in net:
                    return NetworkAuditReceipt(
                        schema=self.SCHEMA_VERSION,
                        target_destination=cleaned,
                        destination_ip_or_host=host,
                        is_permitted=True,
                        verdict_reason=f"ALLOWED_LAN_SUBNET_{net}",
                        timestamp_epoch_ms=ts_ms,
                    )
            # If IP is valid but outside allowed networks -> DENY
            return NetworkAuditReceipt(
                schema=self.SCHEMA_VERSION,
                target_destination=cleaned,
                destination_ip_or_host=host,
                is_permitted=False,
                verdict_reason="EXTERNAL_INTERNET_IP_DENIED",
                timestamp_epoch_ms=ts_ms,
            )
        except ValueError:
            # Host is not an IP; check if it's an unauthorized domain
            return NetworkAuditReceipt(
                schema=self.SCHEMA_VERSION,
                target_destination=cleaned,
                destination_ip_or_host=host,
                is_permitted=False,
                verdict_reason="UNREGISTERED_EXTERNAL_FQDN_DENIED",
                timestamp_epoch_ms=ts_ms,
            )
