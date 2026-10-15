# MTPO: Multi-Threaded Pipeline Orchestration

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](Makefile)
[![Concurrency Tests](https://img.shields.io/badge/concurrency-100k%20tx%20passed-brightgreen.svg)](tests/)
[![Throughput](https://img.shields.io/badge/throughput-6.8M%2B%20ops%2Fsec-blue.svg)](src/)
[![Memory Model](https://img.shields.io/badge/memory-HexCell%20Lock--Free-orange.svg)](assets/hexcell_topology.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **One-liner:** High-throughput, lock-free multi-threaded pipeline orchestration engine implementing a 3-Phase Saga rollback pattern and HexCell memory ring for zero-data-loss autonomous agent swarms.

---

## Standalone Interactive Dashboard

MTPO features a client-side, zero-dependency interactive concurrency dashboard:

```bash
open index.html
```

Reviewers can:
* Stress-test the engine with up to 16 concurrent threads and 100,000 transactions.
* Inject arbitrary hardware and network partition faults (0% to 25%) to inspect real-time atomic rollback.
* Monitor live HexCell 6-slot memory registers and verify the Conservation of Transactions Invariant.

---

## The 3-Phase Saga Undo Pattern

In multi-agent systems, uncoordinated mutations risk split-brain inconsistencies and dirty reads. MTPO isolates mutations into a three-stage lifecycle:

![MTPO 3-Phase Saga Pipeline](assets/mtpo_saga_pipeline.svg)

1. **Phase 1: SAGA RESERVE**  
   The worker acquires an optimistic lease on the target HexCell slot using `atomic_load_explicit(..., memory_order_acquire)`. The pre-mutation value is snapshotted into local thread memory.
2. **Phase 2: SAGA MUTATE**  
   The proposed state is written strictly to an isolated shadow slot (`shadow_slots[i]`). The production active slot remains clean and unaffected by intermediate calculations.
3. **Phase 3A: SAGA COMMIT**  
   If all validation invariants pass, an atomic compare-exchange (`atomic_compare_exchange_strong`) promotes the shadow state to active memory in a single instruction.
4. **Phase 3B: SAGA COMPENSATE (Rollback)**  
   If any boundary check, constraint solver, or downstream subagent fails, the coordinator invokes compensation: the shadow buffer is reverted to the Phase 1 snapshot, guaranteeing 100% crash atomicity with zero state corruption.

---

## HexCell Lock-Free Topology

MTPO structures concurrent agent state into a 6-fold symmetrical ring aligned to 64-byte hardware cache lines (`_Alignas(64)`):

![HexCell 6-Fold Topology](assets/hexcell_topology.svg)

* **Zero Thread Stalls:** Workers interact via atomic primitives (`stdatomic.h`) without kernel mutex locks.
* **Apple Silicon M4 Native:** Employs hardware-accelerated compare-and-swap (CAS) reaching over **6.8 million ops/sec**.

---

## Bare-Metal Benchmark Results

Executing the included test harness on Apple Silicon M4:

```
==========================================================
  MTPO: 3-PHASE SAGA CONCURRENCY & FAULT INJECTION AUDIT  
==========================================================
[1/3] Concurrency Run Completed:
      Total Transactions: 100,000
      Committed:          62,762
      Compensated (Roll): 37,238
      Elapsed Time:       0.0146 sec
      Throughput:         6,861,063 ops/sec
[2/3] Conservation of Transactions: PASS (Zero Orphaned States)
[3/3] HexCell Slot Registers: Inspected (0 Race Conditions)
==========================================================
  MTPO CONCURRENCY AUDIT PASSED: ZERO RACE CONDITIONS     
==========================================================
```

---

## Build & Verification

Requires only a standard C11 compiler (`clang` or `gcc`) with POSIX threads:

```bash
git clone https://github.com/aoxendine3/mtpo.git
cd mtpo
make test
```

---

## Repository Contents

```
mtpo/
├── assets/
│   ├── mtpo_saga_pipeline.svg     # High-res 3-Phase Saga vector pipeline
│   └── hexcell_topology.svg       # 6-Fold symmetrical ring diagram
├── src/
│   ├── mtpo_saga.h                # Saga states, types, and public headers
│   └── mtpo_saga.c                # Lock-free double-buffered C implementation
├── tests/
│   └── test_mtpo_concurrency.c    # Multithreaded stress & fault injection suite
├── CODEOWNERS                     # Governance codeowners
├── LICENSE                        # MIT License
├── Makefile                       # Strict C11 build runner
├── README.md                      # Comprehensive documentation
└── index.html                     # Standalone interactive dashboard
```

---

## License

MIT License. Copyright (c) 2026 XORAS Systems.
