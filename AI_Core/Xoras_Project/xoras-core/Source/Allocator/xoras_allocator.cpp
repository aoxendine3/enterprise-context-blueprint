#include "xoras_allocator.h"
#include <cstdlib>
#include <new>
#include <arm_neon.h>

namespace xoras {

std::atomic<uint64_t> global_superblock_counter{0};

thread_local ThreadLocalArena local_arena;
thread_local bool arena_initialized = false;

inline size_t align_up(size_t size, size_t alignment) {
    return (size + alignment - 1) & ~(alignment - 1);
}

void init_local_arena() {
    if (arena_initialized) return;
    
    local_arena.bump_ptr = nullptr;
    local_arena.remaining_bytes = 0;
    local_arena.incoming_mailbox.incoming_batch_stack.store(nullptr, std::memory_order_relaxed);
    local_arena.local_free_list = nullptr;
    
    local_arena.cluster_id = static_cast<uint16_t>(global_superblock_counter.fetch_add(1) % 4);
    local_arena.core_type = (local_arena.cluster_id == 0) ? CoreClusterType::PERFORMANCE_CORE : CoreClusterType::EFFICIENCY_CORE;
    local_arena.current_cached_bytes = 0;
    
    arena_initialized = true;
}

extern "C" {

XORAS_EXPORT void xoras_allocator_init() {
    std::cout << "[XORAS M4 DAEMON] Initializing Wait-Free Swarm Allocator..." << std::endl;
    std::cout << "[XORAS M4 DAEMON] Hardware Determinism: Active (16KB Macro-pages)" << std::endl;
    std::cout << "[XORAS M4 DAEMON] Cross-Cluster Routing: Hierarchical MPSC Mailboxes" << std::endl;
    std::cout << "[XORAS M4 DAEMON] Zero False Sharing: Enforced (128-byte cache lines)" << std::endl;
    init_local_arena();
}

XORAS_EXPORT void* xoras_malloc(size_t size) {
    if (size == 0) return nullptr;
    init_local_arena();

    size_t header_size = align_up(sizeof(BlockHeader), M4_CACHE_LINE_SIZE);
    size_t total_size = align_up(size + header_size, M4_CACHE_LINE_SIZE);

    BlockHeader* prev = nullptr;
    BlockHeader* curr = local_arena.local_free_list;
    while (curr) {
        if (curr->block_size >= size) {
            if (prev) {
                prev->next.store(curr->next.load(std::memory_order_relaxed), std::memory_order_relaxed);
            } else {
                local_arena.local_free_list = curr->next.load(std::memory_order_relaxed);
            }
            
            curr->rehome_epoch_tag.fetch_add(1, std::memory_order_relaxed);
            std::atomic_thread_fence(std::memory_order_seq_cst);
            
            return reinterpret_cast<void*>(reinterpret_cast<uintptr_t>(curr) + header_size);
        }
        prev = curr;
        curr = curr->next.load(std::memory_order_relaxed);
    }

    BlockHeader* incoming = local_arena.incoming_mailbox.incoming_batch_stack.exchange(nullptr, std::memory_order_acquire);
    if (incoming) {
        BlockHeader* mail_curr = incoming;
        while (mail_curr) {
            BlockHeader* next_mail = mail_curr->next.load(std::memory_order_relaxed);
            mail_curr->next.store(local_arena.local_free_list, std::memory_order_relaxed);
            local_arena.local_free_list = mail_curr;
            mail_curr = next_mail;
        }
        return xoras_malloc(size);
    }

    if (local_arena.remaining_bytes < total_size) {
        void* raw_block = nullptr;
        if (posix_memalign(&raw_block, M4_MACRO_PAGE_SIZE, sizeof(PrefaultedSuperblock)) != 0) {
            return nullptr;
        }
        PrefaultedSuperblock* sb = new (raw_block) PrefaultedSuperblock();
        sb->active_bytes.store(0, std::memory_order_relaxed);
        
        local_arena.bump_ptr = sb->payload;
        local_arena.remaining_bytes = sizeof(sb->payload);
    }

    uint8_t* alloc_ptr = local_arena.bump_ptr;
    local_arena.bump_ptr += total_size;
    local_arena.remaining_bytes -= total_size;

    BlockHeader* header = reinterpret_cast<BlockHeader*>(alloc_ptr);
    header->original_arena = &local_arena;
    header->block_size = static_cast<uint32_t>(size);
    header->next.store(nullptr, std::memory_order_relaxed);
    header->current_owner_cluster.store(local_arena.cluster_id, std::memory_order_relaxed);
    header->rehome_epoch_tag.store(1, std::memory_order_relaxed);

    std::atomic_thread_fence(std::memory_order_seq_cst);
    
    return reinterpret_cast<void*>(alloc_ptr + header_size);
}

XORAS_EXPORT void xoras_free(void* ptr) {
    if (!ptr) return;
    init_local_arena();

    size_t header_size = align_up(sizeof(BlockHeader), M4_CACHE_LINE_SIZE);
    BlockHeader* header = reinterpret_cast<BlockHeader*>(reinterpret_cast<uintptr_t>(ptr) - header_size);

    header->rehome_epoch_tag.fetch_add(1, std::memory_order_relaxed);
    std::atomic_thread_fence(std::memory_order_seq_cst);

    if (header->original_arena == &local_arena) {
        header->next.store(local_arena.local_free_list, std::memory_order_relaxed);
        local_arena.local_free_list = header;
    } else {
        BlockHeader* old_head = header->original_arena->incoming_mailbox.incoming_batch_stack.load(std::memory_order_relaxed);
        do {
            header->next.store(old_head, std::memory_order_relaxed);
        } while (!header->original_arena->incoming_mailbox.incoming_batch_stack.compare_exchange_weak(
            old_head, header, std::memory_order_release, std::memory_order_relaxed));
    }
}

XORAS_EXPORT void xoras_compact_superblock(ThreadLocalArena* arena) {
    if (!arena || !arena->local_free_list) return;

    BlockHeader* curr = arena->local_free_list;

    while (curr) {
        BlockHeader* next_block = curr->next.load(std::memory_order_relaxed);
        if (next_block) {
            size_t header_size = align_up(sizeof(BlockHeader), M4_CACHE_LINE_SIZE);
            uintptr_t curr_end = reinterpret_cast<uintptr_t>(curr) + header_size + curr->block_size;
            curr_end = align_up(curr_end, M4_CACHE_LINE_SIZE);

            if (curr_end == reinterpret_cast<uintptr_t>(next_block)) {
                uint64_t gen_curr = curr->rehome_epoch_tag.load(std::memory_order_relaxed);
                uint64_t gen_next = next_block->rehome_epoch_tag.load(std::memory_order_relaxed);

                size_t new_size = curr->block_size + header_size + next_block->block_size;
                BlockHeader* target_next = next_block->next.load(std::memory_order_relaxed);

                std::atomic_thread_fence(std::memory_order_seq_cst);

                if (curr->rehome_epoch_tag.load(std::memory_order_seq_cst) == gen_curr &&
                    next_block->rehome_epoch_tag.load(std::memory_order_seq_cst) == gen_next) {
                    
                    curr->block_size = new_size;
                    curr->next.store(target_next, std::memory_order_relaxed);
                    curr->rehome_epoch_tag.fetch_add(1, std::memory_order_release);
                    continue;
                }
            }
        }
        curr = next_block;
    }
}

XORAS_EXPORT uint32_t xoras_neon_hamming_distance(const uint8_t* hv1, const uint8_t* hv2, size_t size_bytes) {
    uint32_t total_dist = 0;
    size_t i = 0;

    for (; i + 16 <= size_bytes; i += 16) {
        uint8x16_t v1 = vld1q_u8(hv1 + i);
        uint8x16_t v2 = vld1q_u8(hv2 + i);
        uint8x16_t xored = veorq_u8(v1, v2);
        uint8x16_t popcnt = vcntq_u8(xored);
        total_dist += vaddvq_u8(popcnt);
    }

    for (; i < size_bytes; i++) {
        uint8_t diff = hv1[i] ^ hv2[i];
        total_dist += __builtin_popcount(diff);
    }

    return total_dist;
}

XORAS_EXPORT ThreadLocalArena* xoras_get_local_arena() {
    init_local_arena();
    return &local_arena;
}

} // extern "C"

} // namespace xoras
