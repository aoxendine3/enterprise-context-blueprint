#include "xoras_apex_shm.hpp"
#include <iostream>
#include <chrono>
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <cstring>
#include <thread>

using namespace xoras;

// Helper to push ticks directly in C++
bool push_tick(ApexMemoryBlock* shm, const char* symbol, double bid_p, double ask_p, uint8_t learn_flag) {
    OrderBookTick tick;
    std::memset(&tick, 0, sizeof(OrderBookTick));
    std::strncpy(tick.symbol, symbol, 16);
    
    tick.bid_prices[0] = bid_p;
    tick.ask_prices[0] = ask_p;
    tick.learn_flag = learn_flag;
    tick.timestamp = std::chrono::high_resolution_clock::now().time_since_epoch().count();
    
    return shm->input_ring.push(tick);
}

int main() {
    const char* shm_name = "/xoras_apex_shm";
    std::cout << "[CLIENT] Connecting to POSIX shared memory: " << shm_name << std::endl;
    
    int fd = -1;
    for (int i = 0; i < 30; ++i) {
        fd = shm_open(shm_name, O_RDWR, 0666);
        if (fd >= 0) break;
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
    
    if (fd < 0) {
        std::cerr << "[CLIENT] FATAL: Could not open shared memory after 3 seconds. Make sure the engine is running." << std::endl;
        return 1;
    }
    
    void* ptr = mmap(0, sizeof(ApexMemoryBlock), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (ptr == MAP_FAILED) {
        std::cerr << "[CLIENT] FATAL: mmap failed." << std::endl;
        close(fd);
        return 1;
    }
    
    ApexMemoryBlock* shm = static_cast<ApexMemoryBlock*>(ptr);
    
    // Clear out rings for clean run
    // By resetting the atomic indices to 0
    std::memset(ptr, 0, sizeof(ApexMemoryBlock));
    
    std::cout << "[CLIENT] Rings cleared. Starting C++ native test loop..." << std::endl;
    
    // Stage 1: Push training ticks
    // Train BUY (learn_flag = 1)
    if (!push_tick(shm, "BTCUSDT", 99000.1, 99200.1, 1)) {
        std::cerr << "[CLIENT] Failed to push BUY training tick" << std::endl;
    }
    
    // Train SELL (learn_flag = 2)
    if (!push_tick(shm, "BTCUSDT", 89000.3, 89200.3, 2)) {
        std::cerr << "[CLIENT] Failed to push SELL training tick" << std::endl;
    }
    
    // Give engine thread a small yield window to consume training ticks
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    
    // Stage 2: Push inference tick and measure exact round-trip latency
    auto start_time = std::chrono::high_resolution_clock::now();
    
    if (!push_tick(shm, "BTCUSDT", 99000.1, 99200.1, 0)) {
        std::cerr << "[CLIENT] Failed to push inference tick" << std::endl;
    }
    
    // Poll for the output decision
    MarketDecision decision;
    bool got_decision = false;
    
    // Spin-poll output ring for up to 1 second
    auto timeout_start = std::chrono::high_resolution_clock::now();
    while (std::chrono::duration_cast<std::chrono::seconds>(std::chrono::high_resolution_clock::now() - timeout_start).count() < 1) {
        if (shm->output_ring.pop(decision)) {
            // Check if this is the decision for our active inference tick (action != 0 during inference)
            if (decision.action != 0) {
                got_decision = true;
                break;
            }
        }
        __asm__ __volatile__("yield"); // yield CPU slice
    }
    
    auto end_time = std::chrono::high_resolution_clock::now();
    auto total_latency_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end_time - start_time).count();
    
    if (got_decision) {
        std::cout << "\n==============================================" << std::endl;
        std::cout << "      NATIVE C++ TELEMETRY ROUND-TRIP REPORT" << std::endl;
        std::cout << "==============================================" << std::endl;
        std::cout << "  Symbol           : " << decision.symbol << std::endl;
        std::cout << "  Decision Action  : " << (decision.action == 1 ? "BUY" : (decision.action == 2 ? "SELL" : "HOLD")) << std::endl;
        std::cout << "  Execution Price  : $" << decision.execution_price << std::endl;
        std::cout << "  Confidence Level : " << static_cast<int>(decision.confidence) << "%" << std::endl;
        std::cout << "  Total RTT Latency: " << (total_latency_ns / 1000.0) << " microseconds" << std::endl;
        std::cout << "==============================================\n" << std::endl;
    } else {
        std::cerr << "[CLIENT] Timeout: Did not receive active trade decision from engine." << std::endl;
    }
    
    munmap(ptr, sizeof(ApexMemoryBlock));
    close(fd);
    return 0;
}
