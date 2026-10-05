// src/lib.rs
#![allow(non_snake_case)]
#![allow(dead_code)]

use std::ffi::c_void;
use std::os::raw::{c_int, c_uint, c_ulonglong};
use std::ptr;
use std::slice;

// Re‑declare the structs with C layout
#[repr(C)]
#[derive(Debug, Copy, Clone)]
pub struct sovra_candidate_signal_t {
    pub tag: c_uint,
    pub flags: c_uint,
    pub signal_id: c_ulonglong,
    pub source_session_id: c_ulonglong,
    pub payload_hash_hi: c_ulonglong,
    pub payload_hash_lo: c_ulonglong,
    pub monotonic_timestamp: c_ulonglong,
    pub seq_num: c_ulonglong,
    pub payload_len: c_uint,
    pub reserved: c_uint,
    pub payload_raw: [u8; 1024],
}

#[repr(C)]
#[derive(Debug, Copy, Clone)]
pub struct sovra_certified_decision_t {
    pub tag: c_uint,
    pub quarantine_flag: c_uint,
    pub decision_id: c_ulonglong,
    pub merkle_root_hi: c_ulonglong,
    pub merkle_root_lo: c_ulonglong,
    pub state_delta_verified: c_uint,
    pub attack_class_code: c_uint,
    pub provenance_pointer: c_ulonglong,
    pub disposition: [i8; 64],
    pub reason: [i8; 256],
}

extern "C" {
    fn sovra_init_context_bridge() -> c_int;
    fn sovra_process_intake_signal(candidate: *const sovra_candidate_signal_t, decision: *mut sovra_certified_decision_t) -> c_int;
    fn sovra_register_session(session_id: c_ulonglong) -> c_int;
    fn sovra_verify_simd_hash(payload: *const u8, len: usize, expected_hi: c_ulonglong, expected_lo: c_ulonglong) -> c_int;
    fn sovra_get_lattice_tag(ptr: *const c_void) -> c_uint;
    fn sovra_check_cross_session_replay(session_id: c_ulonglong, hash_hi: c_ulonglong, hash_lo: c_ulonglong, pointer_session_id: c_ulonglong, pointer_node_id: c_ulonglong) -> c_int;
}

#[no_mangle]
pub extern "C" fn sovra_process_intake_signal_rust(candidate: *const sovra_candidate_signal_t, decision: *mut sovra_certified_decision_t) -> c_int {
    // Call the original C implementation to keep exact semantics.
    unsafe { sovra_process_intake_signal(candidate, decision) }
}

#[no_mangle]
pub extern "C" fn sovra_init_context_bridge_rust() -> c_int {
    unsafe { sovra_init_context_bridge() }
}

#[no_mangle]
pub extern "C" fn sovra_register_session_rust(session_id: c_ulonglong) -> c_int {
    unsafe { sovra_register_session(session_id) }
}

#[no_mangle]
pub extern "C" fn sovra_verify_simd_hash_rust(payload: *const u8, len: usize, expected_hi: c_ulonglong, expected_lo: c_ulonglong) -> c_int {
    unsafe { sovra_verify_simd_hash(payload, len, expected_hi, expected_lo) }
}

#[no_mangle]
pub extern "C" fn sovra_get_lattice_tag_rust(ptr: *const c_void) -> c_uint {
    unsafe { sovra_get_lattice_tag(ptr) }
}

#[no_mangle]
pub extern "C" fn sovra_check_cross_session_replay_rust(session_id: c_ulonglong, hash_hi: c_ulonglong, hash_lo: c_ulonglong, pointer_session_id: c_ulonglong, pointer_node_id: c_ulonglong) -> c_int {
    unsafe { sovra_check_cross_session_replay(session_id, hash_hi, hash_lo, pointer_session_id, pointer_node_id) }
}
