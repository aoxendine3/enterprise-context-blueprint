// Calibrated Zig 0.16 18,432-D Hexological Vector Engine Benchmark
// Substrate: Apple Silicon M4 Bare Metal (ARM64 SIMD)

const std = @import("std");

const c = @cImport({
    @cInclude("time.h");
});

const DIM: usize = 18432;
const LANES: usize = 4;
const NUM_CORES: usize = 10;
const TOTAL_VECTORS: usize = 100000;
const ITERATIONS: usize = 50;

var g_volatile_sink: f64 = 0.0;

fn get_time_sec() f64 {
    var ts: c.struct_timespec = undefined;
    _ = c.clock_gettime(c.CLOCK_MONOTONIC, &ts);
    return @as(f64, @floatFromInt(ts.tv_sec)) + @as(f64, @floatFromInt(ts.tv_nsec)) / 1e9;
}

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

const WorkerContext = struct {
    query: []const f32,
    targets: []const f32,
    count: usize,
    sum: *f64,
};

fn worker_fn(ctx: WorkerContext) void {
    const query = ctx.query;
    const targets = ctx.targets;
    const count = ctx.count;

    var local_sum: f64 = 0.0;
    var i: usize = 0;
    while (i < count) : (i += 1) {
        const offset = i * DIM;
        const target = targets[offset .. offset + DIM];
        const dot = zig_18432d_dot_product(query, target);
        local_sum += dot;
    }
    ctx.sum.* = local_sum;
}

pub fn main() !void {
    const allocator = std.heap.page_allocator;

    const query_vec = try allocator.alloc(f32, DIM);
    defer allocator.free(query_vec);

    const target_matrix = try allocator.alloc(f32, TOTAL_VECTORS * DIM);
    defer allocator.free(target_matrix);

    for (query_vec, 0..) |*val, idx| {
        val.* = @as(f32, @floatFromInt(idx % 100)) * 0.001;
    }
    for (target_matrix, 0..) |*val, idx| {
        val.* = @as(f32, @floatFromInt((idx + 1) % 100)) * 0.001;
    }

    const vecs_per_core = TOTAL_VECTORS / NUM_CORES;
    var threads: [NUM_CORES]std.Thread = undefined;
    var thread_sums: [NUM_CORES]f64 = undefined;

    // 1. Warmup Pass (10 passes)
    var warm: usize = 0;
    while (warm < 10) : (warm += 1) {
        var t: usize = 0;
        while (t < NUM_CORES) : (t += 1) {
            const count = if (t == NUM_CORES - 1) (TOTAL_VECTORS - t * vecs_per_core) else vecs_per_core;
            const start_idx = t * vecs_per_core;

            const ctx = WorkerContext{
                .query = query_vec,
                .targets = target_matrix[start_idx * DIM .. (start_idx + count) * DIM],
                .count = count,
                .sum = &thread_sums[t],
            };

            threads[t] = try std.Thread.spawn(.{}, worker_fn, .{ctx});
        }
        for (&threads) |*thread| {
            thread.join();
        }
    }

    // 2. Timed Iterations
    var sample_latencies_ms: [ITERATIONS]f64 = undefined;
    const t_start_all = get_time_sec();

    var iter: usize = 0;
    while (iter < ITERATIONS) : (iter += 1) {
        const iter_start = get_time_sec();

        var t: usize = 0;
        while (t < NUM_CORES) : (t += 1) {
            const count = if (t == NUM_CORES - 1) (TOTAL_VECTORS - t * vecs_per_core) else vecs_per_core;
            const start_idx = t * vecs_per_core;

            const ctx = WorkerContext{
                .query = query_vec,
                .targets = target_matrix[start_idx * DIM .. (start_idx + count) * DIM],
                .count = count,
                .sum = &thread_sums[t],
            };

            threads[t] = try std.Thread.spawn(.{}, worker_fn, .{ctx});
        }

        for (&threads) |*thread| {
            thread.join();
        }

        for (thread_sums) |s| {
            g_volatile_sink += s;
        }

        const iter_end = get_time_sec();
        sample_latencies_ms[iter] = (iter_end - iter_start) * 1000.0;
    }

    const total_elapsed_sec = get_time_sec() - t_start_all;
    const avg_pass_sec = total_elapsed_sec / @as(f64, @floatFromInt(ITERATIONS));
    const avg_pass_ms = avg_pass_sec * 1000.0;

    const ops_sec = @as(f64, @floatFromInt(TOTAL_VECTORS)) / avg_pass_sec;
    const gflops = (@as(f64, @floatFromInt(TOTAL_VECTORS)) * @as(f64, @floatFromInt(DIM)) * 2.0) / (avg_pass_sec * 1e9);
    const gb_sec = ((@as(f64, @floatFromInt(TOTAL_VECTORS)) * @as(f64, @floatFromInt(DIM)) * 4.0) / (1024.0 * 1024.0 * 1024.0)) / avg_pass_sec;

    std.mem.sort(f64, &sample_latencies_ms, {}, std.sort.asc(f64));
    const p50_pass_ms = sample_latencies_ms[@as(usize, @intFromFloat(@as(f64, @floatFromInt(ITERATIONS)) * 0.50))];
    const p90_pass_ms = sample_latencies_ms[@as(usize, @intFromFloat(@as(f64, @floatFromInt(ITERATIONS)) * 0.90))];
    const p99_pass_ms = sample_latencies_ms[@as(usize, @intFromFloat(@as(f64, @floatFromInt(ITERATIONS)) * 0.99))];

    const p50_vec_us = (p50_pass_ms * 1000.0) / @as(f64, @floatFromInt(TOTAL_VECTORS));
    const p90_vec_us = (p90_pass_ms * 1000.0) / @as(f64, @floatFromInt(TOTAL_VECTORS));
    const p99_vec_us = (p99_pass_ms * 1000.0) / @as(f64, @floatFromInt(TOTAL_VECTORS));

    std.debug.print(
        \\{{
        \\  "language": "Zig 0.16 (ReleaseFast)",
        \\  "avg_pass_ms": {d:.2},
        \\  "evals_per_sec": {d:.0},
        \\  "gflops": {d:.2},
        \\  "bandwidth_gb_sec": {d:.2},
        \\  "p50_us": {d:.2},
        \\  "p90_us": {d:.2},
        \\  "p99_us": {d:.2},
        \\  "sink_check": {d:.2}
        \\}}
        \\
    , .{ avg_pass_ms, ops_sec, gflops, gb_sec, p50_vec_us, p90_vec_us, p99_vec_us, g_volatile_sink });
}
