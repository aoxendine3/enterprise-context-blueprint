#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdatomic.h>
#include <pthread.h>
#include <time.h>
#include <sys/resource.h>

#define HEXCELL_SLOTS 6
#define TOTAL_OPS 1000000
#define NUM_THREADS 8
#define OPS_PER_THREAD (TOTAL_OPS / NUM_THREADS)

typedef struct {
    _Alignas(128) _Atomic uint64_t active_slots[HEXCELL_SLOTS];
    _Alignas(128) _Atomic uint64_t shadow_slots[HEXCELL_SLOTS];
    _Atomic uint64_t total_committed;
    _Atomic uint64_t total_compensated;
} HexCellRing;

static HexCellRing g_ring;

static inline double get_time_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

static inline bool saga_execute(HexCellRing *ring, uint32_t slot, uint64_t tx_id, uint64_t new_val) {
    uint64_t initial = atomic_load_explicit(&ring->active_slots[slot], memory_order_acquire);
    atomic_store_explicit(&ring->shadow_slots[slot], new_val, memory_order_release);

    uint64_t expected = initial;
    if (atomic_compare_exchange_strong_explicit(
            &ring->active_slots[slot],
            &expected,
            new_val,
            memory_order_acq_rel,
            memory_order_acquire)) {
        atomic_fetch_add_explicit(&ring->total_committed, 1ULL, memory_order_relaxed);
        return true;
    } else {
        atomic_store_explicit(&ring->shadow_slots[slot], initial, memory_order_release);
        atomic_fetch_add_explicit(&ring->total_compensated, 1ULL, memory_order_relaxed);
        return false;
    }
}

typedef struct {
    int thread_id;
    uint64_t local_committed;
    uint64_t local_retries;
} ThreadArgs;

static void* worker(void *arg) {
    ThreadArgs *targs = (ThreadArgs*)arg;
    uint64_t start_tx = (uint64_t)targs->thread_id * OPS_PER_THREAD + 1;

    for (uint64_t i = 0; i < OPS_PER_THREAD; i++) {
        uint64_t tx_id = start_tx + i;
        uint32_t slot = (uint32_t)(tx_id % HEXCELL_SLOTS);
        uint64_t new_val = 0xBEAF000000000000ULL | tx_id;

        while (!saga_execute(&g_ring, slot, tx_id, new_val)) {
            targs->local_retries++;
            // CAS contention retry
        }
        targs->local_committed++;
    }
    return NULL;
}

int main(void) {
    for (int i = 0; i < HEXCELL_SLOTS; i++) {
        atomic_init(&g_ring.active_slots[i], 0ULL);
        atomic_init(&g_ring.shadow_slots[i], 0ULL);
    }
    atomic_init(&g_ring.total_committed, 0ULL);
    atomic_init(&g_ring.total_compensated, 0ULL);

    pthread_t threads[NUM_THREADS];
    ThreadArgs args[NUM_THREADS];

    double t_start = get_time_sec();

    for (int i = 0; i < NUM_THREADS; i++) {
        args[i].thread_id = i;
        args[i].local_committed = 0;
        args[i].local_retries = 0;
        pthread_create(&threads[i], NULL, worker, &args[i]);
    }

    uint64_t total_retries = 0;
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
        total_retries += args[i].local_retries;
    }

    double t_end = get_time_sec();
    double elapsed_sec = t_end - t_start;
    double ops_sec = (double)TOTAL_OPS / elapsed_sec;
    double avg_latency_ns = (elapsed_sec / (double)TOTAL_OPS) * 1e9;

    struct rusage usage;
    getrusage(RUSAGE_SELF, &usage);
    // On macOS ru_maxrss is in bytes, on Linux in kilobytes
#if defined(__APPLE__)
    double rss_mb = (double)usage.ru_maxrss / (1024.0 * 1024.0);
#else
    double rss_mb = (double)usage.ru_maxrss / 1024.0;
#endif

    printf("{\n");
    printf("  \"language\": \"C11 (stdatomic.h -O3)\",\n");
    printf("  \"standard\": \"ISO/IEC 9899:2011\",\n");
    printf("  \"total_ops\": %d,\n", TOTAL_OPS);
    printf("  \"threads\": %d,\n", NUM_THREADS);
    printf("  \"elapsed_ms\": %.2f,\n", elapsed_sec * 1000.0);
    printf("  \"throughput_ops_sec\": %.0f,\n", ops_sec);
    printf("  \"avg_latency_ns\": %.2f,\n", avg_latency_ns);
    printf("  \"total_committed\": %llu,\n", (unsigned long long)atomic_load(&g_ring.total_committed));
    printf("  \"contention_retries\": %llu,\n", (unsigned long long)total_retries);
    printf("  \"peak_rss_mb\": %.2f\n", rss_mb);
    printf("}\n");

    return 0;
}
