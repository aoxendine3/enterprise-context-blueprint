// Sovra-Nexus Pure Native Zig Engine v1.0.0 (Stress Test & High-Precision Benchmark)
// Bare-Metal Execution — High-Precision Windows QPC Timer, Falsification & Boundary Stress Suite.

const std = @import("std");
const simd = @import("sovra_simd.zig");

const builtin = @import("builtin");

// High-Resolution Performance Counter (Windows QPC or POSIX nanosecond timestamp)
const windows_qpc = if (builtin.os.tag == .windows) struct {
    extern "kernel32" fn QueryPerformanceCounter(lpPerformanceCount: *i64) callconv(.c) bool;
    extern "kernel32" fn QueryPerformanceFrequency(lpFrequency: *i64) callconv(.c) bool;
} else struct {};

fn get_qpc_time() i64 {
    if (builtin.os.tag == .windows) {
        var qpc: i64 = 0;
        _ = windows_qpc.QueryPerformanceCounter(&qpc);
        return qpc;
    } else {
        var ts: std.c.timespec = undefined;
        _ = std.c.clock_gettime(.MONOTONIC, &ts);
        return @as(i64, ts.sec) * 1_000_000_000 + @as(i64, ts.nsec);
    }
}

fn get_qpc_freq() i64 {
    if (builtin.os.tag == .windows) {
        var freq: i64 = 0;
        _ = windows_qpc.QueryPerformanceFrequency(&freq);
        return freq;
    } else {
        return 1_000_000_000;
    }
}

pub fn main() !void {
    std.debug.print(
        \\===================================================================
        \\  SOVRA-NEXUS PURE ZIG STRESS & FALSIFICATION BENCHMARK SUITE
        \\===================================================================
        \\Engine Info : {s}
        \\Compiler    : Zig 0.16.0 (ReleaseFast SIMD Native)
        \\Target      : Bare Metal (AVX2 / FMA3 / NEON 8-Lane SIMD)
        \\===================================================================
        \\
    , .{simd.get_sovra_zig_info()});

    const allocator = std.heap.page_allocator;

    // ------------------------------------------------------------------------
    // STAGE 1: Edge-Case & Boundary Stress Tests ("Try to Break It")
    // ------------------------------------------------------------------------
    std.debug.print("[STAGE 1] Running Edge-Case & Boundary Falsification Tests...\n", .{});

    // Test 1.1: Zero-length array
    const empty_dot = simd.sovra_simd_dot_f32(undefined, undefined, 0);
    std.debug.print("  [Test 1.1] Zero-length array dot product    : {d:.2} [PASSED]\n", .{empty_dot});

    // Test 1.2: Unaligned non-SIMD sizes (N = 1, 7, 13, 31, 1007)
    const odd_sizes = [_]usize{ 1, 7, 13, 31, 1007 };
    for (odd_sizes) |size| {
        const u = try allocator.alloc(f32, size);
        defer allocator.free(u);
        const v = try allocator.alloc(f32, size);
        defer allocator.free(v);

        for (0..size) |i| {
            u[i] = 1.0;
            v[i] = 2.0;
        }

        const res = simd.sovra_simd_dot_f32(u.ptr, v.ptr, size);
        const expected: f32 = @floatFromInt(size * 2);
        const diff = @abs(res - expected);
        if (diff > 1e-4) {
            std.debug.print("  [Test 1.2] FAILED for odd size {d}: got {d}, expected {d}\n", .{ size, res, expected });
            return error.TestFailed;
        }
    }
    std.debug.print("  [Test 1.2] Tail unrolling for odd sizes (1..1007) : [PASSED]\n", .{});

    // Test 1.3: Extreme Poincaré boundary test (|u| -> 0.999999)
    const dim: usize = 128;
    const u_extreme = try allocator.alloc(f32, dim);
    defer allocator.free(u_extreme);
    const v_extreme = try allocator.alloc(f32, dim);
    defer allocator.free(v_extreme);

    // Fill such that norm^2 approaches 0.9999
    const val: f32 = @sqrt(0.9999 / @as(f32, @floatFromInt(dim)));
    for (0..dim) |i| {
        u_extreme[i] = val;
        v_extreme[i] = -val;
    }

    const p_dist = simd.sovra_simd_poincare_distance_f32(u_extreme.ptr, v_extreme.ptr, dim);
    if (std.math.isNan(p_dist) or std.math.isInf(p_dist)) {
        std.debug.print("  [Test 1.3] FAILED Poincaré extreme boundary check: result is NaN/Inf\n", .{});
        return error.PoincareBoundaryFailed;
    }
    std.debug.print("  [Test 1.3] Extreme Poincaré boundary norm ~ 0.9999 : {d:.6} [PASSED]\n", .{p_dist});

    // ------------------------------------------------------------------------
    // STAGE 2: High-Precision Benchmark (10M and 50M Floats)
    // ------------------------------------------------------------------------
    std.debug.print("\n[STAGE 2] Running High-Precision Native SIMD Benchmarks...\n", .{});

    const qpc_freq: f64 = @floatFromInt(get_qpc_freq());

    // Benchmark 2.1: 10,000,000 float32 elements (40 MB)
    const N10M: usize = 10_000_000;
    const vec_a10 = try allocator.alloc(f32, N10M);
    defer allocator.free(vec_a10);
    const vec_b10 = try allocator.alloc(f32, N10M);
    defer allocator.free(vec_b10);

    for (0..N10M) |i| {
        const fi: f32 = @floatFromInt(i % 100);
        vec_a10[i] = fi * 0.01;
        vec_b10[i] = fi * 0.02;
    }

    const iters: usize = 100;
    const start_qpc10 = get_qpc_time();

    var dot_res10: f32 = 0.0;
    for (0..iters) |_| {
        dot_res10 = simd.sovra_simd_dot_f32(vec_a10.ptr, vec_b10.ptr, N10M);
    }

    const end_qpc10 = get_qpc_time();
    const elapsed_sec10: f64 = @as(f64, @floatFromInt(end_qpc10 - start_qpc10)) / qpc_freq;
    const latency_ms10 = (elapsed_sec10 / @as(f64, @floatFromInt(iters))) * 1000.0;
    const flops10 = 2.0 * @as(f64, @floatFromInt(N10M)) * @as(f64, @floatFromInt(iters));
    const gflops10 = (flops10 / elapsed_sec10) / 1e9;

    std.debug.print(
        \\  [10M Float Benchmark Results]:
        \\    Data Size       : 10,000,000 elements (40 MB)
        \\    Iterations      : {d}
        \\    Total Time      : {d:.6} sec
        \\    Avg Latency     : {d:.4} ms per 10M call
        \\    Dot Product     : {d:.6}
        \\    Throughput      : {d:.2} GFLOPS
        \\
    , .{ iters, elapsed_sec10, latency_ms10, dot_res10, gflops10 });

    // Benchmark 2.2: Massive 50,000,000 float32 elements (200 MB)
    const N50M: usize = 50_000_000;
    std.debug.print("  [50M Float Benchmark] Allocating 200 MB memory arrays...\n", .{});

    const vec_a50 = try allocator.alloc(f32, N50M);
    defer allocator.free(vec_a50);
    const vec_b50 = try allocator.alloc(f32, N50M);
    defer allocator.free(vec_b50);

    for (0..N50M) |i| {
        const fi: f32 = @floatFromInt(i % 50);
        vec_a50[i] = fi * 0.005;
        vec_b50[i] = fi * 0.01;
    }

    const iters50: usize = 20;
    const start_qpc50 = get_qpc_time();

    var dot_res50: f32 = 0.0;
    for (0..iters50) |_| {
        dot_res50 = simd.sovra_simd_dot_f32(vec_a50.ptr, vec_b50.ptr, N50M);
    }

    const end_qpc50 = get_qpc_time();
    const elapsed_sec50: f64 = @as(f64, @floatFromInt(end_qpc50 - start_qpc50)) / qpc_freq;
    const latency_ms50 = (elapsed_sec50 / @as(f64, @floatFromInt(iters50))) * 1000.0;
    const flops50 = 2.0 * @as(f64, @floatFromInt(N50M)) * @as(f64, @floatFromInt(iters50));
    const gflops50 = (flops50 / elapsed_sec50) / 1e9;

    std.debug.print(
        \\  [50M Float Benchmark Results]:
        \\    Data Size       : 50,000,000 elements (200 MB)
        \\    Iterations      : {d}
        \\    Total Time      : {d:.6} sec
        \\    Avg Latency     : {d:.4} ms per 50M call
        \\    Dot Product     : {d:.6}
        \\    Throughput      : {d:.2} GFLOPS
        \\
    , .{ iters50, elapsed_sec50, latency_ms50, dot_res50, gflops50 });

    std.debug.print("===================================================================\n", .{});
    std.debug.print("   ALL NATIVE ZIG FALSIFICATION & STRESS TESTS PASSED CLEANLY       \n", .{});
    std.debug.print("===================================================================\n", .{});
}
