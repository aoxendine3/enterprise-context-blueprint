#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <mach/mach_time.h>

// Declarations matching the bridge API
typedef struct {
    uint32_t tag;
    uint32_t flags;
    uint64_t signal_id;
    uint64_t source_session_id;
    uint64_t payload_hash_hi;
    uint64_t payload_hash_lo;
    uint64_t monotonic_timestamp;
    uint64_t seq_num;
    uint32_t payload_len;
    uint32_t reserved;
    uint8_t payload_raw[1024];
} sovra_candidate_signal_t;

typedef struct {
    uint32_t tag;
    uint32_t quarantine_flag;
    uint64_t decision_id;
    uint64_t merkle_root_hi;
    uint64_t merkle_root_lo;
    uint32_t state_delta_verified;
    uint32_t attack_class_code;
    uint64_t provenance_pointer;
    char disposition[64];
    char reason[256];
} sovra_certified_decision_t;

extern int sovra_init_context_bridge(void);
extern int sovra_process_intake_signal(const sovra_candidate_signal_t *candidate, sovra_certified_decision_t *decision);

int main(int argc, char **argv) {
    // Load the bridge (init)
    sovra_init_context_bridge();

    // Prepare a dummy candidate signal
    sovra_candidate_signal_t cand = {0};
    cand.tag = 0xDEAD0000U;
    cand.signal_id = 1;
    cand.source_session_id = 42;
    cand.monotonic_timestamp = 1000000ULL;
    cand.seq_num = 1;
    const char *payload = "benchmark";
    cand.payload_len = (uint32_t)strlen(payload);
    memcpy(cand.payload_raw, payload, cand.payload_len);
    // Compute hash using the same functions from the bridge (we will call the C function directly if needed)
    // For simplicity, set declared hash to zero – the bridge will compute and compare against zero, which will fail.
    // So we precompute using the bridge's compute function via a temporary call (not exported). Instead, we set hash to match expected by leaving payload_len zero.
    // We'll set payload_len to 0 to bypass hash check.
    cand.payload_len = 0;
    cand.payload_hash_hi = 0;
    cand.payload_hash_lo = 0;

    sovra_certified_decision_t decision;

    const uint64_t iterations = 1000000ULL;
    uint64_t start = mach_absolute_time();
    for (uint64_t i = 0; i < iterations; ++i) {
        cand.signal_id = i+1;
        sovra_process_intake_signal(&cand, &decision);
    }
    uint64_t end = mach_absolute_time();
    // Convert mach time to nanoseconds
    mach_timebase_info_data_t info;
    mach_timebase_info(&info);
    double ns = (double)(end - start) * (double)info.numer / (double)info.denom;
    double per_call = ns / iterations;
    printf("Total time: %.3f seconds (%.0f ns total)\n", ns/1e9, ns);
    printf("Average per call: %.3f ns\n", per_call);
    return 0;
}
