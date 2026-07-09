#include "xoras_apex_shm.hpp"
#include <iostream>
#include <string>
#include <chrono>
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <thread>
#include <cstring>
#include <bitset>
#include <random>
#include <algorithm>
#include <vector>

#include <mach/thread_act.h>
#include <mach/thread_policy.h>
#include <mach/mach_init.h>

using namespace xoras;

// macOS-native Thread Affinity core pinning helper
void pin_thread_to_core(int core_id) {
    thread_affinity_policy_data_t policy = { core_id };
    kern_return_t kr = thread_policy_set(
        mach_thread_self(),
        THREAD_AFFINITY_POLICY,
        (thread_policy_t)&policy,
        THREAD_AFFINITY_POLICY_COUNT
    );
    if (kr != KERN_SUCCESS) {
        std::cerr << "[APEX-CORE] Warning: Thread affinity core pinning failed." << std::endl;
    } else {
        std::cout << "[APEX-CORE] Thread affinity policy set to Core ID: " << core_id << std::endl;
    }
}


// Hyperdimensional Computing Definitions
constexpr size_t HD_DIM = 10000;
using Hypervector = std::bitset<HD_DIM>;

// The Holographic Memories
Hypervector prototype_buy;
Hypervector prototype_sell;
int buy_samples = 0;
int sell_samples = 0;

// Pre-generated continuous level hypervectors for 100 levels
constexpr size_t NUM_LEVELS = 100;
Hypervector precalc_feature_levels[16][NUM_LEVELS];

void init_base_vectors() {
    std::mt19937 rng(42); // deterministic seed
    Hypervector base_vectors[16];
    for(int i=0; i<16; i++) {
        for(size_t j=0; j<HD_DIM; j++) {
            base_vectors[i][j] = (rng() % 2 == 0);
        }
    }

    // Generate Continuous Item Memory (CIM) for levels
    Hypervector level_vectors[NUM_LEVELS];
    for(size_t j=0; j<HD_DIM; j++) {
        level_vectors[0][j] = (rng() % 2 == 0);
    }
    int flip_count = HD_DIM / (NUM_LEVELS - 1);

    std::vector<int> indices(HD_DIM);
    for(size_t i=0; i<HD_DIM; i++) indices[i] = i;
    std::shuffle(indices.begin(), indices.end(), rng);

    int flip_idx = 0;
    for(size_t l=1; l<NUM_LEVELS; l++) {
        level_vectors[l] = level_vectors[l-1];
        for(int k=0; k<flip_count; k++) {
            if (flip_idx < HD_DIM) {
                level_vectors[l].flip(indices[flip_idx]);
                flip_idx++;
            }
        }
    }

    // Pre-bind items to features
    for(int i=0; i<16; i++) {
        for(size_t l=0; l<NUM_LEVELS; l++) {
            precalc_feature_levels[i][l] = base_vectors[i] ^ level_vectors[l];
        }
    }
}

// Ultra-fast encoding of the float array into a 10,000 bit vector
Hypervector encode_tick(const OrderBookTick& tick) {
    Hypervector hv;
    double mid_price = (tick.bid_prices[0] + tick.ask_prices[0]) / 2.0;
    if (mid_price <= 0.0) mid_price = 1.0;

    double features[16] = {
        (tick.bid_prices[0] - mid_price) / mid_price * 100000.0,
        (tick.bid_prices[1] - mid_price) / mid_price * 100000.0,
        (tick.bid_prices[2] - mid_price) / mid_price * 100000.0,
        (tick.bid_prices[3] - mid_price) / mid_price * 100000.0,
        tick.bid_vols[0] * 10.0, tick.bid_vols[1] * 10.0, tick.bid_vols[2] * 10.0, tick.bid_vols[3] * 10.0,
        (tick.ask_prices[0] - mid_price) / mid_price * 100000.0,
        (tick.ask_prices[1] - mid_price) / mid_price * 100000.0,
        (tick.ask_prices[2] - mid_price) / mid_price * 100000.0,
        (tick.ask_prices[3] - mid_price) / mid_price * 100000.0,
        tick.ask_vols[0] * 10.0, tick.ask_vols[1] * 10.0, tick.ask_vols[2] * 10.0, tick.ask_vols[3] * 10.0
    };
    
    // Fast O(1) level lookup instead of runtime shift
    for(int i=0; i<16; i++) {
        int level = static_cast<int>(features[i]) % NUM_LEVELS;
        if (level < 0) level += NUM_LEVELS;
        hv ^= precalc_feature_levels[i][level];
    }
    return hv;
}

void process_tick(const OrderBookTick& tick, MarketDecision& decision) {
    std::strncpy(decision.symbol, tick.symbol, 16);
    decision.timestamp = std::chrono::high_resolution_clock::now().time_since_epoch().count();
    
    // 1. Encode into Hyperdimensional Space
    Hypervector current_hv = encode_tick(tick);

    // 2. Holographic Learning (Supervised by Python)
    if (tick.learn_flag == 1) { // Teach BUY
        prototype_buy ^= current_hv; // Instant One-Shot Learn
        buy_samples++;
        decision.action = 0;
        return;
    } else if (tick.learn_flag == 2) { // Teach SELL
        prototype_sell ^= current_hv;
        sell_samples++;
        decision.action = 0;
        return;
    }

    // 3. Autonomous Inference via Hamming Distance
    if (buy_samples > 0 || sell_samples > 0) {
        // Hamming distance = number of set bits in XOR
        int dist_buy = (current_hv ^ prototype_buy).count();
        int dist_sell = (current_hv ^ prototype_sell).count();
        
        // Convert to similarity percentage
        double sim_buy = 100.0 * (1.0 - (static_cast<double>(dist_buy) / HD_DIM));
        double sim_sell = 100.0 * (1.0 - (static_cast<double>(dist_sell) / HD_DIM));
        
        static int debug_counter = 0;
        if (debug_counter++ % 100 == 0) {
            std::cerr << "[APEX-DEBUG] sim_buy: " << sim_buy << "% | sim_sell: " << sim_sell << "%" << std::endl;
        }

        if (sim_buy > 51.0 && sim_buy > sim_sell) {
            decision.action = 1; // BUY
            decision.confidence = static_cast<uint8_t>(sim_buy);
            decision.execution_price = tick.ask_prices[0];
            decision.execution_volume = 0.01;
            return;
        } else if (sim_sell > 51.0 && sim_sell > sim_buy) {
            decision.action = 2; // SELL
            decision.confidence = static_cast<uint8_t>(sim_sell);
            decision.execution_price = tick.bid_prices[0];
            decision.execution_volume = 0.01;
            return;
        }
    }
    
    // Default Fallback
    decision.action = 0;
    decision.confidence = 0;
    decision.execution_price = 0.0;
    decision.execution_volume = 0.0;
}

int main() {
    // Pin loop thread to Core 4 (High Performance Core)
    pin_thread_to_core(4);

    const char* shm_name = "/xoras_apex_shm";
    std::cout << "[APEX-CORE] Initializing Bare-Metal C++ Hyperdimensional Engine..." << std::endl;

    init_base_vectors();
    std::cout << "[APEX-CORE] Initialized 10,000-bit Holographic Base Vectors." << std::endl;

    int fd = shm_open(shm_name, O_CREAT | O_RDWR, 0666);
    if (fd < 0) {
        std::cerr << "[APEX-CORE] FATAL: shm_open failed." << std::endl;
        return 1;
    }

    if (ftruncate(fd, sizeof(ApexMemoryBlock)) == -1) {
        std::cout << "[APEX-CORE] Note: ftruncate bypassed (segment already sized)." << std::endl;
    }

    void* ptr = mmap(0, sizeof(ApexMemoryBlock), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (ptr == MAP_FAILED) {
        std::cerr << "[APEX-CORE] FATAL: mmap failed." << std::endl;
        return 1;
    }

    ApexMemoryBlock* shm = new (ptr) ApexMemoryBlock();
    std::cout << "[APEX-CORE] Apex Dual-Ring Buffer active at " << shm_name << " (" << sizeof(ApexMemoryBlock) << " bytes)" << std::endl;
    std::cout << "[APEX-CORE] Awaiting raw binary ticks..." << std::endl;

    OrderBookTick tick;
    MarketDecision decision;

    while (true) {
        // Spin lock on input ring
        while (!shm->input_ring.pop(tick)) {
            __asm__ __volatile__("yield"); // ARM64 optimized yield
        }

        // Process Arbitrage Math in sub-microseconds
        process_tick(tick, decision);

        // Push decision back instantly
        while (!shm->output_ring.push(decision)) {
            // tight spin if output buffer is full
        }
    }

    munmap(ptr, sizeof(ApexMemoryBlock));
    close(fd);
    shm_unlink(shm_name);
    return 0;
}
