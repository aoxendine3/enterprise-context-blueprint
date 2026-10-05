// SPDX-License-Identifier: MIT
// XORAS Swarm Simulation for CFD Grid (PBFT shard mock)
// This is a bare‑metal Zig prototype that demonstrates the
// sharding of a 2D fluid grid across many consensus nodes.
// Each cell is owned by a "shard" consisting of NODES_PER_SHARD agents.
// The simulation performs a single Red‑Black Gauss‑Seidel iteration
// while exchanging ghost cells between neighboring shards.

const std = @import("std");

const GRID_SIZE: usize = 8; // 8x8 physical cells (for demo)
const NODES_PER_SHARD: usize = 5; // mock PBFT participants per cell
const ITERATIONS: usize = 3;

fn ix(x: usize, y: usize) usize {
    return x + (GRID_SIZE + 2) * y;
}

const Shard = struct {
    // State for a single grid cell (scalar field)
    value: f32,
    // Mock consensus log (just a counter)
    consensus_step: usize,
    pub fn init(val: f32) Shard {
        return Shard{ .value = val, .consensus_step = 0 };
    }
    // Simulate a PBFT consensus round – we just increment a counter
    pub fn consensus(self: *Shard) void {
        // In a real implementation this would run the three‑phase
        // pre‑prepare, prepare, commit algorithm across NODES_PER_SHARD.
        // Here we simply sleep a tiny random amount to emulate network.
        const rand = std.crypto.random.uintLessThan(u32, 100_000);
        // Convert random integer to a fractional millisecond delay (up to 0.1 ms)
        const delay_f64: f64 = @floatFromInt(u32, rand) * 1e-6;
        const delay_ns: u64 = @intFromFloat(u64, delay_f64 * 1_000_000_000.0);
        std.time.sleep(delay_ns);
        self.consensus_step += 1;
    }
};

pub fn main() !void {
    var arena = std.heap.ArenaAllocator.init(std.heap.page_allocator);
    defer arena.deinit();
    const allocator = arena.allocator();

    // Allocate grid of shards (including ghost border)
    const total_cells = (GRID_SIZE + 2) * (GRID_SIZE + 2);
    var shards = try allocator.alloc(Shard, total_cells);
    defer allocator.free(shards);

    // Initialise interior cells with a simple pattern, ghosts = 0
    for (0..total_cells) |i| {
        shards[i] = Shard.init(0.0);
    }
    for (1..GRID_SIZE+1) |x| {
        for (1..GRID_SIZE+1) |y| {
            shards[idx].value = @floatFromInt(f32, x * y);
        }
    }

    const stdout = std.io.getStdOut().writer();
    try stdout.print("=== XORAS Swarm Simulation ===\n", .{});
    try stdout.print("Grid {d}×{d}, {d} nodes per shard, {d} iterations\n\n", .{GRID_SIZE, GRID_SIZE, NODES_PER_SHARD, ITERATIONS});

    // Red‑Black Gauss‑Seidel with mock PBFT consensus
    for (0..ITERATIONS) |iter| {
        // Phase 1: Red cells (x+y even)
        for (1..GRID_SIZE+1) |x| {
            for (1..GRID_SIZE+1) |y| {
                if ((x + y) % 2 != 0) continue; // red
                const idx = ix(x, y);
                // Consensus step for the owning shard
                shards[idx].consensus();
                // Simple averaging with 4‑neighbour ghosts
                const up = shards[ix(x, y-1)].value;
                const down = shards[ix(x, y+1)].value;
                const left = shards[ix(x-1, y)].value;
                const right = shards[ix(x+1, y)].value;
                shards[idx].value = (up + down + left + right) * 0.25;
            }
        }
        // Phase 2: Black cells (x+y odd)
        for (1..GRID_SIZE+1) |x| {
            for (1..GRID_SIZE+1) |y| {
                if ((x + y) % 2 == 0) continue; // black
                const idx = ix(x, y);
                shards[idx].consensus();
                const up = shards[ix(x, y-1)].value;
                const down = shards[ix(x, y+1)].value;
                const left = shards[ix(x-1, y)].value;
                const right = shards[ix(x+1, y)].value;
                shards[idx].value = (up + down + left + right) * 0.25;
            }
        }
        // Simple verification: compute max value
        var max_val: f32 = 0.0;
        for (1..GRID_SIZE+1) |x| {
            for (1..GRID_SIZE+1) |y| {
                const v = shards[ix(x, y)].value;
                if (v > max_val) max_val = v;
            }
        }
        try stdout.print("Iteration {d}: max cell value = {d:.6}\n", .{ iter+1, max_val });
    }
    try stdout.print("\nSimulation complete. Each shard performed {d} consensus rounds per iteration.\n", .{ITERATIONS});
}
