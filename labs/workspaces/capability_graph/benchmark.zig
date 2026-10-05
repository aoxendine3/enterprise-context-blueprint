// workspaces/capability_graph/benchmark.zig
// Native Zig Bare-Metal Tail Latency & Stress Benchmark
// Direct Apple Silicon M4 Hardware Timer (CNTVCT_EL0 register read — 0 syscall overhead)
// Eliminates Darwin POSIX clock_gettime 1µs quantization artifacts.

const std = @import("std");
const Graph = @import("capability_graph.zig").Graph;
const EdgeInfo = @import("capability_graph.zig").EdgeInfo;

inline fn readArm64Timer() u64 {
    var val: u64 = undefined;
    asm volatile ("mrs %[val], cntvct_el0"
        : [val] "=r" (val),
    );
    return val;
}

inline fn readArm64Freq() u64 {
    var val: u64 = undefined;
    asm volatile ("mrs %[val], cntfrq_el0"
        : [val] "=r" (val),
    );
    return val;
}

fn sortF64(slice: []f64) void {
    std.mem.sort(f64, slice, {}, std.sort.asc(f64));
}

pub fn main() !void {
    std.debug.print("\n=== [XORAS SOVEREIGN BARE-METAL ZIG BENCHMARK: CNTVCT_EL0 HARDWARE REGISTER] ===\n", .{});

    const freq = readArm64Freq();
    const ns_per_tick = 1_000_000_000.0 / @as(f64, @floatFromInt(freq));
    std.debug.print("CPU Timer Frequency: {d} Hz ({d:.2} ns/tick)\n", .{ freq, ns_per_tick });

    const allocator = std.heap.c_allocator;

    var graph = Graph.init(allocator);
    defer graph.deinit();

    // 1. Build a realistic 10,000-node DAG
    const num_nodes: u32 = 10000;
    std.debug.print("[1/3] Constructing {d}-node capability graph...\n", .{num_nodes});
    
    const proof: [64]u8 = [_]u8{0xAA} ** 64;
    var i: u32 = 0;
    while (i < num_nodes - 1) : (i += 1) {
        try graph.addEdge(i, i + 1, proof, @as(i64, @intCast(i)));
    }
    i = 0;
    while (i < num_nodes - 10) : (i += 10) {
        try graph.addEdge(i, i + 7, proof, @as(i64, @intCast(i)));
    }

    // 2. Benchmark O(1) Capability Supersession Lookup (250,000 operations)
    const lookup_ops: usize = 250000;
    std.debug.print("[2/3] Benchmarking O(1) SupersededBy lookup ({d} operations via CNTVCT_EL0)...\n", .{lookup_ops});

    const latencies_ns = try allocator.alloc(f64, lookup_ops);
    defer allocator.free(latencies_ns);

    var op: usize = 0;
    var checksum: usize = 0;

    const t_total_start = readArm64Timer();
    while (op < lookup_ops) : (op += 1) {
        const query_id = @as(u32, @intCast(op % num_nodes));
        const t0 = readArm64Timer();
        const res = graph.supersededBy(query_id);
        const t1 = readArm64Timer();
        
        if (res != null) checksum += 1;
        const tick_delta = t1 - t0;
        latencies_ns[op] = @as(f64, @floatFromInt(tick_delta)) * ns_per_tick;
    }
    const t_total_end = readArm64Timer();
    const total_ticks = t_total_end - t_total_start;
    const total_time_sec = @as(f64, @floatFromInt(total_ticks)) / @as(f64, @floatFromInt(freq));
    const throughput = @as(f64, @floatFromInt(lookup_ops)) / total_time_sec;

    // Calculate percentiles
    sortF64(latencies_ns);
    const p50 = latencies_ns[lookup_ops * 50 / 100];
    const p90 = latencies_ns[lookup_ops * 90 / 100];
    const p95 = latencies_ns[lookup_ops * 95 / 100];
    const p99 = latencies_ns[lookup_ops * 99 / 100];
    const p999 = latencies_ns[lookup_ops * 999 / 1000];
    const max_lat = latencies_ns[lookup_ops - 1];

    std.debug.print("\n--- RESULTS: O(1) CAPABILITY LOOKUP ({d} OPS) ---\n", .{lookup_ops});
    std.debug.print("Total Time:        {d:.4} sec\n", .{total_time_sec});
    std.debug.print("Throughput:        {d:.0} ops/sec\n", .{throughput});
    std.debug.print("p50 Latency:       {d:.2} ns\n", .{p50});
    std.debug.print("p90 Latency:       {d:.2} ns\n", .{p90});
    std.debug.print("p95 Latency:       {d:.2} ns\n", .{p95});
    std.debug.print("p99 Latency:       {d:.2} ns\n", .{p99});
    std.debug.print("p99.9 Latency:     {d:.2} ns\n", .{p999});
    std.debug.print("Max Latency:       {d:.2} ns\n", .{max_lat});
    std.debug.print("Checksum Verified: {d}\n", .{checksum});

    // 3. Benchmark Cycle Detection over 10,000-node graph
    std.debug.print("\n[3/3] Benchmarking DFS Cycle Detection across {d} nodes...\n", .{num_nodes});
    const cycle_start = readArm64Timer();
    const has_cycle = graph.hasCycle();
    const cycle_end = readArm64Timer();
    const cycle_ms = (@as(f64, @floatFromInt(cycle_end - cycle_start)) / @as(f64, @floatFromInt(freq))) * 1000.0;

    std.debug.print("Cycle Detected:    {}\n", .{has_cycle});
    std.debug.print("DFS Scan Latency:  {d:.3} ms\n", .{cycle_ms});
    std.debug.print("===================================================================\n\n", .{});
}
