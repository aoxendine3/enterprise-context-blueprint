use arthur_ast_rs::ArthurAstEngine;
use std::env;
use std::fs;
use std::process;
use std::time::Instant;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: arthur_ast_rs <path_to_python_file>");
        process::exit(1);
    }

    let filepath = &args[1];
    let source_code = match fs::read_to_string(filepath) {
        Ok(code) => code,
        Err(e) => {
            eprintln!("Failed to read file {}: {}", filepath, e);
            process::exit(1);
        }
    };

    let engine = ArthurAstEngine::new();
    let start = Instant::now();
    match engine.scan_source(&source_code) {
        Ok(violations) => {
            let duration = start.elapsed();
            println!("Parsed & Scanned in: {:?}", duration);
            if violations.is_empty() {
                println!("ARTHUR_AST_RS: PASSED (Zero Violations)");
                process::exit(0);
            } else {
                println!("ARTHUR_AST_RS: VETO ({} Violations)", violations.len());
                for v in &violations {
                    println!("  - {}", v);
                }
                process::exit(2);
            }
        }
        Err(e) => {
            eprintln!("Scan error: {}", e);
            process::exit(1);
        }
    }
}
