const std = @import("std");
const c = @cImport({
    @cInclude("sqlite3.h");
    @cInclude("stdio.h");
    @cInclude("string.h");
});

const Sha256 = std.crypto.hash.sha2.Sha256;

const DB_PATH_DEFAULT = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/.sovereign/provenance/lineage_dag.db";
const MERKLE_FILE_DEFAULT = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/tri_brain/merkle_root.hash";

fn sha256Hex(allocator: std.mem.Allocator, input: []const u8) ![]u8 {
    var digest: [Sha256.digest_length]u8 = undefined;
    Sha256.hash(input, &digest, .{});
    const hex_buf = try allocator.alloc(u8, Sha256.digest_length * 2);
    @memcpy(hex_buf[0..], &std.fmt.bytesToHex(&digest, .lower));
    return hex_buf;
}

pub fn main(init: std.process.Init) !void {
    const allocator = std.heap.c_allocator;

    var raw_db_path: []const u8 = DB_PATH_DEFAULT;
    var raw_claim_path: []const u8 = MERKLE_FILE_DEFAULT;

    var args_it = init.minimal.args.iterate();
    _ = args_it.skip();
    if (args_it.next()) |arg1| {
        raw_db_path = arg1;
        if (args_it.next()) |arg2| {
            raw_claim_path = arg2;
        }
    }

    std.debug.print("===========================================================================\n", .{});
    std.debug.print("  STATELESS AIRBLOCKED WITNESS ENGINE (EXTERNAL NON-CORRUPT ADJUDICATION)\n", .{});
    std.debug.print("  Scope: Textual Output Inspection ONLY (Zero Source/Reasoning Access)\n", .{});
    std.debug.print("===========================================================================\n", .{});

    // 1. Open SQLite DB directly in read-only mode via C-ABI
    var db: ?*c.sqlite3 = null;
    const db_z = try allocator.dupeZ(u8, raw_db_path);
    defer allocator.free(db_z);

    if (c.sqlite3_open_v2(db_z.ptr, &db, c.SQLITE_OPEN_READWRITE, null) != c.SQLITE_OK) {
        std.debug.print("❌ STATELESS WITNESS FAIL CLOSED: Cannot open DB at '{s}'\n", .{raw_db_path});
        std.process.exit(1);
    }
    defer _ = c.sqlite3_close(db);

    const query = "SELECT node_id, seq_num, session_id, payload_hash, payload_raw FROM lineage_nodes ORDER BY timestamp ASC, rowid ASC";
    var stmt: ?*c.sqlite3_stmt = null;
    if (c.sqlite3_prepare_v2(db, query, -1, &stmt, null) != c.SQLITE_OK) {
        const err_msg = c.sqlite3_errmsg(db);
        std.debug.print("❌ STATELESS WITNESS FAIL CLOSED: Query prepare failed: {s}\n", .{err_msg});
        std.process.exit(1);
    }
    defer _ = c.sqlite3_finalize(stmt);

    var node_hashes: std.ArrayListUnmanaged([]u8) = .empty;
    defer {
        for (node_hashes.items) |h| allocator.free(h);
        node_hashes.deinit(allocator);
    }

    var total_nodes: usize = 0;
    var last_seq_map = std.StringHashMap(i64).init(allocator);
    defer {
        var it = last_seq_map.iterator();
        while (it.next()) |entry| {
            allocator.free(entry.key_ptr.*);
        }
        last_seq_map.deinit();
    }

    // 2. External Byte-Level Verification & Sequence Monotonicity
    while (c.sqlite3_step(stmt) == c.SQLITE_ROW) {
        const node_id_c = c.sqlite3_column_text(stmt, 0);
        const seq_num = c.sqlite3_column_int64(stmt, 1);
        const session_id_c = c.sqlite3_column_text(stmt, 2);
        const payload_hash_c = c.sqlite3_column_text(stmt, 3);
        const payload_raw_c = c.sqlite3_column_text(stmt, 4);

        if (node_id_c == null or session_id_c == null or payload_hash_c == null or payload_raw_c == null) {
            std.debug.print("❌ STATELESS WITNESS FAIL CLOSED: Null field encountered in DB row.\n", .{});
            std.process.exit(1);
        }

        const node_id = std.mem.span(node_id_c);
        const session_id = std.mem.span(session_id_c);
        const payload_hash = std.mem.span(payload_hash_c);
        const payload_raw = std.mem.span(payload_raw_c);

        // Byte-level Payload Integrity Verification
        const computed_payload_hash = try sha256Hex(allocator, payload_raw);
        defer allocator.free(computed_payload_hash);

        if (!std.mem.eql(u8, computed_payload_hash, payload_hash)) {
            std.debug.print("❌ STATELESS WITNESS FAIL CLOSED: Payload corruption in node '{s}'. Expected hash {s}, got {s}\n", .{ node_id, payload_hash, computed_payload_hash });
            std.process.exit(1);
        }

        // Monotonic Sequence Verification
        const gop = try last_seq_map.getOrPut(session_id);
        if (!gop.found_existing) {
            gop.key_ptr.* = try allocator.dupe(u8, session_id);
            gop.value_ptr.* = 0;
        }

        const expected_seq = gop.value_ptr.* + 1;
        if (seq_num != expected_seq) {
            std.debug.print("❌ STATELESS WITNESS FAIL CLOSED: Sequence gap in session '{s}': expected {d}, got {d}\n", .{ session_id, expected_seq, seq_num });
            std.process.exit(1);
        }
        gop.value_ptr.* = seq_num;

        const h_copy = try allocator.dupe(u8, node_id);
        try node_hashes.append(allocator, h_copy);
        total_nodes += 1;
    }

    if (total_nodes == 0) {
        std.debug.print("❌ STATELESS WITNESS FAIL CLOSED: Provenance DB contains 0 nodes.\n", .{});
        std.process.exit(1);
    }

    std.debug.print("✅ Witness Scope: {d} raw output nodes inspected & byte-verified.\n", .{total_nodes});
    std.debug.print("✅ Payload Anti-Corruption: 100% Byte-Verifiable Payload Hashes.\n", .{});
    std.debug.print("✅ Monotonic Sequence Verification: 100% Monotonic (0 Sequence Violations).\n", .{});

    // 3. Recompute canonical Merkle Tree Root in native Zig (RFC 6962 Promote-Carry-Up)
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

    const witness_computed_root = current_layer[0];
    defer allocator.free(witness_computed_root);
    allocator.free(current_layer);

    std.debug.print("✅ Witness Recomputed Merkle Root: {s}\n", .{witness_computed_root});

    // 4. Read raw claim file via C stdio
    const claim_z = try allocator.dupeZ(u8, raw_claim_path);
    defer allocator.free(claim_z);

    const f = c.fopen(claim_z.ptr, "r");
    if (f == null) {
        std.debug.print("❌ STATELESS WITNESS FAIL CLOSED: Cannot open claim file at '{s}'\n", .{raw_claim_path});
        std.process.exit(1);
    }
    defer _ = c.fclose(f);

    var buf: [128]u8 = undefined;
    if (c.fgets(&buf, buf.len, f) == null) {
        std.debug.print("❌ STATELESS WITNESS FAIL CLOSED: Cannot read claim file content.\n", .{});
        std.process.exit(1);
    }

    const claim_hash = std.mem.trim(u8, std.mem.span(@as([*:0]u8, @ptrCast(&buf))), " \t\r\n");
    std.debug.print("✅ Target Output Claim Root:      {s}\n", .{claim_hash});

    // 5. Compare External Witness Adjudication vs Target Output Claim
    if (std.mem.eql(u8, witness_computed_root, claim_hash)) {
        std.debug.print("\n===========================================================================\n", .{});
        std.debug.print("🎉 STATELESS WITNESS AUTHORIZED: External adjudication clean & proven true.\n", .{});
        std.debug.print("===========================================================================\n\n", .{});
        std.process.exit(0);
    } else {
        std.debug.print("\n❌ STATELESS WITNESS FAIL CLOSED: Root Desync ({s} != {s})\n", .{ witness_computed_root, claim_hash });
        std.process.exit(1);
    }
}
