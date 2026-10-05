#!/usr/bin/env bash
# =============================================================================
# XORAS_OS: RING 1 EPHEMERAL RAM COMPILATION SANDBOX (METAL OPTIMIZED)
# Target: Apple Silicon M4 Unified Memory Architecture (16GB UMA)
# Purpose: Zero-disk I/O buffer for Cargo, npm, and build artifacts.
# Security: Hardened per qwen2.5-coder:7b & Vance Discernment Gauntlet.
# Audit Trail: ops/sandbox/ram_sandbox_audit.jsonl
# =============================================================================
set -euo pipefail

VOLUME_NAME="XORAS_RAM_SANDBOX"
MOUNT_POINT="/Volumes/${VOLUME_NAME}"
RAM_SIZE_MB=2048
SECTORS=$(( RAM_SIZE_MB * 2048 )) # 4,194,304 sectors = 2048MB
STATE_DIR="/tmp/xoras_sandbox_state"
DEVICE_FILE="${STATE_DIR}/device_id"
AUDIT_LOG="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/sandbox/ram_sandbox_audit.jsonl"

log_event() {
    local action="$1"
    local status="$2"
    local details="$3"
    local ts
    ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    printf '{"timestamp":"%s","action":"%s","status":"%s","details":"%s"}\n' \
        "$ts" "$action" "$status" "$details" >> "$AUDIT_LOG"
}

cmd="${1:-status}"

case "$cmd" in
    create)
        if [ -d "$MOUNT_POINT" ] && mount | grep -q "$MOUNT_POINT"; then
            echo "[XORAS_OS] RAM Sandbox already mounted at $MOUNT_POINT"
            log_event "create" "NOOP" "Already mounted"
            exit 0
        fi
        
        mkdir -p -m 700 "$STATE_DIR"
        echo "[XORAS_OS] Allocating ${RAM_SIZE_MB}MB APFS RAM disk on Apple Silicon UMA..."
        RAW_DEV=$(hdiutil attach -nomount "ram://$SECTORS" | tr -d "[:space:]")
        diskutil erasevolume APFS "$VOLUME_NAME" "$RAW_DEV" >/dev/null
        echo "$RAW_DEV" > "$DEVICE_FILE"
        chmod 600 "$DEVICE_FILE"
        
        log_event "create" "SUCCESS" "Mounted on $RAW_DEV ($RAM_SIZE_MB MB APFS)"
        echo "[✓] Ring 1 RAM Sandbox active at $MOUNT_POINT ($RAW_DEV)"
        ;;
        
    destroy)
        if [ -f "$DEVICE_FILE" ]; then
            DEV_NAME=$(cat "$DEVICE_FILE")
            echo "[XORAS_OS] Detaching RAM disk $DEV_NAME..."
            diskutil unmount force "$MOUNT_POINT" >/dev/null 2>&1 || true
            hdiutil detach "$DEV_NAME" >/dev/null 2>&1 || true
            rm -rf "$STATE_DIR"
            log_event "destroy" "SUCCESS" "Detached $DEV_NAME and reclaimed memory"
            echo "[✓] Ring 1 RAM Sandbox destroyed. Memory reclaimed."
        else
            # Attempt unmount by volume name if device file is missing
            diskutil unmount force "$MOUNT_POINT" >/dev/null 2>&1 || true
            echo "[XORAS_OS] No active device file. Unmounted volume if present."
            log_event "destroy" "CLEANUP" "Forced unmount"
        fi
        ;;
        
    status)
        if [ -d "$MOUNT_POINT" ] && mount | grep -q "$MOUNT_POINT"; then
            DEV_NAME=$(cat "$DEVICE_FILE" 2>/dev/null || echo "Active Device")
            echo "[XORAS_OS] Ring 1 RAM Sandbox: MOUNTED on $DEV_NAME ($MOUNT_POINT)"
            df -h "$MOUNT_POINT"
            log_event "status" "MOUNTED" "Active on $DEV_NAME"
        else
            echo "[XORAS_OS] Ring 1 RAM Sandbox: UNMOUNTED"
            log_event "status" "UNMOUNTED" "Idle"
        fi
        ;;
        
    run)
        shift
        if [ $# -eq 0 ]; then
            echo "Error: 'run' requires a command to execute." >&2
            exit 1
        fi
        if [ ! -d "$MOUNT_POINT" ] || ! mount | grep -q "$MOUNT_POINT"; then
            "$0" create
        fi
        echo "[XORAS_OS] Executing in isolated Ring 1 RAM Sandbox: $*"
        log_event "run" "EXECUTE" "$*"
        (cd "$MOUNT_POINT" && "$@")
        ;;
        
    *)
        echo "Usage: $0 {create|destroy|status|run <binary> [args...]}" >&2
        exit 1
        ;;
esac
