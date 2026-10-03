const std = @import("std");

const SWARM_SIZE: u64 = 25_000_000;

pub fn main() !void {
    var assimilated: u64 = 0;
    var slashed: u64 = 0;

    var i: u64 = 0;
    while (i < SWARM_SIZE) : (i += 1) {
        if (i % 100 < 15) {
            slashed += 1;
        } else {
            assimilated += 1;
        }
    }

    std.debug.print("Assimilated: {d}\nSlashed: {d}\n", .{assimilated, slashed});
}
