/**
 * MTPO: Multi-Threaded Pipeline Orchestration & 3-Phase Saga Engine
 * =================================================================
 * Implementation of lock-free double-buffered HexCell ring and 3-Phase Saga.
 */

#include "mtpo_saga.h"
#include <string.h>

void mtpo_ring_init(HexCellRing *ring) {
    if (!ring) return;
    for (int i = 0; i < HEXCELL_SLOTS; i++) {
        atomic_init(&ring->active_slots[i], 0ULL);
        atomic_init(&ring->shadow_slots[i], 0ULL);
    }
    atomic_init(&ring->total_committed, 0ULL);
    atomic_init(&ring->total_compensated, 0ULL);
}

bool mtpo_saga_execute(HexCellRing *ring, uint32_t slot_idx, uint64_t tx_id, uint64_t new_val, bool inject_fault) {
    if (!ring || slot_idx >= HEXCELL_SLOTS) return false;

    SagaTransaction tx;
    tx.tx_id = tx_id;
    atomic_init(&tx.state, SAGA_IDLE);
    tx.fault_injected = inject_fault;

    // --- PHASE 1: SAGA RESERVE ---
    uint64_t initial_val = atomic_load_explicit(&ring->active_slots[slot_idx], memory_order_acquire);
    tx.reserve_val = initial_val;
    atomic_store_explicit(&tx.state, SAGA_RESERVED, memory_order_release);

    // --- PHASE 2: SAGA MUTATE (Isolated Shadow Slot) ---
    atomic_store_explicit(&tx.state, SAGA_MUTATING, memory_order_release);
    tx.mutate_val = new_val;
    atomic_store_explicit(&ring->shadow_slots[slot_idx], new_val, memory_order_release);

    // If fault injected, trigger Phase 3B: Compensate (Rollback)
    if (inject_fault) {
        // --- PHASE 3B: SAGA COMPENSATE ---
        // Restore shadow slot to original reserved value
        atomic_store_explicit(&ring->shadow_slots[slot_idx], tx.reserve_val, memory_order_release);
        atomic_store_explicit(&tx.state, SAGA_COMPENSATED, memory_order_release);
        atomic_fetch_add_explicit(&ring->total_compensated, 1ULL, memory_order_relaxed);
        return false; // Transaction rolled back safely
    }

    // --- PHASE 3A: SAGA COMMIT (Atomic Pointer / Slot Promotion) ---
    // Optimistic CAS commit
    uint64_t expected = initial_val;
    if (atomic_compare_exchange_strong_explicit(
            &ring->active_slots[slot_idx],
            &expected,
            new_val,
            memory_order_acq_rel,
            memory_order_acquire)) {
        atomic_store_explicit(&tx.state, SAGA_COMMITTED, memory_order_release);
        atomic_fetch_add_explicit(&ring->total_committed, 1ULL, memory_order_relaxed);
        return true;
    } else {
        // Contention collision detected -> Compensate
        atomic_store_explicit(&ring->shadow_slots[slot_idx], tx.reserve_val, memory_order_release);
        atomic_store_explicit(&tx.state, SAGA_COMPENSATED, memory_order_release);
        atomic_fetch_add_explicit(&ring->total_compensated, 1ULL, memory_order_relaxed);
        return false;
    }
}

uint64_t mtpo_ring_read(HexCellRing *ring, uint32_t slot_idx) {
    if (!ring || slot_idx >= HEXCELL_SLOTS) return 0ULL;
    return atomic_load_explicit(&ring->active_slots[slot_idx], memory_order_acquire);
}
