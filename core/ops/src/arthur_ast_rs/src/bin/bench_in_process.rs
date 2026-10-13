use arthur_ast_rs::ArthurAstEngine;
use std::time::Instant;

fn main() {
    let test_suite = vec![
        ("clean_code", "import json\n\ndef process_event(event_dict):\n    keys = list(event_dict.keys())\n    return len(keys)\n"),
        ("banned_eval", "def dangerous(user_input):\n    return eval(user_input)\n"),
        ("tainted_getattr", "import os\nattr = os.getenv(\"TARGET_OP\")\ngetattr(worker, attr)()\n"),
        ("whitelisted_getattr", "import os\nkey = os.getenv(\"CONFIG_FIELD\")\nif key in (\"host\", \"port\", \"timeout\"):\n    val = getattr(server_config, key)\n"),
        ("dynamic_import", "import importlib\nimportlib.import_module(\"os\")\n"),
    ];

    let engine = ArthurAstEngine::new();

    // Warmup
    for (_, code) in &test_suite {
        let _ = engine.scan_source(code);
    }

    let iterations = 100_000;
    let start = Instant::now();
    for _ in 0..iterations {
        for (_, code) in &test_suite {
            let _ = engine.scan_source(code);
        }
    }
    let total_elapsed = start.elapsed();
    let total_scans = iterations * test_suite.len();
    let per_scan_ns = total_elapsed.as_nanos() as f64 / total_scans as f64;
    let scans_per_sec = 1_000_000_000.0 / per_scan_ns;

    println!("================================================================================");
    println!("  ARTHUR_AST_RS (RUST + TREE-SITTER) RAW IN-PROCESS BENCHMARK");
    println!("================================================================================");
    println!("Total Scans:            {}", total_scans);
    println!("Total Duration:         {:.4?}", total_elapsed);
    println!("Single-Scan Latency:    {:.2} ns ({:.3} µs)", per_scan_ns, per_scan_ns / 1000.0);
    println!("Single-Core Throughput: {:.1} scans/sec", scans_per_sec);
    println!("================================================================================");
}
