use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::Instant;

const HEXCELL_SLOTS: usize = 6;
const TOTAL_OPS: usize = 1_000_000;
const NUM_THREADS: usize = 8;
const OPS_PER_THREAD: usize = TOTAL_OPS / NUM_THREADS;

#[repr(align(128))]
struct AlignedSlot {
    active: AtomicU64,
    shadow: AtomicU64,
}

struct HexCellRing {
    slots: [AlignedSlot; HEXCELL_SLOTS],
    total_committed: AtomicU64,
    total_compensated: AtomicU64,
}

impl HexCellRing {
    fn new() -> Self {
        Self {
            slots: std::array::from_fn(|_| AlignedSlot {
                active: AtomicU64::new(0),
                shadow: AtomicU64::new(0),
            }),
            total_committed: AtomicU64::new(0),
            total_compensated: AtomicU64::new(0),
        }
    }

    fn execute_saga(&self, slot: usize, _tx_id: u64, new_val: u64) -> bool {
        let initial = self.slots[slot].active.load(Ordering::Acquire);
        self.slots[slot].shadow.store(new_val, Ordering::Release);

        match self.slots[slot].active.compare_exchange(
            initial,
            new_val,
            Ordering::AcqRel,
            Ordering::Acquire,
        ) {
            Ok(_) => {
                self.total_committed.fetch_add(1, Ordering::Relaxed);
                true
            }
            Err(_) => {
                self.slots[slot].shadow.store(initial, Ordering::Release);
                self.total_compensated.fetch_add(1, Ordering::Relaxed);
                false
            }
        }
    }
}

#[repr(C)]
struct RUsage {
    ru_utime: [u64; 2],
    ru_stime: [u64; 2],
    ru_maxrss: i64,
    _pad: [i64; 14],
}

extern "C" {
    fn getrusage(who: i32, usage: *mut RUsage) -> i32;
}

fn get_peak_rss_mb() -> f64 {
    unsafe {
        let mut usage: RUsage = std::mem::zeroed();
        getrusage(0, &mut usage); // RUSAGE_SELF = 0
        #[cfg(target_os = "macos")]
        {
            (usage.ru_maxrss as f64) / (1024.0 * 1024.0)
        }
        #[cfg(not(target_os = "macos"))]
        {
            (usage.ru_maxrss as f64) / 1024.0
        }
    }
}

fn main() {
    let ring = Arc::new(HexCellRing::new());
    let start = Instant::now();

    let mut handles = Vec::with_capacity(NUM_THREADS);
    for tid in 0..NUM_THREADS {
        let r = Arc::clone(&ring);
        handles.push(thread::spawn(move || {
            let start_tx = (tid * OPS_PER_THREAD + 1) as u64;
            let mut retries = 0u64;
            let mut committed = 0u64;

            for i in 0..OPS_PER_THREAD {
                let tx_id = start_tx + i as u64;
                let slot = (tx_id as usize) % HEXCELL_SLOTS;
                let new_val = 0xBEAF_0000_0000_0000 | tx_id;

                while !r.execute_saga(slot, tx_id, new_val) {
                    retries += 1;
                }
                committed += 1;
            }
            (committed, retries)
        }));
    }

    let mut total_retries = 0u64;
    for h in handles {
        let (_comm, retries) = h.join().unwrap();
        total_retries += retries;
    }

    let elapsed = start.elapsed();
    let elapsed_sec = elapsed.as_secs_f64();
    let ops_sec = (TOTAL_OPS as f64) / elapsed_sec;
    let avg_latency_ns = (elapsed_sec / (TOTAL_OPS as f64)) * 1e9;
    let rss_mb = get_peak_rss_mb();

    println!("{{");
    println!("  \"language\": \"Rust 2024 / std::sync::atomic\",");
    println!("  \"standard\": \"Safe Memory Abstraction (release -O3)\",");
    println!("  \"total_ops\": {},", TOTAL_OPS);
    println!("  \"threads\": {},", NUM_THREADS);
    println!("  \"elapsed_ms\": {:.2},", elapsed_sec * 1000.0);
    println!("  \"throughput_ops_sec\": {:.0},", ops_sec);
    println!("  \"avg_latency_ns\": {:.2},", avg_latency_ns);
    println!("  \"total_committed\": {},", ring.total_committed.load(Ordering::Relaxed));
    println!("  \"contention_retries\": {},", total_retries);
    println!("  \"peak_rss_mb\": {:.2}", rss_mb);
    println!("}}");
}
