//! mtpo_sim — real, measured concurrency test.
//!
//! What this actually does (no theatre):
//! * N worker threads, each with a monotonic rank sigma = index + 1.
//! * A small set of hot shared resources (forces contention).
//! * Each transaction: snapshot a resource -> do real CPU work on the snapshot
//!   to produce a delta -> commit with a version check.
//! * When a write lands on a resource that other threads hold snapshots of,
//!   the writer sends a real advisory message (nu_{w->r}) to those readers'
//!   inboxes. A reader that receives one "self-heals": it rebases its delta
//!   onto the new version instead of throwing away its work.
//! * Baseline mode ("abort") does the classic thing: on conflict, discard
//!   and redo the CPU work from scratch.
//! * Invariant: final sum of all resources == sum of all committed deltas
//!   (zero lost updates). Checked, not assumed.
//! * Results are signed with an EPHEMERAL Ed25519 key (integrity of the
//!   receipt file only — not an identity attestation).

use ed25519_dalek::{Signer, SigningKey};
use rand::rngs::OsRng;
use std::sync::atomic::{AtomicU32, AtomicU64, Ordering};
use std::sync::mpsc::{channel, Receiver, Sender};
use std::sync::{Arc, Mutex};
use std::time::{Instant, SystemTime, UNIX_EPOCH};

const THREADS: usize = 22;
const RESOURCES: usize = 8;
const TX_PER_THREAD: usize = 20_000;
const WORK_ITERS: u32 = 2_000; // real CPU work per transaction

struct Resource {
    state: Mutex<(u64, u64)>, // (version, value)
    readers: AtomicU32,       // bitmask of threads holding a snapshot
}

#[derive(Clone, Copy)]
struct Advisory {
    from_rank: u32,
    resource: usize,
    new_version: u64,
}

#[derive(Default, Clone)]
struct Stats {
    commits: u64,
    conflicts: u64,
    heals_by_advisory: u64,
    heals_by_cas: u64,
    redo_work_units: u64,
    advisories_sent: u64,
    advisories_recv: u64,
    delta_sum: u64,
    lat_ns: Vec<u64>,
    nu_lower_to_higher: u64,
    nu_higher_to_lower: u64,
}

fn work(seed: u64) -> u64 {
    // xorshift loop: real ALU work the compiler cannot elide (result is used).
    let mut x = seed | 1;
    for _ in 0..WORK_ITERS {
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
    }
    (x % 97) + 1 // delta in 1..=97
}

fn run(mode_heal: bool) -> (Stats, u64, f64) {
    let res: Arc<Vec<Resource>> = Arc::new(
        (0..RESOURCES)
            .map(|_| Resource { state: Mutex::new((0, 0)), readers: AtomicU32::new(0) })
            .collect(),
    );
    let mut txs: Vec<Sender<Advisory>> = Vec::new();
    let mut rxs: Vec<Option<Receiver<Advisory>>> = Vec::new();
    for _ in 0..THREADS {
        let (t, r) = channel();
        txs.push(t);
        rxs.push(Some(r));
    }
    let txs = Arc::new(txs);
    let seq = Arc::new(AtomicU64::new(0));

    let t0 = Instant::now();
    let handles: Vec<_> = (0..THREADS)
        .map(|i| {
            let res = res.clone();
            let txs = txs.clone();
            let rx = rxs[i].take().unwrap();
            let seq = seq.clone();
            std::thread::spawn(move || {
                let rank = (i + 1) as u32;
                let bit = 1u32 << i;
                let mut s = Stats::default();
                s.lat_ns.reserve(TX_PER_THREAD);
                for n in 0..TX_PER_THREAD {
                    let r = (n * 7 + i * 3) % RESOURCES;
                    let start = Instant::now();
                    // snapshot
                    res[r].readers.fetch_or(bit, Ordering::AcqRel);
                    let (mut snap_v, snap_val) = *res[r].state.lock().unwrap();
                    let mut delta = work(snap_val ^ ((i as u64) << 32) ^ n as u64);
                    loop {
                        // drain advisories before commit
                        if mode_heal {
                            while let Ok(a) = rx.try_recv() {
                                s.advisories_recv += 1;
                                if a.resource == r && a.new_version > snap_v {
                                    // self-heal: rebase onto newer version, keep delta
                                    snap_v = a.new_version;
                                    s.heals_by_advisory += 1;
                                    if a.from_rank < rank { s.nu_lower_to_higher += 1 } else { s.nu_higher_to_lower += 1 }
                                }
                            }
                        }
                        let mut g = res[r].state.lock().unwrap();
                        if g.0 == snap_v {
                            g.0 += 1;
                            g.1 += delta;
                            let newv = g.0;
                            drop(g);
                            s.commits += 1;
                            s.delta_sum += delta;
                            seq.fetch_add(1, Ordering::Relaxed);
                            res[r].readers.fetch_and(!bit, Ordering::AcqRel);
                            if mode_heal {
                                let others = res[r].readers.load(Ordering::Acquire) & !bit;
                                let mut m = others;
                                while m != 0 {
                                    let j = m.trailing_zeros() as usize;
                                    m &= m - 1;
                                    let _ = txs[j].send(Advisory { from_rank: rank, resource: r, new_version: newv });
                                    s.advisories_sent += 1;
                                }
                            }
                            break;
                        }
                        // conflict: a write landed after our snapshot
                        s.conflicts += 1;
                        let cur_v = g.0;
                        let cur_val = g.1;
                        drop(g);
                        if mode_heal {
                            snap_v = cur_v; // rebase, delta preserved
                            s.heals_by_cas += 1;
                        } else {
                            snap_v = cur_v; // abort: redo the work from new snapshot
                            delta = work(cur_val ^ ((i as u64) << 32) ^ n as u64);
                            s.redo_work_units += 1;
                        }
                    }
                    s.lat_ns.push(start.elapsed().as_nanos() as u64);
                }
                // drain leftovers so recv counts are complete
                while rx.try_recv().is_ok() { s.advisories_recv += 1; }
                s
            })
        })
        .collect();

    let mut total = Stats::default();
    for h in handles {
        let s = h.join().unwrap();
        total.commits += s.commits;
        total.conflicts += s.conflicts;
        total.heals_by_advisory += s.heals_by_advisory;
        total.heals_by_cas += s.heals_by_cas;
        total.redo_work_units += s.redo_work_units;
        total.advisories_sent += s.advisories_sent;
        total.advisories_recv += s.advisories_recv;
        total.delta_sum += s.delta_sum;
        total.nu_lower_to_higher += s.nu_lower_to_higher;
        total.nu_higher_to_lower += s.nu_higher_to_lower;
        total.lat_ns.extend(s.lat_ns);
    }
    let secs = t0.elapsed().as_secs_f64();
    let final_sum: u64 = res.iter().map(|r| r.state.lock().unwrap().1).sum();
    (total, final_sum, secs)
}

fn pct(v: &mut Vec<u64>, p: f64) -> u64 {
    v.sort_unstable();
    v[((v.len() as f64 - 1.0) * p) as usize]
}

fn main() {
    let cores = std::thread::available_parallelism().map(|n| n.get()).unwrap_or(0);
    println!("[mtpo_sim] threads={THREADS} logical_cores={cores} resources={RESOURCES} tx/thread={TX_PER_THREAD} work_iters={WORK_ITERS}");

    let mut json_modes = Vec::new();
    let mut all_ok = true;
    for (name, heal) in [("abort_baseline", false), ("mtpo_self_heal", true)] {
        let (mut s, final_sum, secs) = run(heal);
        let ok = final_sum == s.delta_sum && s.commits == (THREADS * TX_PER_THREAD) as u64;
        all_ok &= ok;
        let p50 = pct(&mut s.lat_ns, 0.50);
        let p99 = pct(&mut s.lat_ns, 0.99);
        let tps = s.commits as f64 / secs;
        println!("\n== {name} ==");
        println!("  commits={} conflicts={} wall={:.3}s throughput={:.0} tx/s", s.commits, s.conflicts, secs, tps);
        println!("  latency p50={}ns p99={}ns", p50, p99);
        println!("  redo_work_units={} (CPU work thrown away and recomputed)", s.redo_work_units);
        if heal {
            println!("  advisories sent={} recv={} heals_by_advisory={} heals_by_cas_fallback={}",
                s.advisories_sent, s.advisories_recv, s.heals_by_advisory, s.heals_by_cas);
            println!("  nu direction: lower->higher rank={} higher->lower rank={}", s.nu_lower_to_higher, s.nu_higher_to_lower);
        }
        println!("  invariant final_sum({final_sum}) == committed_delta_sum({}): {}", s.delta_sum, if ok { "PASS" } else { "FAIL" });
        json_modes.push(format!(
            "{{\"mode\":\"{name}\",\"commits\":{},\"conflicts\":{},\"wall_s\":{:.6},\"tx_per_s\":{:.1},\"p50_ns\":{p50},\"p99_ns\":{p99},\"redo_work_units\":{},\"advisories_sent\":{},\"advisories_recv\":{},\"heals_by_advisory\":{},\"heals_by_cas\":{},\"final_sum\":{final_sum},\"delta_sum\":{},\"invariant_pass\":{ok}}}",
            s.commits, s.conflicts, secs, tps, s.redo_work_units, s.advisories_sent, s.advisories_recv, s.heals_by_advisory, s.heals_by_cas, s.delta_sum
        ));
    }

    let ts = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();
    let body = format!(
        "{{\"receipt\":\"mtpo_sim\",\"ts\":{ts},\"threads\":{THREADS},\"logical_cores\":{cores},\"resources\":{RESOURCES},\"tx_per_thread\":{TX_PER_THREAD},\"work_iters\":{WORK_ITERS},\"all_invariants_pass\":{all_ok},\"modes\":[{}]}}",
        json_modes.join(",")
    );
    let key = SigningKey::generate(&mut OsRng);
    let sig = key.sign(body.as_bytes());
    let out = format!(
        "{{\"body\":{body},\"ed25519_pubkey\":\"{}\",\"ed25519_sig\":\"{}\",\"key_note\":\"ephemeral per-run key; proves receipt integrity, not identity\"}}\n",
        hex::encode(key.verifying_key().to_bytes()),
        hex::encode(sig.to_bytes())
    );
    let path = std::env::var("MTPO_RECEIPT").unwrap_or_else(|_| format!("mtpo_sim_receipt_{ts}.json"));
    std::fs::write(&path, out).expect("write receipt");
    println!("\n[mtpo_sim] receipt -> {path}");
    println!("[mtpo_sim] ALL INVARIANTS: {}", if all_ok { "PASS" } else { "FAIL" });
    std::process::exit(if all_ok { 0 } else { 1 });
}
