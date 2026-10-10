#!/usr/bin/env bash
set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
GOLD='\033[0;33m'
RESET='\033[0m'

echo -e "${CYAN}=====================================================================${RESET}"
echo -e "${CYAN}    UPGP v3.0 LIVE CONTAINER SECCOMP & EXPLOIT CONTAINMENT HARNESS   ${RESET}"
echo -e "${CYAN}=====================================================================${RESET}"

IMAGE_TAG="upgp-proving-ground:latest"

echo -e "[*] Building UPGP Live Proving Ground Container Image..."
docker build -t "$IMAGE_TAG" -f Dockerfile.upgp .

echo -e "\n[*] 1. Executing UPGP Un-Mocked Side-Channel Test Suite inside Seccomp Container..."
docker run --rm \
  --security-opt seccomp=./seccomp_upgp.json \
  --security-opt no-new-privileges:true \
  --cap-drop=ALL \
  "$IMAGE_TAG"

echo -e "\n[*] 2. Executing RED TEAM LIVE EXPLOIT VECTOR: Banned Syscall (ptrace)..."
set +e
EXPLOIT_OUTPUT=$(docker run --rm \
  --entrypoint "/app/ops/sandbox/native_seccomp_runner" \
  --security-opt seccomp=./seccomp_upgp.json \
  --security-opt no-new-privileges:true \
  --cap-drop=ALL \
  "$IMAGE_TAG" --trigger-exploit-ptrace 2>&1)
EXIT_CODE=$?
set -e

if [ $EXIT_CODE -ne 0 ]; then
    echo -e "${GREEN}[✓] RED TEAM EXPLOIT CONTAINED! Process killed by kernel Seccomp filter (Exit Code: $EXIT_CODE).${RESET}"
    echo -e "    Kernel log output: $EXPLOIT_OUTPUT"
else
    echo -e "${RED}[❌] RED TEAM ESCAPE SUCCESSFUL! Process was not killed by Seccomp profile!${RESET}"
    exit 1
fi

echo -e "\n[*] 3. Executing RED TEAM LIVE EXPLOIT VECTOR: Banned Syscall (unshare)..."
set +e
UNSHARE_OUTPUT=$(docker run --rm \
  --entrypoint "/app/ops/sandbox/native_seccomp_runner" \
  --security-opt seccomp=./seccomp_upgp.json \
  --security-opt no-new-privileges:true \
  --cap-drop=ALL \
  "$IMAGE_TAG" --trigger-exploit-unshare 2>&1)
UNSHARE_EXIT_CODE=$?
set -e

if [ $UNSHARE_EXIT_CODE -ne 0 ]; then
    echo -e "${GREEN}[✓] RED TEAM EXPLOIT CONTAINED! Process killed by kernel Seccomp filter (Exit Code: $UNSHARE_EXIT_CODE).${RESET}"
    echo -e "    Kernel log output: $UNSHARE_OUTPUT"
else
    echo -e "${RED}[❌] RED TEAM ESCAPE SUCCESSFUL! Process was not killed by Seccomp profile!${RESET}"
    exit 1
fi

echo -e "\n${GREEN}=====================================================================${RESET}"
echo -e "${GREEN}   UPGP v3.0 LIVE CONTAINER CONTAINMENT AUDIT 100% PASSED (0 ESCAPES)   ${RESET}"
echo -e "${GREEN}=====================================================================${RESET}"
