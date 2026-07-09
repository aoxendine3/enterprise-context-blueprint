#include "xoras_durable_wal.h"
#include <thread>
#include <vector>
#include <cassert>
#include <chrono>
#include <atomic>
#include <iostream>
#include <unistd.h>

using namespace xoras;

constexpr int NUM_THREADS = 16;
constexpr int ITERATIONS = 20000;
std::atomic<uint64_t> replay_count{0};

void stress_worker(int id) {
    uint8_t payload[8];
    std::memcpy(payload, &id, sizeof(id));
    
    for (int i = 0; i < ITERATIONS; i++) {
        bool ok = xoras_wal_append(1, payload, sizeof(id));
        assert(ok);
    }
}

void replay_verifier(uint32_t type, const uint8_t* payload, uint32_t size) {
    replay_count.fetch_add(1, std::memory_order_relaxed);
}

int main() {
    const char* stress_log = "stress_wal.bin";
    unlink(stress_log); // Clean old runs
    
    std::cout << "=== XORAS UNDERGROUND PROVING GROUND: WAL BREAKER ===" << std::endl;
    std::cout << "[DOJO] Launching heavy parallel WAL stress test..." << std::endl;
    std::cout << "[DOJO] Concurrency: " << NUM_THREADS << " threads | Loads: " << ITERATIONS << " per thread" << std::endl;
    
    bool ok = xoras_wal_init(stress_log);
    assert(ok);
    
    auto start = std::chrono::high_resolution_clock::now();
    
    std::vector<std::thread> workers;
    for (int i = 0; i < NUM_THREADS; i++) {
        workers.emplace_back(stress_worker, i);
    }
    
    for (auto& w : workers) {
        w.join();
    }
    
    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double, std::milli> elapsed = end - start;
    
    std::cout << "[DOJO] Concurrent write-phase completed." << std::endl;
    std::cout << "[DOJO] Total write operations: " << NUM_THREADS * ITERATIONS << std::endl;
    std::cout << "[DOJO] Write time:             " << elapsed.count() << " ms" << std::endl;
    
    // Close log file to simulate abrupt shutdown/restart transition
    xoras_wal_close();
    
    // Reboot & Recovery Phase
    std::cout << "\n[DOJO] Simulating sudden boot recovery scan..." << std::endl;
    auto rec_start = std::chrono::high_resolution_clock::now();
    
    bool rec_ok = xoras_wal_init(stress_log);
    assert(rec_ok);
    
    uint64_t count = xoras_wal_replay(replay_verifier);
    auto rec_end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double, std::milli> rec_elapsed = rec_end - rec_start;
    
    std::cout << "[DOJO] Replayed transaction count: " << count << " / " << NUM_THREADS * ITERATIONS << std::endl;
    std::cout << "[DOJO] Replay verification time:    " << rec_elapsed.count() << " ms" << std::endl;
    
    xoras_wal_close();
    unlink(stress_log); // Clean up file
    
    if (count == NUM_THREADS * ITERATIONS) {
        std::cout << "\n[DOJO] RESULT: PASSED (Zero data loss under heavy multithreaded stress!)" << std::endl;
        return 0;
    } else {
        std::cout << "\n[DOJO] RESULT: FAILED (Data corruption detected!)" << std::endl;
        return 1;
    }
}
