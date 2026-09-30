#!/bin/bash
echo "[!] EVE OVERRIDE: INITIATING KILL SWITCH"
pkill -9 -f xmars_harness
pkill -9 -f sovra
echo "[*] Sandbox processes terminated. Memory maps unlinked."
