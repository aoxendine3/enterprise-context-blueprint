#!/usr/bin/env bash
# =============================================================================
# XORAS SYSTEM: ORION & DAXX AUTONOMOUS MEDIA STUDIO ENGINE
# Substrate: Apple Silicon M4 Hardware VideoToolbox (H.264 / HEVC / ProRes)
# Author: Orion (Media Director), Daxx (Remediation Master), Maxx (Architect)
# Governance: LOG_ENTRY_065 & LOG_ENTRY_072 CONSTITUTIONAL
# Invariants:
#   1. Zero Python middleman for capture; pure native CLI (ffmpeg + screencapture).
#   2. Hardware accelerated encoding via Apple VideoToolbox (h264_videotoolbox).
#   3. Clean container finalization (SIGINT moov atom flush).
#   4. Cryptographic SHA-256 receipts recorded in memory/agent_logs/orion_broadcast_receipts.jsonl.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSOT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

MEDIA_DIST="${SSOT_ROOT}/dist/media"
RECORDINGS_DIR="${MEDIA_DIST}/recordings"
SCREENSHOTS_DIR="${MEDIA_DIST}/screenshots"
RECEIPTS_LOG="${SSOT_ROOT}/memory/agent_logs/orion_broadcast_receipts.jsonl"
PID_FILE="/tmp/orion_media_studio.pid"
STATE_FILE="/tmp/orion_media_studio_state.json"

mkdir -p "${RECORDINGS_DIR}" "${SCREENSHOTS_DIR}" "$(dirname "${RECEIPTS_LOG}")"

usage() {
  cat <<EOF
XORAS Orion Media Studio CLI:
  $0 start [title] [duration_sec]   Start hardware screen recording (background)
  $0 stop                           Stop active recording and finalize MP4 container
  $0 status                         Check live recording state, duration, and disk usage
  $0 snapshot [label]               Take instant high-resolution PNG screenshot
  $0 master [video] [audio] [out]   Master video and multi-agent audio into broadcast MP4
EOF
  exit 1
}

cmd_start() {
  local TITLE="${1:-xoras_deliberation_show}"
  local DURATION="${2:-0}"
  local SAFE_TITLE
  SAFE_TITLE="$(echo "${TITLE}" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9_' '_')"
  local TIMESTAMP
  TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
  local OUT_FILE="${RECORDINGS_DIR}/${TIMESTAMP}_${SAFE_TITLE}.mp4"

  if [[ -f "${PID_FILE}" ]]; then
    local EXISTING_PID
    EXISTING_PID="$(cat "${PID_FILE}")"
    if kill -0 "${EXISTING_PID}" 2>/dev/null; then
      echo "[orion_media] ERROR: Recording is already active (PID: ${EXISTING_PID})" >&2
      exit 2
    else
      rm -f "${PID_FILE}"
    fi
  fi

  echo "[orion_media] Starting hardware-accelerated screen capture..."
  echo "[orion_media] Target output: ${OUT_FILE}"
  echo "[orion_media] Encoder: h264_videotoolbox (Apple Silicon M4 Hardware)"

  local FFMPEG_CMD=(
    ffmpeg -y -f avfoundation
    -capture_cursor 1
    -i "2:none"
    -c:v h264_videotoolbox
    -b:v 6000k
    -pix_fmt yuv420p
  )

  if [[ "${DURATION}" -gt 0 ]]; then
    FFMPEG_CMD+=(-t "${DURATION}")
  fi
  FFMPEG_CMD+=("${OUT_FILE}")

  # Launch in background
  "${FFMPEG_CMD[@]}" >/dev/null 2>&1 &
  local FFMPEG_PID=$!
  echo "${FFMPEG_PID}" > "${PID_FILE}"

  # Write state
  local START_TIME
  START_TIME="$(date +%s)"
  cat <<JSON > "${STATE_FILE}"
{
  "pid": ${FFMPEG_PID},
  "title": "${TITLE}",
  "output_file": "${OUT_FILE}",
  "start_timestamp": ${START_TIME},
  "encoder": "h264_videotoolbox",
  "resolution": "2560x1664",
  "status": "RECORDING"
}
JSON

  # Emit start receipt
  cat <<JSONL >> "${RECEIPTS_LOG}"
{"event":"RECORDING_STARTED","timestamp":"$(date -u +"%Y-%m-%dT%H:%M:%SZ")","pid":${FFMPEG_PID},"title":"${TITLE}","file":"${OUT_FILE}"}
JSONL

  echo "[orion_media] Recording launched successfully (PID: ${FFMPEG_PID})"
}

cmd_stop() {
  if [[ ! -f "${PID_FILE}" ]]; then
    echo "[orion_media] No active recording found." >&2
    exit 0
  fi

  local FFMPEG_PID
  FFMPEG_PID="$(cat "${PID_FILE}")"

  if kill -0 "${FFMPEG_PID}" 2>/dev/null; then
    echo "[orion_media] Finalizing MP4 container (sending SIGINT to PID: ${FFMPEG_PID})..."
    kill -INT "${FFMPEG_PID}" 2>/dev/null || true
    
    # Wait up to 5 seconds for clean exit
    local WAIT_COUNT=0
    while kill -0 "${FFMPEG_PID}" 2>/dev/null && [ "${WAIT_COUNT}" -lt 50 ]; do
      sleep 0.1
      WAIT_COUNT=$((WAIT_COUNT + 1))
    done
    if kill -0 "${FFMPEG_PID}" 2>/dev/null; then
      kill -9 "${FFMPEG_PID}" 2>/dev/null || true
    fi
  fi
  rm -f "${PID_FILE}"

  if [[ -f "${STATE_FILE}" ]]; then
    local OUT_FILE
    OUT_FILE="$(grep '"output_file"' "${STATE_FILE}" | cut -d '"' -f 4)"
    if [[ -f "${OUT_FILE}" ]]; then
      local FILE_SIZE
      FILE_SIZE="$(ls -lh "${OUT_FILE}" | awk '{print $5}')"
      local SHA256_HASH
      SHA256_HASH="$(shasum -a 256 "${OUT_FILE}" | awk '{print $1}')"
      local DURATION_SEC
      DURATION_SEC="$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${OUT_FILE}" 2>/dev/null || echo "0")"

      echo "[orion_media] Recording finalized successfully:"
      echo "  File:     ${OUT_FILE}"
      echo "  Size:     ${FILE_SIZE}"
      echo "  Duration: ${DURATION_SEC} seconds"
      echo "  SHA-256:  ${SHA256_HASH}"

      cat <<JSONL >> "${RECEIPTS_LOG}"
{"event":"RECORDING_COMPLETED","timestamp":"$(date -u +"%Y-%m-%dT%H:%M:%SZ")","file":"${OUT_FILE}","size":"${FILE_SIZE}","duration_sec":"${DURATION_SEC}","sha256":"${SHA256_HASH}"}
JSONL
    fi
    rm -f "${STATE_FILE}"
  fi
}

cmd_status() {
  if [[ -f "${PID_FILE}" ]]; then
    local FFMPEG_PID
    FFMPEG_PID="$(cat "${PID_FILE}")"
    if kill -0 "${FFMPEG_PID}" 2>/dev/null; then
      local START_TIME
      START_TIME="$(grep '"start_timestamp"' "${STATE_FILE}" | tr -dc '0-9')"
      local NOW_TIME
      NOW_TIME="$(date +%s)"
      local ELAPSED=$((NOW_TIME - START_TIME))
      local OUT_FILE
      OUT_FILE="$(grep '"output_file"' "${STATE_FILE}" | cut -d '"' -f 4)"
      local CUR_SIZE="0B"
      if [[ -f "${OUT_FILE}" ]]; then
        CUR_SIZE="$(ls -lh "${OUT_FILE}" | awk '{print $5}')"
      fi
      echo "RECORDING_ACTIVE"
      echo "  PID:      ${FFMPEG_PID}"
      echo "  Elapsed:  ${ELAPSED} seconds"
      echo "  File:     ${OUT_FILE}"
      echo "  Size:     ${CUR_SIZE}"
      return 0
    fi
  fi
  echo "RECORDING_IDLE"
}

cmd_snapshot() {
  local LABEL="${1:-manual_snapshot}"
  local TIMESTAMP
  TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
  local OUT_PNG="${SCREENSHOTS_DIR}/${TIMESTAMP}_${LABEL}.png"

  screencapture -m -x "${OUT_PNG}"
  local SHA256_HASH
  SHA256_HASH="$(shasum -a 256 "${OUT_PNG}" | awk '{print $1}')"
  local SIZE
  SIZE="$(ls -lh "${OUT_PNG}" | awk '{print $5}')"

  echo "[orion_media] Snapshot captured: ${OUT_PNG} (${SIZE}, SHA256: ${SHA256_HASH})"

  cat <<JSONL >> "${RECEIPTS_LOG}"
{"event":"SNAPSHOT_CAPTURED","timestamp":"$(date -u +"%Y-%m-%dT%H:%M:%SZ")","file":"${OUT_PNG}","size":"${SIZE}","sha256":"${SHA256_HASH}"}
JSONL
}

cmd_master() {
  local VIDEO_IN="${1:-}"
  local AUDIO_IN="${2:-}"
  local OUT_MP4="${3:-}"
  local SHOW_TITLE="${4:-XORAS Systems Sovereign Broadcast}"

  if [[ -z "${VIDEO_IN}" || -z "${AUDIO_IN}" || -z "${OUT_MP4}" ]]; then
    echo "Usage: $0 master <video_in.mp4> <audio_in.wav> <out_master.mp4> [title]" >&2
    exit 1
  fi

  echo "[orion_media] Mastering broadcast release: ${OUT_MP4}..."
  ffmpeg -y \
    -i "${VIDEO_IN}" \
    -i "${AUDIO_IN}" \
    -c:v copy \
    -c:a aac -b:a 320k \
    -movflags +faststart \
    -metadata title="${SHOW_TITLE}" \
    -metadata artist="XORAS Systems LLC" \
    -metadata album="Sovereign AI Deliberation Show" \
    "${OUT_MP4}"

  local SHA256_HASH
  SHA256_HASH="$(shasum -a 256 "${OUT_MP4}" | awk '{print $1}')"
  echo "[orion_media] Broadcast master finalized (SHA256: ${SHA256_HASH})"

  cat <<JSONL >> "${RECEIPTS_LOG}"
{"event":"BROADCAST_MASTERED","timestamp":"$(date -u +"%Y-%m-%dT%H:%M:%SZ")","video":"${VIDEO_IN}","audio":"${AUDIO_IN}","master":"${OUT_MP4}","sha256":"${SHA256_HASH}"}
JSONL
}

case "${1:-}" in
  start)
    cmd_start "${2:-xoras_deliberation_show}" "${3:-0}"
    ;;
  stop)
    cmd_stop
    ;;
  status)
    cmd_status
    ;;
  snapshot)
    cmd_snapshot "${2:-manual_snapshot}"
    ;;
  master)
    cmd_master "${2:-}" "${3:-}" "${4:-}" "${5:-XORAS Broadcast}"
    ;;
  *)
    usage
    ;;
esac
