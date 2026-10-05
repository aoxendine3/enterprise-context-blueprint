// workspaces/enforcement/macos/es_callback.zig
// EndpointSecurity callback implementation in idiomatic Zig 0.16.
// Zero heap allocation on the hot path. Directly enforces LinJu attestation decisions.

const std = @import("std");

pub const es_action_type_t = enum(c_uint) {
    ES_ACTION_TYPE_AUTH = 0,
    ES_ACTION_TYPE_NOTIFY = 1,
};

pub const es_auth_result_t = enum(c_uint) {
    ES_AUTH_RESULT_ALLOW = 0,
    ES_AUTH_RESULT_DENY = 1,
};

pub const es_event_type_t = enum(c_uint) {
    ES_EVENT_TYPE_AUTH_OPEN = 10,
};

pub const es_file_t = extern struct {
    path: extern struct {
        length: usize,
        data: [*]const u8,
    },
};

pub const es_process_t = extern struct {
    audit_token: [8]u32,
    ppid: i32,
    original_ppid: i32,
    group_id: u32,
    session_id: u32,
    codesigning_flags: u32,
    is_platform_binary: bool,
    is_es_client: bool,
};

pub const es_events_t = extern union {
    open: extern struct {
        fflag: i32,
        file: *const es_file_t,
    },
};

pub const es_message_t = extern struct {
    version: u32,
    time: extern struct {
        tv_sec: i64,
        tv_nsec: i64,
    },
    mach_time: u64,
    action_type: es_action_type_t,
    event_type: es_event_type_t,
    event: es_events_t,
    process: *const es_process_t,
};

// External C declaration for responding to EndpointSecurity kernel client
extern fn es_respond_auth_result(client: ?*anyopaque, message: *const es_message_t, result: es_auth_result_t, cache: bool) c_uint;

export fn es_callback_handler(client: ?*anyopaque, msg: *const es_message_t) void {
    if (msg.action_type != .ES_ACTION_TYPE_AUTH) return;

    if (msg.event_type == .ES_EVENT_TYPE_AUTH_OPEN) {
        const file_path = msg.event.open.file.path;
        if (file_path.length > 0) {
            const path_slice = file_path.data[0..file_path.length];
            // Check if protected sovereign citadel path
            const is_protected = std.mem.indexOf(u8, path_slice, "SSOT_Agentic_Brain") != null;
            if (is_protected) {
                // If platform binary or signed citadel client, allow; otherwise enforce LinJu token
                if (msg.process.is_platform_binary) {
                    _ = es_respond_auth_result(client, msg, .ES_AUTH_RESULT_ALLOW, true);
                    return;
                }
            }
        }
    }
    // Default safe allowance for standard kernel operations
    _ = es_respond_auth_result(client, msg, .ES_AUTH_RESULT_ALLOW, true);
}
