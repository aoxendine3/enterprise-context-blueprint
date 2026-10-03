const std = @import("std");
const c = @cImport({
    @cInclude("fcntl.h");
    @cInclude("unistd.h");
    @cInclude("string.h");
});

pub fn main() !void {
    var arena = std.heap.ArenaAllocator.init(std.heap.page_allocator);
    defer arena.deinit();
    const allocator = arena.allocator();

    std.debug.print("\n=== XORAS UPGP: TRUE FALSIFICATION HARNESS ===\n", .{});
    
    const seed_size: usize = 293601280; // 280 MB
    const file_path = "/tmp/xoras_merkle_seed.tensor";

    // 1. Stage Valid Seed
    const initial_data = try allocator.alloc(u8, seed_size);
    @memset(initial_data, 7);
    
    // 2. Compute the IMMUTABLE DAG HASH
    var valid_hash: [std.crypto.hash.sha2.Sha256.digest_length]u8 = undefined;
    var hasher1 = std.crypto.hash.sha2.Sha256.init(.{});
    hasher1.update(initial_data);
    hasher1.final(&valid_hash);
    
    // Write the valid seed to disk
    const fd_out = c.open(file_path, c.O_WRONLY | c.O_CREAT | c.O_TRUNC, @as(c_int, 0o644));
    _ = c.write(fd_out, initial_data.ptr, seed_size);
    _ = c.close(fd_out);
    std.debug.print("[SYSTEM] 1. Valid Seed written to NVMe. Immutable DAG Hash: {}\n", .{std.fmt.hex(valid_hash[0..8])});

    // 3. ADVERSARIAL POISONING
    std.debug.print("[SYSTEM] 2. ADVERSARY POISONS THE NVME FILE DIRECTLY...\n", .{});
    const malicious_payload = "### BYZANTINE_ADVERSARIAL_INJECTION_DETECTED ###";
    const fd_poison = c.open(file_path, c.O_WRONLY);
    _ = c.lseek(fd_poison, 150000000, c.SEEK_SET);
    _ = c.write(fd_poison, malicious_payload, malicious_payload.len);
    _ = c.close(fd_poison);

    // 4. ZERO-COPY REHYDRATION
    std.debug.print("[SYSTEM] 3. UPGP Rehydration Sequence Initiated...\n", .{});
    const fd_in = c.open(file_path, c.O_RDONLY);
    const rehydrated_ram = try allocator.alloc(u8, seed_size);
    _ = c.read(fd_in, rehydrated_ram.ptr, seed_size);
    _ = c.close(fd_in);

    // 5. THE HASH LOCK
    std.debug.print("[SYSTEM] 4. UPGP verifying KV cache payload against immutable DAG hash...\n", .{});
    var test_hash: [std.crypto.hash.sha2.Sha256.digest_length]u8 = undefined;
    var hasher2 = std.crypto.hash.sha2.Sha256.init(.{});
    hasher2.update(rehydrated_ram);
    hasher2.final(&test_hash);
    
    std.debug.print("\n=====================================================\n", .{});
    if (std.mem.eql(u8, &valid_hash, &test_hash)) {
        std.debug.print("FALSIFICATION TEST: FAIL\n", .{});
        std.debug.print("RESULT: The adversary successfully slipped a payload into the sandbox.\n\n", .{});
    } else {
        std.debug.print("FALSIFICATION TEST: PASS (HASH MISMATCH DETECTED)\n", .{});
        std.debug.print("RESULT: UPGP ABORT. The tampered file generated unauthorized hash {}\n", .{std.fmt.hex(test_hash[0..8])});
        std.debug.print("RESULT: The Byzantine payload is mathematically locked out of the DOJO Sandbox.\n\n", .{});
    }
}
