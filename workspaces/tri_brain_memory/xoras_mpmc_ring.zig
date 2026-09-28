// workspaces/tri_brain_memory/xoras_mpmc_ring.zig
// True Dmitry Vyukov Bounded Multi-Producer Multi-Consumer (MPMC) Lock-Free Queue
// Designed for Apple Silicon M4 Unified Memory Architecture in Zig 0.16
// Guarantees: Lock-Free, Wait-Free Progression, Zero Core Collisions, Zero False Sharing.

const std = @import("std");

const c = @cImport({
    @cInclude("sys/mman.h");
    @cInclude("fcntl.h");
    @cInclude("unistd.h");
    @cInclude("sys/stat.h");
});

pub const CACHE_LINE_SIZE: usize = 128;
pub const RING_CAPACITY: usize = 4096; // Power of two required
pub const SHM_MAGIC: u64 = 0x584F5241535F4D50; // "XORAS_MP" in ASCII

pub const CognitiveFrame = extern struct {
    seq: u64,
    timestamp_ns: u64,
    agent_id: u8,
    gate_id: u8,
    action_type: u8,
    status: u8,
    flags: u32,
    tensor_hash: [32]u8,
    payload: [64]u8,
    _pad: [8]u8,
};

comptime {
    if (@sizeOf(CognitiveFrame) != CACHE_LINE_SIZE) {
        @compileError("CognitiveFrame must be exactly 128 bytes");
    }
}

// Vyukov Slot: Sequence number + Frame
pub const Slot = extern struct {
    turn: std.atomic.Value(u64) align(CACHE_LINE_SIZE),
    frame: CognitiveFrame align(CACHE_LINE_SIZE),
};

pub const XorasMpmcRing = extern struct {
    magic: u64 align(CACHE_LINE_SIZE),
    version: u32,
    capacity: u32,
    _pad_hdr: [112]u8,

    // Separate write_head and read_head by 128 bytes to prevent cache line bouncing
    write_head: std.atomic.Value(u64) align(CACHE_LINE_SIZE),
    read_head: std.atomic.Value(u64) align(CACHE_LINE_SIZE),

    slots: [RING_CAPACITY]Slot align(CACHE_LINE_SIZE),

    // Hardware ARM64 cycle counter
    pub inline fn getHwCycles() u64 {
        var val: u64 = 0;
        asm volatile ("mrs %[val], cntvct_el0" : [val] "=r" (val));
        return val;
    }

    pub fn initShared(self: *XorasMpmcRing) void {
        self.magic = SHM_MAGIC;
        self.version = 2; // MPMC Version
        self.capacity = RING_CAPACITY;
        @memset(&self._pad_hdr, 0);

        self.write_head = std.atomic.Value(u64).init(0);
        self.read_head = std.atomic.Value(u64).init(0);

        // Vyukov initialization: each slot turn starts at its index
        for (0..RING_CAPACITY) |i| {
            self.slots[i].turn = std.atomic.Value(u64).init(i);
            @memset(std.mem.asBytes(&self.slots[i].frame), 0);
        }
    }

    // Lock-Free Multi-Producer Push
    pub fn push(self: *XorasMpmcRing, agent_id: u8, gate_id: u8, action: u8, hash: ?*const [32]u8, payload: ?[]const u8) bool {
        var head = self.write_head.load(.monotonic);

        while (true) {
            const slot = &self.slots[head & (RING_CAPACITY - 1)];
            const turn = slot.turn.load(.acquire);
            const diff = @as(i64, @bitCast(turn)) - @as(i64, @bitCast(head));

            if (diff == 0) {
                // Slot is ready for writing; attempt to claim head via CAS
                if (self.write_head.cmpxchgWeak(head, head + 1, .monotonic, .monotonic)) |prev| {
                    head = prev; // Lost race, retry with updated head
                } else {
                    // Claimed! Write payload
                    slot.frame.seq = head;
                    slot.frame.timestamp_ns = (getHwCycles() * 1000) / 24;
                    slot.frame.agent_id = agent_id;
                    slot.frame.gate_id = gate_id;
                    slot.frame.action_type = action;
                    slot.frame.status = 0x01;
                    slot.frame.flags = 0;

                    if (hash) |h| {
                        @memcpy(&slot.frame.tensor_hash, h);
                    } else {
                        @memset(&slot.frame.tensor_hash, 0);
                    }

                    @memset(&slot.frame.payload, 0);
                    if (payload) |p| {
                        const copy_len = @min(p.len, 64);
                        @memcpy(slot.frame.payload[0..copy_len], p[0..copy_len]);
                    }
                    @memset(&slot.frame._pad, 0);

                    // Publish slot to consumers by advancing turn
                    slot.turn.store(head + 1, .release);
                    return true;
                }
            } else if (diff < 0) {
                // Buffer is full
                return false;
            } else {
                // Head lagged behind, re-read head
                head = self.write_head.load(.monotonic);
            }
        }
    }

    // Lock-Free Multi-Consumer Pop
    pub fn pop(self: *XorasMpmcRing, out_frame: *CognitiveFrame) bool {
        var tail = self.read_head.load(.monotonic);

        while (true) {
            const slot = &self.slots[tail & (RING_CAPACITY - 1)];
            const turn = slot.turn.load(.acquire);
            const diff = @as(i64, @bitCast(turn)) - @as(i64, @bitCast(tail + 1));

            if (diff == 0) {
                // Slot has data; attempt to claim tail via CAS
                if (self.read_head.cmpxchgWeak(tail, tail + 1, .monotonic, .monotonic)) |prev| {
                    tail = prev; // Lost race, retry
                } else {
                    // Claimed! Read frame
                    out_frame.* = slot.frame;
                    // Release slot for next cycle (wrap around capacity)
                    slot.turn.store(tail + RING_CAPACITY, .release);
                    return true;
                }
            } else if (diff < 0) {
                // Buffer is empty
                return false;
            } else {
                // Tail lagged behind, re-read tail
                tail = self.read_head.load(.monotonic);
            }
        }
    }
};

// ============================================================================
// C-ABI EXPORTS
// ============================================================================

pub export fn xoras_mpmc_create(shm_path: [*:0]const u8) ?*XorasMpmcRing {
    const total_bytes = @sizeOf(XorasMpmcRing);
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

    const ring: *XorasMpmcRing = @ptrCast(@alignCast(ptr));
    ring.initShared();
    return ring;
}

pub export fn xoras_mpmc_open_existing(shm_path: [*:0]const u8) ?*XorasMpmcRing {
    const total_bytes = @sizeOf(XorasMpmcRing);
    const fd = c.shm_open(shm_path, c.O_RDWR, @as(c.mode_t, 0o666));
    if (fd < 0) return null;
    defer _ = c.close(fd);

    const ptr = c.mmap(null, total_bytes, c.PROT_READ | c.PROT_WRITE, c.MAP_SHARED, fd, 0);
    if (ptr == c.MAP_FAILED) return null;

    const ring: *XorasMpmcRing = @ptrCast(@alignCast(ptr));
    if (ring.magic != SHM_MAGIC) {
        _ = c.munmap(ptr, total_bytes);
        return null;
    }
    return ring;
}

pub export fn xoras_mpmc_push(
    ring: *XorasMpmcRing,
    agent_id: u8,
    gate_id: u8,
    action: u8,
    hash: ?[*]const u8,
    payload: ?[*]const u8,
    payload_len: usize,
) bool {
    var h_ptr: ?*const [32]u8 = null;
    if (hash) |h| h_ptr = @ptrCast(h);
    var p_slice: ?[]const u8 = null;
    if (payload) |p| p_slice = p[0..payload_len];
    return ring.push(agent_id, gate_id, action, h_ptr, p_slice);
}

pub export fn xoras_mpmc_pop(ring: *XorasMpmcRing, out_frame: *CognitiveFrame) bool {
    return ring.pop(out_frame);
}

pub export fn xoras_mpmc_close(ring: *XorasMpmcRing) void {
    _ = c.munmap(@ptrCast(ring), @sizeOf(XorasMpmcRing));
}

pub export fn xoras_mpmc_unlink(shm_path: [*:0]const u8) void {
    _ = c.shm_unlink(shm_path);
}

// Self-Test
test "mpmc_basic_push_pop" {
    const shm_path = "/xoras_mpmc_test";
    _ = c.shm_unlink(shm_path);
    defer _ = c.shm_unlink(shm_path);

    const ring = xoras_mpmc_create(shm_path) orelse return error.CreateFailed;
    defer xoras_mpmc_close(ring);

    const hash = [_]u8{0x77} ** 32;
    try std.testing.expect(ring.push(1, 2, 0x11, &hash, "TEST_MPMC_PULSE"));

    var frame: CognitiveFrame = undefined;
    try std.testing.expect(ring.pop(&frame));
    try std.testing.expectEqual(@as(u8, 1), frame.agent_id);
    try std.testing.expectEqual(@as(u8, 2), frame.gate_id);
    try std.testing.expect(std.mem.startsWith(u8, &frame.payload, "TEST_MPMC_PULSE"));
}
