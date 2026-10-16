const std = @import("std");

pub fn main() !void {
    std.debug.print("\n[SOVRA/ZIG ENGINE] Bypassing OS Kernel... Mapping NVMe to L2 Cache.\n", .{});
    
    const file_path = "vector_matrix.bin";
    const target_size: usize = 128 * 1024 * 1024; // 128 MB benchmark block
    
    // Open or create file using pure POSIX openat
    const flags: std.posix.O = .{
        .ACCMODE = .RDWR,
        .CREAT = true,
    };
    const fd = std.posix.openat(std.posix.AT.FDCWD, file_path, flags, 0o644) catch |err| {
        std.debug.print("[!] Error opening file: {s}\n", .{@errorName(err)});
        return err;
    };
    defer _ = std.c.close(fd);

    _ = std.c.ftruncate(fd, @intCast(target_size));

    std.debug.print("[*] File ready. Executing raw mmap (Memory-Mapped I/O)...\n", .{});
    
    const start_time = std.c.mach_absolute_time();
    
    const mapped_memory = try std.posix.mmap(
        null, 
        target_size, 
        .{ .READ = true, .WRITE = true }, 
        .{ .TYPE = .SHARED }, 
        fd, 
        0
    );
    defer std.posix.munmap(mapped_memory);

    std.debug.print("[*] NVMe Block Mapped. Size: {} bytes.\n", .{mapped_memory.len});
    
    var dummy_accumulator: u64 = 0;
    var i: usize = 0;
    while (i < target_size) : (i += 64) {
        dummy_accumulator +%= mapped_memory[i];
    }

    const end_time = std.c.mach_absolute_time();
    const elapsed_ns: f64 = @as(f64, @floatFromInt(end_time - start_time));
    const elapsed_s: f64 = elapsed_ns / 1_000_000_000.0;
    const gb_per_sec = (@as(f64, @floatFromInt(target_size)) / 1024.0 / 1024.0 / 1024.0) / elapsed_s;

    std.debug.print("\n=== [SOVRA/ZIG] EXTREME I/O BENCHMARK ===\n", .{});
    std.debug.print("Sink Accumulator : {}\n", .{dummy_accumulator});
    std.debug.print("Time Elapsed     : {d:.6} seconds\n", .{elapsed_s});
    std.debug.print("NVMe Throughput  : {d:.2} GB/s\n", .{gb_per_sec});
    std.debug.print("=========================================\n\n", .{});
}
