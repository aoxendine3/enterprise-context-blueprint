#pragma once
#include <cstdint>
#include <cstddef>
#include <string>

#define XORAS_EXPORT __attribute__((visibility("default")))

namespace xoras {

struct alignas(64) TransactionRecord {
    uint64_t epoch;
    uint32_t tx_type; // 1 = Alloc, 2 = Free, 3 = Trajectory Update
    uint32_t payload_size;
    uint8_t payload[48]; // Max 48 bytes for address/metadata/vector segment
};

struct DurableLogHeader {
    uint64_t magic_sig;   // 0x584F52415357414C ("XORASWAL")
    uint64_t active_epoch;
    uint64_t record_count;
};

extern "C" {
    XORAS_EXPORT bool xoras_wal_init(const char* filepath);
    XORAS_EXPORT bool xoras_wal_append(uint32_t tx_type, const uint8_t* payload, uint32_t size);
    XORAS_EXPORT uint64_t xoras_wal_replay(void (*replay_callback)(uint32_t type, const uint8_t* payload, uint32_t size));
    XORAS_EXPORT void xoras_wal_close();
}

} // namespace xoras
