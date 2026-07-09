#ifndef XORAS_RING_BUFFER_HPP
#define XORAS_RING_BUFFER_HPP

#include <atomic>
#include <cstdint>
#include <cstddef>
#include <stdexcept>
#include <string.h>

namespace xoras {

// 64-byte struct carefully aligned to prevent false sharing across cache lines
struct alignas(64) MarketSignal {
    char symbol[16];   // e.g. "BTCUSDT" (null terminated)
    double price;
    double volume;
    uint64_t timestamp; // nanoseconds since epoch
    uint8_t side;      // 0 = NONE, 1 = BUY, 2 = SELL
    uint8_t padding[23]; // explicit padding to reach 64 bytes for L1 cache line alignment
};

static_assert(sizeof(MarketSignal) == 64, "MarketSignal must be exactly 64 bytes for L1 cache line alignment.");

template<size_t Capacity>
class SPSCRingBuffer {
    static_assert((Capacity != 0) && ((Capacity & (Capacity - 1)) == 0),
                  "Capacity must be a power of 2");

private:
    // Align atomic indices to 64-byte cache lines to prevent false sharing
    // between the producer thread (head) and consumer thread (tail).
    alignas(64) std::atomic<size_t> head_{0};
    alignas(64) std::atomic<size_t> tail_{0};

    // The contiguous array of signals
    alignas(64) MarketSignal buffer_[Capacity];

public:
    SPSCRingBuffer() = default;

    // Single Producer push (Lock-Free)
    bool push(const MarketSignal& signal) {
        // Load the current head (where we will write)
        const size_t head = head_.load(std::memory_order_relaxed);
        
        // Load the tail using acquire semantics to synchronize with pop()
        // Compute next head position
        const size_t next_head = (head + 1) & (Capacity - 1);
        
        if (next_head == tail_.load(std::memory_order_acquire)) {
            // Buffer is full. In HFT, we might overwrite, but for now we drop or spin.
            return false; 
        }

        // Write the data into the buffer
        buffer_[head] = signal;

        // Publish the new head using release semantics so the consumer sees the data
        head_.store(next_head, std::memory_order_release);
        return true;
    }

    // Single Consumer pop (Lock-Free)
    bool pop(MarketSignal& out_signal) {
        // Load the current tail (where we will read)
        const size_t tail = tail_.load(std::memory_order_relaxed);

        // Load the head using acquire semantics to synchronize with push()
        if (tail == head_.load(std::memory_order_acquire)) {
            // Buffer is empty
            return false;
        }

        // Read the data
        out_signal = buffer_[tail];

        // Advance tail using release semantics
        tail_.store((tail + 1) & (Capacity - 1), std::memory_order_release);
        return true;
    }

    // Utility for Python to check availability
    size_t size() const {
        const size_t head = head_.load(std::memory_order_acquire);
        const size_t tail = tail_.load(std::memory_order_acquire);
        if (head >= tail) {
            return head - tail;
        }
        return Capacity + head - tail;
    }
};

} // namespace xoras

#endif // XORAS_RING_BUFFER_HPP
