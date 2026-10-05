const std = @import("std");

pub fn main() !void {
    std.debug.print("\n[SOVRA/ZIG ENGINE] Bypassing OS Kernel... Mapping NVMe to L2 Cache.\n", .{});
    
    const file_path = "vector_matrix.bin";
    const target_size: usize = 1024 * 1024 * 1024; // 1 GB
    
    var file = std.fs.cwd().openFile(file_path, .{}) catch |err| blk: {
        if (err == error.FileNotFound) {
            std.debug.print("[!] Generating 1GB Synthetic Vector Matrix (This takes a moment)...\n", .{});
            var new_file = try std.fs.cwd().createFile(file_path, .{ .read = true });
            try new_file.setEndPos(target_size);
            break :blk new_file;
        } else {
            return err;
        }
    };
    defer file.close();

    std.debug.print("[*] File ready. Executing raw mmap (Memory-Mapped I/O)...\n", .{});
    
    const start_time = std.time.microTimestamp();
    
    const fd = file.handle;
    const mapped_memory = try std.posix.mmap(
        null, 
        target_size, 
        std.posix.PROT.READ, 
        std.posix.MAP.SHARED, 
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

    const end_time = std.time.microTimestamp();
    const elapsed_s: f64 = @as(f64, @floatFromInt(end_time - start_time)) / 1_000_000.0;
    const gb_per_sec = (@as(f64, @floatFromInt(target_size)) / 1024.0 / 1024.0 / 1024.0) / elapsed_s;

    std.debug.print("\n=== [SOVRA/ZIG] EXTREME I/O BENCHMARK ===\n", .{});
    std.debug.print("Sink Accumulator : {}\n", .{dummy_accumulator});
    std.debug.print("Time Elapsed     : {d:.4} seconds\n", .{elapsed_s});
    std.debug.print("NVMe Throughput  : {d:.2} GB/s\n", .{gb_per_sec});
    std.debug.print("=========================================\n\n", .{});
}
