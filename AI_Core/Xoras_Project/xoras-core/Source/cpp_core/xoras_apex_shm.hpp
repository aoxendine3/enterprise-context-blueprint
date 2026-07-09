#ifndef XORAS_APEX_SHM_HPP
#define XORAS_APEX_SHM_HPP

#include <atomic>
#include <cstdint>
#include <cstddef>

namespace xoras {

// Aligning to 64 bytes
struct alignas(64) OrderBookTick {
    char symbol[16];
    double bid_prices[4];
    double bid_vols[4];
    double ask_prices[4];
    double ask_vols[4];
    uint64_t timestamp;
    uint8_t learn_flag;  // 0 = infer, 1 = learn BUY prototype, 2 = learn SELL prototype
    uint8_t padding[39]; // 16 + 32 + 32 + 32 + 32 + 8 + 1 = 153 bytes. 153 + 39 = 192 bytes (3 cache lines)
};

static_assert(sizeof(OrderBookTick) == 192, "OrderBookTick must be exactly 192 bytes for cache alignment.");

// Re-using the MarketSignal from earlier
struct alignas(64) MarketDecision {
    char symbol[16];   
    double execution_price;
    double execution_volume;
    uint64_t timestamp; 
    uint8_t action;      // 0 = HOLD, 1 = BUY, 2 = SELL
    uint8_t confidence;  // 0-100
    uint8_t padding[22]; 
};

static_assert(sizeof(MarketDecision) == 64, "MarketDecision must be exactly 64 bytes.");

template<typename T, size_t Capacity>
class ApexRingBuffer {
    static_assert((Capacity != 0) && ((Capacity & (Capacity - 1)) == 0), "Capacity must be power of 2");

private:
    alignas(64) std::atomic<size_t> head_{0};
    alignas(64) std::atomic<size_t> tail_{0};
    alignas(64) T buffer_[Capacity];

public:
    ApexRingBuffer() = default;

    bool push(const T& item) {
        const size_t head = head_.load(std::memory_order_relaxed);
        const size_t next_head = (head + 1) & (Capacity - 1);
        if (next_head == tail_.load(std::memory_order_acquire)) {
            return false; 
        }
        buffer_[head] = item;
        head_.store(next_head, std::memory_order_release);
        return true;
    }

    bool pop(T& out_item) {
        const size_t tail = tail_.load(std::memory_order_relaxed);
        if (tail == head_.load(std::memory_order_acquire)) {
            return false;
        }
        out_item = buffer_[tail];
        tail_.store((tail + 1) & (Capacity - 1), std::memory_order_release);
        return true;
    }
};

// The dual-bridge memory layout
struct ApexMemoryBlock {
    ApexRingBuffer<OrderBookTick, 1024> input_ring;   // Python -> C++
    ApexRingBuffer<MarketDecision, 1024> output_ring; // C++ -> Python
};

} // namespace xoras

#endif // XORAS_APEX_SHM_HPP
