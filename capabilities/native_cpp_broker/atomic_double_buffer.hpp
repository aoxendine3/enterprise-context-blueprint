#ifndef ATOMIC_DOUBLE_BUFFER_HPP
#define ATOMIC_DOUBLE_BUFFER_HPP

#include <atomic>
#include <cstdint>
#include <cstring>
#include <memory>
#include <array>
#include <chrono>

namespace xoras {

// Maximum size for context state payload in shared memory
constexpr size_t MAX_STATE_PAYLOAD_BYTES = 65536; // 64 KB per buffer slot
constexpr size_t MAX_AGENTS_COUNT = 64;

#pragma pack(push, 1)
struct AgentTelemetryState {
    uint32_t agent_id;
    char agent_name[32];
    uint64_t last_cycle_timestamp_ns;
    uint32_t current_phase;
    float truth_alignment_score;   // Axis 0: [0.0, 1.0]
    float utility_alignment_score; // Axis 1: [0.0, 1.0]
    uint32_t active_synapse_count;
    uint8_t flags;                 // Bit 0: Active, Bit 1: Consensus Quorum, Bit 2: Quarantined
};

struct SovereignSystemState {
    uint64_t sequence_id;
    uint64_t timestamp_ns;
    uint32_t active_agents;
    uint32_t dream_cycle_epoch;
    uint32_t byzantine_fault_count;
    AgentTelemetryState agents[MAX_AGENTS_COUNT];
    uint32_t payload_len;
    char payload[MAX_STATE_PAYLOAD_BYTES];
};
#pragma pack(pop)

/**
 * AtomicDoubleBuffer
 * 
 * Provides lock-free, zero-wait reads for high-throughput multi-agent execution loops.
 * Multi-reader threads access the front buffer via atomic pointer load (relaxed or acquire)
 * with zero mutex contention, zero context-switching, and zero syscall overhead.
 * Single writer prepares modifications in the private back buffer, and commits via atomic
 * pointer exchange with std::memory_order_release / std::memory_order_acquire.
 */
class AtomicDoubleBuffer {
public:
    AtomicDoubleBuffer() 
        : buffer_a_(std::make_unique<SovereignSystemState>()),
          buffer_b_(std::make_unique<SovereignSystemState>()),
          front_ptr_(buffer_a_.get()),
          back_ptr_(buffer_b_.get()),
          swap_count_(0),
          total_reads_(0),
          total_writes_(0)
    {
        std::memset(buffer_a_.get(), 0, sizeof(SovereignSystemState));
        std::memset(buffer_b_.get(), 0, sizeof(SovereignSystemState));
        buffer_a_->sequence_id = 0;
        buffer_b_->sequence_id = 0;
    }

    ~AtomicDoubleBuffer() = default;

    // Disallow copy/move to preserve atomic memory guarantees
    AtomicDoubleBuffer(const AtomicDoubleBuffer&) = delete;
    AtomicDoubleBuffer& operator=(const AtomicDoubleBuffer&) = delete;

    /**
     * Reader access: Returns pointer to current active front buffer.
     * Guaranteed lock-free and wait-free (O(1)).
     */
    inline const SovereignSystemState* read_front() const noexcept {
        total_reads_.fetch_add(1, std::memory_order_relaxed);
        return front_ptr_.load(std::memory_order_acquire);
    }

    /**
     * Writer access: Returns mutable pointer to back buffer for staged mutations.
     * Single writer thread contract.
     */
    inline SovereignSystemState* stage_back() noexcept {
        return back_ptr_;
    }

    /**
     * Atomic commit: Swaps front and back buffers via atomic store-exchange.
     * After this call returns, all subsequent read_front() invocations see the committed state.
     * Clones committed state back into newly assigned back buffer to ensure continuity.
     */
    inline uint64_t commit_swap() noexcept {
        SovereignSystemState* old_front = front_ptr_.load(std::memory_order_relaxed);
        SovereignSystemState* new_front = back_ptr_;

        // Increment sequence ID
        new_front->sequence_id = old_front->sequence_id + 1;
        new_front->timestamp_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::system_clock::now().time_since_epoch()).count();

        // Atomic swap with acquire-release fence
        front_ptr_.store(new_front, std::memory_order_release);
        back_ptr_ = old_front;

        // Propagate state to new back buffer so future deltas build on committed baseline
        std::memcpy(back_ptr_, new_front, sizeof(SovereignSystemState));

        swap_count_.fetch_add(1, std::memory_order_relaxed);
        total_writes_.fetch_add(1, std::memory_order_relaxed);
        return new_front->sequence_id;
    }

    // Telemetry and observability counters
    uint64_t get_swap_count() const noexcept { return swap_count_.load(std::memory_order_relaxed); }
    uint64_t get_total_reads() const noexcept { return total_reads_.load(std::memory_order_relaxed); }
    uint64_t get_total_writes() const noexcept { return total_writes_.load(std::memory_order_relaxed); }

private:
    std::unique_ptr<SovereignSystemState> buffer_a_;
    std::unique_ptr<SovereignSystemState> buffer_b_;
    
    // Atomic pointer pointing to the current front buffer
    std::atomic<SovereignSystemState*> front_ptr_;
    
    // Pointer to the back buffer (operated exclusively by writer thread)
    SovereignSystemState* back_ptr_;

    mutable std::atomic<uint64_t> swap_count_;
    mutable std::atomic<uint64_t> total_reads_;
    mutable std::atomic<uint64_t> total_writes_;
};

} // namespace xoras

#endif // ATOMIC_DOUBLE_BUFFER_HPP
