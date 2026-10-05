const std = @import("std");

const SWARM_SIZE: usize = 18432;
const ITERATIONS: usize = 10_000;

const Cell128 = extern struct { data: [128]u8 align(128) };
const Cell256 = extern struct { data: [256]u8 align(256) };
const Cell512 = extern struct { data: [512]u8 align(512) };

pub fn main() !void {
    const allocator = std.heap.page_allocator;
    std.debug.print("=== SOVEREIGN BBQ GAUNTLET: CACHE ALIGNMENT (M4) ===\n", .{});

    const swarm128 = try allocator.alloc(Cell128, SWARM_SIZE);
    defer allocator.free(swarm128);
    @memset(std.mem.sliceAsBytes(swarm128), 0);
    
    var start = try std.time.Instant.now();
    for (0..ITERATIONS) |_| {
        for (swarm128) |*cell| {
            for (0..128) |i| cell.data[i] +%= 1;
        }
    }
    var end = try std.time.Instant.now();
    std.debug.print("128-Byte Alignment: {} ns\n", .{end.since(start)});

    const swarm256 = try allocator.alloc(Cell256, SWARM_SIZE);
    defer allocator.free(swarm256);
    @memset(std.mem.sliceAsBytes(swarm256), 0);

    start = try std.time.Instant.now();
    for (0..ITERATIONS) |_| {
        for (swarm256) |*cell| {
            for (0..128) |i| cell.data[i] +%= 1;
        }
    }
    end = try std.time.Instant.now();
    std.debug.print("256-Byte Alignment: {} ns\n", .{end.since(start)});

    const swarm512 = try allocator.alloc(Cell512, SWARM_SIZE);
    defer allocator.free(swarm512);
    @memset(std.mem.sliceAsBytes(swarm512), 0);

    start = try std.time.Instant.now();
    for (0..ITERATIONS) |_| {
        for (swarm512) |*cell| {
            for (0..128) |i| cell.data[i] +%= 1;
        }
    }
    end = try std.time.Instant.now();
    std.debug.print("512-Byte Alignment: {} ns\n", .{end.since(start)});
    std.debug.print("VERDICT: TELEMETRY CAPTURED. PROCEED TO NASA V&V.\n", .{});
}
