# Shell Environment — zenith_env.sh

**Updated:** 2026-07-04  
**Owner:** Anthony (non-coder; agents maintain)

## What zenith_env.sh Does

`zenith_env.sh` is the **Zenith Sovereign LLC key vault** loader. It sets local-only database environment variables used by the Nexus orchestrator:

- `MONGO_URL=mongodb://localhost:27017`
- `DB_NAME=test_database`

It is **not** a secret API key file. It loads local MongoDB connection defaults. The file header says: *DO NOT COMMIT. DO NOT SHARE.*

## Canonical Location (Post-Reorg)

```
~/Desktop/Xoras_Workspace/Backups_and_Configs/_System_Config/sovereign_keys/zenith_env.sh
```

## Old Broken Path (Fixed)

```
~/Desktop/Projects/_System_Config/sovereign_keys/zenith_env.sh   ← DELETED during reorg
```

## .zshrc Fix Applied

`~/.zshrc` now uses a **guarded source** — it only loads the file if it exists, and prints a clear message if missing. No shell startup error.

## USB Backup

- `/Volumes/USB_Backup` — **not mounted** at time of audit (Jul 4, 2026).
- `/Volumes/sovereign_stack` — present but no `zenith_env.sh` found on volume.
- If USB is mounted later, check `sovereign_keys/zenith_env.sh` there before overwriting the workspace copy.

## Plain-English Maintenance

| When | What to do |
|------|------------|
| New terminal shows `[SovereignVault] Local database environment loaded.` | Working correctly |
| New terminal shows `zenith_env.sh not found` | Tell your agent to verify the canonical path above |
| MongoDB not running | zenith_env still loads; apps that need Mongo will fail separately |
