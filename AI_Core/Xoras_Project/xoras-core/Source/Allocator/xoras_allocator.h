#pragma once
#include <atomic>
#include <cstdint>
#include <cstddef>
#include <iostream>

#define XORAS_EXPORT __attribute__((visibility("default")))

namespace xoras {

constexpr size_t M4_CACHE_LINE_SIZE = 128;
constexpr size_t BATCH_SWAP_SIZE = 256;
constexpr size_t M4_MACRO_PAGE_SIZE = 16384; 

enum class CoreClusterType : uint8_t {
    PERFORMANCE_CORE = 0,
    EFFICIENCY_CORE  = 1
};

struct BlockHeader;

// 1. Thread-Local MPSC Mailbox 
struct alignas(M4_CACHE_LINE_SIZE) RemoteMailbox {
    std::atomic<BlockHeader*> incoming_batch_stack;
};

// 2. Cluster Aggregator 
struct alignas(M4_CACHE_LINE_SIZE) ClusterAggregator {
    BlockHeader* local_transit_batch[BATCH_SWAP_SIZE];
    uint32_t current_count;
    uint16_t target_cluster_id;
};

// 3. Cluster-Aware Thread-Local Cache (TLC)
struct alignas(M4_CACHE_LINE_SIZE) ThreadLocalArena {
    uint8_t* bump_ptr;
    size_t remaining_bytes;

    RemoteMailbox incoming_mailbox; 
    BlockHeader* local_free_list;

    uint16_t cluster_id;
    CoreClusterType core_type;
    uint32_t current_cached_bytes; 
};

// 4. Distributed Epoch Matrix & Block Header 
struct alignas(M4_CACHE_LINE_SIZE) DistributedEpochNode {
    std::atomic<uint64_t> core_epoch;
    std::atomic<bool>     is_syncing;
};

struct alignas(M4_CACHE_LINE_SIZE) BlockHeader {
    ThreadLocalArena* original_arena; 
    uint32_t block_size;
    std::atomic<BlockHeader*> next;
    
    std::atomic<uint32_t> current_owner_cluster;
    std::atomic<uint64_t> rehome_epoch_tag; 
};

// 5. Hardware Determinism Superblocks 
struct alignas(M4_MACRO_PAGE_SIZE) PrefaultedSuperblock {
    std::atomic<uint64_t> active_bytes;
    uint8_t payload[M4_MACRO_PAGE_SIZE - 8];
};

extern "C" {
    XORAS_EXPORT void xoras_allocator_init();
    XORAS_EXPORT void* xoras_malloc(size_t size);
    XORAS_EXPORT void xoras_free(void* ptr);
    
    // Core Innovations: Real Compaction & SIMD Hardware Acceleration
    XORAS_EXPORT void xoras_compact_superblock(ThreadLocalArena* arena);
    XORAS_EXPORT uint32_t xoras_neon_hamming_distance(const uint8_t* hv1, const uint8_t* hv2, size_t size_bytes);
    XORAS_EXPORT ThreadLocalArena* xoras_get_local_arena();
}

} // namespace xoras
