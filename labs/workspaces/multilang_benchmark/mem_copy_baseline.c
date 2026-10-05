// Ground-Truth DRAM Memory Streaming Bandwidth Baseline for Apple Silicon M4
// Uses 1 GB streaming buffers to avoid RAM exhaustion on 16GB systems.

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <pthread.h>
#include <mach/mach_time.h>
#include <arm_neon.h>

#define BUFFER_BYTES (1024ULL * 1024ULL * 1024ULL) // 1 GB Buffer
#define NUM_CORES 10
#define ITERATIONS 50

static double get_time_sec(void) {
    static mach_timebase_info_data_t timebase;
    if (timebase.denom == 0) {
        mach_timebase_info(&timebase);
    }
    uint64_t time = mach_absolute_time();
    return (double)time * timebase.numer / timebase.denom / 1e9;
}

typedef struct {
    const uint8_t *src;
    uint8_t *dst;
    size_t count;
} CopyTask;

static void *copy_worker(void *arg) {
    CopyTask *task = (CopyTask *)arg;
    memcpy(task->dst, task->src, task->count);
    return NULL;
}

int main(void) {
    uint8_t *src = (uint8_t *)aligned_alloc(64, BUFFER_BYTES);
    uint8_t *dst = (uint8_t *)aligned_alloc(64, BUFFER_BYTES);

    if (!src || !dst) {
        fprintf(stderr, "❌ Allocation failed for 1 GB STREAM buffers\n");
        return 1;
    }

    memset(src, 0xAB, BUFFER_BYTES);
    memset(dst, 0x00, BUFFER_BYTES);

    // Warmup pass
    for (int iter = 0; iter < 5; iter++) {
        memcpy(dst, src, BUFFER_BYTES);
    }

    pthread_t threads[NUM_CORES];
    CopyTask tasks[NUM_CORES];
    size_t bytes_per_core = BUFFER_BYTES / NUM_CORES;

    double t0 = get_time_sec();
    for (int iter = 0; iter < ITERATIONS; iter++) {
        for (int t = 0; t < NUM_CORES; t++) {
            tasks[t].src = src + t * bytes_per_core;
            tasks[t].dst = dst + t * bytes_per_core;
            tasks[t].count = (t == NUM_CORES - 1) ? (BUFFER_BYTES - t * bytes_per_core) : bytes_per_core;
            pthread_create(&threads[t], NULL, copy_worker, &tasks[t]);
        }
        for (int t = 0; t < NUM_CORES; t++) {
            pthread_join(threads[t], NULL);
        }
    }
    double total_time = get_time_sec() - t0;
    double avg_time_per_pass = total_time / ITERATIONS;

    // 1 GB read + 1 GB write = 2 GB memory traffic per pass
    double total_gigabytes_transferred = (double)(BUFFER_BYTES * 2ULL) / (1024.0 * 1024.0 * 1024.0);
    double bandwidth_gb_sec = total_gigabytes_transferred / avg_time_per_pass;

    printf("{\n");
    printf("  \"benchmark\": \"M4 LPDDR5X Hardware STREAM Baseline\",\n");
    printf("  \"total_dataset_gb\": 1.0000,\n");
    printf("  \"avg_pass_ms\": %.2f,\n", avg_time_per_pass * 1000.0);
    printf("  \"effective_dram_bandwidth_gb_sec\": %.2f\n", bandwidth_gb_sec);
    printf("}\n");

    free(src);
    free(dst);
    return 0;
}
