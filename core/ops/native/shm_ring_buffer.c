/* ==============================================================================
 * XORAS::OS - Shared Memory Lock-Free Atomic Ring Buffer (macOS / Apple Silicon M4)
 * Mandate: Eliminates SQLite POSIX File Lock Contention across 26,000 MTPO Nodes
 * ============================================================================== */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <stdatomic.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <unistd.h>

#define RING_BUFFER_CAPACITY 65536
#define STRIDE_SIZE 3200 // 3,200-byte aligned HexCell stride

typedef struct {
    uint64_t sequence_id;
    uint64_t session_rank;
    uint32_t node_id;
    uint32_t payload_len;
    uint8_t  payload[STRIDE_SIZE - 24];
} __attribute__((packed, aligned(128))) HexCellStride;

typedef struct {
    _Atomic uint64_t head;
    _Atomic uint64_t tail;
    HexCellStride entries[RING_BUFFER_CAPACITY];
} SharedRingBuffer;

static SharedRingBuffer* g_ring_buffer = NULL;

int init_shm_ring_buffer(const char* shm_name) {
    int shm_fd = shm_open(shm_name, O_CREAT | O_RDWR, 0666);
    if (shm_fd < 0) {
        perror("shm_open failed");
        return -1;
    }

    if (ftruncate(shm_fd, sizeof(SharedRingBuffer)) < 0) {
        perror("ftruncate failed");
        close(shm_fd);
        return -1;
    }

    g_ring_buffer = (SharedRingBuffer*)mmap(NULL, sizeof(SharedRingBuffer), PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0);
    close(shm_fd);

    if (g_ring_buffer == MAP_FAILED) {
        perror("mmap failed");
        return -1;
    }

    atomic_store(&g_ring_buffer->head, 0);
    atomic_store(&g_ring_buffer->tail, 0);
    return 0;
}

int push_hexcell_stride(uint64_t sequence_id, uint64_t session_rank, uint32_t node_id, const uint8_t* payload, uint32_t len) {
    if (!g_ring_buffer) return -1;

    uint64_t current_tail = atomic_fetch_add(&g_ring_buffer->tail, 1);
    uint64_t index = current_tail % RING_BUFFER_CAPACITY;

    HexCellStride* entry = &g_ring_buffer->entries[index];
    entry->sequence_id = sequence_id;
    entry->session_rank = session_rank;
    entry->node_id = node_id;
    entry->payload_len = len > (STRIDE_SIZE - 24) ? (STRIDE_SIZE - 24) : len;
    memcpy(entry->payload, payload, entry->payload_len);

    return 0;
}

uint64_t get_shm_tail_count() {
    if (!g_ring_buffer) return 0;
    return atomic_load(&g_ring_buffer->tail);
}
