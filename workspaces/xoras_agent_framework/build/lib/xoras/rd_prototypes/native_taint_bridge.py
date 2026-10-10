"""
XORAS Native Polyglot Substrate Bridge: Hardware Taint Lattice (C FFI)
Binds Python runtime directly to native libxoras_taint_lattice.dylib for microsecond memory-safety gates.
"""

import ctypes
import os
from dataclasses import dataclass
from typing import Optional

class XORASTaintPacket(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("taint_flag", ctypes.c_uint32),
        ("payload_len", ctypes.c_uint32),
        ("memory_tag", ctypes.c_uint64),
        ("source_id", ctypes.c_char * 32),
        ("raw_bytes", ctypes.c_char * 1024),
    ]

class XORASTaintResult(ctypes.Structure):
    _fields_ = [
        ("is_promoted", ctypes.c_int),
        ("final_taint", ctypes.c_uint32),
        ("reason", ctypes.c_char * 128),
    ]

class NativeHardwareTaintLattice:
    def __init__(self):
        dylib_path = os.path.join(os.path.dirname(__file__), "..", "..", "native", "libxoras_taint_lattice.dylib")
        if not os.path.exists(dylib_path):
            dylib_path = os.path.join(os.path.dirname(__file__), "libxoras_taint_lattice.dylib")

        if os.path.exists(dylib_path):
            self.lib = ctypes.CDLL(dylib_path)
            self.lib.create_candidate_packet.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
            self.lib.create_candidate_packet.restype = XORASTaintPacket

            self.lib.evaluate_taint_promotion.argtypes = [ctypes.POINTER(XORASTaintPacket)]
            self.lib.evaluate_taint_promotion.restype = XORASTaintResult
            self.has_native = True
        else:
            self.has_native = False

    def eval_native_taint(self, source_id: str, raw_payload: str) -> dict:
        """Evaluates payload via native C dynamic library."""
        if not self.has_native:
            return {"success": False, "error": "Native library libxoras_taint_lattice.dylib not found"}

        pkt = self.lib.create_candidate_packet(source_id.encode("utf-8"), raw_payload.encode("utf-8"))
        res = self.lib.evaluate_taint_promotion(ctypes.byref(pkt))

        return {
            "is_promoted": bool(res.is_promoted),
            "final_taint": hex(res.final_taint),
            "reason": res.reason.decode("utf-8"),
            "memory_tag": hex(pkt.memory_tag),
            "native_accelerated": True
        }
