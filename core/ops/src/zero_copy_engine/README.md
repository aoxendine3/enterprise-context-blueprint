# XORAS Zero-Copy Engine

The XORAS Zero-Copy Engine is a proprietary, bare-metal Rust FFI library designed to bridge Python's high-level logic with hardware-level memory speed on Apple M4 Silicon.

## Value Proposition
By eliminating memory serialization and utilizing 128-byte cache-line alignments (`#[repr(align(128))]`), this engine allows Python to stream and validate millions of cryptographic signatures directly from RAM at **over 220 GB/s**—a 13x speedup over native CPython structures.

## Quick Start
1. **Build the engine:**
   ```bash
   cargo build --release
   ```
2. **Run the benchmarks:**
   ```bash
   python3 tests/benchmark.py
   ```
3. **Run the FFI verification:**
   ```bash
   python3 tests/verify_ffi.py
   ```

## Architecture Overview
The engine expects a contiguous byte buffer from Python. Using `ctypes`, the memory pointer is passed directly to the Rust binary where it is transmuted into a slice of `HexCell` structs. No data is copied. No heap allocations are made.

See [docs/architecture.md](docs/architecture.md) for the exact memory layout and shared-memory handshakes.
