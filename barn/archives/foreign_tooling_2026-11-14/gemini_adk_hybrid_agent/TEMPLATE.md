# Standard Template: Gemini ADK Hybrid Agent (Dual-Track Agent + Paper)

Use this canonical template whenever creating a dual-track Google Gemma/Gemini ADK Agent repository that requires both a SWE-Bench execution agent (`submission.zip`) and a research paper submission.

## Directory Structure
```text
<project_repo>/
├── Cargo.toml                       # Native Rust FFI crate configuration
├── pyproject.toml                   # Python workspace setup & dependencies
├── README.md                        # Project whitepaper, architecture & visual media
├── LICENSE                          # Apache 2.0 License
├── agent.yaml                       # Mandatory Google ADK Agent manifest (Main Track)
├── adk_agent.py                     # Google ADK Agent implementation (SWE-Bench patching)
├── submission.zip                   # Main Track submission package
├── run_gauntlet_tests.py            # Master entry point for 14-Stage Sovereign Gauntlet
│
├── src/                             # Native C/Rust Core
│   ├── lib.rs                       # C-ABI export interface (`extern "C"`)
│   ├── ffi_bridge.rs                # Low-level FFI bridge
│   ├── lattice/                     # State lattice & space manager
│   └── safety/                      # Atomic ring buffers & lock-free sync
│
├── hexcell/                         # Python Swarm Orchestration
│   ├── __init__.py
│   ├── lattice.py                   # FFI ctypes loader
│   ├── gemma_agent.py               # Gemma agent integration
│   └── swarm_orchestrator.py        # Sub-agent handoffs & task router
│
├── gauntlet/                        # 14-Stage Sovereign Gauntlet Suite
│   ├── __init__.py
│   ├── stage_01_latency.py
│   ├── ...
│   └── stage_14_determinism.py
│
└── docs/                            # Research Paper, Media & Receipts
    ├── GAUNTLET_RECEIPT.json        # Immutable verification receipt
    ├── images/                      # Architecture diagrams & benchmark plots
    └── paper/                       # Camera-ready LaTeX paper manuscript (.tex)
```
