// workspaces/policy_daemon/policy_daemon.zig
// Anthony's Policy Daemon – idiomatic Zig 0.16
// High-performance decision engine without heap allocation at decision time.
// Decision enum is binary: Allow or Deny. Legacy Python integration yields Deny.

const std = @import("std");

const c = @cImport({
    @cInclude("unistd.h");
});

pub const Decision = enum { Allow, Deny };

pub fn decide(attestation_hash: ?[]const u8) Decision {
    // Zero heap allocation: pattern match on optional
    if (attestation_hash) |hash| {
        if (hash.len > 0) return Decision.Allow else return Decision.Deny;
    } else {
        return Decision.Deny;
    }
}

// Simple REPL for manual testing (zero heap allocation, direct POSIX IO)
pub fn main() !void {
    var buf: [256]u8 = undefined;
    while (true) {
        const bytes_read = c.read(0, &buf, buf.len);
        if (bytes_read <= 0) break;
        var len: usize = @intCast(bytes_read);
        while (len > 0 and (buf[len - 1] == '\n' or buf[len - 1] == '\r')) {
            len -= 1;
        }
        const line = buf[0..len];
        const decision = decide(if (line.len == 0) null else line);
        const out: []const u8 = switch (decision) {
            .Allow => "ALLOW\n",
            .Deny => "DENY\n",
        };
        _ = c.write(1, out.ptr, out.len);
    }
}

test "deny_legacy_python_no_attestation" {
    const decision = decide(null);
    try std.testing.expect(decision == Decision.Deny);
}

test "allow_attested_asset" {
    const hash = "somehash";
    const decision = decide(hash);
    try std.testing.expect(decision == Decision.Allow);
}
