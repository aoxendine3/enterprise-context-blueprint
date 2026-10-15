/**
 * MTPO: Monotonic Trajectory Pre-Order & 3-Phase Saga Engine
 * =================================================================
 * HexCell lock-free concurrent memory lattice and 3-Phase Saga Undo coordinator.
 *
 * SAGA STAGES:
 *   1. SAGA_RESERVE   - Optimistic atomic slot reservation
 *   2. SAGA_MUTATE    - Isolated shadow page mutation
 *   3. SAGA_COMMIT    - Atomic pointer swap into active register
 *   4. SAGA_COMPENSATE- Guaranteed rollback on fault / constraint failure
 */

#ifndef MTPO_SAGA_H
#define MTPO_SAGA_H

#include <stdint.h>
#include <stdbool.h>
#include <stdatomic.h>
#include <stddef.h>

#define HEXCELL_SLOTS 6
#define CACHE_LINE_SIZE 64

typedef enum {
    SAGA_IDLE = 0,
    SAGA_RESERVED = 1,
    SAGA_MUTATING = 2,
    SAGA_COMMITTED = 3,
    SAGA_COMPENSATED = 4
} SagaState;

typedef struct {
    uint64_t tx_id;
    _Atomic uint32_t state;
    uint64_t reserve_val;
    uint64_t mutate_val;
    uint64_t commit_val;
    bool fault_injected;
} SagaTransaction;

typedef struct {
    // 6-fold symmetrical lock-free slots aligned to cache lines
    _Alignas(CACHE_LINE_SIZE) _Atomic uint64_t active_slots[HEXCELL_SLOTS];
    _Alignas(CACHE_LINE_SIZE) _Atomic uint64_t shadow_slots[HEXCELL_SLOTS];
    _Atomic uint64_t total_committed;
    _Atomic uint64_t total_compensated;
} HexCellRing;

// Public API
void mtpo_ring_init(HexCellRing *ring);
bool mtpo_saga_execute(HexCellRing *ring, uint32_t slot_idx, uint64_t tx_id, uint64_t new_val, bool inject_fault);
uint64_t mtpo_ring_read(HexCellRing *ring, uint32_t slot_idx);

#endif // MTPO_SAGA_H
