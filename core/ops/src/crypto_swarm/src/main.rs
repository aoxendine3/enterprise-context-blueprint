use rayon::prelude::*;
use sha2::{Sha256, Digest};
use std::fs;
use std::time::Instant;

fn main() {
    let file_content = fs::read_to_string("../../../ops/scripts/agent_speak.sh")
        .expect("Failed to read target file");
    
    let swarm_size: u64 = 25_000_000;
    
    println!("Initiating Bare-Metal Cryptographic Swarm...");
    println!("Target Payload Size: {} bytes", file_content.len());
    println!("Swarm Operations: {}", swarm_size);
    
    let start = Instant::now();
    
    let assimilated: usize = (0..swarm_size).into_par_iter().map(|_| {
        let mut hasher = Sha256::new();
        hasher.update(file_content.as_bytes());
        let result = hasher.finalize();
        if result[0] != 0 { 1 } else { 0 }
    }).sum();
    
    let duration = start.elapsed();
    let throughput = swarm_size as f64 / duration.as_secs_f64();
    
    println!("========================================");
    println!("Total Execution Time: {:.5} seconds", duration.as_secs_f64());
    println!("Throughput: {:.0} hashes/sec", throughput);
    println!("Assimilated (Non-Zero Hashed Nodes): {}", assimilated);
    println!("========================================");
}
