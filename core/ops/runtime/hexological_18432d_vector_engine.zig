// ops/runtime/hexological_18432d_vector_engine.zig
// Native Zig 18,432-Dimensional Hexological Vectoring Substrate
// Substrate: Apple Silicon M4 Bare Metal (ARM64 SIMD)

const std = @import("std");
const time = std.time;

const DIM: usize = 18432;
const LANES: usize = 4;
const STEPS: usize = DIM / LANES; // 4,608 SIMD steps
const NUM_CORES: usize = 10;
const TOTAL_VECTORS: usize = 100000; // 100,000 18,432-D Nodes (7.37 GB Vector Data)

fn get_time_ns() i128 {
    return time.nanoTimestamp();
}

// ----------------------------------------------------------------------
// NATIVE ZIG 128-BIT SIMD 18,432-D DOT PRODUCT KERNEL
// ----------------------------------------------------------------------
inline fn zig_18432d_dot_product(a: []const f32, b: []const f32) f32 {
    var acc0: @Vector(LANES, f32) = @splat(0.0);
    var acc1: @Vector(LANES, f32) = @splat(0.0);

    var i: usize = 0;
    while (i < DIM) : (i += LANES * 2) {
        const va0: @Vector(LANES, f32) = a[i..][0..LANES].*;
        const vb0: @Vector(LANES, f32) = b[i..][0..LANES].*;
        acc0 += va0 * vb0;

        const va1: @Vector(LANES, f32) = a[i + LANES ..][0..LANES].*;
        const vb1: @Vector(LANES, f32) = b[i + LANES ..][0..LANES].*;
        acc1 += va1 * vb1;
    }

    const sum_vec = acc0 + acc1;
    return @reduce(.Add, sum_vec);
}

// ----------------------------------------------------------------------
// WORKER THREAD FOR 10-CORE PARALLEL ZIG SWEEP
// ----------------------------------------------------------------------
const WorkerContext = struct {
    query: []const f32,
    targets: []const f32,
    count: usize,
    latencies: []f64,
};

fn worker_fn(ctx: WorkerContext) void {
    const query = ctx.query;
    const targets = ctx.targets;
    const count = ctx.count;

    var i: usize = 0;
    while (i < count) : (i += 1) {
        const t0 = get_time_ns();
        const offset = i * DIM;
        const target = targets[offset .. offset + DIM];
        const dot = zig_18432d_dot_product(query, target);
        _ = dot;
        const elapsed_us = @as(f64, @floatFromInt(get_time_ns() - t0)) / 1000.0;
        ctx.latencies[i] = elapsed_us;
    }
}

pub fn main() !void {
    const stdout = std.io.getStdOut().writer();

    try stdout.print("======================================================================\n", .{});
    try stdout.print("  XORAS NATIVE ZIG 18,432-DIMENSIONAL HEXOLOGICAL VECTOR ENGINE\n", .{});
    try stdout.print("  Substrate: Apple Silicon M4 Bare Metal (10 Cores | Native Zig SIMD)\n", .{});
    try stdout.print("======================================================================\n\n", .{});

    try stdout.print("⚡ Allocating %d 18,432-D Hexological Memory Nodes (7.37 GB Vector Data)...\n", .{TOTAL_VECTORS});

    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    const query_vec = try allocator.alloc(f32, DIM);
    defer allocator.free(query_vec);

    const target_matrix = try allocator.alloc(f32, TOTAL_VECTORS * DIM);
    defer allocator.free(target_matrix);

    const all_latencies = try allocator.alloc(f64, TOTAL_VECTORS);
    defer allocator.free(all_latencies);

    // Populate data
    for (query_vec, 0..) |*val, idx| {
        val.* = @as(f32, @floatFromInt(idx % 100)) * 0.001;
    }
    for (target_matrix, 0..) |*val, idx| {
        val.* = @as(f32, @floatFromInt((idx + 1) % 100)) * 0.001;
    }

    try stdout.print("🔥 Launching Native Zig 10-Core Parallel 18,432-D Vector Engine...\n", .{});

    const vecs_per_core = TOTAL_VECTORS / NUM_CORES;
    var threads: [NUM_CORES]std.Thread = undefined;

    const t_start = get_time_ns();

    var t: usize = 0;
    while (t < NUM_CORES) : (t += 1) {
        const count = if (t == NUM_CORES - 1) (TOTAL_VECTORS - t * vecs_per_core) else vecs_per_core;
        const start_idx = t * vecs_per_core;

        const ctx = WorkerContext{
            .query = query_vec,
            .targets = target_matrix[start_idx * DIM .. (start_idx + count) * DIM],
            .count = count,
            .latencies = all_latencies[start_idx .. start_idx + count],
        };

        threads[t] = try std.Thread.spawn(.{}, worker_fn, .{ctx});
    }

    for (&threads) |*thread| {
        thread.join();
    }

    const elapsed_ns = get_time_ns() - t_start;
    const elapsed_ms = @as(f64, @floatFromInt(elapsed_ns)) / 1e6;
    const elapsed_sec = elapsed_ms / 1000.0;

    const ops_sec = @as(f64, @floatFromInt(TOTAL_VECTORS)) / elapsed_sec;
    const gflops = (@as(f64, @floatFromInt(TOTAL_VECTORS)) * @as(f64, @floatFromInt(DIM)) * 2.0) / (elapsed_sec * 1e9);
    const gb_sec = ((@as(f64, @floatFromInt(TOTAL_VECTORS)) * @as(f64, @floatFromInt(DIM)) * 4.0) / (1024.0 * 1024.0 * 1024.0)) / elapsed_sec;

    std.mem.sort(f64, all_latencies, {}, std.sort.asc(f64));
    const p50 = all_latencies[@as(usize, @intFromFloat(@as(f64, @floatFromInt(TOTAL_VECTORS)) * 0.50))];
    const p90 = all_latencies[@as(usize, @intFromFloat(@as(f64, @floatFromInt(TOTAL_VECTORS)) * 0.90))];
    const p99 = all_latencies[@as(usize, @intFromFloat(@as(f64, @floatFromInt(TOTAL_VECTORS)) * 0.99))];

    try stdout.print("\n======================================================================\n", .{});
    try stdout.print("  NATIVE ZIG 18,432-D HEXOLOGICAL VECTORING RESULTS\n", .{});
    try stdout.print("======================================================================\n", .{});
    try stdout.print("   Evaluations Completed : {d} 18,432-D Nodes (7.37 GB Vector Data)\n", .{TOTAL_VECTORS});
    try stdout.print("   Total Execution Time  : {d:.2} ms ({d:.3} sec)\n", .{ elapsed_ms, elapsed_sec });
    try stdout.print("   Vector Throughput     : {d:.0} 18,432-D evaluations/sec\n", .{ops_sec});
    try stdout.print("   Compute Performance   : {d:.2} GFLOPS (Native Zig SIMD @ M4 Bare Metal)\n", .{gflops});
    try stdout.print("   Memory Bandwidth      : {d:.2} GB/s Unified Memory Stream\n", .{gb_sec});
    try stdout.print("   Latency Distribution  : p50 = {d:.2} µs | p90 = {d:.2} µs | p99 = {d:.2} µs\n", .{ p50, p90, p99 });
    try stdout.print("======================================================================\n", .{});
}
