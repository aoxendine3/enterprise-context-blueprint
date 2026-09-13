"""
XORAS SOVEREIGN CORE: 3,200-BYTE HEXCELL MEMORY ENGINE
Layout:
- 0x0000 - 0x003F (64 bytes): Header (Magic, Cell ID, Timestamp, Epoch, Flags)
- 0x0040 - 0x007F (64 bytes): 16-D Poincare Ball Coordinates (16 x Float32)
- 0x0080 - 0x087F (2048 bytes): 512-D Embedding Vector (512 x Float32)
- 0x0880 - 0x08BF (64 bytes): Ed25519 Cryptographic Signature
- 0x08C0 - 0x08DF (32 bytes): Blake3 / SHA-256 Digest
- 0x08E0 - 0x095F (128 bytes): Fast Rule Bitmask (16 x UInt64)
- 0x0960 - 0x0C7F (800 bytes): Source Trace Payload & Metadata
Total: exactly 3,200 bytes (50 contiguous 64-byte CPU cache lines)
"""

import struct
import time
from typing import Optional, List

HEXCELL_SIZE = 3200
MAGIC_HEADER = b"HEXC"

class HexCell:
    __slots__ = (
        "cell_id", "timestamp", "epoch", "flags",
        "poincare_coord", "vector", "signature",
        "digest", "bitmask", "payload"
    )

    def __init__(
        self,
        cell_id: int = 0,
        timestamp: Optional[float] = None,
        epoch: int = 1,
        flags: int = 0,
        poincare_coord: Optional[List[float]] = None,
        vector: Optional[List[float]] = None,
        signature: bytes = b"\x00" * 64,
        digest: bytes = b"\x00" * 32,
        bitmask: Optional[List[int]] = None,
        payload: bytes = b""
    ):
        self.cell_id = cell_id
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.epoch = epoch
        self.flags = flags
        self.poincare_coord = poincare_coord or [0.0] * 16
        self.vector = vector or [0.0] * 512
        self.signature = signature[:64].ljust(64, b"\x00")
        self.digest = digest[:32].ljust(32, b"\x00")
        self.bitmask = bitmask or [0] * 16
        self.payload = payload[:800].ljust(800, b"\x00")

    def pack(self) -> bytes:
        """Packs cell into exactly 3,200 contiguous bytes."""
        # Header: 64 bytes
        # Magic (4s) + cell_id (Q) + timestamp (d) + epoch (I) + flags (I) + reserved (36s)
        header = struct.pack(
            "=4sQdII36s",
            MAGIC_HEADER,
            self.cell_id,
            self.timestamp,
            self.epoch,
            self.flags,
            b"\x00" * 36
        )

        # 16-D Poincare coords: 16 * 4 = 64 bytes
        p_coords = struct.pack("=16f", *self.poincare_coord[:16])

        # 512-D vector: 512 * 4 = 2048 bytes
        vec = struct.pack("=512f", *self.vector[:512])

        # Signature: 64 bytes
        sig = self.signature

        # Digest: 32 bytes
        dig = self.digest

        # Bitmask: 16 * 8 = 128 bytes
        bmask = struct.pack("=16Q", *self.bitmask[:16])

        # Trace payload: 800 bytes
        pay = self.payload

        packed = header + p_coords + vec + sig + dig + bmask + pay
        if len(packed) != HEXCELL_SIZE:
            raise ValueError(f"HexCell pack size mismatch: expected {HEXCELL_SIZE}, got {len(packed)}")
        return packed

    @classmethod
    def unpack(cls, data: bytes) -> "HexCell":
        """Unpacks a 3,200-byte buffer into a HexCell."""
        if len(data) != HEXCELL_SIZE:
            raise ValueError(f"Data length must be exactly {HEXCELL_SIZE} bytes")

        magic, cell_id, ts, epoch, flags, _ = struct.unpack("=4sQdII36s", data[0:64])
        if magic != MAGIC_HEADER:
            raise ValueError(f"Invalid HexCell magic: {magic}")

        p_coords = list(struct.unpack("=16f", data[64:128]))
        vec = list(struct.unpack("=512f", data[128:2176]))
        sig = data[2176:2240]
        dig = data[2240:2272]
        bmask = list(struct.unpack("=16Q", data[2272:2400]))
        pay = data[2400:3200]

        return cls(
            cell_id=cell_id,
            timestamp=ts,
            epoch=epoch,
            flags=flags,
            poincare_coord=p_coords,
            vector=vec,
            signature=sig,
            digest=dig,
            bitmask=bmask,
            payload=pay
        )

class HexCellEngine:
    """Ring buffer allocator for high-throughput zero-copy HexCell streaming."""

    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.buffer = bytearray(capacity * HEXCELL_SIZE)
        self.head = 0

    def write_cell(self, cell: HexCell) -> int:
        idx = self.head % self.capacity
        offset = idx * HEXCELL_SIZE
        self.buffer[offset:offset + HEXCELL_SIZE] = cell.pack()
        self.head += 1
        return idx

    def read_cell(self, index: int) -> HexCell:
        offset = (index % self.capacity) * HEXCELL_SIZE
        data = bytes(self.buffer[offset:offset + HEXCELL_SIZE])
        return HexCell.unpack(data)
