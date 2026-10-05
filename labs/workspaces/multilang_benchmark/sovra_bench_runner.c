// Pure Native C Orchestrator for SOVRA 5-Language Bare-Metal Benchmark Matrix
// Substrate: Apple Silicon M4 Bare Metal (Zero Python dependencies)

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define MAX_OUT 8192

typedef struct {
    const char *name;
    const char *cmd;
    const char *cwd;
} Target;

static void execute_and_capture(const char *cmd, const char *cwd, char *out_buf, size_t buf_size) {
    char full_cmd[1024];
    snprintf(full_cmd, sizeof(full_cmd), "cd \"%s\" && %s 2>&1", cwd, cmd);
    
    FILE *fp = popen(full_cmd, "r");
    if (!fp) {
        snprintf(out_buf, buf_size, "❌ Failed to launch: %s", full_cmd);
        return;
    }

    size_t offset = 0;
    while (fgets(out_buf + offset, (int)(buf_size - offset), fp) != NULL) {
        offset = strlen(out_buf);
        if (offset >= buf_size - 1) break;
    }
    pclose(fp);
}

int main(void) {
    printf("================================================================================\n");
    printf("  XORAS 5-LANGUAGE SIDE-BY-SIDE BARE-METAL NATIVE C BENCHMARK RUNNER\n");
    printf("  Substrate: Apple Silicon M4 (10 Cores) | 100,000 x 18,432-D Vectors (7.37 GB)\n");
    printf("================================================================================\n\n");

    const char *base_dir = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/workspaces/multilang_benchmark";
    const char *rust_dir = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/workspaces/hexological_engine";
    const char *report_path = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/docs/audits/MULTILANG_18432D_SIDE_BY_SIDE_BENCHMARK.md";

    // 1. Build all 6 binaries
    printf("  [BUILD] Compiling C++20 kernel...\n");
    system("clang++ -O3 -std=c++20 -march=armv8.5-a /Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/workspaces/multilang_benchmark/cpp/bench_18432d.cpp -o /Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/workspaces/multilang_benchmark/cpp/bench_cpp");

    printf("  [BUILD] Compiling SOVRA C/NEON kernel...\n");
    system("clang -O3 -march=armv8.5-a /Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/workspaces/multilang_benchmark/sovra_c/bench_18432d.c -o /Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/workspaces/multilang_benchmark/sovra_c/bench_sovra");

    printf("  [BUILD] Compiling Sovereign Rust cargo release...\n");
    system("cargo build --manifest-path /Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/workspaces/hexological_engine/Cargo.toml --release");

    printf("  [BUILD] Compiling Zig ReleaseFast binary...\n");
    system("/opt/homebrew/bin/zig build-exe -O ReleaseFast /Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/workspaces/multilang_benchmark/zig/bench_18432d.zig -femit-bin=/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/workspaces/multilang_benchmark/zig/bench_18432d");

    printf("  [BUILD] Compiling Go 1.22 binary...\n");
    system("/opt/homebrew/bin/go build -o /Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/workspaces/multilang_benchmark/go/bench_go /Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/workspaces/multilang_benchmark/go/bench_18432d.go");

    printf("  [BUILD] Compiling STREAM DRAM Baseline...\n");
    system("clang -O3 -march=armv8.5-a /Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/workspaces/multilang_benchmark/mem_copy_baseline.c -o /Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/workspaces/multilang_benchmark/mem_copy_baseline");

    printf("\n🔥 EXECUTING BARE-METAL BENCHMARK MATRIX (50 WARMUP + 50 MEASURED PASSES)...\n\n");

    Target targets[6] = {
        {"M4 Hardware STREAM Baseline", "./mem_copy_baseline", base_dir},
        {"SOVRA C/NEON", "./sovra_c/bench_sovra", base_dir},
        {"C++20 (clang++ -O3)", "./cpp/bench_cpp", base_dir},
        {"Rust 1.95 (Cargo + Rayon)", "./target/release/hexological_18432d_engine --json", rust_dir},
        {"Zig 0.16 (ReleaseFast)", "./zig/bench_18432d", base_dir},
        {"Go 1.22 (go build)", "./go/bench_go", base_dir}
    };

    char raw_outputs[6][MAX_OUT];
    for (int i = 0; i < 6; i++) {
        printf("  [RUNNING %d/6] %s...\n", i + 1, targets[i].name);
        execute_and_capture(targets[i].cmd, targets[i].cwd, raw_outputs[i], MAX_OUT);
    }

    printf("\n================================================================================\n");
    printf("  GROUND-TRUTH BARE-METAL BENCHMARK RESULTS\n");
    printf("================================================================================\n\n");

    FILE *f_report = fopen(report_path, "w");
    if (f_report) {
        fprintf(f_report, "# 🏆 XORAS 5-LANGUAGE BARE-METAL GROUND-TRUTH BENCHMARK AUDIT REPORT\n\n");
        fprintf(f_report, "> **Workload**: 100,000 18,432-D Vector Comparisons (7.37 GB Vector Matrix Footprint)\n");
        fprintf(f_report, "> **Substrate**: Apple Silicon M4 Bare Metal (`Mac16,12`, 10 CPU Cores, 16 GB LPDDR5X RAM)\n");
        fprintf(f_report, "> **Calibration**: 50 Warmup Passes + 50 Measurement Passes with Volatile DCE Prevention\n\n");
        fprintf(f_report, "| Runtime / Target | Avg Pass Time | Vector Throughput | GFLOPS | DRAM / SIMD Bandwidth | p50 Latency | p99 Latency | Raw Telemetry |\n");
        fprintf(f_report, "|---|---|---|---|---|---|---|---|\n");
    }

    for (int i = 0; i < 6; i++) {
        printf("--- Target %d: %s ---\n%s\n\n", i + 1, targets[i].name, raw_outputs[i]);
        if (f_report) {
            fprintf(f_report, "### %s\n```json\n%s\n```\n\n", targets[i].name, raw_outputs[i]);
        }
    }

    if (f_report) {
        fclose(f_report);
        printf("[+] Full Bare-Metal Ground-Truth Audit saved to: %s\n", report_path);
    }

    return 0;
}
