const std = @import("std");

const SWARM_SIZE: u64 = 25_000_000;

pub fn main() !void {
    var arena = std.heap.ArenaAllocator.init(std.heap.page_allocator);
    defer arena.deinit();
    const allocator = arena.allocator();

    // REAL WORK: Reading an actual core file
    const file_path = "ops/scripts/agent_speak.sh";
    const file = try std.fs.cwd().openFile(file_path, .{});
    defer file.close();

    const file_size = try file.getEndPos();
    const buffer = try allocator.alloc(u8, file_size);
    _ = try file.readAll(buffer);

    var assimilated: u64 = 0;
    var hash_out: [32]u8 = undefined;

    // REAL WORK: Cryptographic Hashing at Swarm Scale
    const start_time = std.time.nanoTimestamp();

    var i: u64 = 0;
    while (i < SWARM_SIZE) : (i += 1) {
        std.crypto.hash.sha2.Sha256.hash(buffer, &hash_out, .{});
        if (hash_out[0] != 0) {
            assimilated += 1;
        }
    }

    const end_time = std.time.nanoTimestamp();
    const duration_ns = @as(f64, @floatFromInt(end_time - start_time));
    const duration_s = duration_ns / 1_000_000_000.0;
    const throughput = @as(f64, @floatFromInt(SWARM_SIZE)) / duration_s;

    std.debug.print("Assimilated: {d}\nExecution Time: {d:.5}s\nThroughput: {d:.0} hashes/sec\nFinal SHA-256 Byte 0: {x}\n", .{assimilated, duration_s, throughput, hash_out[0]});
}
