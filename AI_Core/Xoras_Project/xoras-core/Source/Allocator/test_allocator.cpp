#include "xoras_allocator.h"
#include <thread>
#include <vector>
#include <cassert>
#include <chrono>

using namespace xoras;

void worker(int id) {
    xoras_allocator_init();
    
    std::vector<void*> ptrs;
    ptrs.reserve(1000);
    
    // Allocate blocks
    for(int i = 0; i < 1000; i++) {
        void* p = xoras_malloc(64);
        assert(p != nullptr);
        
        int* int_ptr = reinterpret_cast<int*>(p);
        *int_ptr = id * 1000 + i;
        
        ptrs.push_back(p);
    }
    
    // Free blocks
    for(void* p : ptrs) {
        xoras_free(p);
    }
    
    // Core Innovation Test: Compaction
    xoras_compact_superblock(xoras_get_local_arena());
}

int main() {
    xoras_allocator_init();
    
    std::cout << "[TEST] Starting concurrent multithreaded allocator test..." << std::endl;
    auto start = std::chrono::high_resolution_clock::now();
    
    std::vector<std::thread> threads;
    for(int i = 0; i < 8; i++) {
        threads.emplace_back(worker, i);
    }
    
    for(auto& t : threads) {
        t.join();
    }
    
    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double, std::milli> elapsed = end - start;
    
    std::cout << "[TEST] All threads joined successfully." << std::endl;
    std::cout << "[TEST] Executed 8000 allocations & frees in: " << elapsed.count() << " ms" << std::endl;
    
    // Core Innovation Test: NEON SIMD popcount correctness
    std::cout << "[TEST] Testing ARM NEON SIMD popcount correctness..." << std::endl;
    
    constexpr size_t HV_BYTES = 1250; // 10,000 bits
    uint8_t hv1[HV_BYTES];
    uint8_t hv2[HV_BYTES];
    
    for (size_t i = 0; i < HV_BYTES; i++) {
        hv1[i] = 0xAA; // 10101010
        hv2[i] = 0x55; // 01010101
    }
    
    uint32_t dist = xoras_neon_hamming_distance(hv1, hv2, HV_BYTES);
    std::cout << "[TEST] NEON distance calculated: " << dist << " / 10000" << std::endl;
    assert(dist == 10000);
    
    std::cout << "[TEST] NEON SIMD popcount verified successfully." << std::endl;
    
    return 0;
}
