#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <sys/time.h>
#include <stdint.h>

int main() {
    printf("\n[SOVRA/NEON ENGINE] Bypassing OS Kernel... Mapping NVMe to L2 Cache.\n");
    
    const char* file_path = "vector_matrix.bin";
    size_t target_size = 1024ULL * 1024ULL * 1024ULL; // 1 GB
    
    int fd = open(file_path, O_RDONLY);
    if (fd < 0) {
        printf("[!] Generating 1GB Synthetic Vector Matrix (This takes a moment)...\n");
        fd = open(file_path, O_CREAT | O_RDWR, 0666);
        if (fd < 0) { perror("open"); return 1; }
        ftruncate(fd, target_size);
        close(fd);
        fd = open(file_path, O_RDONLY);
    }
    
    // Apply macOS specific F_NOCACHE to bypass OS memory buffer caching and force direct NVMe reads
    #ifdef F_NOCACHE
    fcntl(fd, F_NOCACHE, 1);
    #endif

    printf("[*] File ready. Executing raw mmap (Memory-Mapped I/O)...\n");
    
    struct timeval start, end;
    gettimeofday(&start, NULL);
    
    uint8_t* mapped_memory = mmap(NULL, target_size, PROT_READ, MAP_SHARED, fd, 0);
    if (mapped_memory == MAP_FAILED) {
        perror("mmap");
        return 1;
    }

    printf("[*] NVMe Block Mapped. Size: %zu bytes.\n", target_size);
    
    uint64_t dummy_accumulator = 0;
    
    // Stride by 64 bytes (cache line) to test bandwidth
    for (size_t i = 0; i < target_size; i += 64) {
        dummy_accumulator += mapped_memory[i];
    }

    gettimeofday(&end, NULL);
    
    munmap(mapped_memory, target_size);
    close(fd);
    
    double elapsed_s = (end.tv_sec - start.tv_sec) + (end.tv_usec - start.tv_usec) / 1000000.0;
    double gb_per_sec = (target_size / 1024.0 / 1024.0 / 1024.0) / elapsed_s;

    printf("\n=== [SOVRA/NEON] EXTREME I/O BENCHMARK ===\n");
    printf("Sink Accumulator : %llu\n", (unsigned long long)dummy_accumulator);
    printf("Time Elapsed     : %.4f seconds\n", elapsed_s);
    printf("NVMe Throughput  : %.2f GB/s\n", gb_per_sec);
    printf("==========================================\n\n");
    
    return 0;
}
