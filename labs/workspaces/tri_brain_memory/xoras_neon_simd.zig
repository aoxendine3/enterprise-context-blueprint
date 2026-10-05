// workspaces/tri_brain_memory/xoras_neon_simd.zig
// Bare-Metal Apple Silicon M4 NEON Vector Engine in Zig 0.16
// Zero-Heap, Hardware Vectorized 768-D Dot Product, Cosine Similarity, and Cache-Line Folding.

const std = @import("std");

pub const EMBEDDING_DIM: usize = 768;
pub const SIMD_LANES: usize = 4; // 128-bit NEON register holds 4 x 32-bit floats
pub const Vec4f = @Vector(SIMD_LANES, f32);
pub const Vec16u8 = @Vector(16, u8);

// 1. Hardware-Vectorized Dot Product for 768-D Embeddings
pub fn dotProduct768(a: *const [EMBEDDING_DIM]f32, b: *const [EMBEDDING_DIM]f32) f32 {
    comptime std.debug.assert(EMBEDDING_DIM % (SIMD_LANES * 4) == 0);

    var acc0: Vec4f = @splat(0.0);
    var acc1: Vec4f = @splat(0.0);
    var acc2: Vec4f = @splat(0.0);
    var acc3: Vec4f = @splat(0.0);

    comptime var offset: usize = 0;
    inline while (offset < EMBEDDING_DIM) : (offset += SIMD_LANES * 4) {
        const va0: Vec4f = a[offset .. offset + 4].*;
        const vb0: Vec4f = b[offset .. offset + 4].*;
        acc0 += va0 * vb0;

        const va1: Vec4f = a[offset + 4 .. offset + 8].*;
        const vb1: Vec4f = b[offset + 4 .. offset + 8].*;
        acc1 += va1 * vb1;

        const va2: Vec4f = a[offset + 8 .. offset + 12].*;
        const vb2: Vec4f = b[offset + 8 .. offset + 12].*;
        acc2 += va2 * vb2;

        const va3: Vec4f = a[offset + 12 .. offset + 16].*;
        const vb3: Vec4f = b[offset + 12 .. offset + 16].*;
        acc3 += va3 * vb3;
    }

    const total_acc = acc0 + acc1 + acc2 + acc3;
    return @reduce(.Add, total_acc);
}

// 2. Hardware-Vectorized L2 Norm
pub fn l2Norm768(a: *const [EMBEDDING_DIM]f32) f32 {
    const sum_sq = dotProduct768(a, a);
    return @sqrt(sum_sq);
}

// 3. Hardware-Vectorized Cosine Similarity
pub fn cosineSimilarity768(a: *const [EMBEDDING_DIM]f32, b: *const [EMBEDDING_DIM]f32) f32 {
    const dot = dotProduct768(a, b);
    const norm_a = l2Norm768(a);
    const norm_b = l2Norm768(b);
    const denom = norm_a * norm_b;
    if (denom <= 1e-12) return 0.0;
    return dot / denom;
}

// 4. Hardware-Vectorized 128-Byte Cache-Line Parity Hash
// Folds a 128-byte M4 cache-line down to 16 bytes via 8 parallel 128-bit vector XOR steps
pub fn parityFold128(line: *const [128]u8) [16]u8 {
    var v: Vec16u8 = line[0..16].*;
    comptime var i: usize = 16;
    inline while (i < 128) : (i += 16) {
        const next_v: Vec16u8 = line[i .. i + 16].*;
        v ^= next_v;
    }
    return @as([16]u8, v);
}

// Baseline Scalar Dot Product for Verification & Benchmarking
pub fn scalarDotProduct768(a: *const [EMBEDDING_DIM]f32, b: *const [EMBEDDING_DIM]f32) f32 {
    var sum: f32 = 0.0;
    for (0..EMBEDDING_DIM) |i| {
        sum += a[i] * b[i];
    }
    return sum;
}

// Direct ARM64 cycle counter
inline fn getHwCycles() u64 {
    var val: u64 = 0;
    asm volatile ("mrs %[val], cntvct_el0" : [val] "=r" (val));
    return val;
}

pub fn main() !void {
    const iterations: usize = 200_000;
    var vec_a: [EMBEDDING_DIM]f32 align(128) = undefined;
    var vec_b: [EMBEDDING_DIM]f32 align(128) = undefined;

    // Deterministic test data initialization
    for (0..EMBEDDING_DIM) |i| {
        const fi: f32 = @floatFromInt(i);
        vec_a[i] = @sin(fi * 0.01);
        vec_b[i] = @cos(fi * 0.01);
    }

    // Warmup
    _ = dotProduct768(&vec_a, &vec_b);
    _ = scalarDotProduct768(&vec_a, &vec_b);

    // 1. Benchmark Scalar Dot Product
    const t0 = getHwCycles();
    var scalar_res: f32 = 0.0;
    var it: usize = 0;
    while (it < iterations) : (it += 1) {
        scalar_res += scalarDotProduct768(&vec_a, &vec_b);
        std.mem.doNotOptimizeAway(&scalar_res);
    }
    const t1 = getHwCycles();

    // 2. Benchmark NEON Vector Dot Product
    const t2 = getHwCycles();
    var simd_res: f32 = 0.0;
    it = 0;
    while (it < iterations) : (it += 1) {
        simd_res += dotProduct768(&vec_a, &vec_b);
        std.mem.doNotOptimizeAway(&simd_res);
    }
    const t3 = getHwCycles();

    const scalar_cycles = t1 - t0;
    const simd_cycles = t3 - t2;

    // Convert cycles to nanoseconds (24 MHz on Apple Silicon = 41.6667 ns/cycle)
    const scalar_ns_per_op = (@as(f64, @floatFromInt(scalar_cycles)) * (1000.0 / 24.0)) / @as(f64, @floatFromInt(iterations));
    const simd_ns_per_op = (@as(f64, @floatFromInt(simd_cycles)) * (1000.0 / 24.0)) / @as(f64, @floatFromInt(iterations));
    const speedup = scalar_ns_per_op / simd_ns_per_op;

    // 3. Cache-line Parity Fold Benchmark
    var cache_line: [128]u8 align(128) = undefined;
    for (0..128) |i| cache_line[i] = @intCast(i & 0xFF);

    const t4 = getHwCycles();
    var hash_acc: u8 = 0;
    it = 0;
    while (it < iterations) : (it += 1) {
        const h = parityFold128(&cache_line);
        hash_acc ^= h[0];
        std.mem.doNotOptimizeAway(&hash_acc);
    }
    const t5 = getHwCycles();
    const fold_cycles = t5 - t4;
    const fold_ns_per_op = (@as(f64, @floatFromInt(fold_cycles)) * (1000.0 / 24.0)) / @as(f64, @floatFromInt(iterations));

    std.debug.print(
        "\n============================================================\n" ++
            "  XORAS BARE-METAL ZIG 0.16 APPLE SILICON M4 SIMD BENCHMARK\n" ++
            "============================================================\n" ++
            "Hardware: Apple Silicon M4 (ARM64 NEON)\n" ++
            "Vector Dimension: 768-D Single Precision (f32)\n" ++
            "Total Iterations: {d}\n\n" ++
            "--- 768-D Dot Product Performance ---\n" ++
            "  Scalar Execution Latency:    {d:.2} ns/op\n" ++
            "  NEON SIMD Vector Latency:    {d:.2} ns/op\n" ++
            "  Hardware Vector Speedup:     {d:.2}x faster\n" ++
            "  SIMD Throughput:             {d:.0} vectors/sec\n\n" ++
            "--- 128-Byte Cache-Line Vector Parity Fold ---\n" ++
            "  NEON Fold Latency:           {d:.2} ns/line\n" ++
            "  Fold Throughput:             {d:.0} lines/sec\n" ++
            "============================================================\n\n",
        .{
            iterations,
            scalar_ns_per_op,
            simd_ns_per_op,
            speedup,
            (1_000_000_000.0 / simd_ns_per_op),
            fold_ns_per_op,
            (1_000_000_000.0 / fold_ns_per_op),
        },
    );
}

test "simd_matches_scalar" {
    var a: [EMBEDDING_DIM]f32 align(128) = undefined;
    var b: [EMBEDDING_DIM]f32 align(128) = undefined;
    for (0..EMBEDDING_DIM) |i| {
        a[i] = @floatFromInt(i);
        b[i] = @floatFromInt(EMBEDDING_DIM - i);
    }
    const scalar = scalarDotProduct768(&a, &b);
    const simd = dotProduct768(&a, &b);
    try std.testing.expectApproxEqRel(scalar, simd, 1e-4);
}

test "cosine_similarity_bounds" {
    var a: [EMBEDDING_DIM]f32 align(128) = undefined;
    for (0..EMBEDDING_DIM) |i| a[i] = 1.0;
    // Cosine similarity of a vector with itself must be 1.0
    const sim = cosineSimilarity768(&a, &a);
    try std.testing.expectApproxEqAbs(@as(f32, 1.0), sim, 1e-5);
}
