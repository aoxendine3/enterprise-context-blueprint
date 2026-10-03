#!/usr/bin/env bash
# One door. Hosts are shells. Identity stays frozen.
set -euo pipefail
SSOT="/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain"
cd "$SSOT"

echo "============================================================"
echo "  XORAS SSOT DOOR  —  $(date '+%Y-%m-%d %H:%M')"
echo "  Root: $SSOT"
echo "============================================================"
echo
echo "[FROZEN] identity/  Xoras_agent_cards/  AGENTS.md"
ls identity | sed 's/^/    /'
echo "    cards: $(ls Xoras_agent_cards/*.json 2>/dev/null | wc -l | tr -d ' ') json"
echo
echo "[SPEAK]  bash ops/scripts/agent_speak.sh maxx|clara|jarvis|vance \"text\""
echo "[KOKORO] capabilities/neural_models/kokoro-v1.0.onnx"
echo "[COVENANT] identity/working_covenant.md"
echo
echo "[HOST SHELLS — not SSOT]"
printf "    ~/.gemini     "; du -sh "$HOME/.gemini" 2>/dev/null | awk '{print $1}'
printf "    ~/.sovereign  "; du -sh "$HOME/.sovereign" 2>/dev/null | awk '{print $1}'
printf "    ~/.agents     "; du -sh "$HOME/.agents" 2>/dev/null | awk '{print $1}'
printf "    ~/.ollama     "; du -sh "$HOME/.ollama" 2>/dev/null | awk '{print $1}'
echo "    pointer: $HOME/.sovereign/CANONICAL.txt"
echo
echo "[BARN] archives/the_barn/   [BINS] scratch/hardware_bins/"
echo
echo "[SIZE]"
du -sh "$SSOT" identity Xoras_agent_cards capabilities/neural_models archives scratch memory 2>/dev/null
echo
if [ -L memory/gemini_brain_symlink ]; then
  echo "[FAIL] gemini_brain_symlink is back. Cut it."
  exit 1
else
  echo "[OK] Gemini is not wired into SSOT memory."
fi
echo "============================================================"
