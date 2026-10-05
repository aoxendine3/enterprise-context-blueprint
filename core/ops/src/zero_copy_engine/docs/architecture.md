# Zero-Copy Engine Architecture & IPC Handshake

## The Memory Model: HexCell
The foundational memory unit is the `HexCell`, an exactly 3,200-byte structure.

```rust
#[repr(C, align(128))]
pub struct HexCell {
    pub header: [u8; 128],         // 128 bytes
    pub payload: [u8; 3040],       // 3040 bytes
    pub cryptographic_sig: [u8; 32], // 32 bytes (Ed25519 length)
}
```

### Why 128-byte Alignment?
Apple Silicon (M-series) utilizes a 128-byte L1 cache line architecture (compared to standard x86 64-byte). By aggressively aligning the structs to 128 bytes, we prevent false sharing and ensure that reading the `cryptographic_sig` does not thrash the L1 cache.

## The Python FFI Handshake
**Failure Mode:** If Python passes a buffer that is not cleanly divisible by 3,200 bytes, or if the pointer is null, the Rust engine immediately faults and returns `-1` or `-2`.

**The Handshake Protocol:**
1. Python allocates a contiguous `bytearray` (pinned memory).
2. Python uses `ctypes.c_char_p.from_buffer()` to grab the physical C-pointer.
3. The pointer and the `num_cells` count are passed to `process_batch_zero_copy()`.
4. Rust calls `slice::from_raw_parts()`, converting the pointer into an iterable slice of `HexCell` structs.
5. Rust iterates the slice and returns a checksum. Python validates the checksum.

## Health Checks
If integrating this engine into a long-running daemon, a readiness probe must construct a 3,200-byte dummy payload, pass it to `process_zero_copy_hexcell`, and expect the exact first byte of the signature block as the return value. Do not declare the service healthy until this memory round-trip succeeds.
