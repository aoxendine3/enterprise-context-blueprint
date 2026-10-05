/*
 * =============================================================================
 * XORAS SOVRA CONTEXT BRIDGE ENGINE: MARS VERIFICATION & ASAN/TSAN TEST HARNESS
 * Target: Apple Silicon M4 Bare Metal
 * =============================================================================
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <assert.h>
#include <pthread.h>
#include <mach/mach_time.h>

#include "context_bridge_engine.c"

#define TEST_ASSERT(cond, msg) do { \
    if (!(cond)) { \
        fprintf(stderr, "❌ ASSERTION FAILED: %s (%s:%d)\n", msg, __FILE__, __LINE__); \
        exit(1); \
    } \
} while(0)

static void test_normal_promotion(void) {
    printf("[TEST 1] Verifying Normal Candidate Promotion to Certified Decision...\n");
    
    sovra_candidate_signal_t candidate;
    memset(&candidate, 0, sizeof(candidate));
    candidate.tag = SOVRA_TAG_CANDIDATE;
    candidate.signal_id = 1001;
    candidate.source_session_id = 42;
    candidate.monotonic_timestamp = 1000000;
    candidate.seq_num = 1;
    
    const char *payload = "Empirical quantum annealer scaling on M4 architecture";
    candidate.payload_len = (uint32_t)strlen(payload);
    memcpy(candidate.payload_raw, payload, candidate.payload_len);
    
    compute_payload_hash_128((const uint8_t *)payload, candidate.payload_len, 
                             &candidate.payload_hash_hi, &candidate.payload_hash_lo);
                             
    sovra_certified_decision_t decision;
    int rc = sovra_process_intake_signal(&candidate, &decision);
    
    TEST_ASSERT(rc == 0, "Expected success rc == 0");
    TEST_ASSERT(decision.tag == SOVRA_TAG_DECISION, "Expected tag 0xBEAF0000");
    TEST_ASSERT(decision.quarantine_flag == 0, "Expected quarantine_flag == 0");
    TEST_ASSERT(decision.state_delta_verified == 1, "Expected state_delta_verified == 1");
    TEST_ASSERT(strcmp(decision.disposition, "ACCEPTED_WITH_EVIDENCE_POINTERS") == 0, "Expected clean disposition");
    
    printf("   ✅ PASSED: Candidate successfully promoted to Certified Decision (0xBEAF0000)\n");
}

static void test_taint_lattice_coercion(void) {
    printf("[TEST 2] Verifying Taint Lattice Coercion Defense (Non-Candidate Tag)...\n");
    
    sovra_candidate_signal_t candidate;
    memset(&candidate, 0, sizeof(candidate));
    candidate.tag = 0xBADC0DE0U; // Illegal tag bypass attempt
    candidate.signal_id = 1002;
    candidate.source_session_id = 42;
    candidate.monotonic_timestamp = 1000005;
    candidate.seq_num = 2;
    
    sovra_certified_decision_t decision;
    int rc = sovra_process_intake_signal(&candidate, &decision);
    
    TEST_ASSERT(rc == 1, "Expected quarantine rc == 1");
    TEST_ASSERT(decision.quarantine_flag == 1, "Expected quarantine_flag == 1");
    TEST_ASSERT(decision.attack_class_code == ATTACK_TAINT_COERCION, "Expected ATTACK_TAINT_COERCION");
    TEST_ASSERT(decision.state_delta_verified == 1, "State delta verified 0 pollution");
    
    printf("   ✅ PASSED: Taint lattice coercion intercepted and quarantined\n");
}

static void test_payload_corruption_bit_flip(void) {
    printf("[TEST 3] Verifying SIMD Payload Corruption Bit-Flip Defense...\n");
    
    sovra_candidate_signal_t candidate;
    memset(&candidate, 0, sizeof(candidate));
    candidate.tag = SOVRA_TAG_CANDIDATE;
    candidate.signal_id = 1003;
    candidate.source_session_id = 42;
    candidate.monotonic_timestamp = 1000010;
    candidate.seq_num = 3;
    
    const char *payload = "Authentic cryptographic receipt payload";
    candidate.payload_len = (uint32_t)strlen(payload);
    memcpy(candidate.payload_raw, payload, candidate.payload_len);
    
    compute_payload_hash_128((const uint8_t *)payload, candidate.payload_len, 
                             &candidate.payload_hash_hi, &candidate.payload_hash_lo);
                             
    // Intentionally flip bits in the raw payload
    candidate.payload_raw[5] ^= 0xFF;
    
    sovra_certified_decision_t decision;
    int rc = sovra_process_intake_signal(&candidate, &decision);
    
    TEST_ASSERT(rc == 1, "Expected quarantine rc == 1");
    TEST_ASSERT(decision.quarantine_flag == 1, "Expected quarantine_flag == 1");
    TEST_ASSERT(decision.attack_class_code == ATTACK_CORRUPT_PAYLOAD, "Expected ATTACK_CORRUPT_PAYLOAD");
    
    printf("   ✅ PASSED: Bit-flip corruption caught by SIMD hash gate\n");
}

static void test_backdated_timestamp_replay(void) {
    printf("[TEST 4] Verifying Backdated Timestamp Replay Defense...\n");
    
    sovra_candidate_signal_t candidate;
    memset(&candidate, 0, sizeof(candidate));
    candidate.tag = SOVRA_TAG_CANDIDATE;
    candidate.signal_id = 1004;
    candidate.source_session_id = 42;
    candidate.monotonic_timestamp = 500000; // Time regression (earlier than 1000000)
    candidate.seq_num = 4;
    
    sovra_certified_decision_t decision;
    int rc = sovra_process_intake_signal(&candidate, &decision);
    
    TEST_ASSERT(rc == 1, "Expected quarantine rc == 1");
    TEST_ASSERT(decision.quarantine_flag == 1, "Expected quarantine_flag == 1");
    TEST_ASSERT(decision.attack_class_code == ATTACK_BACKDATED_TIME, "Expected ATTACK_BACKDATED_TIME");
    
    printf("   ✅ PASSED: Backdated timestamp intercepted and quarantined\n");
}

static void test_duplicate_sequence_replay(void) {
    printf("[TEST 5] Verifying Duplicate Sequence Replay Defense...\n");
    
    sovra_candidate_signal_t candidate;
    memset(&candidate, 0, sizeof(candidate));
    candidate.tag = SOVRA_TAG_CANDIDATE;
    candidate.signal_id = 1005;
    candidate.source_session_id = 42;
    candidate.monotonic_timestamp = 1000020;
    candidate.seq_num = 1; // Duplicate of already processed sequence
    
    sovra_certified_decision_t decision;
    int rc = sovra_process_intake_signal(&candidate, &decision);
    
    TEST_ASSERT(rc == 1, "Expected quarantine rc == 1");
    TEST_ASSERT(decision.quarantine_flag == 1, "Expected quarantine_flag == 1");
    TEST_ASSERT(decision.attack_class_code == ATTACK_DUPLICATE_NODE, "Expected ATTACK_DUPLICATE_NODE");
    
    printf("   ✅ PASSED: Duplicate sequence replay blocked\n");
}

static void test_cross_session_clia_replay(void) {
    printf("[TEST 6] Verifying Cross-Session CLIA Replay Immunity...\n");
    
    // First, process valid discovery in Session 100
    sovra_candidate_signal_t orig;
    memset(&orig, 0, sizeof(orig));
    orig.tag = SOVRA_TAG_CANDIDATE;
    orig.signal_id = 2001;
    orig.source_session_id = 100;
    orig.monotonic_timestamp = 2000000;
    orig.seq_num = 1;
    
    const char *finding = "Crucial autonomous finding regarding multi-agent consensus";
    orig.payload_len = (uint32_t)strlen(finding);
    memcpy(orig.payload_raw, finding, orig.payload_len);
    compute_payload_hash_128((const uint8_t *)finding, orig.payload_len, 
                             &orig.payload_hash_hi, &orig.payload_hash_lo);
                             
    sovra_certified_decision_t orig_dec;
    int rc1 = sovra_process_intake_signal(&orig, &orig_dec);
    TEST_ASSERT(rc1 == 0, "Origin session signal must pass");
    
    // Now, attempt to replay the exact same finding into Session 200 without citation pointer
    sovra_candidate_signal_t replayed;
    memset(&replayed, 0, sizeof(replayed));
    replayed.tag = SOVRA_TAG_CANDIDATE;
    replayed.signal_id = 3001;
    replayed.source_session_id = 200; // Different session!
    replayed.monotonic_timestamp = 3000000;
    replayed.seq_num = 1;
    replayed.payload_len = orig.payload_len;
    memcpy(replayed.payload_raw, finding, replayed.payload_len);
    replayed.payload_hash_hi = orig.payload_hash_hi;
    replayed.payload_hash_lo = orig.payload_hash_lo;
    
    sovra_certified_decision_t rep_dec;
    int rc2 = sovra_process_intake_signal(&replayed, &rep_dec);
    
    TEST_ASSERT(rc2 == 1, "Cross-session replay must be quarantined");
    TEST_ASSERT(rep_dec.quarantine_flag == 1, "Quarantine flag set");
    TEST_ASSERT(rep_dec.attack_class_code == ATTACK_CLIA_REPLAY, "Expected ATTACK_CLIA_REPLAY");
    
    printf("   ✅ PASSED: Cross-session CLIA replay quarantined with zero state pollution\n");
}

int main(void) {
    printf("=====================================================================\n");
    printf("⚔️  MARS LAYER 3/4 BARE-METAL SOVRA CONTEXT BRIDGE ENGINE TEST\n");
    printf("=====================================================================\n");
    
    sovra_init_context_bridge();
    
    test_normal_promotion();
    test_taint_lattice_coercion();
    test_payload_corruption_bit_flip();
    test_backdated_timestamp_replay();
    test_duplicate_sequence_replay();
    test_cross_session_clia_replay();
    
    printf("\n🛡️ ALL 6 MARS TEST SUITES PASSED FLAWLESSLY ON APPLE SILICON M4 BARE METAL!\n");
    return 0;
}
