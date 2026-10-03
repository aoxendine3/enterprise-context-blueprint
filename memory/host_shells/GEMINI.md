# Gemini is a host cache, not the brain

Path: `~/.gemini` (~10 GB). Conversations ~8.2 GB. Antigravity brain ~2.0 GB.

On 2026-10-03 the inverted symlink `memory/gemini_brain_symlink` → `~/.gemini/antigravity/brain` was **removed**. That link made SSOT greps walk a foreign 2 GB tree and treated a vendor cache as memory.

Do not recreate that symlink. `ops/discernment/gemini_boundary_lock.py` must not pull Gemini into SSOT.

Canonical memory lives under `Desktop/SSOT_Agentic_Brain/memory/`.
