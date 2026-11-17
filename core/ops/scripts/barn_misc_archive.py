#!/usr/bin/env python3
"""
barn_misc_archive.py — XORAS barn offload of misc/ (quarantine protocol §10.5)

Moves the git-able bulk of misc/ to the private GitHub barn repo
(xoras-barn-misc) in orphan-commit batches, FAIL-CLOSED:

  For every batch:
    1. Guard: system free space must exceed MIN_FREE_MB or we abort.
    2. git add -- <files>   (orphan branch, own root commit)
    3. git commit
    4. git push barn <branch>
    5. VERIFY: remote ref SHA == local commit SHA, else FAIL (nothing deleted).
    6. Manifest: path + sha256 + size for every file in the batch,
       written to memory/catch_log/barn_misc_manifests/batch_<NN>.json
    7. Only after 5+6 pass: delete the batch's local files (the remote IS
       the preserved copy; the manifest is the restore map).
    8. Drop the local branch ref and prune objects to reclaim disk.

Files GitHub cannot hold (>100 MB blobs) and binary bulk are NEVER touched:
they are reported for owner disposition.

Nothing is deleted without a verified remote push + manifest. Fail at any
step and the batch stays fully intact locally.
"""

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

MISC = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/misc"
MAIN = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain"
RECEIPT_DIR = os.path.join(MAIN, "memory/catch_log/barn_misc_manifests")
REPO_URL = "https://aoxendine3@github.com/aoxendine3/xoras-barn-misc.git"
LOG = os.path.join(MAIN, "scratch/barn_misc_push.log")

MIN_FREE_MB = 250          # abort if system free space below this before a batch
BATCH_RAW_CAP = 200_000_000  # max raw bytes of source files per batch
MAX_FILE_BYTES = 95_000_000  # GitHub blob limit safety margin (100 MB hard)

TEXT_EXTS = {
    ".html", ".htm", ".md", ".txt", ".json", ".js", ".mjs", ".cjs", ".css",
    ".xml", ".eml", ".emlx", ".svg", ".ts", ".tsx", ".jsx", ".py", ".pyi",
    ".sh", ".c", ".h", ".rs", ".zig", ".dart", ".proto", ".csv", ".yml",
    ".yaml", ".toml", ".ini", ".cfg", ".conf", ".sql", ".rb", ".go", ".java",
    ".kt", ".swift", ".php", ".pl", ".lua", ".bat", ".ps1", ".gradle",
    ".properties", ".scss", ".less", ".vue", ".svelte", ".tf", ".env",
}


def log(msg):
    line = f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def sh(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def free_mb():
    st = os.statvfs("/")
    return (st.f_bavail * st.f_frsize) // (1024 * 1024)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_text_files():
    """All misc/ text files within GitHub blob limits. Returns list of abs paths."""
    out = []
    for root, dirs, files in os.walk(MISC):
        # never walk our own .git
        if ".git" in dirs:
            dirs.remove(".git")
        for name in files:
            p = os.path.join(root, name)
            try:
                st = os.lstat(p)
            except OSError:
                continue
            if not os.path.isfile(p) or os.path.islink(p):
                continue
            if st.st_size > MAX_FILE_BYTES or st.st_size == 0:
                continue
            ext = os.path.splitext(name)[1].lower()
            if ext in TEXT_EXTS:
                out.append(p)
    out.sort()
    return out


def batch_files(files):
    """Split into raw-size-capped batches."""
    batches, cur, cur_bytes = [], [], 0
    for p in files:
        sz = os.lstat(p).st_size
        if cur and cur_bytes + sz > BATCH_RAW_CAP:
            batches.append(cur)
            cur, cur_bytes = [], 0
        cur.append(p)
        cur_bytes += sz
    if cur:
        batches.append(cur)
    return batches


def ensure_repo():
    gitdir = os.path.join(MISC, ".git")
    if not os.path.isdir(gitdir):
        r = sh(["git", "init", "-q"], cwd=MISC)
        if r.returncode != 0:
            log(f"FATAL init: {r.stderr}")
            sys.exit(1)
    for k, v in [
        ("user.name", "aoxendine3"),
        ("user.email", "47148897+aoxendine3@users.noreply.github.com"),
        ("core.compression", "9"),
        ("pack.threads", "1"),
    ]:
        sh(["git", "config", k, v], cwd=MISC)
    r = sh(["git", "remote"], cwd=MISC)
    if "barn" in r.stdout.split():
        sh(["git", "remote", "set-url", "barn", REPO_URL], cwd=MISC)
    else:
        sh(["git", "remote", "add", "barn", REPO_URL], cwd=MISC)


def run_batch(idx, files):
    branch = f"barn-batch-{idx:04d}"
    rels = [os.path.relpath(p, MISC) for p in files]

    # 1. free-space guard
    fmb = free_mb()
    if fmb < MIN_FREE_MB:
        log(f"ABORT batch {idx}: free space {fmb} MB < {MIN_FREE_MB} MB (fail-closed)")
        return False

    # 2-3. orphan add + commit
    sh(["git", "checkout", "--orphan", branch], cwd=MISC)
    sh(["git", "reset"], cwd=MISC)
    r = subprocess.run(["git", "add", "--"] + rels, cwd=MISC,
                       capture_output=True, text=True)
    if r.returncode != 0:
        log(f"FAIL batch {idx}: git add: {r.stderr[:400]}")
        return False
    r = subprocess.run(
        ["git", "commit", "-q", "-m",
         f"barn archive batch {idx}: {len(files)} files, "
         f"{sum(os.lstat(p).st_size for p in files)} raw bytes, moved intact "
         f"from SSOT_Agentic_Brain/misc (quarantine protocol)"],
        cwd=MISC, capture_output=True, text=True)
    if r.returncode != 0:
        log(f"FAIL batch {idx}: commit: {r.stderr[:400]}")
        return False
    r = sh(["git", "rev-parse", "HEAD"], cwd=MISC)
    local_sha = r.stdout.strip()

    # 4. push
    r = subprocess.run(["git", "push", "-q", "barn", f"{branch}:{branch}"],
                       cwd=MISC, capture_output=True, text=True)
    if r.returncode != 0:
        log(f"FAIL batch {idx}: push: {r.stderr[:400]}")
        return False

    # 5. verify remote SHA
    r = sh(["git", "ls-remote", "barn", branch], cwd=MISC)
    remote_sha = r.stdout.split()[0] if r.stdout.strip() else ""
    if remote_sha != local_sha:
        log(f"FAIL batch {idx}: remote {remote_sha} != local {local_sha} "
            f"(nothing deleted)")
        return False

    # 6. manifest
    os.makedirs(RECEIPT_DIR, exist_ok=True)
    manifest = {
        "batch": idx,
        "branch": branch,
        "commit_sha": local_sha,
        "remote": REPO_URL,
        "verified_remote_match": True,
        "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "file_count": len(files),
        "raw_bytes": sum(os.lstat(p).st_size for p in files),
        "files": [
            {"path": os.path.relpath(p, MAIN), "sha256": sha256(p),
             "size": os.lstat(p).st_size}
            for p in files
        ],
    }
    mpath = os.path.join(RECEIPT_DIR, f"batch_{idx:04d}.json")
    with open(mpath, "w") as f:
        json.dump(manifest, f, indent=1)

    # 7. delete local copies (remote verified + manifest on disk)
    missing = 0
    for p in files:
        try:
            os.remove(p)
        except OSError:
            missing += 1
    if missing:
        log(f"WARN batch {idx}: {missing} files could not be deleted")

    # 8. prune local objects, drop branch ref
    sh(["git", "update-ref", "-d", f"refs/heads/{branch}"], cwd=MISC)
    sh(["git", "gc", "--prune=now", "--quiet"], cwd=MISC)

    freed = free_mb()
    log(f"OK batch {idx}: {len(files)} files, {manifest['raw_bytes']} raw bytes, "
        f"pushed+verified {local_sha[:12]}, manifest {os.path.basename(mpath)}, "
        f"local copies removed, free now {freed} MB")
    return True


def main():
    t0 = time.time()
    log("=== barn_misc_archive start ===")
    ensure_repo()
    files = collect_text_files()
    total_bytes = sum(os.lstat(p).st_size for p in files)
    log(f"collected {len(files)} text files, {total_bytes} raw bytes")
    batches = batch_files(files)
    log(f"{len(batches)} batches (cap {BATCH_RAW_CAP} raw each)")
    ok = 0
    for i, b in enumerate(batches, 1):
        if run_batch(i, b):
            ok += 1
        else:
            log(f"stopping fail-closed after batch {i}")
            break
    log(f"=== done: {ok}/{len(batches)} batches pushed+verified+reclaimed "
        f"in {time.time()-t0:.0f}s; free space now {free_mb()} MB ===")
    return 0 if ok == len(batches) else 1


if __name__ == "__main__":
    sys.exit(main())
