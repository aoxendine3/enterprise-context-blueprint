const std = @import("std");
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
        std.debug.print("ERROR: Missing db path\n", .{});
        return 2;
    }
    const db_path = argv[1];

    var db: ?*c.sqlite3 = null;
    if (c.sqlite3_open_v2(db_path, &db, c.SQLITE_OPEN_READONLY, null) != c.SQLITE_OK) {
        const err_msg = c.sqlite3_errmsg(db);
        std.debug.print("SQLITE_OPEN_ERROR: {s}\n", .{err_msg});
        return 10;
    }
    defer _ = c.sqlite3_close(db);

    _ = c.sqlite3_busy_timeout(db, 5000);

    // Explicit read transaction ensures point-in-time snapshot isolation
    if (c.sqlite3_exec(db, "BEGIN DEFERRED;", null, null, null) != c.SQLITE_OK) {
        std.debug.print("SQLITE_BEGIN_ERROR\n", .{});
        return 11;
    }
    defer _ = c.sqlite3_exec(db, "COMMIT;", null, null, null);

    const query = "SELECT node_id FROM lineage_nodes ORDER BY timestamp ASC, rowid ASC;";
    var stmt: ?*c.sqlite3_stmt = null;
    if (c.sqlite3_prepare_v2(db, query, -1, &stmt, null) != c.SQLITE_OK) {
        const err_msg = c.sqlite3_errmsg(db);
        std.debug.print("SQLITE_PREPARE_ERROR: {s}\n", .{err_msg});
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
        std.debug.print("HASH:{s}:COUNT:0\n", .{genesis_empty});
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

    std.debug.print("HASH:{s}:COUNT:{d}\n", .{zig_root, total_nodes});
    return 0;
}
