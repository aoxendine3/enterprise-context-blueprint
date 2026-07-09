#include "xoras_durable_wal.h"
#include <iostream>
#include <cassert>
#include <unistd.h>

using namespace xoras;

uint32_t recovered_allocations = 0;
uint32_t recovered_frees = 0;
uint32_t recovered_sentinel_updates = 0;

void mock_replay_callback(uint32_t type, const uint8_t* payload, uint32_t size) {
    if (type == 1) {
        recovered_allocations++;
    } else if (type == 2) {
        recovered_frees++;
    } else if (type == 3) {
        recovered_sentinel_updates++;
    }
}

int main(int argc, char* argv[]) {
    const char* log_file = "durable_wal.bin";
    
    // Check if we are running in recovery mode
    bool is_recovery = (argc > 1 && std::string(argv[1]) == "recovery");
    
    if (is_recovery) {
        std::cout << "[TEST] --- RECOVERY RUN (Process Resurrected) ---" << std::endl;
        bool ok = xoras_wal_init(log_file);
        assert(ok);
        
        uint64_t count = xoras_wal_replay(mock_replay_callback);
        std::cout << "[TEST] Replayed " << count << " transaction logs since epoch zero." << std::endl;
        std::cout << "[TEST] Recovered Allocations: " << recovered_allocations << std::endl;
        std::cout << "[TEST] Recovered Frees:       " << recovered_frees << std::endl;
        std::cout << "[TEST] Recovered Sentinel Updates: " << recovered_sentinel_updates << std::endl;
        
        assert(count == 3);
        assert(recovered_allocations == 1);
        assert(recovered_frees == 1);
        assert(recovered_sentinel_updates == 1);
        
        std::cout << "[TEST] Zero-Data-Loss state recovery verified successfully." << std::endl;
        
        xoras_wal_close();
        unlink(log_file); // Clean up
        return 0;
    }
    
    std::cout << "[TEST] --- NORMAL RUN (Simulating active operations) ---" << std::endl;
    // Clean up old log if exists
    unlink(log_file);
    
    bool ok = xoras_wal_init(log_file);
    assert(ok);
    
    // Simulate transaction logs
    uint8_t payload1[] = {0x01, 0x02, 0x03}; // Mock Alloc
    xoras_wal_append(1, payload1, 3);
    
    uint8_t payload2[] = {0xAA, 0xBB}; // Mock Free
    xoras_wal_append(2, payload2, 2);
    
    uint8_t payload3[] = {0x99}; // Mock Sentinel Update
    xoras_wal_append(3, payload3, 1);
    
    std::cout << "[TEST] Appended 3 transaction logs. Simulating abrupt process termination..." << std::endl;
    
    // Simulate immediate crash without closing
    return 0;
}
