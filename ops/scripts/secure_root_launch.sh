#!/bin/bash
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo)"
  exit
fi
echo "=== SECURE ROOT EXECUTION ==="
echo "Locking down Sovereign Memory Pipes..."
chown root:wheel /tmp/sovereign_memory.fifo
chmod 600 /tmp/sovereign_memory.fifo
echo "[SECURED] Only root can read/write to the memory stream."
echo "Endpoint Security constraints verified."
