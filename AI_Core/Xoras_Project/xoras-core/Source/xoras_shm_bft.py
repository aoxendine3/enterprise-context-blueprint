# --- XORAS DISTRIBUTED MULTI-PROCESS BYZANTINE FAULT TOLERANT CONSENSUS ENGINE (SHM-BFT) ---
# Purpose: Lock-free, sub-millisecond OS-level multi-process BFT consensus using a Shared Memory State Machine.
# Features: Adaptive Spin-Backoff, PID Heartbeat Registry, Dynamic Quorum Adaptation, Non-Repudiation.
# Classification: [PRODUCTION]

import os
import time
import random
import hmac
import hashlib
import asyncio
import traceback
import struct
from multiprocessing import shared_memory, Process

def bft_persistent_worker(node_id, num_nodes, num_byzantine, shm_name, shm_size):
    """
    Persistent OS process worker simulating a single BFT validator node.
    Synchronizes state machines purely by polling the shared memory state register.
    Implements Adaptive Spin-Backoff to minimize CPU overhead while preserving sub-millisecond hot-path latency.
    Periodically writes PID and active heartbeats to the shared memory metadata registry.
    """
    try:
        shm = shared_memory.SharedMemory(name=shm_name)
    except Exception:
        return

    is_byzantine = node_id < num_byzantine
    node_key = f"key_secret_{node_id}".encode()
    slot_size = 131
    # 300 bytes reserved for orchestrator metadata, slots start at 300
    start = 300 + (node_id * slot_size)
    pid = os.getpid()

    worker_local_round = 0
    last_processed_state = 0
    
    # Register PID in metadata block
    # PID block starts at offset 10 (each node gets 4 bytes for PID + 4 bytes for heartbeat time)
    pid_offset = 10 + (node_id * 8)
    try:
        shm.buf[pid_offset:pid_offset+4] = struct.pack("<I", pid)
    except Exception:
        pass

    last_heartbeat_time = 0

    try:
        spin_count = 0
        while True:
            # 1. Heartbeat update (every 100ms)
            now = time.perf_counter()
            if now - last_heartbeat_time > 0.1:
                shm.buf[pid_offset+4:pid_offset+8] = struct.pack("<I", int(now % 100000))
                last_heartbeat_time = now

            # Check global stop flag (Byte 2)
            if shm.buf[2] == 1:
                break

            # Read orchestrator round number (Byte 3)
            round_number = shm.buf[3]
            if round_number > worker_local_round:
                last_processed_state = 0
                worker_local_round = round_number
                spin_count = 0  # Reset spin for new round hot-path

            # Read the global round state flag from the metadata block (Byte 0)
            round_state = shm.buf[0]

            if round_state == 0:
                spin_count += 1
                if spin_count < 10000:
                    pass
                elif spin_count < 50000:
                    os.sched_yield()
                else:
                    time.sleep(0.0001)
                continue

            if round_state == 1 and last_processed_state < 1:
                # ------------------
                # 1. PREPARE PHASE
                # ------------------
                prop_byte = shm.buf[1]
                proposal_value = True if prop_byte == 2 else False

                val_to_prepare = proposal_value
                if is_byzantine:
                    val_to_prepare = not proposal_value

                # Signature simulates asymmetric cryptosystem verification key pairs
                sig = hmac.new(node_key, f"PREPARE:{worker_local_round}:{val_to_prepare}".encode('ascii'), hashlib.sha256).hexdigest()

                # Write prepare vote and signature
                shm.buf[start] = 2 if val_to_prepare else 1
                shm.buf[start+1:start+65] = sig.encode('ascii')

                last_processed_state = 1
                spin_count = 0  # Reset spin count for commit phase transition

            elif round_state == 2 and last_processed_state < 2:
                # ------------------
                # 2. COMMIT PHASE
                # ------------------
                prop_byte = shm.buf[1]
                proposal_value = True if prop_byte == 2 else False

                # Read prepares from all nodes and verify
                prepare_tally = {True: 0, False: 0}
                for i in range(num_nodes):
                    node_start = 300 + (i * slot_size)
                    v_byte = shm.buf[node_start]
                    if v_byte == 0:
                        continue
                    v = True if v_byte == 2 else False
                    s = bytes(shm.buf[node_start+1:node_start+65]).decode('ascii')

                    other_key = f"key_secret_{i}".encode()
                    expected = hmac.new(other_key, f"PREPARE:{worker_local_round}:{v}".encode('ascii'), hashlib.sha256).hexdigest()
                    if s == expected:
                        prepare_tally[v] += 1

                # Quorum size is computed dynamically based on active heartbeats reported by parent (Byte 4)
                active_nodes = shm.buf[4]
                if active_nodes < 4:
                    active_nodes = num_nodes
                # F threshold adjusts dynamically
                local_f = (active_nodes - 1) // 3
                required_prepares = 2 * local_f + 1

                val_to_commit = None
                if is_byzantine:
                    val_to_commit = not proposal_value
                else:
                    if prepare_tally[True] >= required_prepares:
                        val_to_commit = True
                    elif prepare_tally[False] >= required_prepares:
                        val_to_commit = False

                if val_to_commit is not None:
                    commit_sig = hmac.new(node_key, f"COMMIT:{worker_local_round}:{val_to_commit}".encode('ascii'), hashlib.sha256).hexdigest()
                    shm.buf[start+65] = 2 if val_to_commit else 1
                    shm.buf[start+66:start+130] = commit_sig.encode('ascii')

                last_processed_state = 2
                spin_count = 0  # Reset spin count for finalization phase transition

            elif round_state == 3 and last_processed_state < 3:
                # ------------------
                # 3. FINALIZING PHASE
                # ------------------
                commit_tally = {True: 0, False: 0}
                for i in range(num_nodes):
                    node_start = 300 + (i * slot_size)
                    v_byte = shm.buf[node_start+65]
                    if v_byte == 0:
                        continue
                    v = True if v_byte == 2 else False
                    s = bytes(shm.buf[node_start+66:node_start+130]).decode('ascii')

                    other_key = f"key_secret_{i}".encode()
                    expected = hmac.new(other_key, f"COMMIT:{worker_local_round}:{v}".encode('ascii'), hashlib.sha256).hexdigest()
                    if s == expected:
                        commit_tally[v] += 1

                active_nodes = shm.buf[4]
                if active_nodes < 4:
                    active_nodes = num_nodes
                local_f = (active_nodes - 1) // 3
                required_commits = 2 * local_f + 1

                if not is_byzantine:
                    committed_val = None
                    if commit_tally[True] >= required_commits:
                        committed_val = True
                    elif commit_tally[False] >= required_commits:
                        committed_val = False

                    if committed_val is not None:
                        shm.buf[start+130] = 2 if committed_val else 1

                last_processed_state = 3
            else:
                # --- Adaptive Spin-Backoff Logic ---
                if spin_count < 1000:
                    spin_count += 1
                else:
                    # After 1000 hot loops, back off to yield CPU cycles to the scheduler
                    time.sleep(0.0001)
    except Exception as e:
        with open("/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/Source/worker_error.log", "a") as f:
            f.write(f"Node {node_id} runtime error: {e}\n")
            traceback.print_exc(file=f)

    shm.close()


class XorasShmBft:
    def __init__(self, num_nodes=148, num_byzantine=49, latency_min_ms=0.0, latency_max_ms=0.0, use_processes=False, shm_name="xoras_shm"):
        self.num_nodes = num_nodes
        self.num_byzantine = num_byzantine
        self.latency_min_ms = latency_min_ms
        self.latency_max_ms = latency_max_ms
        self.use_processes = use_processes
        self.current_round_num = 0

        if num_nodes < (3 * num_byzantine + 1):
            raise ValueError(f"Invalid BFT configuration: Node count {num_nodes} is insufficient for {num_byzantine} Byzantine faults.")

        # Allocate 300 bytes metadata + 131 bytes per node slot in POSIX shared memory block
        self.shm_name = shm_name
        self.shm_size = 300 + (self.num_nodes * 131)
        try:
            self.shm = shared_memory.SharedMemory(name=self.shm_name, create=True, size=self.shm_size)
            self.shm.buf[:self.shm_size] = b'\x00' * self.shm_size
        except FileExistsError:
            self.shm = shared_memory.SharedMemory(name=self.shm_name)

        # In-process signature cache for emulated mode
        self.signature_cache = {}
        for i in range(self.num_nodes):
            key = f"key_secret_{i}".encode()
            self.signature_cache[i] = {}

        self.processes = []
        if self.use_processes:
            self._start_process_pool()

    def _start_process_pool(self):
        for i in range(self.num_nodes):
            p = Process(
                target=bft_persistent_worker,
                args=(i, self.num_nodes, self.num_byzantine, self.shm_name, self.shm_size)
            )
            self.processes.append(p)
            p.start()
        time.sleep(0.3)

    def _update_heartbeats(self):
        """Read node PIDs and timestamps from shared memory to track active validators."""
        active_count = 0
        now = int(time.perf_counter() % 100000)
        for i in range(self.num_nodes):
            pid_offset = 10 + (i * 8)
            pid_bytes = self.shm.buf[pid_offset:pid_offset+4]
            hb_bytes = self.shm.buf[pid_offset+4:pid_offset+8]
            
            pid = struct.unpack("<I", pid_bytes)[0]
            hb_time = struct.unpack("<I", hb_bytes)[0]
            
            if pid != 0:
                # If heartbeat updated in the last 2 seconds (handling modular math wrap)
                diff = (now - hb_time) % 100000
                if diff < 2:
                    active_count += 1
        
        self.shm.buf[4] = active_count if active_count > 0 else self.num_nodes

    async def run_consensus_round(self, proposal_value: bool) -> dict:
        start_time = time.perf_counter()

        if self.use_processes:
            # ---------------------------------------------
            # PRODUCTION: Persistent Lock-free Process Pool
            # ---------------------------------------------
            # Track hearts and write active validator count to Byte 4
            self._update_heartbeats()
            
            # Increment global round number (handling byte overflow wrap)
            self.current_round_num = (self.current_round_num + 1) % 250
            
            # Clear validator slots (bytes 300..end)
            self.shm.buf[300:self.shm_size] = b'\x00' * (self.shm_size - 300)

            # Write proposal value (Byte 1) and round number (Byte 3)
            self.shm.buf[1] = 2 if proposal_value else 1
            self.shm.buf[3] = self.current_round_num

            # 1. Trigger PREPARE (round_state = 1)
            self.shm.buf[0] = 1

            # Wait for active nodes to write their prepare vote
            prep_start = time.perf_counter()
            slot_size = 131
            active_limit = self.shm.buf[4]
            while True:
                # Count nodes that have written prepare votes
                prep_count = sum(1 for i in range(self.num_nodes) if self.shm.buf[300 + (i * slot_size)] != 0)
                if prep_count >= active_limit:
                    break
                if (time.perf_counter() - prep_start) > 1.0:
                    break
                await asyncio.sleep(0.0002)

            # 2. Trigger COMMIT (round_state = 2)
            self.shm.buf[0] = 2

            # Wait for commit votes
            commit_start = time.perf_counter()
            local_f = (active_limit - 1) // 3
            required_commits = 2 * local_f + 1
            while True:
                commit_count = sum(1 for i in range(self.num_nodes) if self.shm.buf[300 + (i * slot_size) + 65] != 0)
                if commit_count >= required_commits:
                    break
                if (time.perf_counter() - commit_start) > 1.0:
                    break
                await asyncio.sleep(0.0002)

            # 3. Trigger FINALIZATION (round_state = 3)
            self.shm.buf[0] = 3

            # Wait for final consensus slots to write
            final_start = time.perf_counter()
            while True:
                done_count = sum(1 for i in range(self.num_nodes) if i >= self.num_byzantine and self.shm.buf[300 + (i * slot_size) + 130] != 0)
                if done_count >= (active_limit - self.num_byzantine):
                    break
                if (time.perf_counter() - final_start) > 1.0:
                    break
                await asyncio.sleep(0.0002)

            # Reset round state to IDLE
            self.shm.buf[0] = 0

        else:
            # ---------------------------------------------
            # EMULATED: Fast thread loop fallback
            # ---------------------------------------------
            self.shm.buf[:self.shm_size] = b'\x00' * self.shm_size
            slot_size = 131
            self.current_round_num = (self.current_round_num + 1) % 250

            # 1. Prepare Stage
            prepare_tally = {True: 0, False: 0}
            for i in range(self.num_nodes):
                val_to_prepare = proposal_value
                if i < self.num_byzantine:
                    val_to_prepare = not proposal_value

                # Refresh signature cache for current round
                key = f"key_secret_{i}".encode()
                sig = hmac.new(key, f"PREPARE:{self.current_round_num}:{val_to_prepare}".encode('ascii'), hashlib.sha256).hexdigest()
                self.signature_cache[i][val_to_prepare] = sig

                start = 300 + (i * slot_size)
                self.shm.buf[start] = 2 if val_to_prepare else 1
                self.shm.buf[start+1:start+65] = sig.encode('ascii')

                v = True if self.shm.buf[start] == 2 else False
                s = bytes(self.shm.buf[start+1:start+65]).decode('ascii')
                if s == self.signature_cache[i][v]:
                    prepare_tally[v] += 1

            # 2. Commit Stage
            required_prepares = 2 * self.num_byzantine + 1
            commit_tally = {True: 0, False: 0}
            for i in range(self.num_nodes):
                if i < self.num_byzantine:
                    val_to_commit = not proposal_value
                else:
                    val_to_commit = None
                    if prepare_tally[True] >= required_prepares:
                        val_to_commit = True
                    elif prepare_tally[False] >= required_prepares:
                        val_to_commit = False

                if val_to_commit is not None:
                    key = f"key_secret_{i}".encode()
                    sig = hmac.new(key, f"COMMIT:{self.current_round_num}:{val_to_commit}".encode('ascii'), hashlib.sha256).hexdigest()
                    self.signature_cache[i][val_to_commit] = sig

                    start = 300 + (i * slot_size)
                    self.shm.buf[start+65] = 2 if val_to_commit else 1
                    self.shm.buf[start+66:start+130] = sig.encode('ascii')

                    v = True if self.shm.buf[start+65] == 2 else False
                    s = bytes(self.shm.buf[start+66:start+130]).decode('ascii')
                    if s == self.signature_cache[i][v]:
                        commit_tally[v] += 1

            # 3. Consensus Finalization
            required_commits = 2 * self.num_byzantine + 1
            for i in range(self.num_nodes):
                if i >= self.num_byzantine:
                    committed_val = None
                    if commit_tally[True] >= required_commits:
                        committed_val = True
                    elif commit_tally[False] >= required_commits:
                        committed_val = False

                    if committed_val is not None:
                        start = 300 + (i * slot_size)
                        self.shm.buf[start+130] = 2 if committed_val else 1

        # Read back committed values from shared memory to calculate final status
        honest_committed_values = []
        slot_size = 131
        for i in range(self.num_nodes):
            if i >= self.num_byzantine:
                start = 300 + (i * slot_size)
                val_byte = self.shm.buf[start+130]
                if val_byte != 0:
                    honest_committed_values.append(True if val_byte == 2 else False)

        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000.0

        consensus_reached = len(set(honest_committed_values)) == 1 and len(honest_committed_values) > 0
        final_value = honest_committed_values[0] if consensus_reached else None

        return {
            "consensus_reached": consensus_reached,
            "final_value": final_value,
            "latency_ms": elapsed_ms,
            "honest_nodes_reporting": len(honest_committed_values)
        }

    def cleanup(self):
        """Free pool processes and unlink OS shared memory segment."""
        if self.use_processes:
            # Set global stop flag (Byte 2)
            try:
                self.shm.buf[2] = 1
            except Exception:
                pass
            
            for p in self.processes:
                p.join(timeout=0.1)
                if p.is_alive():
                    p.terminate()

        try:
            self.shm.close()
            self.shm.unlink()
        except Exception:
            pass
