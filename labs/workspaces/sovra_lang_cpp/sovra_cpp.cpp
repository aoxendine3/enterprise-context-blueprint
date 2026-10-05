// sovra_cpp.cpp
#include <cstdio>
#include "../labs/workspaces/sovra_lang/context_bridge_engine.c"

extern "C" int sovra_init_context_bridge();
extern "C" int sovra_process_intake_signal(const sovra_candidate_signal_t *candidate, sovra_certified_decision_t *decision);
extern "C" int sovra_register_session(uint64_t session_id);
extern "C" int sovra_verify_simd_hash(const uint8_t *payload, size_t len, uint64_t expected_hi, uint64_t expected_lo);
extern "C" uint32_t sovra_get_lattice_tag(const void *ptr);
extern "C" int sovra_check_cross_session_replay(uint64_t session_id, uint64_t hash_hi, uint64_t hash_lo, uint64_t pointer_session_id, uint64_t pointer_node_id);

// No extra logic – just expose the C symbols via C++ compilation.
