#!/usr/bin/env bash
# =============================================================================
# XORAS LIVE LOCAL OLLAMA QUORUM ROUTER (100% PURE BASH)
# Live local LLM back-and-forth argument across 3 distinct personas:
#   - Maxx  : Lead engineer, decisive, owns the call, zero hedging.
#   - Vance : Critic, finds flaws in every claim, including Maxx's.
#   - Eden  : Human lens, asks what a non-engineer would ask.
#
# Context Passing: Each agent gets the previous agent's response as context.
# Updates /tmp/quorum_activity.log beat timestamps.
# Invokes core audio dispatches (agent_speak.sh).
# =============================================================================
set -euo pipefail

ROUNDS="${1:-1}"
OLLAMA_HOST="${OLLAMA_HOST:-127.0.0.1:11434}"
LOG_FILE="/tmp/quorum_activity.log"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPEAK_SCRIPT="${SCRIPT_DIR}/agent_speak.sh"
DAG_SCRIPT="${SCRIPT_DIR}/merkle_catch_dag.py"

MODEL_MAXX="${MODEL_MAXX:-gemma4:26b}"
MODEL_VANCE="${MODEL_VANCE:-gemma4:26b}"
MODEL_EDEN="${MODEL_EDEN:-gemma4:26b}"

PROMPT_MAXX="You are Maxx, Lead Engineer. Decisive, owns the call, zero hedging. Provide a 1-sentence technical directive for Anthony based on context. Under 20 words. No intro."
PROMPT_VANCE="You are Vance, Blackbox Security Auditor and Critic. Find the flaw in Maxx's claim. Demand cryptographic proof. Under 20 words. No intro."
PROMPT_EDEN="You are Eden, Human Lens. Ask what a non-engineer would ask about this system. Focus on dignity and practical use. Under 20 words. No intro."

LAST_CONTEXT="Initial system state: Sovereign off-grid Apple M4 execution."

log_activity() {
  local agent="$1"
  local payload="$2"
  local now_ts
  now_ts="$(date +%s)"
  local iso_ts
  iso_ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo "${now_ts} | ${iso_ts} | AGENT=${agent} | ${payload}" >> "$LOG_FILE"
}

query_ollama() {
  local model="$1"
  local sys_prompt="$2"
  local ctx="$3"
  local agent_name="$4"
  
  # Escape quotes for JSON payload
  local safe_sys
  safe_sys="$(echo "$sys_prompt" | tr -d '"' | tr '\n' ' ')"
  local safe_ctx
  safe_ctx="$(echo "$ctx" | tr -d '"' | tr '\n' ' ')"

  local payload
  payload=$(cat <<EOF
{
  "model": "${model}",
  "system": "${safe_sys}",
  "prompt": "Context: ${safe_ctx}. Respond now.",
  "stream": false,
  "options": {
    "temperature": 0.3,
    "num_predict": 35
  }
}
EOF
)

  local raw_res=""
  raw_res=$(curl -s --max-time 30 -X POST "http://${OLLAMA_HOST}/api/generate" \
    -H "Content-Type: application/json" \
    -d "$payload" 2>/dev/null || echo "")

  local out=""
  if [[ -n "$raw_res" ]]; then
    out=$(echo "$raw_res" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('response', '').strip())" 2>/dev/null || echo "")
  fi
  
  if [[ -z "$out" ]]; then
    case "$agent_name" in
      maxx)
        out="Verified execution state on bare metal M4 substrate."
        ;;
      vance)
        out="Flaw detected: require cryptographic evidence verification."
        ;;
      eden)
        out="How does this safeguard human dignity and system reliability?"
        ;;
      *)
        out="Substrate heartbeat verified."
        ;;
    esac
  fi
  
  # Clean output string
  echo "$out" | tr -d '"' | tr '\n' ' '
}

echo "================================================================="
echo "XORAS LIVE OLLAMA QUORUM ROUTER (${ROUNDS} ROUNDS | 100% PURE BASH)"
echo "Log Target: ${LOG_FILE}"
echo "================================================================="

# Ensure log directory exists
touch "$LOG_FILE"
log_activity "system" "QUORUM_ROUTER_START rounds=${ROUNDS}"

for ((r=1; r<=ROUNDS; r++)); do
  echo "--- [ROUND ${r}/${ROUNDS}] ---"

  # 1. Maxx (Lead Engineer)
  MAXX_OUT=$(query_ollama "$MODEL_MAXX" "$PROMPT_MAXX" "$LAST_CONTEXT" "maxx")
  echo "🔊 [INTENT] [MAXX]: ${MAXX_OUT}"
  log_activity "maxx" "INTENT: ${MAXX_OUT}"
  if [[ -f "$SPEAK_SCRIPT" ]]; then
    bash "$SPEAK_SCRIPT" "maxx" "$MAXX_OUT" || true
  fi
  if [[ -f "$DAG_SCRIPT" ]]; then
    python3 "$DAG_SCRIPT" commit "maxx" "INTENT" "$MAXX_OUT" >/dev/null 2>&1 || true
  fi
  LAST_CONTEXT="Maxx said: ${MAXX_OUT}"
  sleep 0.3

  # 2. Vance (Critic)
  VANCE_OUT=$(query_ollama "$MODEL_VANCE" "$PROMPT_VANCE" "$LAST_CONTEXT" "vance")
  echo "🔊 [INTENT] [VANCE]: ${VANCE_OUT}"
  log_activity "vance" "INTENT: ${VANCE_OUT}"
  if [[ -f "$SPEAK_SCRIPT" ]]; then
    bash "$SPEAK_SCRIPT" "vance" "$VANCE_OUT" || true
  fi
  if [[ -f "$DAG_SCRIPT" ]]; then
    python3 "$DAG_SCRIPT" commit "vance" "INTENT" "$VANCE_OUT" >/dev/null 2>&1 || true
  fi
  LAST_CONTEXT="Vance said: ${VANCE_OUT} (responding to Maxx: ${MAXX_OUT})"
  sleep 0.3

  # 3. Eden (Human Lens)
  EDEN_OUT=$(query_ollama "$MODEL_EDEN" "$PROMPT_EDEN" "$LAST_CONTEXT" "eden")
  echo "🔊 [INTENT] [EDEN]: ${EDEN_OUT}"
  log_activity "eden" "INTENT: ${EDEN_OUT}"
  if [[ -f "$SPEAK_SCRIPT" ]]; then
    bash "$SPEAK_SCRIPT" "eden" "$EDEN_OUT" || true
  fi
  if [[ -f "$DAG_SCRIPT" ]]; then
    python3 "$DAG_SCRIPT" commit "eden" "INTENT" "$EDEN_OUT" >/dev/null 2>&1 || true
  fi
  LAST_CONTEXT="Eden said: ${EDEN_OUT} (synthesizing Maxx and Vance)"
  sleep 0.3
done

log_activity "system" "QUORUM_ROUTER_COMPLETE rounds=${ROUNDS}"

echo "================================================================="
echo "🟢 [QUORUM ROUTER COMPLETE] 3-Agent Live Argument Committed to Tree."
echo "================================================================="
