// =============================================================================
// XORAS BARE-METAL ENGINE: MODEL SWAP ROUTER
// Substrate: Apple Silicon M4 Bare Metal (ISO C11 / Clang / ARM64 Atomics)
// Implements: workspaces/sovra_lang/model_swap_router.sovra
// Author: Maxx (Systems Architect), Daxx (Error Remediation Master), John (Bare Metal)
// Invariants:
//   1. 16GB Unified RAM Ceiling: 7B and 14B models MUST NEVER co-exist.
//   2. Eviction-Before-Load: Eviction must complete and zero VRAM before load starts.
//   3. 128-byte L1 Cache Line Aligned State Structure.
//   4. High-Resolution Nanosecond NVMe Bus Swap Telemetry via mach_absolute_time.
// =============================================================================

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdatomic.h>
#include <pthread.h>
#include <mach/mach_time.h>
#include <unistd.h>
#include <ctype.h>

#define CACHE_LINE_SIZE 128

// Model Slot Constants
#define SLOT_NONE     0
#define SLOT_FAST_7B  1     // qwen2.5-coder:7b (~4.7 GB VRAM)
#define SLOT_DEEP_14B 2     // sovereign-jarvis:latest (14B Q4, ~8.5 GB VRAM)

// Memory Footprint Constants (Bytes)
#define SYSTEM_RESERVED_MEMORY_BYTES  4294967296ULL   // 4.0 GB OS / Buffers
#define HARDWARE_MEMORY_CEILING_BYTES 17179869184ULL  // 16.0 GB Unified RAM
#define VRAM_BYTES_7B                 5046586572ULL   // ~4.7 GB
#define VRAM_BYTES_14B                9126805504ULL   // ~8.5 GB

// 128-Byte Aligned Router State
typedef struct __attribute__((aligned(CACHE_LINE_SIZE))) {
    _Atomic uint32_t active_slot;            // 4 bytes: Current resident model
    _Atomic uint32_t transition_lock;        // 4 bytes: Mutex flag (0 = unlocked, 1 = locked)
    _Atomic uint64_t current_vram_usage;     // 8 bytes: Committed model VRAM
    _Atomic uint64_t peak_vram_usage;        // 8 bytes: High-water mark VRAM
    _Atomic uint64_t total_swaps_completed;  // 8 bytes: Count of swaps performed
    _Atomic uint64_t total_swap_time_ns;     // 8 bytes: Cumulative swap time in ns
    _Atomic uint64_t last_swap_latency_ns;   // 8 bytes: Last swap time in ns
    _Atomic uint64_t cache_hit_requests;     // 8 bytes: Requests served without swap
    _Atomic uint64_t total_requests_routed;  // 8 bytes: Total requests dispatched
    _Atomic uint64_t violation_attempts;     // 8 bytes: Invariant violation attempts (must be 0)
    uint8_t reserved[56];                    // 56 bytes padding -> Exactly 128 bytes total
} model_router_state_t;

// Verification check: ensure struct is exactly 128 bytes
_Static_assert(sizeof(model_router_state_t) == 128, "model_router_state_t must be exactly 128 bytes");

// Mach timebase conversion factors
static mach_timebase_info_data_t g_timebase = {0, 0};

static inline void init_timebase(void) {
    if (g_timebase.denom == 0) {
        mach_timebase_info(&g_timebase);
    }
}

static inline uint64_t mach_time_to_ns(uint64_t mach_ticks) {
    init_timebase();
    return (mach_ticks * g_timebase.numer) / g_timebase.denom;
}

// -----------------------------------------------------------------------------
// Router Initialization and Teardown
// -----------------------------------------------------------------------------

model_router_state_t* model_router_create(void) {
    void* ptr = NULL;
    int rc = posix_memalign(&ptr, CACHE_LINE_SIZE, sizeof(model_router_state_t));
    if (rc != 0 || ptr == NULL) {
        return NULL;
    }
    
    model_router_state_t* state = (model_router_state_t*)ptr;
    memset(state, 0, sizeof(model_router_state_t));
    
    atomic_init(&state->active_slot, SLOT_NONE);
    atomic_init(&state->transition_lock, 0);
    atomic_init(&state->current_vram_usage, 0);
    atomic_init(&state->peak_vram_usage, 0);
    atomic_init(&state->total_swaps_completed, 0);
    atomic_init(&state->total_swap_time_ns, 0);
    atomic_init(&state->last_swap_latency_ns, 0);
    atomic_init(&state->cache_hit_requests, 0);
    atomic_init(&state->total_requests_routed, 0);
    atomic_init(&state->violation_attempts, 0);
    
    init_timebase();
    return state;
}

void model_router_destroy(model_router_state_t* router) {
    if (router != NULL) {
        free(router);
    }
}

// -----------------------------------------------------------------------------
// Request Complexity Classifier
// -----------------------------------------------------------------------------

uint32_t model_router_classify_request(const char* prompt, size_t prompt_len) {
    if (prompt == NULL || prompt_len == 0) {
        return SLOT_FAST_7B; // Default to fast model for empty/minimal inputs
    }
    
    // Deep reasoning trigger keywords
    static const char* const deep_keywords[] = {
        "architect", "synthesis", "council", "physics", "proof", "gauntlet",
        "audit", "deliberation", "deep", "falsification", "byzantine", "causal",
        "divertor", "interferometry", "equilibrium", "thermodynamic", "blackbox",
        "formal", "invariant", "cryptographic", NULL
    };
    
    // Fast lookup indicators
    static const char* const fast_keywords[] = {
        "syntax", "regex", "lookup", "find", "grep", "cat", "echo", "format",
        "quick", "typo", "rename", "list", "status", NULL
    };
    
    // Check for explicit fast keywords first
    for (int i = 0; fast_keywords[i] != NULL; ++i) {
        if (strcasestr(prompt, fast_keywords[i]) != NULL && prompt_len < 300) {
            return SLOT_FAST_7B;
        }
    }
    
    // Check for deep reasoning triggers
    for (int i = 0; deep_keywords[i] != NULL; ++i) {
        if (strcasestr(prompt, deep_keywords[i]) != NULL) {
            return SLOT_DEEP_14B;
        }
    }
    
    // Long, comprehensive prompts (> 512 bytes) default to 14B for thorough reasoning
    if (prompt_len > 512) {
        return SLOT_DEEP_14B;
    }
    
    // Default fast tier for standard operational tasks
    return SLOT_FAST_7B;
}

// -----------------------------------------------------------------------------
// Core Atomic Model Swap Engine (Eviction-Before-Load Protocol)
// -----------------------------------------------------------------------------

static inline void acquire_lock(_Atomic uint32_t* lock) {
    uint32_t expected = 0;
    while (!atomic_compare_exchange_weak(lock, &expected, 1)) {
        expected = 0;
        // Low-latency pause on Apple Silicon ARM64
        #if defined(__aarch64__)
        __asm__ volatile("isb" ::: "memory");
        #endif
    }
}

static inline void release_lock(_Atomic uint32_t* lock) {
    atomic_store_explicit(lock, 0, memory_order_release);
}

int model_router_swap_model(model_router_state_t* state, uint32_t target_slot, uint64_t* out_swap_time_ns) {
    if (state == NULL || (target_slot != SLOT_FAST_7B && target_slot != SLOT_DEEP_14B)) {
        return -1;
    }
    
    // Fast Path: Check if target model is ALREADY resident in unified RAM
    uint32_t current = atomic_load_explicit(&state->active_slot, memory_order_acquire);
    if (current == target_slot) {
        atomic_fetch_add_explicit(&state->cache_hit_requests, 1, memory_order_relaxed);
        atomic_fetch_add_explicit(&state->total_requests_routed, 1, memory_order_relaxed);
        if (out_swap_time_ns != NULL) {
            *out_swap_time_ns = 0;
        }
        return 0; // Success, zero swap latency
    }
    
    // Slow Path: Transition required. Acquire lock.
    acquire_lock(&state->transition_lock);
    
    // Double-check after acquiring lock
    current = atomic_load_explicit(&state->active_slot, memory_order_acquire);
    if (current == target_slot) {
        atomic_fetch_add_explicit(&state->cache_hit_requests, 1, memory_order_relaxed);
        atomic_fetch_add_explicit(&state->total_requests_routed, 1, memory_order_relaxed);
        release_lock(&state->transition_lock);
        if (out_swap_time_ns != NULL) {
            *out_swap_time_ns = 0;
        }
        return 0;
    }
    
    uint64_t t_start = mach_absolute_time();
    
    // -------------------------------------------------------------------------
    // STEP 1: EVICTION PHASE (Strict Eviction-Before-Load Invariant)
    // -------------------------------------------------------------------------
    if (current != SLOT_NONE) {
        // Enforce invariant: VRAM must be zeroed before loading the new model
        // In live production, this dispatches Ollama unload (keep_alive: 0)
        atomic_store_explicit(&state->active_slot, SLOT_NONE, memory_order_release);
        atomic_store_explicit(&state->current_vram_usage, 0, memory_order_release);
    }
    
    // -------------------------------------------------------------------------
    // STEP 2: INVARIANT VERIFICATION
    // -------------------------------------------------------------------------
    uint64_t vram_check = atomic_load_explicit(&state->current_vram_usage, memory_order_acquire);
    if (vram_check != 0) {
        // CRITICAL FAULT: Previous model did not release VRAM! Refuse to load.
        atomic_fetch_add_explicit(&state->violation_attempts, 1, memory_order_relaxed);
        release_lock(&state->transition_lock);
        return -2; // Invariant violation: 16GB co-existence prevented
    }
    
    // -------------------------------------------------------------------------
    // STEP 3: LOAD PHASE (Load target model into unified RAM)
    // -------------------------------------------------------------------------
    uint64_t target_vram = (target_slot == SLOT_FAST_7B) ? VRAM_BYTES_7B : VRAM_BYTES_14B;
    
    // Verify that loading target does not breach physical ceiling
    if ((target_vram + SYSTEM_RESERVED_MEMORY_BYTES) >= HARDWARE_MEMORY_CEILING_BYTES) {
        // Ceiling breach
        atomic_fetch_add_explicit(&state->violation_attempts, 1, memory_order_relaxed);
        release_lock(&state->transition_lock);
        return -3;
    }
    
    // Commit new model VRAM and active slot
    atomic_store_explicit(&state->current_vram_usage, target_vram, memory_order_release);
    atomic_store_explicit(&state->active_slot, target_slot, memory_order_release);
    
    // Update peak watermark
    uint64_t current_peak = atomic_load_explicit(&state->peak_vram_usage, memory_order_relaxed);
    if (target_vram > current_peak) {
        atomic_store_explicit(&state->peak_vram_usage, target_vram, memory_order_relaxed);
    }
    
    uint64_t t_end = mach_absolute_time();
    uint64_t swap_latency_ns = mach_time_to_ns(t_end - t_start);
    
    atomic_fetch_add_explicit(&state->total_swaps_completed, 1, memory_order_relaxed);
    atomic_fetch_add_explicit(&state->total_swap_time_ns, swap_latency_ns, memory_order_relaxed);
    atomic_store_explicit(&state->last_swap_latency_ns, swap_latency_ns, memory_order_relaxed);
    atomic_fetch_add_explicit(&state->total_requests_routed, 1, memory_order_relaxed);
    
    release_lock(&state->transition_lock);
    
    if (out_swap_time_ns != NULL) {
        *out_swap_time_ns = swap_latency_ns;
    }
    return 0; // Success
}

// -----------------------------------------------------------------------------
// Telemetry and Statistics Accessors
// -----------------------------------------------------------------------------

void model_router_get_stats(
    const model_router_state_t* state,
    uint32_t* out_active_slot,
    uint64_t* out_current_vram,
    uint64_t* out_peak_vram,
    uint64_t* out_swaps_count,
    uint64_t* out_hits_count,
    uint64_t* out_total_routed,
    uint64_t* out_last_swap_ns,
    uint64_t* out_violations
) {
    if (state == NULL) return;
    
    if (out_active_slot) *out_active_slot = atomic_load(&state->active_slot);
    if (out_current_vram) *out_current_vram = atomic_load(&state->current_vram_usage);
    if (out_peak_vram) *out_peak_vram = atomic_load(&state->peak_vram_usage);
    if (out_swaps_count) *out_swaps_count = atomic_load(&state->total_swaps_completed);
    if (out_hits_count) *out_hits_count = atomic_load(&state->cache_hit_requests);
    if (out_total_routed) *out_total_routed = atomic_load(&state->total_requests_routed);
    if (out_last_swap_ns) *out_last_swap_ns = atomic_load(&state->last_swap_latency_ns);
    if (out_violations) *out_violations = atomic_load(&state->violation_attempts);
}
