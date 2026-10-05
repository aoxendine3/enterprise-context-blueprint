const std = @import("std");
const c = @cImport({
    @cInclude("sqlite3.h");
    @cInclude("stdio.h");
    @cInclude("string.h");
});

const Sha256 = std.crypto.hash.sha2.Sha256;

const DB_PATH = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/.sovereign/provenance/lineage_dag.db";
const MERKLE_FILE = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/tri_brain/merkle_root.hash";

fn sha256Hex(allocator: std.mem.Allocator, input: []const u8) ![]u8 {
    var digest: [Sha256.digest_length]u8 = undefined;
    Sha256.hash(input, &digest, .{});
    const hex_buf = try allocator.alloc(u8, Sha256.digest_length * 2);
    _ = std.fmt.bytesToHex(&digest, .lower);
    @memcpy(hex_buf[0..], &std.fmt.bytesToHex(&digest, .lower));
    return hex_buf;
}

pub fn main() !void {
    const allocator = std.heap.c_allocator;

    std.debug.print("===========================================================================\n", .{});
    std.debug.print("  INDEPENDENT NATIVE ZIG MERKLE VERIFIER (ZERO PYTHON CODE SHARING)\n", .{});
    std.debug.print("===========================================================================\n", .{});

    // 1. Open SQLite DB via direct C-ABI binding
    var db: ?*c.sqlite3 = null;
    if (c.sqlite3_open_v2(DB_PATH, &db, c.SQLITE_OPEN_READWRITE, null) != c.SQLITE_OK) {
        const err_msg = c.sqlite3_errmsg(db);
        std.debug.print("❌ ZIG VERIFIER FAIL: Unable to open SQLite DB at {s} ({s})\n", .{ DB_PATH, err_msg });
        std.process.exit(1);
    }
    defer _ = c.sqlite3_close(db);

    const query = "SELECT node_id, seq_num, session_id FROM lineage_nodes ORDER BY timestamp ASC, rowid ASC";
    var stmt: ?*c.sqlite3_stmt = null;
    const rc = c.sqlite3_prepare_v2(db, query, -1, &stmt, null);
    if (rc != c.SQLITE_OK) {
        const err_msg = c.sqlite3_errmsg(db);
        std.debug.print("❌ ZIG VERIFIER FAIL: Unable to prepare SQL query: {s}\n", .{err_msg});
        std.process.exit(1);
    }
    defer _ = c.sqlite3_finalize(stmt);

    var node_hashes: std.ArrayListUnmanaged([]u8) = .empty;
    defer {
        for (node_hashes.items) |h| allocator.free(h);
        node_hashes.deinit(allocator);
    }

    var total_nodes: usize = 0;
    var last_seq_per_session = std.StringHashMap(i64).init(allocator);
    defer {
        var it = last_seq_per_session.iterator();
        while (it.next()) |entry| {
            allocator.free(entry.key_ptr.*);
        }
        last_seq_per_session.deinit();
    }

    var sequence_violations: usize = 0;

    while (c.sqlite3_step(stmt) == c.SQLITE_ROW) {
        const node_id_c = c.sqlite3_column_text(stmt, 0);
        const seq_num = c.sqlite3_column_int64(stmt, 1);
        const session_id_c = c.sqlite3_column_text(stmt, 2);

        if (node_id_c == null or session_id_c == null) continue;

        const node_id = std.mem.span(node_id_c);
        const session_id = std.mem.span(session_id_c);

        // Sequence monotonicity check per session
        const gop = try last_seq_per_session.getOrPut(session_id);
        if (!gop.found_existing) {
            gop.key_ptr.* = try allocator.dupe(u8, session_id);
            gop.value_ptr.* = 0;
        }

        const expected_seq = gop.value_ptr.* + 1;
        if (seq_num != expected_seq) {
            std.debug.print("⚠️  SEQUENCE COLLAPSE: Session '{s}' expected seq {d}, got {d}\n", .{ session_id, expected_seq, seq_num });
            sequence_violations += 1;
        }
        gop.value_ptr.* = seq_num;

        const h_copy = try allocator.dupe(u8, node_id);
        try node_hashes.append(allocator, h_copy);
        total_nodes += 1;
    }

    if (sequence_violations > 0) {
        std.debug.print("❌ ZIG VERIFIER FAIL: Found {d} sequence monotonicity violations in DB.\n", .{sequence_violations});
        std.process.exit(1);
    }

    std.debug.print("✅ Processed {d} lineage nodes across SQLite database.\n", .{total_nodes});
    std.debug.print("✅ Monotonic Sequence Verification: 100% Monotonic (0 Gaps).\n", .{});

    // 2. Recompute Merkle Root in Native Zig
    var current_layer = try allocator.alloc([]u8, node_hashes.items.len);
    for (node_hashes.items, 0..) |h, i| {
        current_layer[i] = try allocator.dupe(u8, h);
    }

    while (current_layer.len > 1) {
        var next_len = current_layer.len / 2;
        if (current_layer.len % 2 != 0) next_len += 1;

        var next_layer = try allocator.alloc([]u8, next_len);
        var idx: usize = 0;
        var i: usize = 0;

        while (i < current_layer.len) : (i += 2) {
            if (i + 1 < current_layer.len) {
                const combined = try std.fmt.allocPrint(allocator, "{s}{s}", .{ current_layer[i], current_layer[i + 1] });
                defer allocator.free(combined);
                next_layer[idx] = try sha256Hex(allocator, combined);
            } else {
                next_layer[idx] = try allocator.dupe(u8, current_layer[i]);
            }
            idx += 1;
        }

        for (current_layer) |h| allocator.free(h);
        allocator.free(current_layer);
        current_layer = next_layer;
    }

    const zig_computed_merkle_root = current_layer[0];
    defer allocator.free(zig_computed_merkle_root);
    allocator.free(current_layer);

    std.debug.print("✅ Native Zig Independent Merkle Root: {s}\n", .{zig_computed_merkle_root});

    // 3. Read disk hash from Python/system guard via C fopen
    const f = c.fopen(MERKLE_FILE, "r");
    if (f == null) {
        std.debug.print("❌ ZIG VERIFIER FAIL: Unable to open Merkle file at {s}\n", .{MERKLE_FILE});
        std.process.exit(1);
    }
    defer _ = c.fclose(f);

    var buf: [128]u8 = undefined;
    if (c.fgets(&buf, buf.len, f) == null) {
        std.debug.print("❌ ZIG VERIFIER FAIL: Unable to read Merkle file content.\n", .{});
        std.process.exit(1);
    }

    const disk_hash = std.mem.trim(u8, std.mem.span(@as([*:0]u8, @ptrCast(&buf))), " \t\r\n");

    std.debug.print("✅ On-Disk Python/System Merkle Root: {s}\n", .{disk_hash});

    // 4. Compare Zig Native Computation vs On-Disk Python Claim
    if (std.mem.eql(u8, zig_computed_merkle_root, disk_hash)) {
        std.debug.print("\n===========================================================================\n", .{});
        std.debug.print("🎉 DUAL-SUBSTRATE CONSENSUS VERIFIED (ZIG NATIVE == PYTHON GUARD)\n", .{});
        std.debug.print("   Independent codebases agree 100% on lineage sequence & Merkle root!\n", .{});
        std.debug.print("===========================================================================\n\n", .{});
        std.process.exit(0);
    } else {
        std.debug.print("\n❌ DESYNC DETECTED: Zig Native Root ({s}) != Python Disk Claim ({s})\n", .{ zig_computed_merkle_root, disk_hash });
        std.process.exit(1);
    }
}
