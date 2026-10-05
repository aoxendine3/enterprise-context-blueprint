// workspaces/tri_brain_memory/xoras_shm_ring.zig
// Multi-Process POSIX Shared Memory Ring Buffer for Apple Silicon M4
// Bare-Metal Zig 0.16 with Zero-Lock Atomics & C-ABI Dynamic Library Export.

const std = @import("std");

const c = @cImport({
    @cInclude("sys/mman.h");
    @cInclude("fcntl.h");
    @cInclude("unistd.h");
    @cInclude("sys/stat.h");
});

pub const CACHE_LINE_SIZE: usize = 128;
pub const RING_CAPACITY: usize = 4096; // Power of two for mask bitwise indexing
pub const SHM_MAGIC: u64 = 0x584F5241535F5348; // "XORAS_SH" in ASCII

// CognitiveFrame: Exact 128-byte layout (1 full Apple Silicon M4 cache line)
pub const CognitiveFrame = extern struct {
    seq: u64,
    timestamp_ns: u64,
    agent_id: u8,
    gate_id: u8, // 0: Perception, 1: Intent, 2: Concurrency, 3: Verification
    action_type: u8,
    status: u8,
    flags: u32,
    tensor_hash: [32]u8,
    payload: [64]u8,
    _pad: [8]u8, // Padding to guarantee exact 128-byte size
};

comptime {
    if (@sizeOf(CognitiveFrame) != CACHE_LINE_SIZE) {
        @compileError("CognitiveFrame must be exactly 128 bytes to align with M4 cache lines");
    }
}

// Memory-mapped shared memory layout
pub const XorasShmRing = extern struct {
    magic: u64 align(CACHE_LINE_SIZE),
    version: u32,
    capacity: u32,
    _pad_header: [112]u8, // Pads to 128 bytes

    write_head: std.atomic.Value(u64) align(CACHE_LINE_SIZE),
    read_head: std.atomic.Value(u64) align(CACHE_LINE_SIZE),

    frames: [RING_CAPACITY]CognitiveFrame align(CACHE_LINE_SIZE),

    pub fn initShared(self: *XorasShmRing) void {
        self.magic = SHM_MAGIC;
        self.version = 1;
        self.capacity = RING_CAPACITY;
        @memset(&self._pad_header, 0);
        self.write_head = std.atomic.Value(u64).init(0);
        self.read_head = std.atomic.Value(u64).init(0);
        @memset(std.mem.asBytes(&self.frames), 0);
    }

    // Direct hardware ARM64 cycle counter (nanosecond-grade bare-metal clock)
    pub inline fn getHwCycles() u64 {
        var val: u64 = 0;
        asm volatile ("mrs %[val], cntvct_el0" : [val] "=r" (val));
        return val;
    }

    pub fn push(self: *XorasShmRing, agent_id: u8, gate_id: u8, action: u8, hash: ?*const [32]u8, payload: ?[]const u8) bool {
        const head = self.write_head.load(.monotonic);
        const tail = self.read_head.load(.acquire);

        if (head - tail >= RING_CAPACITY) {
            return false; // Ring buffer full (backpressure)
        }

        const idx = head & (RING_CAPACITY - 1);
        var frame = &self.frames[idx];

        frame.seq = head;
        // Convert ARM64 24MHz cycles to approximate nanoseconds
        frame.timestamp_ns = (getHwCycles() * 1000) / 24;
        frame.agent_id = agent_id;
        frame.gate_id = gate_id;
        frame.action_type = action;
        frame.status = 0x01; // Active
        frame.flags = 0;

        if (hash) |h| {
            @memcpy(&frame.tensor_hash, h);
        } else {
            @memset(&frame.tensor_hash, 0);
        }

        @memset(&frame.payload, 0);
        if (payload) |p| {
            const copy_len = @min(p.len, 64);
            @memcpy(frame.payload[0..copy_len], p[0..copy_len]);
        }
        @memset(&frame._pad, 0);

        self.write_head.store(head + 1, .release);
        return true;
    }

    pub fn pop(self: *XorasShmRing, out_frame: *CognitiveFrame) bool {
        const tail = self.read_head.load(.monotonic);
        const head = self.write_head.load(.acquire);

        if (tail >= head) {
            return false; // Empty
        }

        const idx = tail & (RING_CAPACITY - 1);
        out_frame.* = self.frames[idx];
        self.read_head.store(tail + 1, .release);
        return true;
    }

    pub fn peekLatest(self: *XorasShmRing, out_frame: *CognitiveFrame) bool {
        const head = self.write_head.load(.acquire);
        if (head == 0) return false;

        const idx = (head - 1) & (RING_CAPACITY - 1);
        out_frame.* = self.frames[idx];
        return true;
    }
};

comptime {
    // Assert entire shared memory structure size is aligned to 128 bytes
    if (@sizeOf(XorasShmRing) % CACHE_LINE_SIZE != 0) {
        @compileError("XorasShmRing must be a multiple of CACHE_LINE_SIZE");
    }
}

// ============================================================================
// C-ABI EXPORTS FOR DYNAMIC LIBRARY (libxoras_shm.dylib)
// ============================================================================

pub export fn xoras_shm_create(shm_path: [*:0]const u8) ?*XorasShmRing {
    const total_bytes = @sizeOf(XorasShmRing);
    const fd = c.shm_open(shm_path, c.O_CREAT | c.O_RDWR | c.O_TRUNC, @as(c.mode_t, 0o666));
    if (fd < 0) return null;
    defer _ = c.close(fd);

    if (c.ftruncate(fd, @intCast(total_bytes)) != 0) {
        _ = c.shm_unlink(shm_path);
        return null;
    }

    const ptr = c.mmap(null, total_bytes, c.PROT_READ | c.PROT_WRITE, c.MAP_SHARED, fd, 0);
    if (ptr == c.MAP_FAILED) {
        _ = c.shm_unlink(shm_path);
        return null;
    }

    const ring: *XorasShmRing = @ptrCast(@alignCast(ptr));
    ring.initShared();
    return ring;
}

pub export fn xoras_shm_open_existing(shm_path: [*:0]const u8) ?*XorasShmRing {
    const total_bytes = @sizeOf(XorasShmRing);
    const fd = c.shm_open(shm_path, c.O_RDWR, @as(c.mode_t, 0o666));
    if (fd < 0) return null;
    defer _ = c.close(fd);

    const ptr = c.mmap(null, total_bytes, c.PROT_READ | c.PROT_WRITE, c.MAP_SHARED, fd, 0);
    if (ptr == c.MAP_FAILED) return null;

    const ring: *XorasShmRing = @ptrCast(@alignCast(ptr));
    if (ring.magic != SHM_MAGIC) {
        _ = c.munmap(ptr, total_bytes);
        return null;
    }
    return ring;
}

pub export fn xoras_shm_push(
    ring: *XorasShmRing,
    agent_id: u8,
    gate_id: u8,
    action: u8,
    hash: ?[*]const u8,
    payload: ?[*]const u8,
    payload_len: usize,
) bool {
    var h_ptr: ?*const [32]u8 = null;
    if (hash) |h| {
        h_ptr = @ptrCast(h);
    }

    var p_slice: ?[]const u8 = null;
    if (payload) |p| {
        p_slice = p[0..payload_len];
    }

    return ring.push(agent_id, gate_id, action, h_ptr, p_slice);
}

pub export fn xoras_shm_pop(ring: *XorasShmRing, out_frame: *CognitiveFrame) bool {
    return ring.pop(out_frame);
}

pub export fn xoras_shm_peek_latest(ring: *XorasShmRing, out_frame: *CognitiveFrame) bool {
    return ring.peekLatest(out_frame);
}

pub export fn xoras_shm_close(ring: *XorasShmRing) void {
    const total_bytes = @sizeOf(XorasShmRing);
    _ = c.munmap(@ptrCast(ring), total_bytes);
}

pub export fn xoras_shm_unlink(shm_path: [*:0]const u8) void {
    _ = c.shm_unlink(shm_path);
}

// ============================================================================
// STANDALONE BENCHMARK & TEST RUNNER
// ============================================================================

pub fn main() !void {
    const shm_path = "/xoras_tri_brain_bench";
    _ = c.shm_unlink(shm_path);
    defer _ = c.shm_unlink(shm_path);

    const ring = xoras_shm_create(shm_path) orelse {
        std.debug.print("Failed to create shared memory ring\n", .{});
        return;
    };
    defer xoras_shm_close(ring);

    const iterations: usize = 100_000;
    const dummy_hash = [_]u8{0x7A} ** 32;
    const dummy_payload = "GATE_DELIBERATION_TELEMETRY_REFLEX_PULSE_OK";

    var dummy_frame: CognitiveFrame = undefined;

    const t0 = XorasShmRing.getHwCycles();
    var i: usize = 0;
    while (i < iterations) : (i += 1) {
        _ = ring.push(
            @intCast(i % 9), // agent_id (0-8 Lead 9 roster)
            @intCast((i >> 3) % 4), // gate_id (0-3 Reflex Gates)
            0x42, // action
            &dummy_hash,
            dummy_payload,
        );
        _ = ring.pop(&dummy_frame);
    }
    const t1 = XorasShmRing.getHwCycles();

    const total_cycles = t1 - t0;
    const total_ns = (total_cycles * 1000) / 24;
    const ns_per_roundtrip = @as(f64, @floatFromInt(total_ns)) / @as(f64, @floatFromInt(iterations));
    const ops_per_sec = 1_000_000_000.0 / ns_per_roundtrip;

    std.debug.print(
        "\n============================================================\n" ++
            "  XORAS MULTI-PROCESS SHARED MEMORY (POSIX SHM) BENCHMARK\n" ++
            "============================================================\n" ++
            "Memory Substrate: POSIX shm_open + mmap (Shared RAM)\n" ++
            "Total Size of Shm Region: {d} bytes ({d:.2} KiB)\n" ++
            "Ring Capacity: {d} Frames\n" ++
            "Cache Alignment: 128 bytes (Zero False Sharing)\n" ++
            "Total Roundtrips (Push + Pop): {d}\n" ++
            "Total Time: {d} ns\n" ++
            "Latency per Roundtrip: {d:.2} ns\n" ++
            "Throughput: {d:.0} ops/sec\n" ++
            "Heap Allocations: 0 (Pure Zero-Heap Memory-Mapped IPC)\n" ++
            "C-ABI Dynamic Library Export: Ready for Python / Rust FFI\n" ++
            "============================================================\n\n",
        .{
            @sizeOf(XorasShmRing),
            @as(f64, @floatFromInt(@sizeOf(XorasShmRing))) / 1024.0,
            RING_CAPACITY,
            iterations,
            total_ns,
            ns_per_roundtrip,
            ops_per_sec,
        },
    );
}

test "shm_ring_lifecycle" {
    const test_path = "/xoras_shm_test";
    _ = c.shm_unlink(test_path);
    defer _ = c.shm_unlink(test_path);

    const ring = xoras_shm_create(test_path) orelse return error.ShmCreateFailed;
    defer xoras_shm_close(ring);

    const hash = [_]u8{0xEE} ** 32;
    try std.testing.expect(ring.push(3, 1, 0x10, &hash, "TEST_PAYLOAD"));

    var out_frame: CognitiveFrame = undefined;
    try std.testing.expect(ring.pop(&out_frame));
    try std.testing.expectEqual(@as(u8, 3), out_frame.agent_id);
    try std.testing.expectEqual(@as(u8, 1), out_frame.gate_id);
    try std.testing.expectEqual(hash, out_frame.tensor_hash);
    try std.testing.expect(std.mem.startsWith(u8, &out_frame.payload, "TEST_PAYLOAD"));
}
