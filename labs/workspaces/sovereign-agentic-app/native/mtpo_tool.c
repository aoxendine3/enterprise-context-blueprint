/**
 * MTPO Tool: High-Performance CLI & IPC Bridge to libmtpo_engine.dylib
 * ===================================================================
 * Maps HexCellRing to POSIX Shared Memory (/mtpo_hexcell_ring) with C11 atomic CAS.
 * Provides microsecond-level JSON output for Node.js / Remix server singletons.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <inttypes.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>

#include "../../mtpo/src/mtpo_saga.h"

#define SHM_RING_NAME "/mtpo_hexcell_ring"

static HexCellRing* get_shared_ring(bool reset) {
    int flags = O_RDWR | O_CREAT;
    int fd = shm_open(SHM_RING_NAME, flags, 0666);
    if (fd < 0) {
        fprintf(stderr, "{\"error\": \"shm_open failed: %s\"}\n", strerror(errno));
        return NULL;
    }

    struct stat sb;
    if (fstat(fd, &sb) != 0 || sb.st_size < (off_t)sizeof(HexCellRing)) {
        if (ftruncate(fd, sizeof(HexCellRing)) != 0) {
            fprintf(stderr, "{\"error\": \"ftruncate failed: %s\"}\n", strerror(errno));
            close(fd);
            return NULL;
        }
        reset = true;
    }

    void *addr = mmap(NULL, sizeof(HexCellRing), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);

    if (addr == MAP_FAILED) {
        fprintf(stderr, "{\"error\": \"mmap failed: %s\"}\n", strerror(errno));
        return NULL;
    }

    HexCellRing *ring = (HexCellRing*)addr;
    if (reset) {
        mtpo_ring_init(ring);
    }
    return ring;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("{\"error\": \"Usage: %s <init|read|execute> [args...]\"}\n", argv[0]);
        return 1;
    }

    const char *cmd = argv[1];

    if (strcmp(cmd, "init") == 0) {
        HexCellRing *ring = get_shared_ring(true);
        if (!ring) return 1;
        printf("{\"status\": \"INITIALIZED\", \"shm\": \"%s\", \"slots\": %d, \"slot_size_bytes\": %zu}\n",
               SHM_RING_NAME, HEXCELL_SLOTS, sizeof(HexCellRing));
        munmap(ring, sizeof(HexCellRing));
        return 0;
    }

    if (strcmp(cmd, "read") == 0) {
        HexCellRing *ring = get_shared_ring(false);
        if (!ring) return 1;

        printf("{\n");
        printf("  \"status\": \"OK\",\n");
        printf("  \"slots\": [\n");
        for (int i = 0; i < HEXCELL_SLOTS; i++) {
            uint64_t val = mtpo_ring_read(ring, i);
            uint64_t shadow = atomic_load_explicit(&ring->shadow_slots[i], memory_order_acquire);
            printf("    {\"slot\": %d, \"active\": \"0x%016" PRIx64 "\", \"shadow\": \"0x%016" PRIx64 "\" }%s\n",
                   i, val, shadow, (i == HEXCELL_SLOTS - 1) ? "" : ",");
        }
        printf("  ],\n");
        printf("  \"total_committed\": %" PRIu64 ",\n", atomic_load_explicit(&ring->total_committed, memory_order_relaxed));
        printf("  \"total_compensated\": %" PRIu64 "\n", atomic_load_explicit(&ring->total_compensated, memory_order_relaxed));
        printf("}\n");

        munmap(ring, sizeof(HexCellRing));
        return 0;
    }

    if (strcmp(cmd, "execute") == 0) {
        if (argc < 5) {
            printf("{\"error\": \"Usage: %s execute <slot_idx> <tx_id> <new_val_hex_or_dec> [inject_fault:0|1]\"}\n", argv[0]);
            return 1;
        }

        uint32_t slot_idx = (uint32_t)strtoul(argv[2], NULL, 10);
        uint64_t tx_id = (uint64_t)strtoull(argv[3], NULL, 10);
        uint64_t new_val = (argv[4][0] == '0' && (argv[4][1] == 'x' || argv[4][1] == 'X')) ?
                           (uint64_t)strtoull(argv[4], NULL, 16) :
                           (uint64_t)strtoull(argv[4], NULL, 10);
        bool fault = (argc >= 6 && atoi(argv[5]) == 1);

        HexCellRing *ring = get_shared_ring(false);
        if (!ring) return 1;

        bool success = mtpo_saga_execute(ring, slot_idx, tx_id, new_val, fault);
        uint64_t active_after = mtpo_ring_read(ring, slot_idx);
        uint64_t shadow_after = atomic_load_explicit(&ring->shadow_slots[slot_idx], memory_order_acquire);
        uint64_t committed = atomic_load_explicit(&ring->total_committed, memory_order_relaxed);
        uint64_t compensated = atomic_load_explicit(&ring->total_compensated, memory_order_relaxed);

        printf("{\n");
        printf("  \"status\": \"%s\",\n", success ? "COMMITTED" : "COMPENSATED_ROLLBACK");
        printf("  \"success\": %s,\n", success ? "true" : "false");
        printf("  \"slot_idx\": %u,\n", slot_idx);
        printf("  \"tx_id\": %" PRIu64 ",\n", tx_id);
        printf("  \"active_val\": \"0x%016" PRIx64 "\",\n", active_after);
        printf("  \"shadow_val\": \"0x%016" PRIx64 "\",\n", shadow_after);
        printf("  \"total_committed\": %" PRIu64 ",\n", committed);
        printf("  \"total_compensated\": %" PRIu64 "\n", compensated);
        printf("}\n");

        munmap(ring, sizeof(HexCellRing));
        return success ? 0 : 2;
    }

    printf("{\"error\": \"Unknown command '%s'\"}\n", cmd);
    return 1;
}
