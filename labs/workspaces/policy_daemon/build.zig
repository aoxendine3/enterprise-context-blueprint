// workspaces/policy_daemon/build.zig
// Build script for Policy Daemon – Zig 0.13 idiomatic.

const std = @import("std");

pub fn build(b: *std.Build) void {
    const mode = b.standardOptimizeOption(.{});
    const exe = b.addExecutable(.{
        .name = "policy_daemon",
        .root_source_file = b.path("../policy_daemon.zig"),
        .target = b.standardTargetOptions(.{}),
        .optimize = mode,
    });
    exe.install();
    const run_cmd = b.addRunArtifact(exe);
    run_cmd.step.dependOn(b.getInstallStep());
    b.default_step.dependOn(&run_cmd.step);
}
