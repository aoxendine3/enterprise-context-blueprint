//! Sovereign 18,432-Dimensional Hexological Vectoring Engine (Rust 1.95+)
//! Substrate: Apple Silicon M4 Bare Metal (10 CPU Cores, Rayon Multithreading)

use rayon::prelude::*;
use serde::Serialize;
use std::env;
use std::hint::black_box;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Instant;

const DIM: usize = 18432;
const TOTAL_VECTORS: usize = 1_000_000;
const ITERATIONS: usize = 50;

static GLOBAL_SINK: AtomicU64 = AtomicU64::new(0);

#[derive(Serialize)]
struct AuditReport {
    language: String,
    avg_pass_ms: f64,
    evals_per_sec: f64,
    gflops: f64,
    bandwidth_gb_sec: f64,
    p50_us: f64,
    p90_us: f64,
    p99_us: f64,
    sink_check: u64,
}

#[inline(always)]
fn hexological_18432d_dot_product(a: &[f32], b: &[f32]) -> f32 {
    debug_assert_eq!(a.len(), DIM);
    debug_assert_eq!(b.len(), DIM);

    let mut sum0 = 0.0f32;
    let mut sum1 = 0.0f32;
    let mut sum2 = 0.0f32;
    let mut sum3 = 0.0f32;

    let chunks_a = a.chunks_exact(4);
    let chunks_b = b.chunks_exact(4);

    for (ca, cb) in chunks_a.zip(chunks_b) {
        sum0 += ca[0] * cb[0];
        sum1 += ca[1] * cb[1];
        sum2 += ca[2] * cb[2];
        sum3 += ca[3] * cb[3];
    }

    sum0 + sum1 + sum2 + sum3
}

fn main() {
    let json_mode = env::args().any(|arg| arg == "--json");

    let query_vec: Vec<f32> = (0..DIM).map(|i| (i % 100) as f32 * 0.001).collect();
    let target_matrix: Vec<f32> = (0..(TOTAL_VECTORS * DIM))
        .map(|i| ((i + 1) % 100) as f32 * 0.001)
        .collect();

    // 1. Warmup Pass (10 passes)
    for _ in 0..10 {
        let warm_sum: f32 = target_matrix
            .par_chunks_exact(DIM)
            .map(|target_node| {
                black_box(hexological_18432d_dot_product(&query_vec, target_node))
            })
            .sum();
        GLOBAL_SINK.fetch_add(warm_sum.to_bits() as u64, Ordering::Relaxed);
    }

    // 2. Timed Iterations
    let mut sample_latencies_ms = Vec::with_capacity(ITERATIONS);
    let t_start_all = Instant::now();

    for _ in 0..ITERATIONS {
        let iter_start = Instant::now();
        let pass_sum: f32 = target_matrix
            .par_chunks_exact(DIM)
            .map(|target_node| {
                black_box(hexological_18432d_dot_product(&query_vec, target_node))
            })
            .sum();
        let iter_ms = iter_start.elapsed().as_secs_f64() * 1000.0;
        sample_latencies_ms.push(iter_ms);
        GLOBAL_SINK.fetch_add(pass_sum.to_bits() as u64, Ordering::Relaxed);
    }

    let total_elapsed_sec = t_start_all.elapsed().as_secs_f64();
    let avg_pass_sec = total_elapsed_sec / ITERATIONS as f64;
    let avg_pass_ms = avg_pass_sec * 1000.0;

    let evals_per_sec = TOTAL_VECTORS as f64 / avg_pass_sec;
    let gflops = (TOTAL_VECTORS as f64 * DIM as f64 * 2.0) / (avg_pass_sec * 1e9);
    let bytes_gb = (TOTAL_VECTORS as f64 * DIM as f64 * 4.0) / (1024.0 * 1024.0 * 1024.0);
    let bandwidth_gb_sec = bytes_gb / avg_pass_sec;

    sample_latencies_ms.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let p50_pass_ms = sample_latencies_ms[(ITERATIONS as f64 * 0.50) as usize];
    let p90_pass_ms = sample_latencies_ms[(ITERATIONS as f64 * 0.90) as usize];
    let p99_pass_ms = sample_latencies_ms[(ITERATIONS as f64 * 0.99) as usize];

    let p50_vec_us = (p50_pass_ms * 1000.0) / TOTAL_VECTORS as f64;
    let p90_vec_us = (p90_pass_ms * 1000.0) / TOTAL_VECTORS as f64;
    let p99_vec_us = (p99_pass_ms * 1000.0) / TOTAL_VECTORS as f64;

    let report = AuditReport {
        language: "Rust 1.95 (Cargo + Rayon)".to_string(),
        avg_pass_ms,
        evals_per_sec,
        gflops,
        bandwidth_gb_sec,
        p50_us: p50_vec_us,
        p90_us: p90_vec_us,
        p99_us: p99_vec_us,
        sink_check: GLOBAL_SINK.load(Ordering::Relaxed),
    };

    let report_json = serde_json::to_string_pretty(&report).unwrap();

    if json_mode {
        println!("{}", report_json);
    } else {
        println!("======================================================================");
        println!("  XORAS SOVEREIGN RUST 18,432-DIMENSIONAL HEXOLOGICAL VECTOR ENGINE");
        println!("======================================================================");
        println!("{}", report_json);
    }
}
