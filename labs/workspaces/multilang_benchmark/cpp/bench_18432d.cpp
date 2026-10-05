// Calibrated C++20 18,432-D Hexological Vector Engine Benchmark
// Substrate: Apple Silicon M4 Bare Metal (ARM NEON, Multi-Threaded)

#include <iostream>
#include <vector>
#include <chrono>
#include <numeric>
#include <algorithm>
#include <thread>
#include <atomic>
#include <cmath>
#include <arm_neon.h>

constexpr size_t DIM = 18432;
constexpr size_t TOTAL_VECTORS = 100000;
constexpr size_t NUM_CORES = 10;
constexpr size_t ITERATIONS = 50;

std::atomic<double> g_volatile_sink{0.0};

inline float cpp_18432d_dot(const float* a, const float* b) {
    float32x4_t acc0 = vdupq_n_f32(0.0f);
    float32x4_t acc1 = vdupq_n_f32(0.0f);

    for (size_t i = 0; i < DIM; i += 8) {
        float32x4_t va0 = vld1q_f32(a + i);
        float32x4_t vb0 = vld1q_f32(b + i);
        acc0 = vmlaq_f32(acc0, va0, vb0);

        float32x4_t va1 = vld1q_f32(a + i + 4);
        float32x4_t vb1 = vld1q_f32(b + i + 4);
        acc1 = vmlaq_f32(acc1, va1, vb1);
    }
    float32x4_t sum = vaddq_f32(acc0, acc1);
    return vaddvq_f32(sum);
}

int main() {
    std::vector<float> query(DIM);
    for (size_t i = 0; i < DIM; ++i) query[i] = (i % 100) * 0.001f;

    std::vector<float> matrix(TOTAL_VECTORS * DIM);
    for (size_t i = 0; i < TOTAL_VECTORS * DIM; ++i) matrix[i] = ((i + 1) % 100) * 0.001f;

    size_t vecs_per_thread = TOTAL_VECTORS / NUM_CORES;

    // 1. Warmup Pass (10 passes)
    for (size_t warm = 0; warm < 10; ++warm) {
        std::vector<std::thread> warm_threads;
        for (size_t t = 0; t < NUM_CORES; ++t) {
            size_t start_idx = t * vecs_per_thread;
            size_t count = (t == NUM_CORES - 1) ? (TOTAL_VECTORS - start_idx) : vecs_per_thread;
            warm_threads.emplace_back([&query, &matrix, start_idx, count]() {
                float local_sum = 0.0f;
                for (size_t i = 0; i < count; ++i) {
                    size_t vec_idx = start_idx + i;
                    local_sum += cpp_18432d_dot(query.data(), matrix.data() + (vec_idx * DIM));
                }
                g_volatile_sink.fetch_add(local_sum, std::memory_order_relaxed);
            });
        }
        for (auto& th : warm_threads) th.join();
    }

    // 2. Timed Iterations
    std::vector<double> sample_latencies_ms;
    sample_latencies_ms.reserve(ITERATIONS);

    double total_accumulated_sum = 0.0;
    auto t_start = std::chrono::high_resolution_clock::now();

    for (size_t iter = 0; iter < ITERATIONS; ++iter) {
        auto iter_start = std::chrono::high_resolution_clock::now();

        std::vector<std::thread> threads;
        std::vector<double> thread_sums(NUM_CORES, 0.0);

        for (size_t t = 0; t < NUM_CORES; ++t) {
            size_t start_idx = t * vecs_per_thread;
            size_t count = (t == NUM_CORES - 1) ? (TOTAL_VECTORS - start_idx) : vecs_per_thread;
            threads.emplace_back([&query, &matrix, &thread_sums, t, start_idx, count]() {
                double local_sum = 0.0;
                for (size_t i = 0; i < count; ++i) {
                    size_t vec_idx = start_idx + i;
                    local_sum += cpp_18432d_dot(query.data(), matrix.data() + (vec_idx * DIM));
                }
                thread_sums[t] = local_sum;
            });
        }

        for (auto& th : threads) th.join();

        for (double s : thread_sums) total_accumulated_sum += s;

        auto iter_end = std::chrono::high_resolution_clock::now();
        double iter_ms = std::chrono::duration<double, std::milli>(iter_end - iter_start).count();
        sample_latencies_ms.push_back(iter_ms);
    }

    auto t_end = std::chrono::high_resolution_clock::now();
    g_volatile_sink.fetch_add(total_accumulated_sum, std::memory_order_relaxed);

    double total_elapsed_ms = std::chrono::duration<double, std::milli>(t_end - t_start).count();
    double avg_pass_ms = total_elapsed_ms / ITERATIONS;
    double avg_pass_sec = avg_pass_ms / 1000.0;

    double evals_per_sec = TOTAL_VECTORS / avg_pass_sec;
    double gflops = (TOTAL_VECTORS * DIM * 2.0) / (avg_pass_sec * 1e9);
    double gb_sec = ((TOTAL_VECTORS * DIM * 4.0) / (1024.0 * 1024.0 * 1024.0)) / avg_pass_sec;

    std::sort(sample_latencies_ms.begin(), sample_latencies_ms.end());
    double p50_pass_ms = sample_latencies_ms[ITERATIONS * 0.50];
    double p90_pass_ms = sample_latencies_ms[ITERATIONS * 0.90];
    double p99_pass_ms = sample_latencies_ms[ITERATIONS * 0.99];

    // Per-vector latencies in microseconds
    double p50_vec_us = (p50_pass_ms * 1000.0) / TOTAL_VECTORS;
    double p90_vec_us = (p90_pass_ms * 1000.0) / TOTAL_VECTORS;
    double p99_vec_us = (p99_pass_ms * 1000.0) / TOTAL_VECTORS;

    std::cout << "{\n"
              << "  \"language\": \"C++20 (clang++ -O3)\",\n"
              << "  \"avg_pass_ms\": " << avg_pass_ms << ",\n"
              << "  \"evals_per_sec\": " << evals_per_sec << ",\n"
              << "  \"gflops\": " << gflops << ",\n"
              << "  \"bandwidth_gb_sec\": " << gb_sec << ",\n"
              << "  \"p50_us\": " << p50_vec_us << ",\n"
              << "  \"p90_us\": " << p90_vec_us << ",\n"
              << "  \"p99_us\": " << p99_vec_us << ",\n"
              << "  \"sink_check\": " << g_volatile_sink.load() << "\n"
              << "}\n";

    return 0;
}
