# Home reclaim and team invocation (2026-10-03)

SSOT is organized. Home is still a war zone **outside** the brain. Do not delete the next list without Anthony saying so.

## Leave (host shells, not SSOT)
| Path | Size | Why |
|---|---|---|
| `~/Library` | 65G | macOS |
| `~/.ollama` | 28G | local models the roundtable uses |
| `~/.gemini` | 10G | vendor cache; unwired from SSOT |
| `~/.lmstudio` | 6.9G | host |
| `~/.docker` / `.colima` / `.minikube` | ~4.5G | host |
| `Desktop/SSOT_Agentic_Brain` | 3.3G | **the brain** |
| `capabilities/neural_models/kokoro-v1.0.onnx` + `voices.bin` | 316M | speak path |
| `Xoras_agent_cards/` + `identity/` | tiny | frozen council |

## Optional reclaim (ask first)
| Path | Size | Risk |
|---|---|---|
| `~/.gemini/antigravity/conversations` | 8.2G | loses Gemini chat history, not Xoras identity |
| `archives/the_barn/models_retired/kokoro-v0_19.onnx` | 310M | unused by current speak |
| `scratch/hardware_bins/` | 488M | hexcell test blobs; benchmark path updated |
| `~/.sovereign/models` | 317M | **different SHA than SSOT Kokoro** — do not symlink blindly |
| `~/.Trash` | 1.0G | empty trash |
| `workspaces/` venvs | ~192M hyperforge | Merkle pollution source |

## How the triad is actually invoked
- **Pattern in BBQ briefs:** John strategy, Daxx execution, Vance falsification (`docs/briefings/BBQ_GLOBAL_SCOUR_002_*.md`).
- **Roundtable:** `python3 ops/scripts/full_team_deliberation_roundtable.py "<focus>"`
- **Speak allowlist:** `bash ops/scripts/agent_speak.sh` only maxx, clara, jarvis, vance.
- **14-gate:** `python3 ops/discernment/fourteen_gate_blackbox_gauntlet.py` — HexCell/SQLite suite, not a folder janitor.
- **Blackbox review:** `python3 ops/discernment/blackbox_review_engine.py`
- **One door:** `bash ops/scripts/ssot_door.sh`
- **Cursor Task spawn:** blocked on this Free plan (named models). Orchestrator ran the unify checks in-process.

## Auto-research
`workspaces/hyperforge_autoresearch/` exists (~192M). Treat as incubation, not the SSOT root.
