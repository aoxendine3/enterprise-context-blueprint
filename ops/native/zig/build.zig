const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{
        .preferred_optimize_mode = .ReleaseFast,
    });

    const lib = b.addSharedLibrary(.{
        .name = "sovra_simd",
        .root_module = b.createModule(.{
            .root_source_file = b.path("sovra_simd.zig"),
            .target = target,
            .optimize = optimize,
        }),
    });

    b.installArtifact(lib);
}
