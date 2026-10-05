// sovra_zig.zig
const std = @import("std");

// Import the C bridge header for struct definitions
const c = @cImport({
    @cInclude("../labs/workspaces/sovra_lang/context_bridge_engine.c");
});

// Exported wrappers matching the original C ABI
export fn sovra_init_context_bridge() c_int {
    return c.sovra_init_context_bridge();
}

export fn sovra_process_intake_signal(candidate: *const c.sovra_candidate_signal_t, decision: *c.sovra_certified_decision_t) c_int {
    return c.sovra_process_intake_signal(candidate, decision);
}

export fn sovra_register_session(session_id: u64) c_int {
    return c.sovra_register_session(session_id);
}

export fn sovra_verify_simd_hash(payload: *const u8, len: usize, expected_hi: u64, expected_lo: u64) c_int {
    return c.sovra_verify_simd_hash(payload, len, expected_hi, expected_lo);
}

export fn sovra_get_lattice_tag(ptr: *const c_void) u32 {
    return c.sovra_get_lattice_tag(ptr);
}

export fn sovra_check_cross_session_replay(session_id: u64, hash_hi: u64, hash_lo: u64, pointer_session_id: u64, pointer_node_id: u64) c_int {
    return c.sovra_check_cross_session_replay(session_id, hash_hi, hash_lo, pointer_session_id, pointer_node_id);
}
