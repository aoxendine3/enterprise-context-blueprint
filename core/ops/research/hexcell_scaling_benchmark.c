#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <sys/time.h>

#define NUM_CELLS 10000000 // 10 Million

typedef struct { uint8_t data[128]; } Cell128;
typedef struct { uint8_t data[256]; } Cell256;
typedef struct { uint8_t data[512]; } Cell512;

double get_time() {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec + tv.tv_usec * 1e-6;
}

int main() {
    printf("====================================================\n");
    printf(" XORAS BARE-METAL HEXCELL SCALING BENCHMARK (M4)\n");
    printf("====================================================\n\n");

    // 128-BYTE
    Cell128* arr128 = malloc(sizeof(Cell128) * NUM_CELLS);
    double start = get_time();
    for(int i=0; i<NUM_CELLS; i++) {
        arr128[i].data[0] = 0xBE;
        arr128[i].data[127] = 0xAF;
    }
    double elapsed = get_time() - start;
    double mb = (NUM_CELLS * 128.0) / (1024.0 * 1024.0);
    printf("[128-BYTE HEXCELL] Elements: %d | Memory: %.2f MB | Time: %.4f s | Throughput: %.2f GB/s\n", NUM_CELLS, mb, elapsed, (mb / 1024.0) / elapsed);
    free(arr128);

    // 256-BYTE
    Cell256* arr256 = malloc(sizeof(Cell256) * NUM_CELLS);
    start = get_time();
    for(int i=0; i<NUM_CELLS; i++) {
        arr256[i].data[0] = 0xBE;
        arr256[i].data[255] = 0xAF;
    }
    elapsed = get_time() - start;
    mb = (NUM_CELLS * 256.0) / (1024.0 * 1024.0);
    printf("[256-BYTE HEXCELL] Elements: %d | Memory: %.2f MB | Time: %.4f s | Throughput: %.2f GB/s\n", NUM_CELLS, mb, elapsed, (mb / 1024.0) / elapsed);
    free(arr256);

    // 512-BYTE
    Cell512* arr512 = malloc(sizeof(Cell512) * NUM_CELLS);
    start = get_time();
    for(int i=0; i<NUM_CELLS; i++) {
        arr512[i].data[0] = 0xBE;
        arr512[i].data[511] = 0xAF;
    }
    elapsed = get_time() - start;
    mb = (NUM_CELLS * 512.0) / (1024.0 * 1024.0);
    printf("[512-BYTE HEXCELL] Elements: %d | Memory: %.2f MB | Time: %.4f s | Throughput: %.2f GB/s\n", NUM_CELLS, mb, elapsed, (mb / 1024.0) / elapsed);
    free(arr512);

    return 0;
}
