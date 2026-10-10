# Standard Template: Sovereign Bare-Metal Rust Microservice

Use this template for high-throughput, low-latency native microservices on Apple Silicon UMA.

## Directory Structure
```text
<rust_microservice>/
├── Cargo.toml                       # Crate metadata, release profiles, optimization flags
├── README.md                        # Technical overview & performance benchmark figures
├── LICENSE                          # Apache 2.0 License
├── src/
│   ├── main.rs                      # Main service launcher & signal handlers
│   ├── lib.rs                       # Crate root
│   ├── core/                        # Pure domain logic & vector math
│   ├── shm/                         # POSIX shared memory ring buffers
│   └── ffi/                         # C-ABI export handlers
├── tests/                           # Integration & unit test suite
└── benches/                         # Criterion / benchmark suites
```
