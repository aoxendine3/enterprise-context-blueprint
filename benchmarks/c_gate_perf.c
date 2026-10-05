#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include "../labs/workspaces/sovra_lang/context_bridge_engine.c"

int main(){
    // replicate a simple candidate similar to gate0
    sovra_candidate_signal_t cand = {0};
    cand.tag = SOVRA_TAG_CANDIDATE;
    cand.signal_id = 1234;
    cand.source_session_id = 42;
    cand.monotonic_timestamp = (uint64_t)time(NULL)*1000000;
    cand.seq_num = 1;
    const char *payload = "Performance test payload";
    cand.payload_len = (uint32_t)strlen(payload);
    memcpy(cand.payload_raw, payload, cand.payload_len);
    compute_payload_hash_128((const uint8_t*)payload, cand.payload_len, &cand.payload_hash_hi, &cand.payload_hash_lo);
    sovra_certified_decision_t dec;
    int rc = sovra_process_intake_signal(&cand, &dec);
    printf("rc=%d tag=0x%x quarantine=%u\n", rc, dec.tag, dec.quarantine_flag);
    return rc;
}
