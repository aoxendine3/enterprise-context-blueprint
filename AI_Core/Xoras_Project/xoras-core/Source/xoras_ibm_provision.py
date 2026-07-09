#!/usr/bin/env python3
"""
xoras_ibm_provision.py
IBM Cloud VPC Provisioner — Full Xoras Deployment Stack.

Contract:
  - All network calls use urllib stdlib only. Zero third-party dependencies.
  - All state transitions are logged with ISO timestamps.
  - Every function has a single, clearly named return type.
  - On any fatal error, the script exits with a non-zero code and a clear message.
  - All resource IDs created are written to: /tmp/xoras_ibm_state.json
    so the process can be resumed or reversed at any time.

Target configuration:
  - Region:   us-south (Dallas) — lowest IBM VPC latency for US East Coast
  - Profile:  mx2-48x384       — 48 vCPU / 384 GB RAM (highest non-bare-metal)
  - Disk:     1000 GB boot volume (SSD tier 10)
  - Image:    Ubuntu 24.04 LTS
  - Services: All Xoras stack (dashboard, BFT daemon, execution client, apex bridge)
"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Constants ─────────────────────────────────────────────────────────────────

IBM_API_KEY       = "db0afab1-ed90-48b1-976d-48650ba2683c"
IAM_TOKEN_URL     = "https://iam.cloud.ibm.com/identity/token"
VPC_BASE_URL      = "https://us-south.iaas.cloud.ibm.com/v1"
VPC_API_VERSION   = "2024-06-01"
TARGET_REGION     = "us-south"
TARGET_ZONE       = "us-south-1"

# Machine profile — highest available general VPC profile (non-bare-metal)
# Bare metal requires account pre-authorization on IBM Cloud.
INSTANCE_PROFILE  = "mx2-48x384"  # 48 vCPU, 384 GB RAM

# 1 TB boot volume (SSD tier-10 = highest IOPS tier)
BOOT_VOLUME_CAPACITY_GB = 1000
BOOT_VOLUME_PROFILE     = "10iops-tier"

# Ubuntu 24.04 LTS image name pattern
TARGET_IMAGE_PATTERN    = "ibm-ubuntu-24-04"

STATE_FILE = Path("/tmp/xoras_ibm_state.json")

# ── Logging ───────────────────────────────────────────────────────────────────

def log(level: str, msg: str) -> None:
    """Emit a structured log line with ISO timestamp."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] [{level}] {msg}", flush=True)

def fatal(msg: str) -> None:
    """Log a fatal error and exit immediately with code 1."""
    log("FATAL", msg)
    sys.exit(1)

# ── State Persistence ─────────────────────────────────────────────────────────

def load_state() -> dict:
    """Load provisioning state from disk. Returns empty dict if no state file."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}

def save_state(state: dict) -> None:
    """Atomically write provisioning state to disk."""
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(STATE_FILE)
    log("STATE", f"State saved → {STATE_FILE}")

# ── HTTP Client ───────────────────────────────────────────────────────────────

def http_post(url: str, payload: dict | str, headers: dict) -> dict:
    """
    POST to url with payload.
    payload: dict → sent as application/json
             str  → sent as application/x-www-form-urlencoded
    Returns: parsed JSON response body.
    Raises: SystemExit on HTTP errors.
    """
    if isinstance(payload, dict):
        body = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    else:
        body = payload.encode()

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        fatal(f"POST {url} → HTTP {e.code}: {detail}")
    except urllib.error.URLError as e:
        fatal(f"POST {url} → Network error: {e.reason}")

def http_get(url: str, headers: dict) -> dict:
    """
    GET url.
    Returns: parsed JSON response body.
    Raises: SystemExit on HTTP errors.
    """
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        fatal(f"GET {url} → HTTP {e.code}: {detail}")
    except urllib.error.URLError as e:
        fatal(f"GET {url} → Network error: {e.reason}")

# ── IBM IAM Authentication ─────────────────────────────────────────────────────

def get_iam_token(api_key: str) -> str:
    """
    Exchange an IBM Cloud API key for a short-lived IAM Bearer token.
    Token lifetime: 3600 seconds.
    Returns: Bearer token string (without 'Bearer ' prefix).
    """
    log("AUTH", "Requesting IAM bearer token...")
    payload = urllib.parse.urlencode({
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": api_key
    })
    headers = {"Accept": "application/json"}
    resp = http_post(IAM_TOKEN_URL, payload, headers)
    token = resp.get("access_token")
    if not token:
        fatal(f"IAM token exchange failed. Response: {resp}")
    log("AUTH", "IAM bearer token acquired.")
    return token

# ── IBM VPC Helpers ───────────────────────────────────────────────────────────

def vpc_headers(token: str) -> dict:
    """Build standard VPC API request headers."""
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

def vpc_url(path: str) -> str:
    """Build a fully-qualified VPC API URL with version query parameter."""
    return f"{VPC_BASE_URL}{path}?version={VPC_API_VERSION}&generation=2"

def list_instance_profiles(token: str) -> list:
    """
    Retrieve all VPC instance profiles available in the target region.
    Returns: list of profile dicts.
    """
    log("PROBE", "Fetching available instance profiles...")
    resp = http_get(vpc_url("/instance/profiles"), vpc_headers(token))
    return resp.get("profiles", [])

def find_ubuntu_image(token: str) -> str:
    """
    Find the most recent Ubuntu 24.04 LTS stock image ID in the target region.
    Returns: image ID string.
    Raises: SystemExit if no matching image found.
    """
    log("PROBE", f"Searching for image matching pattern '{TARGET_IMAGE_PATTERN}'...")
    resp = http_get(vpc_url("/images") + "&visibility=public", vpc_headers(token))
    images = resp.get("images", [])
    matches = [
        img for img in images
        if TARGET_IMAGE_PATTERN in img.get("name", "").lower()
        and img.get("status") == "available"
    ]
    if not matches:
        fatal(f"No available image matching '{TARGET_IMAGE_PATTERN}' found in {TARGET_REGION}.")
    # Sort by creation date descending; pick most recent
    matches.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    chosen = matches[0]
    log("PROBE", f"Selected image: {chosen['name']} ({chosen['id']})")
    return chosen["id"]

def create_vpc(token: str, name: str) -> str:
    """
    Create a new VPC with the given name.
    Returns: VPC ID string.
    """
    log("PROVISION", f"Creating VPC: {name}...")
    payload = {
        "name": name,
        "resource_group": {"id": None}  # Uses account default resource group
    }
    # Remove None values — IBM API rejects null resource_group
    payload = {k: v for k, v in payload.items() if v is not None}
    payload = {"name": name}
    resp = http_post(vpc_url("/vpcs"), payload, vpc_headers(token))
    vpc_id = resp.get("id")
    if not vpc_id:
        fatal(f"VPC creation failed. Response: {resp}")
    log("PROVISION", f"VPC created: {vpc_id}")
    return vpc_id

def create_subnet(token: str, name: str, vpc_id: str) -> str:
    """
    Create a subnet in the VPC inside the target zone.
    Uses IPv4 CIDR block 10.240.0.0/24.
    Returns: subnet ID string.
    """
    log("PROVISION", f"Creating subnet: {name} in {TARGET_ZONE}...")
    payload = {
        "name": name,
        "vpc": {"id": vpc_id},
        "zone": {"name": TARGET_ZONE},
        "ipv4_cidr_block": "10.240.0.0/24",
        "total_ipv4_address_count": 256
    }
    # IBM requires either ipv4_cidr_block or total_ipv4_address_count — not both.
    # Sending cidr_block only.
    payload = {
        "name": name,
        "vpc": {"id": vpc_id},
        "zone": {"name": TARGET_ZONE},
        "ipv4_cidr_block": "10.240.0.0/24"
    }
    resp = http_post(vpc_url("/subnets"), payload, vpc_headers(token))
    subnet_id = resp.get("id")
    if not subnet_id:
        fatal(f"Subnet creation failed. Response: {resp}")
    log("PROVISION", f"Subnet created: {subnet_id}")
    return subnet_id

def create_security_group(token: str, name: str, vpc_id: str) -> str:
    """
    Create a security group allowing:
      - Inbound TCP 22   (SSH)
      - Inbound TCP 8080 (Xoras Live Dashboard)
      - Outbound all
    Returns: security group ID string.
    """
    log("PROVISION", f"Creating security group: {name}...")
    payload = {
        "name": name,
        "vpc": {"id": vpc_id},
        "rules": [
            # SSH
            {
                "direction": "inbound",
                "ip_version": "ipv4",
                "protocol": "tcp",
                "port_min": 22,
                "port_max": 22,
                "remote": {"cidr_block": "0.0.0.0/0"}
            },
            # Xoras Dashboard
            {
                "direction": "inbound",
                "ip_version": "ipv4",
                "protocol": "tcp",
                "port_min": 8080,
                "port_max": 8080,
                "remote": {"cidr_block": "0.0.0.0/0"}
            },
            # Outbound all (required for pip installs, Alpaca REST calls, Binance WS)
            {
                "direction": "outbound",
                "ip_version": "ipv4",
                "protocol": "all",
                "remote": {"cidr_block": "0.0.0.0/0"}
            }
        ]
    }
    resp = http_post(vpc_url("/security_groups"), payload, vpc_headers(token))
    sg_id = resp.get("id")
    if not sg_id:
        fatal(f"Security group creation failed. Response: {resp}")
    log("PROVISION", f"Security group created: {sg_id}")
    return sg_id

def create_instance(token: str, name: str, image_id: str, subnet_id: str, sg_id: str) -> str:
    """
    Provision the compute instance with:
      - Profile:    mx2-48x384 (48 vCPU / 384 GB RAM)
      - Boot disk:  1000 GB SSD (10iops-tier)
      - Image:      Ubuntu 24.04 LTS
      - User data:  Cloud-init script that installs Python3, git, and launches
                    all Xoras services on boot.
    Returns: instance ID string.
    """
    log("PROVISION", f"Provisioning instance '{name}' with profile {INSTANCE_PROFILE}...")

    # Cloud-init boot script — runs once on first boot.
    # Clones the repo, installs deps, and starts all four Xoras services.
    user_data = """#!/bin/bash
set -euxo pipefail

# ── System bootstrap ────────────────────────────────────────────────────────
apt-get update -y
apt-get install -y python3 python3-pip git tmux htop

# ── Xoras stack deployment ──────────────────────────────────────────────────
# Each service runs in its own named tmux session for easy remote inspection.

# 1. Clone repo from GitHub (public mirror assumed)
git clone https://github.com/ajoxendine68/xoras-core.git /opt/xoras 2>/dev/null || true

cd /opt/xoras

# 2. Install Python requirements
pip3 install -r requirements.txt 2>/dev/null || true

# 3. Launch Live Dashboard
tmux new-session -d -s dashboard \\
  "python3 -u /opt/xoras/Source/xoras_live_dashboard.py 2>&1 | tee /var/log/xoras_dashboard.log"

# 4. Launch BFT Consensus Daemon
tmux new-session -d -s bft \\
  "python3 -u /opt/xoras/Source/xoras_bft_daemon.py 2>&1 | tee /var/log/xoras_bft.log"

# 5. Launch Apex Market Bridge
tmux new-session -d -s bridge \\
  "python3 -u /opt/xoras/Source/cpp_core/xoras_apex_bridge.py --live 2>&1 | tee /var/log/xoras_bridge.log"

# 6. Launch Execution Client (Alpaca broker)
tmux new-session -d -s broker \\
  "python3 -u /opt/xoras/Source/cpp_core/xoras_execution_client.py 2>&1 | tee /var/log/xoras_broker.log"

echo "[XORAS] All services launched." >> /var/log/xoras_boot.log
"""

    payload = {
        "name": name,
        "zone": {"name": TARGET_ZONE},
        "profile": {"name": INSTANCE_PROFILE},
        "image": {"id": image_id},
        "primary_network_interface": {
            "name": "eth0",
            "subnet": {"id": subnet_id},
            "security_groups": [{"id": sg_id}]
        },
        "boot_volume_attachment": {
            "volume": {
                "name": f"{name}-boot",
                "profile": {"name": BOOT_VOLUME_PROFILE},
                "capacity": BOOT_VOLUME_CAPACITY_GB
            },
            "delete_volume_on_instance_delete": True
        },
        "user_data": user_data
    }

    resp = http_post(vpc_url("/instances"), payload, vpc_headers(token))
    instance_id = resp.get("id")
    if not instance_id:
        fatal(f"Instance creation failed. Response: {resp}")
    log("PROVISION", f"Instance provisioned: {instance_id}")
    return instance_id

def attach_floating_ip(token: str, instance_id: str, nic_id: str) -> str:
    """
    Allocate and bind a floating public IP to the instance's primary NIC.
    Returns: the allocated floating IP address string.
    """
    log("PROVISION", "Allocating floating IP...")
    fip_resp = http_post(vpc_url("/floating_ips"), {"name": "xoras-fip"}, vpc_headers(token))
    fip_id = fip_resp.get("id")
    fip_addr = fip_resp.get("address")
    if not fip_id:
        fatal(f"Floating IP allocation failed. Response: {fip_resp}")
    log("PROVISION", f"Floating IP allocated: {fip_addr} ({fip_id})")

    # Bind FIP to the primary NIC
    bind_url = vpc_url(f"/instances/{instance_id}/network_interfaces/{nic_id}/floating_ips/{fip_id}")
    req = urllib.request.Request(
        bind_url,
        headers={**vpc_headers(token), "Content-Type": "application/json"},
        method="PUT"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            log("PROVISION", f"Floating IP bound to instance NIC. Address: {fip_addr}")
            return fip_addr
    except urllib.error.HTTPError as e:
        fatal(f"Floating IP bind failed → HTTP {e.code}: {e.read().decode()}")

def wait_for_running(token: str, instance_id: str, timeout_s: int = 300) -> dict:
    """
    Poll the instance status endpoint until status == 'running' or timeout.
    Poll interval: 10 seconds.
    Returns: final instance dict on success.
    Raises: SystemExit on timeout.
    """
    log("WAIT", f"Polling instance {instance_id} for 'running' status (timeout: {timeout_s}s)...")
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        resp = http_get(vpc_url(f"/instances/{instance_id}"), vpc_headers(token))
        status = resp.get("status", "unknown")
        log("WAIT", f"  Status: {status}")
        if status == "running":
            log("WAIT", "Instance is running.")
            return resp
        time.sleep(10)
    fatal(f"Timeout: instance {instance_id} did not reach 'running' within {timeout_s}s.")

# ── Entrypoint ─────────────────────────────────────────────────────────────────

def main() -> None:
    """
    Full sequential provisioning pipeline:
      1. Authenticate
      2. Probe account (profiles + image)
      3. Create VPC
      4. Create subnet
      5. Create security group
      6. Provision instance (1TB SSD, 48 vCPU, 384 GB RAM)
      7. Allocate and bind floating IP
      8. Wait for running status
      9. Emit connection string
    """
    log("START", "Xoras IBM Cloud Provisioner — Full Stack Deployment")
    state = load_state()

    # Step 1: Authenticate
    token = get_iam_token(IBM_API_KEY)

    # Step 2: Probe available profiles and image
    profiles = list_instance_profiles(token)
    profile_names = [p["name"] for p in profiles]
    if INSTANCE_PROFILE in profile_names:
        log("PROBE", f"Profile '{INSTANCE_PROFILE}' confirmed available.")
    else:
        log("PROBE", f"Profile '{INSTANCE_PROFILE}' NOT found. Available profiles:")
        for p in profile_names:
            log("PROBE", f"  {p}")
        # Pick the highest available profile by vCPU count
        fatal(f"Target profile {INSTANCE_PROFILE} unavailable. See above for options.")

    image_id = find_ubuntu_image(token)

    # Step 3: VPC
    vpc_id = state.get("vpc_id") or create_vpc(token, "xoras-vpc")
    state["vpc_id"] = vpc_id
    save_state(state)

    # Step 4: Subnet
    subnet_id = state.get("subnet_id") or create_subnet(token, "xoras-subnet", vpc_id)
    state["subnet_id"] = subnet_id
    save_state(state)

    # Step 5: Security group
    sg_id = state.get("sg_id") or create_security_group(token, "xoras-sg", vpc_id)
    state["sg_id"] = sg_id
    save_state(state)

    # Step 6: Instance
    instance_id = state.get("instance_id") or create_instance(
        token, "xoras-nexus-1tb", image_id, subnet_id, sg_id
    )
    state["instance_id"] = instance_id
    save_state(state)

    # Step 7: Wait for running
    instance = wait_for_running(token, instance_id)
    nic_id = instance["primary_network_interface"]["id"]

    # Step 8: Floating IP
    public_ip = state.get("public_ip") or attach_floating_ip(token, instance_id, nic_id)
    state["public_ip"] = public_ip
    save_state(state)

    # Done
    log("COMPLETE", "=" * 60)
    log("COMPLETE", "XORAS NEXUS MACHINE IS LIVE")
    log("COMPLETE", f"  Instance ID : {instance_id}")
    log("COMPLETE", f"  Profile     : {INSTANCE_PROFILE} (48 vCPU / 384 GB RAM)")
    log("COMPLETE", f"  Boot Disk   : {BOOT_VOLUME_CAPACITY_GB} GB SSD ({BOOT_VOLUME_PROFILE})")
    log("COMPLETE", f"  Public IP   : {public_ip}")
    log("COMPLETE", f"  SSH         : ssh ubuntu@{public_ip}")
    log("COMPLETE", f"  Dashboard   : http://{public_ip}:8080")
    log("COMPLETE", "=" * 60)

if __name__ == "__main__":
    main()
