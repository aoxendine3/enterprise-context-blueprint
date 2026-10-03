const std = @import("std");

const NUM_CELLS: usize = 10_000_000;

pub fn main() !void {
    var arena = std.heap.ArenaAllocator.init(std.heap.page_allocator);
    defer arena.deinit();
    const allocator = arena.allocator();

    std.debug.print("====================================================\n", .{});
    std.debug.print(" XORAS BARE-METAL HEXCELL SCALING BENCHMARK (M4)\n", .{});
    std.debug.print("====================================================\n\n", .{});

    const Cell128 = struct { data: [128]u8, };
    const array_128 = try allocator.alloc(Cell128, NUM_CELLS);
    var timer = try std.time.Timer.start();
    for (array_128) |*cell| {
        cell.data[0] = 0xBE;
        cell.data[127] = 0xAF;
    }
    const elapsed_128 = timer.read();
    const mb_128: f64 = @as(f64, @floatFromInt(NUM_CELLS * 128)) / (1024.0 * 1024.0);
    const sec_128: f64 = @as(f64, @floatFromInt(elapsed_128)) / 1_000_000_000.0;
    std.debug.print("[128-BYTE HEXCELL] Elements: {d} | Memory: {d:.2} MB | Time: {d:.4} s | Throughput: {d:.2} GB/s\n", .{
        NUM_CELLS, mb_128, sec_128, (mb_128 / 1024.0) / sec_128
    });

    const Cell256 = struct { data: [256]u8, };
    const array_256 = try allocator.alloc(Cell256, NUM_CELLS);
    timer.reset();
    for (array_256) |*cell| {
        cell.data[0] = 0xBE;
        cell.data[255] = 0xAF;
    }
    const elapsed_256 = timer.read();
    const mb_256: f64 = @as(f64, @floatFromInt(NUM_CELLS * 256)) / (1024.0 * 1024.0);
    const sec_256: f64 = @as(f64, @floatFromInt(elapsed_256)) / 1_000_000_000.0;
    std.debug.print("[256-BYTE HEXCELL] Elements: {d} | Memory: {d:.2} MB | Time: {d:.4} s | Throughput: {d:.2} GB/s\n", .{
        NUM_CELLS, mb_256, sec_256, (mb_256 / 1024.0) / sec_256
    });

    const Cell512 = struct { data: [512]u8, };
    const array_512 = try allocator.alloc(Cell512, NUM_CELLS);
    timer.reset();
    for (array_512) |*cell| {
        cell.data[0] = 0xBE;
        cell.data[511] = 0xAF;
    }
    const elapsed_512 = timer.read();
    const mb_512: f64 = @as(f64, @floatFromInt(NUM_CELLS * 512)) / (1024.0 * 1024.0);
    const sec_512: f64 = @as(f64, @floatFromInt(elapsed_512)) / 1_000_000_000.0;
    std.debug.print("[512-BYTE HEXCELL] Elements: {d} | Memory: {d:.2} MB | Time: {d:.4} s | Throughput: {d:.2} GB/s\n", .{
        NUM_CELLS, mb_512, sec_512, (mb_512 / 1024.0) / sec_512
    });
}
