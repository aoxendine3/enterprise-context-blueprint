const std = @import("std");
const Build = std.Build;

pub fn build(b: *Build) void {
    const mode = b.standardReleaseOptions();
    const lib = b.addSharedLibrary(.{
        .name = "context_bridge",
        .target = b.standardTargetOptions(.{}),
        .optimize = mode,
    });
    // Add the original C source
    lib.addCSourceFile(.{ .file = b.path("../labs/workspaces/sovra_lang/context_bridge_engine.c"), .flags = &.{"-O3", "-fPIC"} });
    // Add the Zig source
    lib.addCSourceFile(.{ .file = b.path("sovra_zig.zig"), .flags = &.{"-O3"} });
    lib.linkLibC();
    lib.install();
}
