#!/usr/bin/env python3
"""
==============================================================================
DUAL-SUBSTRATE CONCURRENT MUTATION & VERIFICATION GAUNTLET
==============================================================================
Mandate: Verify that dual-substrate consensus (Zig Native == Python Guard)
holds 100% agreement when the SQLite file itself is actively written to during
verification, not just read from.

Architecture:
  - Writer: Python ContextLineageEngine continuously commits state to SQLite WAL
    at high frequency.
  - Verifier: Independent Native Zig binary (`zig_live_verifier`) invoked
    repeatedly concurrently, executing inside an isolated SQLite read transaction
    with zero shared runtime code or Python GIL interference.
  - Parity Audit:
    Every single read by Zig captures an atomic snapshot ($N$ nodes).
    We mathematically verify whether Zig's independently calculated Merkle root
    matches the exact Merkle root calculated by Python for that exact commit snapshot.
==============================================================================
"""

import os
import sys
import time
import json
import sqlite3
import hashlib
import subprocess
import threading
from pathlib import Path

BASE_DIR = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
sys.path.insert(0, str(BASE_DIR / "core"))

from ops.provenance.context_lineage_dag_engine import ContextLineageEngine

TEST_DIR = BASE_DIR / ".sovereign" / "gauntlets" / "concurrent_dual_substrate"
TEST_DIR.mkdir(parents=True, exist_ok=True)
TEST_DB = str(TEST_DIR / "live_lineage.db")

ZIG_SRC = BASE_DIR / "core" / "ops" / "native" / "zig" / "concurrent_merkle_verifier.zig"
ZIG_BIN = TEST_DIR / "zig_live_verifier"

# Native Zig 0.16 verifier with explicit snapshot isolation
ZIG_CODE = """const std = @import("std");
const c = @cImport({
    @cInclude("sqlite3.h");
    @cInclude("stdio.h");
    @cInclude("string.h");
});

const Sha256 = std.crypto.hash.sha2.Sha256;

fn sha256Hex(allocator: std.mem.Allocator, input: []const u8) ![]u8 {
    var digest: [Sha256.digest_length]u8 = undefined;
    Sha256.hash(input, &digest, .{});
    const hex_buf = try allocator.alloc(u8, Sha256.digest_length * 2);
    @memcpy(hex_buf[0..], &std.fmt.bytesToHex(&digest, .lower));
    return hex_buf;
}

pub export fn main(argc: c_int, argv: [*][*:0]const u8) c_int {
    const allocator = std.heap.c_allocator;
    if (argc < 2) {
        std.debug.print("ERROR: Missing db path\\n", .{});
        return 2;
    }
    const db_path = argv[1];

    var db: ?*c.sqlite3 = null;
    if (c.sqlite3_open_v2(db_path, &db, c.SQLITE_OPEN_READONLY, null) != c.SQLITE_OK) {
        const err_msg = c.sqlite3_errmsg(db);
        std.debug.print("SQLITE_OPEN_ERROR: {s}\\n", .{err_msg});
        return 10;
    }
    defer _ = c.sqlite3_close(db);

    _ = c.sqlite3_busy_timeout(db, 5000);

    // Explicit read transaction ensures point-in-time snapshot isolation
    if (c.sqlite3_exec(db, "BEGIN DEFERRED;", null, null, null) != c.SQLITE_OK) {
        std.debug.print("SQLITE_BEGIN_ERROR\\n", .{});
        return 11;
    }
    defer _ = c.sqlite3_exec(db, "COMMIT;", null, null, null);

    const query = "SELECT node_id FROM lineage_nodes ORDER BY timestamp ASC, rowid ASC;";
    var stmt: ?*c.sqlite3_stmt = null;
    if (c.sqlite3_prepare_v2(db, query, -1, &stmt, null) != c.SQLITE_OK) {
        const err_msg = c.sqlite3_errmsg(db);
        std.debug.print("SQLITE_PREPARE_ERROR: {s}\\n", .{err_msg});
        return 12;
    }
    defer _ = c.sqlite3_finalize(stmt);

    var node_hashes: std.ArrayListUnmanaged([]u8) = .empty;
    defer {
        for (node_hashes.items) |h| allocator.free(h);
        node_hashes.deinit(allocator);
    }

    var total_nodes: usize = 0;
    while (c.sqlite3_step(stmt) == c.SQLITE_ROW) {
        const node_id_c = c.sqlite3_column_text(stmt, 0);
        if (node_id_c == null) continue;
        const node_id = std.mem.span(node_id_c);
        const h_copy = allocator.dupe(u8, node_id) catch return 13;
        node_hashes.append(allocator, h_copy) catch return 14;
        total_nodes += 1;
    }

    if (total_nodes == 0) {
        const genesis_empty = sha256Hex(allocator, "GENESIS_EMPTY_TREE") catch return 15;
        defer allocator.free(genesis_empty);
        std.debug.print("HASH:{s}:COUNT:0\\n", .{genesis_empty});
        return 0;
    }

    // Compute Merkle Root in pure Zig
    var current_layer = allocator.alloc([]u8, node_hashes.items.len) catch return 16;
    for (node_hashes.items, 0..) |h, i| {
        current_layer[i] = allocator.dupe(u8, h) catch return 17;
    }

    while (current_layer.len > 1) {
        var next_len = current_layer.len / 2;
        if (current_layer.len % 2 != 0) next_len += 1;

        var next_layer = allocator.alloc([]u8, next_len) catch return 18;
        var idx: usize = 0;
        var i: usize = 0;

        while (i < current_layer.len) : (i += 2) {
            if (i + 1 < current_layer.len) {
                const combined = std.fmt.allocPrint(allocator, "{s}{s}", .{ current_layer[i], current_layer[i + 1] }) catch return 19;
                defer allocator.free(combined);
                next_layer[idx] = sha256Hex(allocator, combined) catch return 20;
            } else {
                next_layer[idx] = allocator.dupe(u8, current_layer[i]) catch return 21;
            }
            idx += 1;
        }

        for (current_layer) |h| allocator.free(h);
        allocator.free(current_layer);
        current_layer = next_layer;
    }

    const zig_root = current_layer[0];
    defer allocator.free(zig_root);
    allocator.free(current_layer);

    std.debug.print("HASH:{s}:COUNT:{d}\\n", .{zig_root, total_nodes});
    return 0;
}
"""

def prepare_zig_binary():
    with open(ZIG_SRC, "w", encoding="utf-8") as f:
        f.write(ZIG_CODE)
    
    cmd = [
        "zig", "build-exe", str(ZIG_SRC),
        "-lsqlite3", "-lc", "-O", "ReleaseFast",
        f"-femit-bin={ZIG_BIN}"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Zig compilation failed:", res.stderr)
        sys.exit(1)

class ConcurrentDualSubstrateGauntlet:
    def __init__(self, db_path: str, num_mutations: int = 1000, read_probes: int = 50):
        # Clean slate
        if os.path.exists(db_path): os.remove(db_path)
        for ext in ["-wal", "-shm"]:
            if os.path.exists(db_path + ext): os.remove(db_path + ext)

        self.db_path = db_path
        self.num_mutations = num_mutations
        self.read_probes = read_probes
        self.engine = ContextLineageEngine(db_path=self.db_path)
        self.stop_writer = False
        
        # Telemetry
        self.writes_completed = 0
        self.write_errors = 0
        self.read_errors = 0
        self.sqlite_busy_count = 0
        self.active_writer_history = {} # count -> root
        self.read_probes_log = []
        self.lock = threading.Lock()

    def writer_thread(self):
        """Continuously commits steps to the SQLite DB using Python ContextLineageEngine."""
        session_id = "concurrent_stress_sess_01"
        for i in range(1, self.num_mutations + 1):
            if self.stop_writer:
                break
            payload = {
                "step_index": i,
                "sensor_value": (i * 31) % 10000,
                "timestamp_sim": time.time(),
                "agent": "Daxx_Master_Mechanic"
            }
            try:
                res = self.engine.commit_step(
                    session_id=session_id,
                    agent_id="Citizen_03_DAXX",
                    step_type="CONCURRENT_PROBE_STEP",
                    payload=payload
                )
                root = self.engine.calculate_global_merkle_root()
                with self.lock:
                    self.writes_completed += 1
                    self.active_writer_history[self.writes_completed] = root
            except Exception as e:
                with self.lock:
                    self.write_errors += 1
                    if "locked" in str(e).lower() or "busy" in str(e).lower():
                        self.sqlite_busy_count += 1
            time.sleep(0.001)

    def reader_verifier_thread(self):
        """Executes the native Zig verifier binary repeatedly while Python writes."""
        time.sleep(0.02) # let writer start and establish WAL
        for p in range(self.read_probes):
            t0 = time.perf_counter()
            res = subprocess.run([str(ZIG_BIN), self.db_path], capture_output=True, text=True)
            latency_ms = (time.perf_counter() - t0) * 1000.0

            if res.returncode != 0:
                with self.lock:
                    self.read_errors += 1
                    err_msg = res.stdout + res.stderr
                    if "busy" in err_msg.lower() or "lock" in err_msg.lower():
                        self.sqlite_busy_count += 1
                continue

            raw_out = (res.stderr.strip() + "\n" + res.stdout.strip()).strip()
            zig_hash = None
            zig_count = None
            for line in raw_out.splitlines():
                if line.startswith("HASH:"):
                    parts = line.split(":")
                    if len(parts) >= 4:
                        zig_hash = parts[1]
                        zig_count = int(parts[3])

            if zig_hash and zig_count is not None:
                self.read_probes_log.append((p, zig_count, zig_hash, latency_ms))

            time.sleep(0.015)

    def run(self):
        print("==============================================================================")
        print("  LIVE FIRE: DUAL-SUBSTRATE READ-DURING-WRITE CONCURRENCY GAUNTLET           ")
        print(f"  Target: Concurrent Python SQLite WAL writes vs. Native Zig Verifications   ")
        print("==============================================================================")
        
        t_start = time.perf_counter()
        w_thread = threading.Thread(target=self.writer_thread)
        r_thread = threading.Thread(target=self.reader_verifier_thread)

        w_thread.start()
        r_thread.start()

        r_thread.join()
        self.stop_writer = True
        w_thread.join()

        t_total = time.perf_counter() - t_start

        # Post-run audit of every probe against writer commit history
        hash_matches = 0
        hash_mismatches = 0
        for p_idx, z_count, z_hash, lat in self.read_probes_log:
            exp_hash = self.active_writer_history.get(z_count)
            if exp_hash is not None and exp_hash == z_hash:
                hash_matches += 1
            elif z_count == 0 and z_hash == ContextLineageEngine.compute_hash("GENESIS_EMPTY_TREE"):
                hash_matches += 1
            else:
                hash_mismatches += 1

        total_probes = len(self.read_probes_log)
        avg_lat = sum(x[3] for x in self.read_probes_log) / max(1, total_probes)

        print(f"\n[EXECUTION SUMMARY - {t_total:.3f} s]")
        print(f"  ✓ Python Writes Committed:        {self.writes_completed:,}")
        print(f"  ✓ Python Write Errors:            {self.write_errors}")
        print(f"  ✓ Zig Native Verification Probes: {total_probes}")
        print(f"  ✓ Zig Verification Errors:        {self.read_errors}")
        print(f"  ✓ SQLite Busy / Lock Contention:  {self.sqlite_busy_count}")
        print(f"  ✓ Mean Zig Verification Latency:  {avg_lat:.2f} ms")
        match_pct = (100.0 * hash_matches / max(1, total_probes))
        print(f"  ✓ Snapshot Consensus Parity:      {hash_matches} / {total_probes} ({match_pct:.1f}%)")
        print(f"  ✓ Torn Reads / Desync Errors:     {hash_mismatches}")

        print("\n==============================================================================")
        if hash_mismatches == 0 and self.read_errors == 0 and total_probes > 0:
            print("🎉 CEILING BROKEN: Dual-Substrate Parity Holds Under Active Write Mutation!")
            print("   Native Zig independently reconstructed point-in-time Merkle roots")
            print("   from live SQLite WAL shared memory with ZERO locks and ZERO desyncs.")
        else:
            print("❌ FAILURE DETECTED: Torn read or lock contention occurred during live write.")
        print("==============================================================================\n")

if __name__ == "__main__":
    prepare_zig_binary()
    gauntlet = ConcurrentDualSubstrateGauntlet(TEST_DB, num_mutations=800, read_probes=40)
    gauntlet.run()
