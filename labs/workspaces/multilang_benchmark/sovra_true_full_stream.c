// SOVRA True Full-Stream Bare-Metal Memory Benchmark (Zero Sample-Cap Shortcuts)
// Substrate: Apple Silicon M4 Bare Metal (16 GB Physical LPDDR5X RAM, 10 Cores)
// Purpose: Stream through EVERY SINGLE FLOAT in the vector matrix to prove true physical DRAM throughput.

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <time.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/resource.h>
#include <pthread.h>
#include <arm_neon.h>
#include <mach/mach_time.h>

#define DIM 18432
#define NUM_CORES 10

static volatile double g_volatile_sink = 0.0;

static double get_time_sec(void) {
    static mach_timebase_info_data_t timebase;
    if (timebase.denom == 0) {
        mach_timebase_info(&timebase);
    }
    uint64_t time = mach_absolute_time();
    return (double)time * timebase.numer / timebase.denom / 1e9;
}

static inline float sovra_18432d_dot_neon(const float *a, const float *b) {
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

typedef struct {
    const float *query;
    const float *matrix;
    size_t start_node;
    size_t node_count;
    double local_sum;
} WorkerTask;

static void *full_stream_worker(void *arg) {
    WorkerTask *task = (WorkerTask *)arg;
    double sum = 0.0;
    for (size_t i = 0; i < task->node_count; i++) {
        size_t node_idx = task->start_node + i;
        const float *target = task->matrix + (node_idx * DIM);
        float dot = sovra_18432d_dot_neon(task->query, target);
        sum += dot;
    }
    task->local_sum = sum;
    return NULL;
}

void benchmark_true_full_stream(size_t total_nodes, const char *label) {
    size_t total_floats = total_nodes * DIM;
    size_t total_bytes = total_floats * sizeof(float);
    double total_gb = (double)total_bytes / (1024.0 * 1024.0 * 1024.0);

    printf("================================================================================\n");
    printf("  [FULL STREAM STAGE: %s] %zu Nodes | Dataset Size: %.4f GB\n", label, total_nodes, total_gb);
    printf("================================================================================\n");

    float *query = (float *)aligned_alloc(64, DIM * sizeof(float));
    float *matrix = (float *)aligned_alloc(64, total_bytes);

    if (!query || !matrix) {
        printf("❌ Memory allocation failed for %.2f GB (RAM limit reached)\n", total_gb);
        if (query) free(query);
        if (matrix) free(matrix);
        return;
    }

    for (size_t i = 0; i < DIM; i++) query[i] = (float)(i % 100) * 0.001f;
    for (size_t i = 0; i < total_floats; i++) matrix[i] = (float)((i + 1) % 100) * 0.001f;

    pthread_t threads[NUM_CORES];
    WorkerTask tasks[NUM_CORES];
    size_t nodes_per_core = total_nodes / NUM_CORES;

    // Warmup Pass
    for (int t = 0; t < NUM_CORES; t++) {
        tasks[t].query = query;
        tasks[t].matrix = matrix;
        tasks[t].start_node = t * nodes_per_core;
        tasks[t].node_count = (t == NUM_CORES - 1) ? (total_nodes - t * nodes_per_core) : nodes_per_core;
        pthread_create(&threads[t], NULL, full_stream_worker, &tasks[t]);
    }
    for (int t = 0; t < NUM_CORES; t++) {
        pthread_join(threads[t], NULL);
        g_volatile_sink += tasks[t].local_sum;
    }

    // 5 Timed Full Stream Passes
    double pass_times_ms[5];
    double total_sum = 0.0;

    double t0_all = get_time_sec();
    for (int pass = 0; pass < 5; pass++) {
        double pass_start = get_time_sec();

        for (int t = 0; t < NUM_CORES; t++) {
            tasks[t].query = query;
            tasks[t].matrix = matrix;
            tasks[t].start_node = t * nodes_per_core;
            tasks[t].node_count = (t == NUM_CORES - 1) ? (total_nodes - t * nodes_per_core) : nodes_per_core;
            pthread_create(&threads[t], NULL, full_stream_worker, &tasks[t]);
        }

        for (int t = 0; t < NUM_CORES; t++) {
            pthread_join(threads[t], NULL);
            total_sum += tasks[t].local_sum;
        }

        double pass_end = get_time_sec();
        pass_times_ms[pass] = (pass_end - pass_start) * 1000.0;
        printf("    Pass %d/5: %.2f ms | Accumulator Check: %.2f\n", pass + 1, pass_times_ms[pass], total_sum);
    }
    double total_sec = get_time_sec() - t0_all;
    double avg_pass_sec = total_sec / 5.0;
    g_volatile_sink += total_sum;

    double evals_sec = (double)total_nodes / avg_pass_sec;
    double gflops = ((double)total_nodes * DIM * 2.0) / (avg_pass_sec * 1e9);
    double gb_sec = total_gb / avg_pass_sec;
    double p50_vec_us = (avg_pass_sec * 1e6) / (double)total_nodes;

    printf("\n  [TRUE GROUND-TRUTH RESULT: %s]\n", label);
    printf("    Dataset Size     : %.4f GB\n", total_gb);
    printf("    Avg Pass Time    : %.2f ms (%.4f seconds)\n", avg_pass_sec * 1000.0, avg_pass_sec);
    printf("    Evaluations/sec  : %.0f evals/sec\n", evals_sec);
    printf("    GFLOPS           : %.2f GFLOPS\n", gflops);
    printf("    Sustained DRAM BW: %.2f GB/s\n", gb_sec);
    printf("    Per-Vector Latency: %.2f µs\n\n", p50_vec_us);

    free(query);
    free(matrix);
}

int main(void) {
    printf("================================================================================\n");
    printf("  SOVRA TRUE FULL-STREAM BARE-METAL BENCHMARK (ZERO SAMPLE SHORTCUTS)\n");
    printf("  Substrate: Apple Silicon M4 Bare Metal (16 GB RAM, 10 Cores)\n");
    printf("================================================================================\n\n");

    benchmark_true_full_stream(10000, "10k Nodes (0.737 GB - Fits in L2/SLC Cache)");
    benchmark_true_full_stream(50000, "50k Nodes (3.686 GB - Fits in System RAM)");
    benchmark_true_full_stream(100000, "100k Nodes (7.373 GB - Exceeds Cache, Hits DRAM)");
    benchmark_true_full_stream(150000, "150k Nodes (11.059 GB - Heavy DRAM Memory Pressure)");

    printf("================================================================================\n");
    printf("  [VERDICT] TRUE FULL-STREAM AUDIT COMPLETE\n");
    printf("================================================================================\n");
    return 0;
}
