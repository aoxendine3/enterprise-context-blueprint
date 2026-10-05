#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <sys/time.h>

#define NUM_CELLS 10000000 // 10 Million

typedef struct __attribute__((packed)) { uint8_t data[128]; } Cell128;
typedef struct __attribute__((packed)) { uint8_t data[512]; } Cell512;

double get_time() {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec + tv.tv_usec * 1e-6;
}

int main() {
    printf("====================================================\n");
    printf(" XORAS BARE-METAL HEXCELL: 128 vs 512 BENCHMARK \n");
    printf("====================================================\n\n");

    volatile uint64_t checksum = 0; // Prevent compiler optimization

    // ----------------------------------------------------
    // BEFORE: 128-BYTE HEXCELL
    // ----------------------------------------------------
    Cell128* arr128 = malloc(sizeof(Cell128) * NUM_CELLS);
    if (!arr128) { printf("OOM\n"); return 1; }
    
    double start_128 = get_time();
    for(int i = 0; i < NUM_CELLS; i++) {
        arr128[i].data[0] = (i & 0xFF);
        arr128[i].data[64] = 0xAA;
        arr128[i].data[127] = 0xBB;
        checksum += arr128[i].data[0] + arr128[i].data[127];
    }
    double elapsed_128 = get_time() - start_128;
    double mb_128 = (NUM_CELLS * 128.0) / (1024.0 * 1024.0);
    double tp_128 = (mb_128 / 1024.0) / elapsed_128;
    
    printf("[BEFORE] 128-BYTE HEXCELL\n");
    printf("  Elements  : %d\n", NUM_CELLS);
    printf("  Memory    : %.2f MB\n", mb_128);
    printf("  Time      : %.4f seconds\n", elapsed_128);
    printf("  Throughput: %.2f GB/s\n", tp_128);
    printf("  Latency   : %.2f ns/cell\n\n", (elapsed_128 * 1e9) / NUM_CELLS);
    free(arr128);

    // ----------------------------------------------------
    // AFTER: 512-BYTE HEXCELL
    // ----------------------------------------------------
    Cell512* arr512 = malloc(sizeof(Cell512) * NUM_CELLS);
    if (!arr512) { printf("OOM\n"); return 1; }
    
    double start_512 = get_time();
    for(int i = 0; i < NUM_CELLS; i++) {
        arr512[i].data[0] = (i & 0xFF);
        arr512[i].data[256] = 0xAA;
        arr512[i].data[511] = 0xBB;
        checksum += arr512[i].data[0] + arr512[i].data[511];
    }
    double elapsed_512 = get_time() - start_512;
    double mb_512 = (NUM_CELLS * 512.0) / (1024.0 * 1024.0);
    double tp_512 = (mb_512 / 1024.0) / elapsed_512;
    
    printf("[AFTER] 512-BYTE HEXCELL\n");
    printf("  Elements  : %d\n", NUM_CELLS);
    printf("  Memory    : %.2f MB\n", mb_512);
    printf("  Time      : %.4f seconds\n", elapsed_512);
    printf("  Throughput: %.2f GB/s\n", tp_512);
    printf("  Latency   : %.2f ns/cell\n\n", (elapsed_512 * 1e9) / NUM_CELLS);
    free(arr512);
    
    // Output checksum so compiler doesn't kill it
    printf("Integrity Checksum: %llu\n", checksum);

    return 0;
}
