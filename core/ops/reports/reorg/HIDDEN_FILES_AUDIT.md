# Hidden Files Audit — Desktop, Documents, Xoras_Workspace

**Generated:** 2026-07-04  
**Auditor scope:** dot entries on Desktop and Documents, hidden assets in `Xoras_Workspace`, and home-dir tool state (`~/.gemini`, `~/.cursor`) that affects what Anthony sees on Desktop.  
**Safety policy:** Recommendations only. No deletions performed. Any future delete requires a numbered manifest and explicit approval.

---

## Plain English Summary (for Anthony)

**Short answer:** Yes — there is useful Xoras-related stuff hidden on your Desktop, but it is mostly *agent tooling*, not your main project files.

The big one is **`.agents` on your Desktop** — a hidden folder with ~21 AI “skills” (instructions and data that Antigravity/Gemini-style agents use). Your real Xoras code and docs live in the **visible** `Xoras_Workspace` folder. The hidden items are support files: macOS housekeeping, git internals, secret keys, and AI app memory stored in your home folder (`~/.gemini`, `~/.cursor`).

**You do not need to “unhide” dotfiles** to use Xoras day to day. Better approach: keep secrets and system junk hidden, and add **Desktop shortcuts** to the folders you actually care about (`Xoras_Workspace`, `agents/xoras-agent-skills`, reports).

**Do not delete** anything from this audit without checking the delete manifest at the bottom. The only things safe to clean occasionally are `.DS_Store` files (macOS view cache) — and even those regenerate automatically.

---

## Executive Findings

| Finding | Severity | Action |
|---|---|---|
| `Desktop/.agents` (~17 MB, 21 skills) | Medium — useful, misplaced | **Move or symlink** into `Xoras_Workspace/agents/` after dependency check |
| `Desktop/skills-lock.json` (visible, not hidden) | Low — companion to `.agents` | **Move** with `.agents` or keep on Desktop until agents consolidated |
| `Dev_Workspaces/Projects/.credentials` | **High — secrets** | **Keep** hidden; never expose on Desktop |
| Multiple `.env` files under `Dev_Workspaces/` | **High — secrets** | **Keep** hidden |
| `~/.gemini/antigravity/brain/` (~284 MB total for `~/.gemini`) | Medium — AI memory/state | **Keep** in home dir; optional Desktop shortcut for awareness |
| `~/.cursor/` (~52 MB) | Low — Cursor IDE cache/state | **Keep**; linked to `Xoras_Workspace` sessions |
| `~/.xoras_wake.log`, `~/xoras-sentry/.xoras_ledger.json` | Low — Xoras runtime logs | **Keep**; optional symlink into `memory/` for ops visibility |
| Legacy Desktop roots (`Xoras`, `Xoras_Project`, etc.) | Medium — migration debt | **Keep** until Phase 4/5 redirects complete (see `LEGACY_REDIRECTS.md`) |
| `.DS_Store` scattered everywhere | Low — macOS cache | **Optional delete** (regenerates); do not “make visible” |

---

## Table 1 — Desktop Dot Entries (`/Users/ajoxendine68/Desktop`)

| Path | Purpose | Keep / Move / Symlink / Delete | Make visible? | Xoras? |
|---|---|---|---|---|
| `.DS_Store` | macOS Finder folder view cache | **Keep** (or optional delete) | No | No |
| `.localized` | macOS system marker for localized folder name | **Keep** | No | No |
| `.agents/` | Antigravity/agent skill packs (21 skills: ui-ux-pro-max, brainstorming, tdd, etc.) + `skills-lock.json` inside | **Move** → `Xoras_Workspace/agents/desktop-agent-skills/` or **symlink** from canonical `agents/` | **Shortcut yes** (not unhide) | **Yes — agent config** |
| `.agents/skills/skills-lock.json` | Pinning/hashes for installed agent skills | **Move** with `.agents` | No | Yes |

**Visible Desktop items related to this audit (not hidden but relevant):**

| Path | Purpose | Recommendation | Xoras? |
|---|---|---|---|
| `skills-lock.json` | Duplicate/companion skill lock at Desktop root | **Move** with `.agents` consolidation | Yes |
| `sovereign` | 82-byte bash launcher → `~/sovereign/.venv/bin/sovereign` | **Keep**; later **symlink** per `LEGACY_REDIRECTS.md` | Yes |
| `Xoras_Workspace/` | Canonical workspace root | **Keep** — primary visible entry point | Yes |
| `Xoras/`, `Xoras_Project/`, `Xoras_Sovereign_AI_Stack/` | Legacy roots (migration in progress) | **Keep** until redirect phase; do not delete | Yes (legacy) |

---

## Table 2 — Documents Dot Entries (`/Users/ajoxendine68/Documents`)

| Path | Purpose | Keep / Move / Symlink / Delete | Make visible? | Xoras? |
|---|---|---|---|---|
| `.DS_Store` | macOS Finder cache | Optional delete | No | No |
| `.localized` | macOS system marker | **Keep** | No | No |
| `antigravity/proud-hertz/.git/` | Git metadata for Antigravity project | **Keep** (standard git) | No | Partial — Antigravity project |
| `antigravity/.DS_Store` | Finder cache | Optional delete | No | No |

**Note:** `Documents/antigravity/proud-hertz` is registered in `~/.gemini/config/projects/` as an Antigravity git project. The folder itself is **visible**; only `.git` and dot caches are hidden.

---

## Table 3 — Xoras_Workspace Hidden Assets (grouped)

Top level of `Xoras_Workspace` has only `.DS_Store` hidden — good. Important hidden items live deeper:

### Xoras-flagged — configs, brain, keys, agent state

| Path | Purpose | Keep / Move / Symlink / Delete | Make visible? | Category |
|---|---|---|---|---|
| `agents/xoras-agent-skills/` | Canonical agent skills (visible parent; may contain nested dotfiles) | **Keep** | Already visible folder | Agent config |
| `AI_Core/Xoras_Project/xoras-core/.agents/` | AGENTS.md, hooks.json, project skills | **Keep** | No | Agent config |
| `AI_Core/Xoras_Project/xoras-core/.env` | Runtime secrets for xoras-core | **Keep** hidden | **Never** | Keys |
| `AI_Core/Xoras_Project/xoras-config/.agents/` | AGENTS.md, blobs, manifests | **Keep** | No | Agent config |
| `AI_Core/Xoras_Knowledge/ai_intel_scour/.agents/` | Agent instructions for intel scour | **Keep** | No | Agent config |
| `Dev_Workspaces/Projects/.credentials/` | `firebase-adminsdk.json`, `master_config.env`, API key stubs | **Keep** hidden | **Never** | Keys |
| `Dev_Workspaces/AI_Agents/*/.env` | Per-project environment secrets | **Keep** hidden | **Never** | Keys |
| `Dev_Workspaces/Spectra-Audit-Competition/.env` | Project secrets | **Keep** hidden | **Never** | Keys |
| `Dev_Workspaces/Quantum/Quantum_env_xoras/.env` | Quantum env secrets | **Keep** hidden | **Never** | Keys |
| `Dev_Workspaces/scratch/.env` | Scratch secrets | **Keep** hidden | **Never** | Keys |
| `memory/` | Canonical memory store (currently empty placeholder) | **Keep**; migrate `~/.xoras_wake.log` content here when ready | Shortcut optional | Brain/state |

### Standard dev hidden files (not Xoras-specific — keep as-is)

| Pattern | Count (approx.) | Action | Make visible? |
|---|---|---|---|
| `.git/` directories | Many repos under `Dev_Workspaces/`, `AI_Core/` | **Keep** | No |
| `.gitignore`, `.prettierrc`, `.nvmrc`, etc. | Per-repo tooling | **Keep** | No |
| `.venv/` Python virtualenvs | Several projects | **Keep** | No |
| `.DS_Store` | Widespread | Optional bulk delete | No |
| `Backups_and_Configs/_Backups/*/.Spotlight-V100`, `.fseventsd` | USB/disk image mount metadata | **Keep** on backups; ignore | No |

---

## Table 4 — Home Directory Tool State (not on Desktop, affects visibility)

These folders are **hidden in Finder by default** (leading dot). They hold AI app memory and IDE state tied to Desktop projects.

| Path | Size (approx.) | Purpose | Keep / Move / Symlink / Delete | Desktop shortcut? | Xoras? |
|---|---|---|---|---|---|
| `~/.gemini/` | 284 MB | Google Antigravity / Gemini IDE config + runtime | **Keep** in home | Optional alias: “Antigravity Data” | **Yes — brain/state** |
| `~/.gemini/antigravity/brain/` | (majority of gemini) | Per-conversation agent memory, transcripts, brainstorm artifacts | **Keep** | Shortcut for awareness only | **Yes — brain** |
| `~/.gemini/antigravity/conversations/` | — | Chat/conversation persistence | **Keep** | No | Yes |
| `~/.gemini/config/config.json` | — | Antigravity settings (may contain tokens) | **Keep** hidden | **Never** | Config |
| `~/.gemini/config/projects/*.json` | — | Maps projects to folders (`Desktop`, `Documents/antigravity/proud-hertz`) | **Keep** | No | Yes |
| `~/.cursor/` | 52 MB | Cursor IDE extensions, skills, MCP, per-project agent transcripts | **Keep** | Optional alias: “Cursor Data” | Yes |
| `~/.cursor/projects/Users-ajoxendine68-Desktop-Xoras-Workspace/` | — | Cursor session state for this workspace | **Keep** | No | Yes |
| `~/.cursor/skills-cursor/` | — | Built-in Cursor agent skills | **Keep** | No | Agent config |
| `~/.agents/skills/` | 1 MB | Older/home copy of agent skills (subset of Desktop `.agents`) | **Consolidate** with Desktop `.agents` → canonical `Xoras_Workspace/agents/` | No | Yes |
| `~/sovereign/` (`.env`, `.venv`) | — | Sovereign CLI Python project | **Keep**; Desktop `sovereign` launcher points here | No | Yes |
| `~/.xoras_wake.log` | 78 B | Xoras wake event log | **Keep**; consider copy/symlink → `Xoras_Workspace/memory/` | Optional | **Yes — agent state** |
| `~/xoras-sentry/.xoras_ledger.json` | 250 B | Xoras Sentry integrity ledger | **Keep** | Optional | **Yes — agent state** |

**Gemini ↔ Desktop link confirmed:** `~/.gemini/config/projects/f0360a2b-…json` names project **"Desktop"** with `folderUri: file:///Users/ajoxendine68/Desktop`. Antigravity brain folders are UUID-keyed under `~/.gemini/antigravity/brain/`.

**Cursor ↔ Desktop link confirmed:** `~/.cursor/projects/Users-ajoxendine68-Desktop-Xoras-Workspace/` tracks this workspace.

---

## Recommended Desktop Shortcuts (non-coder friendly)

Create these as **aliases in Finder** (right-click → Make Alias, drag to Desktop). Do not rename or unhide dotfolders.

| Shortcut name | Target | Why |
|---|---|---|
| **Xoras Home** | `~/Desktop/Xoras_Workspace` | Main hub (already visible; pin if needed) |
| **Xoras Agent Skills** | `~/Desktop/Xoras_Workspace/agents/xoras-agent-skills` | Visible agent tooling |
| **Xoras Reports** | `~/Desktop/Xoras_Workspace/ops/reports/reorg` | Audits and migration status |
| **Xoras Docs** | `~/Desktop/Xoras_Workspace/docs` | Prompts, SOPs, analyses |
| **Xoras Memory** | `~/Desktop/Xoras_Workspace/memory` | Future home for wake logs / state |
| **Sovereign Launcher** | `~/Desktop/sovereign` | Already present; keep |
| *(optional)* **Antigravity Brain** | `~/.gemini/antigravity/brain` | Read-only awareness of AI memory (advanced) |

To show hidden files temporarily in Finder: **Cmd+Shift+.** (toggle). Use only for troubleshooting — not recommended as default.

---

## Safe Consolidation Plan (no deletes)

### Phase A — Document only (this report)
- [x] Inventory hidden entries
- [x] Flag secrets and agent state
- [ ] Anthony reviews shortcut list

### Phase B — Low risk moves (manifest before execution)

| # | Action | From | To | Risk |
|---|---|---|---|---|
| B1 | Move | `Desktop/.agents` | `Xoras_Workspace/agents/desktop-agent-skills` | Low — update skill paths |
| B2 | Move | `Desktop/skills-lock.json` | same destination as B1 | Low |
| B3 | Merge/dedupe | `~/.agents/skills` | into canonical `agents/` tree | Low |
| B4 | Symlink | `~/.xoras_wake.log` | `Xoras_Workspace/memory/xoras_wake.log` | Low — preserve original until verified |
| B5 | Desktop alias | (new) | `ops/reports/reorg` | None |

### Phase C — Deferred (per `LEGACY_REDIRECTS.md`)
- Legacy Desktop roots → symlinks into `Xoras_Workspace`
- `sovereign` launcher → `ops/launchers/sovereign`

---

## Delete Manifest

**Status: EMPTY — nothing approved for deletion.**

| # | Path | Reason | Approved? |
|---|---|---|---|
| — | — | No deletes recommended in this audit | — |

**If bulk `.DS_Store` cleanup is desired later**, add rows here first. Example template:

```
| D1 | **/Desktop/**/.DS_Store | Regenerable Finder cache | PENDING |
```

---

## Cross-Reference: `FULL_SYSTEM_AUDIT.md`

**`FULL_SYSTEM_AUDIT.md` was not found** under `Xoras_Workspace` or home (searched 2026-07-04). Use these sibling reports instead:

| Report | Relationship |
|---|---|
| [`inventory-before.md`](./inventory-before.md) | Baseline Desktop/workspace inventory (Phase 1) |
| [`inventory-before-phase1.md`](./inventory-before-phase1.md) through [`inventory-after-phase4-lowrisk.md`](./inventory-after-phase4-lowrisk.md) | Phased before/after snapshots |
| [`high-confidence-cleanup-report.md`](./high-confidence-cleanup-report.md) | Safe cache/symlink cleanup already performed |
| [`wake-surface-hardening-report.md`](./wake-surface-hardening-report.md) | Wake/log surface hardening (relates to `~/.xoras_wake.log`) |
| [`memory-trust-hardening-report.md`](./memory-trust-hardening-report.md) | Memory/trust boundaries (relates to `memory/`, `.gemini/brain`) |
| [`LEGACY_REDIRECTS.md`](../../LEGACY_REDIRECTS.md) | Planned Desktop symlink migrations |
| [`ROOTS.md`](../../ROOTS.md) | Canonical folder schema and guardrails |

When `FULL_SYSTEM_AUDIT.md` is created, add a back-link from that doc to this file under **Hidden & Home-Dir State**.

---

## Appendix — Desktop `.agents` Skill Inventory

Skills found in `Desktop/.agents/skills/` (2026-07-04):

`ai-image-generation`, `ai-video-generation`, `brainstorming`, `develop-userscripts`, `elevenlabs-music-generation`, `find-skills`, `frontend-design`, `grill-me`, `image-inpainting`, `image-outpainting`, `improve-codebase-architecture`, `pr-finisher`, `prototype`, `secure-linux-web-hosting`, `skill-creator`, `sleek-design-mobile-apps`, `tdd`, `ui-ux-pro-max`, `vercel-react-best-practices`

---

*End of audit. No filesystem changes were made during generation.*
