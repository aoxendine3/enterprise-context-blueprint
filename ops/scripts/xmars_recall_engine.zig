const std = @import("std");

pub fn main() !void {
    const parent_hash = "hash_seed_456";
    const score_str = "98.4";

    var hash: [std.crypto.hash.sha2.Sha256.digest_length]u8 = undefined;
    var hasher = std.crypto.hash.sha2.Sha256.init(.{});
    hasher.update(parent_hash);
    hasher.update(score_str);
    hasher.final(&hash);

    const hex_charset = "0123456789abcdef";
    var hex_hash: [64]u8 = undefined;
    for (hash, 0..) |b, i| {
        hex_hash[i * 2] = hex_charset[b >> 4];
        hex_hash[i * 2 + 1] = hex_charset[b & 15];
    }

    std.debug.print("BEGIN;\n", .{});
    std.debug.print("INSERT INTO memory_nodes (node_hash, node_type, parent_hashes, payload_data) VALUES ('{s}', 'RECALL_VERIFICATION', '{s}', '{{\"accuracy_score\": {s}}}');\n", .{hex_hash, parent_hash, score_str});
    std.debug.print("INSERT INTO memory_edges (parent_hash, child_hash) VALUES ('{s}', '{s}');\n", .{parent_hash, hex_hash});
    std.debug.print("COMMIT;\n", .{});
}
