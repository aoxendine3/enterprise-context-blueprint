#include "xoras_durable_wal.h"
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <cstring>
#include <atomic>
#include <iostream>

namespace xoras {

constexpr size_t WAL_MAX_RECORDS = 500000; // Increase capacity for heavy stress
constexpr size_t WAL_FILE_SIZE = sizeof(DurableLogHeader) + (sizeof(TransactionRecord) * WAL_MAX_RECORDS);
constexpr uint64_t MAGIC_SIGNATURE = 0x584F52415357414CULL; // "XORASWAL"

int wal_fd = -1;
uint8_t* wal_mmap_ptr = nullptr;
DurableLogHeader* wal_header = nullptr;
TransactionRecord* wal_records = nullptr;

extern "C" {

XORAS_EXPORT bool xoras_wal_init(const char* filepath) {
    bool is_new = access(filepath, F_OK) == -1;
    
    wal_fd = open(filepath, O_RDWR | O_CREAT, 0666);
    if (wal_fd == -1) return false;
    
    if (is_new) {
        if (ftruncate(wal_fd, WAL_FILE_SIZE) == -1) {
            close(wal_fd);
            return false;
        }
    }
    
    wal_mmap_ptr = reinterpret_cast<uint8_t*>(mmap(nullptr, WAL_FILE_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, wal_fd, 0));
    if (wal_mmap_ptr == MAP_FAILED) {
        close(wal_fd);
        return false;
    }
    
    wal_header = reinterpret_cast<DurableLogHeader*>(wal_mmap_ptr);
    wal_records = reinterpret_cast<TransactionRecord*>(wal_mmap_ptr + sizeof(DurableLogHeader));
    
    if (is_new) {
        wal_header->magic_sig = MAGIC_SIGNATURE;
        wal_header->active_epoch = 1;
        wal_header->record_count = 0;
        msync(wal_mmap_ptr, WAL_FILE_SIZE, MS_SYNC);
    }
    
    return true;
}

XORAS_EXPORT bool xoras_wal_append(uint32_t tx_type, const uint8_t* payload, uint32_t size) {
    if (!wal_header || wal_header->magic_sig != MAGIC_SIGNATURE) return false;
    
    // Cast record_count to std::atomic<uint64_t> to prevent race conditions during parallel appends
    auto* record_count_ptr = reinterpret_cast<std::atomic<uint64_t>*>(&wal_header->record_count);
    uint64_t idx = record_count_ptr->fetch_add(1, std::memory_order_relaxed);
    
    if (idx >= WAL_MAX_RECORDS) {
        // Log buffer overflowed
        return false;
    }
    
    TransactionRecord& rec = wal_records[idx];
    rec.epoch = idx + 1; // Thread-safe epoch assignment matching the index
    rec.tx_type = tx_type;
    rec.payload_size = (size > 48) ? 48 : size;
    
    std::memcpy(rec.payload, payload, rec.payload_size);
    
    // Memory fence to ensure data is written before flush
    std::atomic_thread_fence(std::memory_order_seq_cst);
    
    // Asynchronous non-blocking flush to flash storage
    msync(&rec, sizeof(TransactionRecord), MS_ASYNC);
    
    return true;
}

XORAS_EXPORT uint64_t xoras_wal_replay(void (*replay_callback)(uint32_t type, const uint8_t* payload, uint32_t size)) {
    if (!wal_header || wal_header->magic_sig != MAGIC_SIGNATURE) return 0;
    
    uint64_t count = wal_header->record_count;
    for (uint64_t i = 0; i < count; i++) {
        TransactionRecord& rec = wal_records[i];
        replay_callback(rec.tx_type, rec.payload, rec.payload_size);
    }
    
    return count;
}

XORAS_EXPORT void xoras_wal_close() {
    if (wal_mmap_ptr) {
        munmap(wal_mmap_ptr, WAL_FILE_SIZE);
        wal_mmap_ptr = nullptr;
    }
    if (wal_fd != -1) {
        close(wal_fd);
        wal_fd = -1;
    }
}

} // extern "C"

} // namespace xoras
