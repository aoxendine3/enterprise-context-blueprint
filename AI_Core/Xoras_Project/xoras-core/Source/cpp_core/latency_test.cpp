#include "xoras_shm_manager.cpp"
#include <iostream>
#include <thread>
#include <vector>
#include <chrono>

using namespace xoras;

void producer_thread(SHMManager* shm_manager, size_t num_messages) {
    MarketSignal sig;
    memset(&sig, 0, sizeof(MarketSignal));
    strcpy(sig.symbol, "BTCUSDT");
    sig.price = 100000.50;
    sig.volume = 1.5;
    sig.side = 1;

    for (size_t i = 0; i < num_messages; ++i) {
        sig.timestamp = std::chrono::high_resolution_clock::now().time_since_epoch().count();
        // Spin until we can push (in case consumer is slow)
        while (!shm_manager->ring_buffer->push(sig)) {
            // tight loop
        }
    }
}

void consumer_thread(SHMManager* shm_manager, size_t num_messages) {
    MarketSignal sig;
    int64_t total_latency_ns = 0;
    size_t max_latency_ns = 0;

    for (size_t i = 0; i < num_messages; ++i) {
        // Spin until we can pop
        while (!shm_manager->ring_buffer->pop(sig)) {
            // tight loop
        }
        
        uint64_t now = std::chrono::high_resolution_clock::now().time_since_epoch().count();
        int64_t latency = now - sig.timestamp;
        
        total_latency_ns += latency;
        if (latency > max_latency_ns) {
            max_latency_ns = latency;
        }
    }

    std::cout << "--- Ring Buffer Benchmark Results ---" << std::endl;
    std::cout << "Total Messages Transferred: " << num_messages << std::endl;
    std::cout << "Average Latency (Producer -> Consumer): " << (total_latency_ns / num_messages) << " ns" << std::endl;
    std::cout << "Max Latency Spike: " << max_latency_ns << " ns" << std::endl;
}

int main() {
    try {
        // Create SHM block
        SHMManager shm_manager(true);
        
        size_t test_volume = 1'000'000;
        
        std::cout << "[BENCHMARK] Initializing zero-copy ring buffer latency test..." << std::endl;
        
        // Launch consumer and producer threads to simulate HFT IPC
        std::thread consumer(consumer_thread, &shm_manager, test_volume);
        
        // Give consumer a tiny head start to avoid initial spikes
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
        
        auto start_time = std::chrono::high_resolution_clock::now();
        std::thread producer(producer_thread, &shm_manager, test_volume);
        
        producer.join();
        consumer.join();
        
        auto end_time = std::chrono::high_resolution_clock::now();
        auto duration_ms = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time).count();
        
        std::cout << "Total Time for 1 Million Ticks: " << duration_ms << " ms" << std::endl;
        std::cout << "Throughput: " << (1000000.0 / (duration_ms / 1000.0)) << " messages/second" << std::endl;
        std::cout << "Test Complete." << std::endl;

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
    }
    
    return 0;
}
