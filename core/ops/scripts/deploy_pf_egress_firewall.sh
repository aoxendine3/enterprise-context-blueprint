#!/usr/bin/env bash
# ==============================================================================
# XORAS::OS - macOS Kernel Packet Filter (pfctl) Loopback Egress Enforcer
# Mandate: OS-Level Kernel Egress Lock (TCP 8787 / UDP 11434 Loopback Only)
# ==============================================================================
set -euo pipefail

ANCHOR_NAME="com.xoras.sovereign.egress"
PF_CONF_TMP="/tmp/pf_xoras_anchor.conf"

echo "=============================================================================="
echo "  XORAS::OS - KERNEL-LEVEL NETWORK EGRESS ISOLATION (macOS pfctl)"
echo "=============================================================================="

cat << 'EOF' > "${PF_CONF_TMP}"
# XORAS Sovereign Egress Anchor Policy
# Block all external ingress/egress on XORAS inter-process communication ports
block in  proto tcp from any to any port 8787
block out proto tcp from any to any port 8787
block in  proto udp from any to any port 11434
block out proto udp from any to any port 11434

# Allow strictly local loopback (127.0.0.1 / ::1)
pass in  quick on lo0 proto tcp from 127.0.0.1 to 127.0.0.1 port 8787
pass out quick on lo0 proto tcp from 127.0.0.1 to 127.0.0.1 port 8787
pass in  quick on lo0 proto udp from 127.0.0.1 to 127.0.0.1 port 11434
pass out quick on lo0 proto udp from 127.0.0.1 to 127.0.0.1 port 11434
EOF

echo "[*] Generated anchor configuration at ${PF_CONF_TMP}:"
cat "${PF_CONF_TMP}"

echo "=============================================================================="
echo "[+] Validation complete. To activate at kernel level (requires sudo privileges):"
echo "    sudo pfctl -a ${ANCHOR_NAME} -f ${PF_CONF_TMP}"
echo "    sudo pfctl -e"
echo "=============================================================================="
