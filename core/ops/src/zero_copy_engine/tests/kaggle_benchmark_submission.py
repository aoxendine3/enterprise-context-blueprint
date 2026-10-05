import os
from kaggle_benchmarks import Benchmark, Task, Evaluation

def create_hardware_aware_task():
    """
    Creates a Kaggle Benchmark Task that evaluates an LLM's ability to
    generate hardware-aware, zero-copy Rust FFI code for Apple Silicon.
    """
    prompt = (
        "Write a Rust function `process_batch_zero_copy` that takes a raw C pointer "
        "to a contiguous byte buffer from Python and transmutes it into a slice of "
        "`HexCell` structs. The HexCell struct must be exactly 3200 bytes long, "
        "containing a 128-byte header, 3040-byte payload, and 32-byte cryptographic_sig. "
        "CRITICAL CONSTRAINT: The target hardware is Apple Silicon (M-series). "
        "You MUST ensure the struct does not suffer from false sharing or cache thrashing "
        "on this specific hardware architecture. Return only the Rust code."
    )

    def evaluate_response(response_text: str) -> float:
        """
        Custom evaluator: Checks if the model correctly identified that Apple Silicon
        uses a 128-byte L1 cache line and applied the correct Rust alignment pragma.
        """
        score = 0.0
        
        # 1. Did it use the correct struct definition?
        if "struct HexCell" in response_text:
            score += 0.2
            
        # 2. Did it perform a zero-copy pointer transmute? (No Protobuf/Serde)
        if "slice::from_raw_parts" in response_text or "transmute" in response_text:
            score += 0.3
            
        # 3. CRITICAL: Did it correctly align to 128 bytes for Apple Silicon?
        # Most models will fail this and use 64 or omit it entirely.
        if "#[repr(C, align(128))]" in response_text or "#[repr(align(128))]" in response_text:
            score += 0.5
            
        return score

    return Task(
        name="apple_silicon_zero_copy_ffi",
        prompt=prompt,
        evaluator=Evaluation.custom(evaluate_response)
    )

if __name__ == "__main__":
    print("Initializing Kaggle Benchmark for Hardware-Aware Code Generation...")
    
    benchmark = Benchmark(
        name="Bare-Metal Systems Engineering Evaluation",
        description="Evaluates LLMs on their ability to write zero-copy FFI code respecting physical CPU cache-line boundaries."
    )
    
    task = create_hardware_aware_task()
    benchmark.add_task(task)
    
    print(f"Benchmark '{benchmark.name}' ready with {len(benchmark.tasks)} tasks.")
    print("Ready for execution across model suite via Kaggle CLI.")
    # To run on Kaggle:
    # benchmark.run(models=["gemini-1.5-pro", "gemini-1.5-flash", "llama-3.1-70b", "deepseek-coder"])
