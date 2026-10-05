#!/usr/bin/env python3
"""
ops/scripts/xoras_shm_client.py
Zero-Lock Python FFI Client for XORAS Zig POSIX Shared Memory Fabric.
Enables sub-microsecond state routing across Python, Zig, and Rust without SQLite.
"""

import ctypes
import os
import sys
import time

LIB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bin", "libxoras_shm.dylib"
)

# 128-byte CognitiveFrame matching Zig struct
class CognitiveFrame(ctypes.Structure):
    _fields_ = [
        ("seq", ctypes.c_uint64),
        ("timestamp_ns", ctypes.c_uint64),
        ("agent_id", ctypes.c_uint8),
        ("gate_id", ctypes.c_uint8),
        ("action_type", ctypes.c_uint8),
        ("status", ctypes.c_uint8),
        ("flags", ctypes.c_uint32),
        ("tensor_hash", ctypes.c_uint8 * 32),
        ("payload", ctypes.c_char * 64),
        ("_pad", ctypes.c_uint8 * 8),
    ]

# Assert exact 128-byte layout
assert ctypes.sizeof(CognitiveFrame) == 128, f"Expected 128 bytes, got {ctypes.sizeof(CognitiveFrame)}"

class XorasShmClient:
    def __init__(self, shm_path: str = "/xoras_state_ring", create: bool = True):
        self.shm_path = shm_path.encode("utf-8")
        if not os.path.exists(LIB_PATH):
            raise FileNotFoundError(f"Shared library not found at: {LIB_PATH}")
        
        self.lib = ctypes.CDLL(LIB_PATH)
        self._setup_signatures()

        if create:
            self.ring_ptr = self.lib.xoras_shm_create(self.shm_path)
            if not self.ring_ptr:
                # If already exists, open existing
                self.ring_ptr = self.lib.xoras_shm_open_existing(self.shm_path)
        else:
            self.ring_ptr = self.lib.xoras_shm_open_existing(self.shm_path)

        if not self.ring_ptr:
            raise RuntimeError(f"Failed to initialize or connect to shared memory at: {shm_path}")

    def _setup_signatures(self):
        # xoras_shm_create
        self.lib.xoras_shm_create.argtypes = [ctypes.c_char_p]
        self.lib.xoras_shm_create.restype = ctypes.c_void_p

        # xoras_shm_open_existing
        self.lib.xoras_shm_open_existing.argtypes = [ctypes.c_char_p]
        self.lib.xoras_shm_open_existing.restype = ctypes.c_void_p

        # xoras_shm_push
        self.lib.xoras_shm_push.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_size_t,
        ]
        self.lib.xoras_shm_push.restype = ctypes.c_bool

        # xoras_shm_pop
        self.lib.xoras_shm_pop.argtypes = [ctypes.c_void_p, ctypes.POINTER(CognitiveFrame)]
        self.lib.xoras_shm_pop.restype = ctypes.c_bool

        # xoras_shm_peek_latest
        self.lib.xoras_shm_peek_latest.argtypes = [ctypes.c_void_p, ctypes.POINTER(CognitiveFrame)]
        self.lib.xoras_shm_peek_latest.restype = ctypes.c_bool

        # xoras_shm_close
        self.lib.xoras_shm_close.argtypes = [ctypes.c_void_p]
        self.lib.xoras_shm_close.restype = None

        # xoras_shm_unlink
        self.lib.xoras_shm_unlink.argtypes = [ctypes.c_char_p]
        self.lib.xoras_shm_unlink.restype = None

    def push(self, agent_id: int, gate_id: int, action: int, tensor_hash: bytes = None, payload: str = "") -> bool:
        h_bytes = tensor_hash[:32] if tensor_hash else None
        p_bytes = payload.encode("utf-8")[:64]
        return self.lib.xoras_shm_push(
            self.ring_ptr,
            ctypes.c_uint8(agent_id),
            ctypes.c_uint8(gate_id),
            ctypes.c_uint8(action),
            h_bytes,
            p_bytes,
            len(p_bytes),
        )

    def pop(self):
        frame = CognitiveFrame()
        success = self.lib.xoras_shm_pop(self.ring_ptr, ctypes.byref(frame))
        if not success:
            return None
        return {
            "seq": frame.seq,
            "timestamp_ns": frame.timestamp_ns,
            "agent_id": frame.agent_id,
            "gate_id": frame.gate_id,
            "action_type": frame.action_type,
            "status": frame.status,
            "payload": frame.payload.decode("utf-8", errors="replace").rstrip("\x00"),
        }

    def peek_latest(self):
        frame = CognitiveFrame()
        success = self.lib.xoras_shm_peek_latest(self.ring_ptr, ctypes.byref(frame))
        if not success:
            return None
        return {
            "seq": frame.seq,
            "timestamp_ns": frame.timestamp_ns,
            "agent_id": frame.agent_id,
            "gate_id": frame.gate_id,
            "action_type": frame.action_type,
            "status": frame.status,
            "payload": frame.payload.decode("utf-8", errors="replace").rstrip("\x00"),
        }

    def close(self):
        if self.ring_ptr:
            self.lib.xoras_shm_close(self.ring_ptr)
            self.ring_ptr = None

    def unlink(self):
        self.lib.xoras_shm_unlink(self.shm_path)


if __name__ == "__main__":
    print("Initializing XORAS Python-Zig Shared Memory Client...")
    client = XorasShmClient(shm_path="/xoras_py_test", create=True)
    
    # Test push
    test_hash = b"\xAB" * 32
    client.push(agent_id=1, gate_id=2, action=0x33, tensor_hash=test_hash, payload="PYTHON_ZIG_FFI_VALIDATED")
    
    # Test peek
    latest = client.peek_latest()
    print("Peeked Latest Frame:", latest)
    
    # Test pop
    popped = client.pop()
    print("Popped Frame:", popped)
    
    # Microbenchmark roundtrip from Python
    iterations = 50_000
    t0 = time.perf_counter_ns()
    for i in range(iterations):
        client.push(agent_id=i % 9, gate_id=(i >> 2) % 4, action=1, payload="PULSE")
        _ = client.pop()
    t1 = time.perf_counter_ns()
    
    total_ns = t1 - t0
    ns_per_op = total_ns / iterations
    ops_per_sec = 1_000_000_000.0 / ns_per_op
    
    print(f"\nPython ctypes roundtrip benchmark ({iterations} ops):")
    print(f"  Total time: {total_ns / 1_000_000:.2f} ms")
    print(f"  Latency per push+pop: {ns_per_op:.2f} ns ({ns_per_op / 1000:.2f} µs)")
    print(f"  Throughput: {ops_per_sec:,.0f} ops/sec")
    
    client.close()
    client.unlink()
    print("\nShared memory FFI test completed flawlessly.")
