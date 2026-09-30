// Calibrated SOVRA C/NEON 18,432-D Hexological Vector Engine Benchmark
// Substrate: Apple Silicon M4 Bare Metal (10 CPU Cores / ARM64 NEON SIMD FMA)

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <time.h>
#include <pthread.h>
#include <arm_neon.h>
#include <mach/mach_time.h>

#define DIM 18432
#define TOTAL_VECTORS 100000
#define NUM_CORES 10
#define ITERATIONS 50

static volatile double g_volatile_sink = 0.0;

static double get_time_sec(void) {
    static mach_timebase_info_data_t timebase;
    if (timebase.denom == 0) {
        mach_timebase_info(&timebase);
    }
    uint64_t time = mach_absolute_time();
    return (double)time * timebase.numer / timebase.denom / 1e9;
}

static inline float sovra_18432d_dot(const float *a, const float *b) {
    float32x4_t acc0 = vdupq_n_f32(0.0f);
    float32x4_t acc1 = vdupq_n_f32(0.0f);

    for (int i = 0; i < DIM; i += 8) {
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
    uint32_t start_idx;
    uint32_t count;
    double local_sum;
} WorkerTask;

static void *sovra_worker(void *arg) {
    WorkerTask *task = (WorkerTask *)arg;
    double sum = 0.0;
    for (uint32_t i = 0; i < task->count; i++) {
        uint32_t vec_idx = task->start_idx + i;
        float dot = sovra_18432d_dot(task->query, task->matrix + (vec_idx * DIM));
        sum += dot;
    }
    task->local_sum = sum;
    return NULL;
}

static int compare_doubles(const void *a, const void *b) {
    double da = *(const double *)a;
    double db = *(const double *)b;
    return (da > db) - (da < db);
}

int main(void) {
    float *query = (float *)aligned_alloc(64, DIM * sizeof(float));
    float *matrix = (float *)aligned_alloc(64, (size_t)TOTAL_VECTORS * DIM * sizeof(float));

    for (int i = 0; i < DIM; i++) query[i] = (i % 100) * 0.001f;
    for (size_t i = 0; i < (size_t)TOTAL_VECTORS * DIM; i++) matrix[i] = ((i + 1) % 100) * 0.001f;

    uint32_t vecs_per_core = TOTAL_VECTORS / NUM_CORES;
    pthread_t threads[NUM_CORES];
    WorkerTask tasks[NUM_CORES];

    // Warmup Pass (10 passes)
    for (int warm = 0; warm < 10; warm++) {
        for (int t = 0; t < NUM_CORES; t++) {
            tasks[t].query = query;
            tasks[t].matrix = matrix;
            tasks[t].start_idx = t * vecs_per_core;
            tasks[t].count = (t == NUM_CORES - 1) ? (TOTAL_VECTORS - tasks[t].start_idx) : vecs_per_core;
            pthread_create(&threads[t], NULL, sovra_worker, &tasks[t]);
        }
        for (int t = 0; t < NUM_CORES; t++) {
            pthread_join(threads[t], NULL);
            g_volatile_sink += tasks[t].local_sum;
        }
    }

    // Timed Iterations
    double sample_latencies_ms[ITERATIONS];
    double total_sum = 0.0;

    double t0_all = get_time_sec();
    for (int iter = 0; iter < ITERATIONS; iter++) {
        double iter_start = get_time_sec();

        for (int t = 0; t < NUM_CORES; t++) {
            tasks[t].query = query;
            tasks[t].matrix = matrix;
            tasks[t].start_idx = t * vecs_per_core;
            tasks[t].count = (t == NUM_CORES - 1) ? (TOTAL_VECTORS - tasks[t].start_idx) : vecs_per_core;
            pthread_create(&threads[t], NULL, sovra_worker, &tasks[t]);
        }

        for (int t = 0; t < NUM_CORES; t++) {
            pthread_join(threads[t], NULL);
            total_sum += tasks[t].local_sum;
        }

        double iter_end = get_time_sec();
        sample_latencies_ms[iter] = (iter_end - iter_start) * 1000.0;
    }
    double total_elapsed_sec = get_time_sec() - t0_all;
    g_volatile_sink += total_sum;

    double avg_pass_sec = total_elapsed_sec / ITERATIONS;
    double avg_pass_ms = avg_pass_sec * 1000.0;

    double ops_sec = TOTAL_VECTORS / avg_pass_sec;
    double gflops = ((double)TOTAL_VECTORS * DIM * 2.0) / (avg_pass_sec * 1e9);
    double gb_sec = (((double)TOTAL_VECTORS * DIM * 4.0) / (1024.0 * 1024.0 * 1024.0)) / avg_pass_sec;

    qsort(sample_latencies_ms, ITERATIONS, sizeof(double), compare_doubles);
    double p50_pass_ms = sample_latencies_ms[(int)(ITERATIONS * 0.50)];
    double p90_pass_ms = sample_latencies_ms[(int)(ITERATIONS * 0.90)];
    double p99_pass_ms = sample_latencies_ms[(int)(ITERATIONS * 0.99)];

    double p50_vec_us = (p50_pass_ms * 1000.0) / TOTAL_VECTORS;
    double p90_vec_us = (p90_pass_ms * 1000.0) / TOTAL_VECTORS;
    double p99_vec_us = (p99_pass_ms * 1000.0) / TOTAL_VECTORS;

    printf("{\n");
    printf("  \"language\": \"SOVRA C/NEON (clang -O3)\",\n");
    printf("  \"avg_pass_ms\": %.2f,\n", avg_pass_ms);
    printf("  \"evals_per_sec\": %.0f,\n", ops_sec);
    printf("  \"gflops\": %.2f,\n", gflops);
    printf("  \"bandwidth_gb_sec\": %.2f,\n", gb_sec);
    printf("  \"p50_us\": %.2f,\n", p50_vec_us);
    printf("  \"p90_us\": %.2f,\n", p90_vec_us);
    printf("  \"p99_us\": %.2f,\n", p99_vec_us);
    printf("  \"sink_check\": %.2f\n", g_volatile_sink);
    printf("}\n");

    free(query);
    free(matrix);
    return 0;
}
