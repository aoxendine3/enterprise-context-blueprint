---
name: github-repository-governance
description: Enterprise-grade GitHub repository lifecycle management, visibility auditing, fork privatization, team access governance, and Merkle provenance tracking for XORAS Systems.
---

# GitHub Repository Governance Skill

## 1. Core Mandate & Operational Standard
This skill enforces enterprise-grade governance across all GitHub repositories under the `aoxendine3` organization and associated agent swarms.

- **Clean Public Footprint**: Public repositories must represent production-hardened, verified artifacts (`upgp-proving-ground`, `kaggle-benchmark-assets`). All intermediate forks, legacy RevOps experiments, and draft repositories must be set to `PRIVATE`.
- **Daxx Team Access**: Ensure DAXX Master Engine and subagent swarms possess active execution credentials (`gh` CLI token with `repo` and `workflow` scopes) for automated deployment and testing.
- **Fail-Closed Verification**: No release or public commit advances without verified evidence receipts committed to the Merkle DAG ledger.

---

## 2. Automated Fork Privatization Protocol

### Command Execution
To audit and convert all public forked repositories to `PRIVATE`:
```bash
python3 ops/scripts/privatize_github_forks.py
```

### Manual CLI Fallback
```bash
# Check visibility status of target repository
gh repo view <owner>/<repo> --json name,isFork,visibility

# Convert public fork to private
gh repo edit <owner>/<repo> --visibility private --accept-visibility-change-consequences
```

---

## 3. Repository Lifecycle Rules & Perimeter Security

| Category | Visibility | Permitted Content | Audit Frequency |
| :--- | :--- | :--- | :---: |
| **Sovereign Core** | `PUBLIC` | Hardened, audited releases, verified benchmarks, NASA V&V docs | Continuous / Event-Driven |
| **Asset Hubs** | `PUBLIC` | Media assets, visual evidence figures, benchmark data packets | Weekly |
| **Forks & Dependencies** | `PRIVATE` | Upstream libraries, dependency clones, legacy RevOps code | Automatic Quarantine |
| **Internal Workspaces** | `PRIVATE` | Active agent scratchpads, raw telemetry, raw dataset dumps | Daily Sweep |

---

## 4. Daxx Team Swarm Integration & Access Matrix
1. **Authentication**: Enforce `gh auth status` pre-flight checks before executing any remote repository mutation.
2. **Key Rotation**: Store backup Personal Access Tokens in `/Users/ajoxendine68/.env` (`GITHUB_TOKEN` / `GH_TOKEN`).
3. **CI/CD Automation**: Maintain GitHub Actions workflows in `.github/workflows/` for containerized Seccomp gauntlet execution and node-gyp native builds.

---

## 5. Cryptographic Merkle Provenance
Every repository update must commit a SHA-256 Merkle journal record to:
`/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/tri_brain/merkle_asset_registry.jsonl`
