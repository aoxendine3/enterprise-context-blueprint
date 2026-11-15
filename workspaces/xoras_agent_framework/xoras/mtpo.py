"""
XORAS MTPO: Monotonic Trajectory Pre-Order Concurrency Engine
=============================================================
6-slot HexCell memory ring with a 3-Phase Saga deterministic undo coordinator
(Reserve -> Mutate -> Commit / Compensate).

HONESTY NOTE — THIS IS A LOCK-SHARDED MODEL, NOT A LOCK-FREE RING
-----------------------------------------------------------------
Earlier revisions of this file described the ring as "lock-free" and claimed a
"sub-2µs p99 guarantee under total cache-line contention". Both claims were
false: the implementation used one process-wide ``threading.Lock`` and the
latency numbers came from a benchmark whose critical section was a single
counter increment.

What the ring actually is: six independently locked slots, so a transaction on
slot *i* contends only with other transactions on slot *i* (1/6 of the swarm
under uniform selection, 100% under a hotspot). Per-slot mutation is
copy-on-write except for the increment of an in-flight counter, and
compensation restores the pre-image, so a failed transaction leaves no partial
state.

What it is not: it is not wait-free, it does not elide the GIL, and its p99
under real contention depends on the payload size, not on a constant. Measured
behaviour lives in ``tests/test_mtpo_ast_gate_scaling.py``; treat the numbers in
that receipt as the only claim we make.

Scaling beyond a single Python process requires moving each slot's lock into a
shared-memory primitive or replacing the ring with an SPSC queue per worker —
see the scaling receipt for the measured breakpoint on this host.
"""

import threading
from typing import List, Optional

HEXCELL_SLOTS = 6
CACHE_LINE_SIZE = 128


class SagaState:
    IDLE = 0
    RESERVED = 1
    MUTATING = 2
    COMMITTED = 3
    COMPENSATED = 4


class HexCellRing:
    """Six independently locked saga slots (lock-sharded, not lock-free).

    A transaction on slot *i* only contends with other transactions on slot *i*.
    Global counters (``total_committed``, ``total_compensated``) are updated
    under their own lock and are the only cross-slot serialization point.
    """

    def __init__(self) -> None:
        # One lock per slot: contention scales with the number of writers on the
        # same slot, not with the size of the swarm.
        self._slot_locks: List[threading.Lock] = [threading.Lock() for _ in range(HEXCELL_SLOTS)]
        self.active_slots = [0] * HEXCELL_SLOTS
        self.shadow_slots = [0] * HEXCELL_SLOTS
        self._counter_lock = threading.Lock()
        self.total_committed = 0
        self.total_compensated = 0

    def execute_saga(self, slot_idx: int, tx_id: int, new_val: int, inject_fault: bool = False) -> bool:
        """Execute a 3-Phase Saga transaction on ``slot_idx``.

        Phase 1 — reserve: read the pre-image.
        Phase 2 — mutate: write the isolated shadow register.
        Phase 3A — commit: publish the shadow value and bump ``total_committed``.
        Phase 3B — compensate: restore the pre-image and bump ``total_compensated``.

        Returns True on commit, False on compensated rollback. Raises
        ``ValueError`` for an out-of-range slot index (never silently ignores).
        """
        if slot_idx < 0 or slot_idx >= HEXCELL_SLOTS:
            raise ValueError(f"slot_idx must be between 0 and {HEXCELL_SLOTS - 1}")

        with self._slot_locks[slot_idx]:
            initial_val = self.active_slots[slot_idx]
            self.shadow_slots[slot_idx] = new_val

            if inject_fault:
                self.shadow_slots[slot_idx] = initial_val
                with self._counter_lock:
                    self.total_compensated += 1
                return False

            self.active_slots[slot_idx] = new_val

        # Counter update happens outside the slot lock so a slow counter cannot
        # hold the slot hostage; the counter lock is a single increment wide.
        with self._counter_lock:
            self.total_committed += 1
        return True

    def apply_delta(self, slot_idx: int, delta: int) -> int:
        """Atomically add ``delta`` to a slot and return the new value.

        Atomic read-modify-write is what lets a swarm share six slots without
        lost updates: the read and the write happen inside the same slot lock.
        A compensating write is just ``apply_delta(slot, -delta)``; because
        addition commutes, interleaving with other writers cannot corrupt the
        invariant ``sum(final) == sum(committed deltas)``.
        """
        if slot_idx < 0 or slot_idx >= HEXCELL_SLOTS:
            raise ValueError(f"slot_idx must be between 0 and {HEXCELL_SLOTS - 1}")
        with self._slot_locks[slot_idx]:
            self.active_slots[slot_idx] += delta
            self.shadow_slots[slot_idx] = self.active_slots[slot_idx]
            return self.active_slots[slot_idx]

    def read(self, slot_idx: int) -> int:
        if slot_idx < 0 or slot_idx >= HEXCELL_SLOTS:
            raise ValueError(f"slot_idx must be between 0 and {HEXCELL_SLOTS - 1}")
        with self._slot_locks[slot_idx]:
            return self.active_slots[slot_idx]


__all__ = ["HexCellRing", "HEXCELL_SLOTS", "SagaState"]
