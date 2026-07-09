# --- XORAS SOVEREIGN SWARM CONSENSUS ORCHESTRATOR ---
# File: Source/xoras_swarm_consensus.py
# Classification: [PRODUCTION]

import os
import sys
import time
import asyncio
import subprocess
import argparse
from xoras_shm_bft import XorasShmBft

# ANSI Colors for Elite Terminal Interface
GREEN = "\033[92m"
BLUE = "\033[94m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_banner(mode):
    print(BOLD + CYAN + "==========================================================")
    print(f"         XSNA SOVEREIGN SWARM CONSENSUS ENGINE: {mode.upper()}")
    print("==========================================================" + RESET)

async def run_consensus_loop(bft, proposals):
    print(f"[*] Initializing local BFT validator registry...")
    print(f"[*] SHM name allocated: {BOLD}{bft.shm_name}{RESET} (Size: {bft.shm_size} bytes)")
    
    for i, prop in enumerate(proposals):
        print(f"\n{BOLD}{BLUE}--- CONSENSUS ROUND {i+1} ---{RESET}")
        print(f"{BOLD}Proposed Action:{RESET} {CYAN}{prop['action']}{RESET}")
        print(f"[*] Initial status: {YELLOW}PENDING DEBATE{RESET}")
        
        # Simulating cross-criticism and debate wait
        await asyncio.sleep(1.5)
        
        print(f"[*] Launching consensus vote (Proposal: {prop['value']})...")
        start_time = time.perf_counter()
        
        # Run BFT consensus round
        res = await bft.run_consensus_round(prop['value'])
        
        latency = (time.perf_counter() - start_time) * 1000
        
        # Check if consensus was reached
        if res.get("consensus_reached", False):
            print(f"{GREEN}[✓] CONSENSUS REACHED in {latency:.3f} ms!{RESET}")
            print(f"    - Quorum votes: {res.get('active_nodes', bft.num_nodes)} nodes verified.")
            print(f"    - Signatures validated: {GREEN}SECURE{RESET}")
            print(f"    - Action committed: {BOLD}{GREEN}APPROVED{RESET}")
        else:
            print(f"{RED}[✗] CONSENSUS FAILED / BYZANTINE FAULT DETECTED!{RESET}")
            print(f"    - Action state: {BOLD}{RED}REJECTED{RESET}")

        await asyncio.sleep(1.0)

def main():
    parser = argparse.ArgumentParser(description="Xoras Sovereign Swarm Consensus Manager")
    parser.add_argument("--mode", choices=["host", "client", "standalone"], default="standalone", help="Run mode (host, client, standalone)")
    parser.add_argument("--client-ip", type=str, default="127.0.0.1", help="Client node IP address (required in --mode host)")
    args = parser.parse_args()

    print_banner(args.mode)

    # Initialize BFT engine: 8 nodes, 2 max Byzantine faults to keep local debugging responsive
    bft = XorasShmBft(num_nodes=8, num_byzantine=2, use_processes=True)
    
    # Define our real-world collaborative consensus proposals
    proposals = [
        {"action": "Approve Rita's Pulmonary Expectorant Dosage (Ginger Sipper)", "value": True},
        {"action": "Verify Dr. Jeremy's SpO2 Emergency Threshold (90% SpO2)", "value": True},
        {"action": "Trigger Continuous Sleep Phase Archetype Consolidation", "value": True},
        {"action": "Confirm LAN Cluster Synchronization Integrity", "value": True}
    ]

    relay_process = None

    try:
        if args.mode == "host":
            # Launch the BFT network sync relay in the background pointing to Client Node B
            print(f"[*] Spawning BFT Network Relay to client {args.client_ip}...")
            relay_process = subprocess.Popen([
                sys.executable, "Source/xoras_shm_bft_network.py", "--host", bft.shm_name, args.client_ip
            ])
            
        elif args.mode == "client":
            # Launch client-mode socket listener
            print(f"[*] Spawning BFT Network Relay Listener...")
            relay_process = subprocess.Popen([
                sys.executable, "Source/xoras_shm_bft_network.py", "--client", bft.shm_name
            ])

        # Run the consensus rounds
        asyncio.run(run_consensus_loop(bft, proposals))

    except KeyboardInterrupt:
        print(f"\n[-] Interrupted. Shutting down Swarm processes cleanly...")
    finally:
        # Set stop flag in SHM (Byte 2)
        try:
            bft.shm.buf[2] = 1
            bft.shm.close()
            # Allow time for workers to terminate
            time.sleep(0.5)
            bft.shm.unlink()
            print("[+] SHM segment unlinked successfully.")
        except Exception:
            pass

        if relay_process:
            relay_process.terminate()
            relay_process.wait()
            print("[+] Network Relay process terminated.")

if __name__ == "__main__":
    main()
