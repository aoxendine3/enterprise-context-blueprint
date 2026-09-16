# Language Server Launch Issue – Implementation Plan

## Goal Description
We need to locate and remediate the failure that prevents the language server (e.g., rust‑analyzer, pyright, tsserver, etc.) from starting in the Xoras environment.  At the same time we will verify that critical state‑preservation mechanisms (write‑ahead logs, session checkpoints, cross‑conversation buffers) are intact and hardened.  Finally, we will enlist the Daxx remediation squad to execute the remediation steps in parallel.

## User Review Required
[!IMPORTANT]
- Approve creation of Daxx subagents and the execution of automated searches outside the canonical workspace (`c:/Users/admin/...`).  This is required to locate the Antigravity‑related components you mentioned.
- Confirm whether any production data may be modified during the remediation; the plan may touch configuration files and log directories.

## Open Questions
[!WARNING]
- Which specific language server is failing, and can you provide the exact error output or log snippet?
- Do you have a preferred location for the language‑server binary or VS Code extension (e.g., `c:/Program Files/Antigravity/...`)?
- What does *"WaL, W behind l"* refer to in your environment?  Is this a write‑ahead‑log directory, a process named `W` behind a symbolic link, or something else?
- Are there any files in `Documents` or `Desktop` that you consider part of the Xoras stack and that we may modify?

## Proposed Changes
---
### Diagnostics
- Use the `search_web` and `read_url_content` skills to gather typical launch patterns for the identified language server.
- Run a filesystem scan (via `find_by_name` and `grep_search`) in `c:/Users/admin` for configuration files (`settings.json`, `.lspconfig`, `Antigravity*`).
- Collect the language‑server log (`*.log` under the user profile) and copy it into the artifact location `docs/briefings/` for review.

---
### Remediation
- If the language server binary is corrupted or missing, replace it with a fresh download (using the appropriate package manager, e.g., `winget` or direct URL).  Store the new binary under `workspaces/third_party/` and update the PATH in `ops/scripts/env_setup.ps1`.
- Adjust VS Code or editor launch scripts (`.vscode/settings.json`, `ops/scripts/start_editor.ps1`) to point to the correct binary location.
- Harden write‑ahead‑log directories by setting immutable flags (`chflags uchg`) after confirming backups.
- Verify that cross‑conversation buffers (`memory/agent_logs/`) have proper permissions and are not world‑writable.

---
### Daxx Team Engagement
- Define a subagent named `daxx_remediator` with write‑tools enabled to perform the above file edits.
- Invoke three Daxx subagents (or the existing Daxx team) to run in parallel:
  1. Diagnostic collector.
  2. Binary replacement and PATH update.
  3. Log‑directory hardening.
- Each subagent will post progress to `memory/journals/agents/daxx_progress.jsonl`.

---
### Verification Plan
**Automated Tests**
- Run the language server launch command (`<language_server> --version`) and capture exit code.
- Execute `cargo build` (if Rust) or `npm run lint` (if JavaScript) to ensure the environment is healthy.

**Manual Verification**
- Ask you to open the editor and confirm the language server attaches successfully.
- Review the copied logs in `docs/briefings/` for any remaining warnings.

---
## Verification Summary
We will verify success by:
- Seeing a zero‑exit‑code from the language‑server binary.
- Confirming no lingering error messages in the editor console.
- Ensuring immutable flags are set on critical state files.
- Receiving a completion report from all Daxx subagents.
