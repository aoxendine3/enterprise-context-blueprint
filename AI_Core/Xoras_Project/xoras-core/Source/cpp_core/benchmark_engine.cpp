#define main apex_main
#include "xoras_apex_engine.cpp"
#undef main

void run_benchmark() {
    std::cout << "Initializing base vectors..." << std::endl;
    init_base_vectors();

    OrderBookTick tick;
    memset(&tick, 0, sizeof(OrderBookTick));
    tick.bid_prices[0] = 100.0;
    tick.ask_prices[0] = 100.1;

    MarketDecision decision;
    
    // warmup
    for (int i=0; i<1000; i++) process_tick(tick, decision);

    size_t iters = 1000000;
    auto start = std::chrono::high_resolution_clock::now();
    for(size_t i=0; i<iters; i++) {
        tick.bid_prices[0] += 0.001;
        process_tick(tick, decision);
    }
    auto end = std::chrono::high_resolution_clock::now();

    auto duration_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
    std::cout << "Hot-path Latency: " << (double)duration_ns / iters << " ns per tick" << std::endl;
}

int main() {
    run_benchmark();
    return 0;
}
