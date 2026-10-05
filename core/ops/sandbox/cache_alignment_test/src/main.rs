use std::time::Instant;
use std::hint::black_box;
use rayon::prelude::*;

const ITERATIONS: usize = 10_000;
const SWARM_SIZE: usize = 18432;

#[repr(C, align(128))]
#[derive(Clone)]
struct Cell128 { data: [u8; 128] }

#[repr(C, align(256))]
#[derive(Clone)]
struct Cell256 { data: [u8; 256] }

#[repr(C, align(512))]
#[derive(Clone)]
struct Cell512 { data: [u8; 512] }

fn main() {
    println!("--- XORAS M4 SILICON FULL-BLOCK ABSORPTION BENCHMARK ---");

    // Test 128
    let mut swarm128 = vec![Cell128 { data: [0; 128] }; SWARM_SIZE];
    let start = Instant::now();
    swarm128.par_iter_mut().for_each(|cell| {
        for _ in 0..ITERATIONS {
            for i in 0..128 {
                cell.data[i] = cell.data[i].wrapping_add(1);
            }
        }
    });
    println!("128-byte (Full Mutation): {:?}", start.elapsed());

    // Test 256
    let mut swarm256 = vec![Cell256 { data: [0; 256] }; SWARM_SIZE];
    let start = Instant::now();
    swarm256.par_iter_mut().for_each(|cell| {
        for _ in 0..ITERATIONS {
            // Only mutate the first 128 bytes to keep workload identical,
            // but the cell is spaced out by 256 bytes!
            for i in 0..128 {
                cell.data[i] = cell.data[i].wrapping_add(1);
            }
        }
    });
    println!("256-byte (128 Workload, 256 Padding): {:?}", start.elapsed());

    // Test 512
    let mut swarm512 = vec![Cell512 { data: [0; 512] }; SWARM_SIZE];
    let start = Instant::now();
    swarm512.par_iter_mut().for_each(|cell| {
        for _ in 0..ITERATIONS {
            // Only mutate the first 128 bytes to keep workload identical!
            for i in 0..128 {
                cell.data[i] = cell.data[i].wrapping_add(1);
            }
        }
    });
    println!("512-byte (128 Workload, 512 Padding): {:?}", start.elapsed());
}
