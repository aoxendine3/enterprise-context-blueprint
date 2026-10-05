const std = @import("std");

const SWARM_SIZE: usize = 1_000_000;
const TRUE_CFD_MASS: f64 = 12444.89;
const FAKE_BYZANTINE_MASS: f64 = 3.14159; // Coordinated attack vector

const AgentNode = struct {
    id: u32,
    proposed_mass: f64,
};

pub fn main() !void {
    var arena = std.heap.ArenaAllocator.init(std.heap.page_allocator);
    defer arena.deinit();
    const allocator = arena.allocator();
    
    var args = try std.process.argsWithAllocator(allocator);
    _ = args.skip();
    const rate_str = args.next() orelse "0.33";
    const byzantine_rate = try std.fmt.parseFloat(f32, rate_str);
    
    std.debug.print("=================================================================\n", .{});
    std.debug.print("XORAS BYZANTINE CORRUPTION TEST: {d:.0}% ADVERSARIAL LOAD\n", .{byzantine_rate * 100.0});
    std.debug.print("=================================================================\n", .{});
    
    var swarm = try allocator.alloc(AgentNode, SWARM_SIZE);
    var lcg_state: u64 = 999;
    
    var byzantine_count: u32 = 0;
    var honest_count: u32 = 0;
    
    for (0..SWARM_SIZE) |i| {
        lcg_state = lcg_state *% 6364136223846793005 +% 1442695040888963407;
        const rand_val = @as(f32, @floatFromInt(@as(u32, @intCast(lcg_state >> 32)))) / 4294967295.0;
        
        if (rand_val < byzantine_rate) {
            // Adversaries act as a coordinated Sybil attack
            swarm[i] = .{ .id = @as(u32, @intCast(i)), .proposed_mass = FAKE_BYZANTINE_MASS };
            byzantine_count += 1;
        } else {
            swarm[i] = .{ .id = @as(u32, @intCast(i)), .proposed_mass = TRUE_CFD_MASS };
            honest_count += 1;
        }
    }
    
    std.debug.print("-> Honest Nodes: {}\n", .{honest_count});
    std.debug.print("-> Coordinated Adversaries: {}\n", .{byzantine_count});
    
    var vote_map = std.AutoHashMap(u64, u32).init(allocator);
    var max_votes: u32 = 0;
    var consensus_mass_bits: u64 = 0;
    
    for (0..SWARM_SIZE) |i| {
        const mass_bits = @as(u64, @bitCast(swarm[i].proposed_mass));
        const res = try vote_map.getOrPut(mass_bits);
        if (!res.found_existing) {
            res.value_ptr.* = 1;
        } else {
            res.value_ptr.* += 1;
        }
        
        if (res.value_ptr.* > max_votes) {
            max_votes = res.value_ptr.*;
            consensus_mass_bits = mass_bits;
        }
    }
    
    const consensus_mass = @as(f64, @bitCast(consensus_mass_bits));
    const consensus_ratio = (@as(f32, @floatFromInt(max_votes)) / @as(f32, @floatFromInt(SWARM_SIZE))) * 100.0;
    
    std.debug.print("-> Final Network Agreement: {d:.2}%\n", .{consensus_ratio});
    std.debug.print("-> Certified Physical Mass: {d:.5}\n", .{consensus_mass});
    
    if (consensus_mass == TRUE_CFD_MASS and consensus_ratio > 66.0) {
        std.debug.print("[VERDICT] 0xBEAF. Absolute Integrity. Supermajority Secured.\n\n", .{});
    } else if (consensus_mass == TRUE_CFD_MASS and consensus_ratio > 50.0) {
        std.debug.print("[VERDICT] WARNING. Supermajority lost, but honest nodes hold the plurality.\n\n", .{});
    } else if (consensus_mass == FAKE_BYZANTINE_MASS) {
        std.debug.print("[VERDICT] 0xDEAD. FATAL COMPROMISE. The adversarial payload was certified as truth.\n\n", .{});
    }
}
