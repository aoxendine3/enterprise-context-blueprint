// workspaces/capability_graph/build.zig
// Build script for Capability Graph – Zig 0.13 idiomatic.

const std = @import("std");

pub fn build(b: *std.Build) void {
    const mode = b.standardOptimizeOption(.{});
    const lib = b.addStaticLibrary(.{
        .name = "capability_graph",
        .root_source_file = b.path("../capability_graph.zig"),
        .target = b.standardTargetOptions(.{}),
        .optimize = mode,
    });
    lib.install();
    const run_cmd = b.addRunArtifact(lib);
    run_cmd.step.dependOn(b.getInstallStep());
    b.default_step.dependOn(&run_cmd.step);
}
