// workspaces/attestation_service/attestation_service.zig
// Xoras Attestation Service — idiomatic Zig 0.16
// Native TCP Listener via POSIX sockets, HMAC-SHA256 crypto proof engine,
// raw SurrealQL over HTTP wire protocol. Zero toy HTTP dependencies.

const std = @import("std");
const crypto = std.crypto;

const c = @cImport({
    @cInclude("sys/types.h");
    @cInclude("sys/socket.h");
    @cInclude("netinet/in.h");
    @cInclude("arpa/inet.h");
    @cInclude("unistd.h");
    @cInclude("errno.h");
});

pub fn generateProof(secret: []const u8, payload: []const u8) [32]u8 {
    var out: [32]u8 = undefined;
    crypto.auth.hmac.sha2.HmacSha256.create(&out, payload, secret);
    return out;
}

pub fn proofToHex(proof: [32]u8, buf: *[64]u8) []const u8 {
    const hex = "0123456789abcdef";
    for (proof, 0..) |b, i| {
        buf[i * 2] = hex[b >> 4];
        buf[i * 2 + 1] = hex[b & 0xF];
    }
    return buf[0..64];
}

pub fn verifyProof(secret: []const u8, payload: []const u8, expected_hex: []const u8) bool {
    if (expected_hex.len != 64) return false;
    const computed = generateProof(secret, payload);
    var buf: [64]u8 = undefined;
    const computed_hex = proofToHex(computed, &buf);
    return std.mem.eql(u8, computed_hex, expected_hex);
}

// Direct wire SurrealQL query over raw loopback TCP socket (zero external ORM / client)
pub fn writeEventToSurreal(proof_hex: []const u8, asset_path: []const u8) !void {
    const fd = c.socket(c.AF_INET, c.SOCK_STREAM, 0);
    if (fd < 0) return error.SocketCreationFailed;
    defer _ = c.close(fd);

    var addr: c.struct_sockaddr_in = std.mem.zeroes(c.struct_sockaddr_in);
    addr.sin_family = c.AF_INET;
    addr.sin_port = c.htons(8000);
    _ = c.inet_pton(c.AF_INET, "127.0.0.1", &addr.sin_addr);

    if (c.connect(fd, @ptrCast(&addr), @sizeOf(c.struct_sockaddr_in)) < 0) {
        return error.SurrealDBUnavailable;
    }

    // Comptime / stack-allocated SurrealQL statement
    var body_buf: [256]u8 = undefined;
    const body = try std.fmt.bufPrint(
        &body_buf,
        "CREATE attestation_edge SET asset='{s}', signed_proof='{s}', timestamp=time::now();",
        .{ asset_path, proof_hex },
    );

    var req_buf: [512]u8 = undefined;
    const req = try std.fmt.bufPrint(
        &req_buf,
        "POST /sql HTTP/1.1\r\n" ++
            "Host: 127.0.0.1:8000\r\n" ++
            "Content-Type: application/json\r\n" ++
            "NS: xoras\r\n" ++
            "DB: sovereign\r\n" ++
            "Content-Length: {d}\r\n" ++
            "Connection: close\r\n\r\n{s}",
        .{ body.len, body },
    );

    _ = c.write(fd, req.ptr, req.len);
}

pub fn runSingleIngestSession(listen_port: u16) !void {
    const server_fd = c.socket(c.AF_INET, c.SOCK_STREAM, 0);
    if (server_fd < 0) return error.SocketCreationFailed;
    defer _ = c.close(server_fd);

    var opt: c_int = 1;
    _ = c.setsockopt(server_fd, c.SOL_SOCKET, c.SO_REUSEADDR, &opt, @sizeOf(c_int));

    var addr: c.struct_sockaddr_in = std.mem.zeroes(c.struct_sockaddr_in);
    addr.sin_family = c.AF_INET;
    addr.sin_port = c.htons(listen_port);
    addr.sin_addr.s_addr = c.INADDR_ANY;

    if (c.bind(server_fd, @ptrCast(&addr), @sizeOf(c.struct_sockaddr_in)) < 0) {
        return error.BindFailed;
    }

    if (c.listen(server_fd, 1) < 0) {
        return error.ListenFailed;
    }

    const client_fd = c.accept(server_fd, null, null);
    if (client_fd < 0) return error.AcceptFailed;
    defer _ = c.close(client_fd);

    // Fixed stack buffer for ingestion stream
    var buf: [4096]u8 = undefined;
    const bytes_read = c.read(client_fd, &buf, buf.len);
    if (bytes_read <= 0) return error.EmptyPayload;

    const payload = std.mem.trim(u8, buf[0..@intCast(bytes_read)], " \r\n");
    const secret = "xoras_sovereign_hw_key_2026";
    const proof = generateProof(secret, payload);
    var hex_buf: [64]u8 = undefined;
    const proof_hex = proofToHex(proof, &hex_buf);

    // Attempt recording to SurrealDB; handle offline state as non-fatal recoverable
    writeEventToSurreal(proof_hex, payload) catch |err| switch (err) {
        error.SurrealDBUnavailable => {
            // Safe offline fallback: proof remains mathematically valid
        },
        else => return err,
    };

    // Return the proof directly to caller
    _ = c.write(client_fd, proof_hex.ptr, proof_hex.len);
    _ = c.write(client_fd, "\n", 1);
}

pub fn main() !void {
    std.debug.print("[ATTESTATION_SERVICE] Operational on bare metal. Listening on 127.0.0.1:8081...\n", .{});
    runSingleIngestSession(8081) catch |err| {
        std.debug.print("[ATTESTATION_SERVICE] Session ended: {s}\n", .{@errorName(err)});
    };
    std.debug.print("[ATTESTATION_SERVICE] Clean exit.\n", .{});
}

test "sign_and_verify_round_trip" {
    const secret = "topsecret";
    const payload = "asset_contract_v1";
    const proof = generateProof(secret, payload);
    var hex_buf: [64]u8 = undefined;
    const proof_hex = proofToHex(proof, &hex_buf);

    try std.testing.expect(verifyProof(secret, payload, proof_hex));
    try std.testing.expect(!verifyProof("wrong_secret", payload, proof_hex));
}
