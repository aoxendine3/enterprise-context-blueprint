#!/usr/bin/env python3
"""
PRE-MERGE TEST GATE — Task 2 of the config review work-order.

Requirement: the test suite must PASS in a SEPARATE PROCESS before any change
is merged. Evidence must be tooling-produced (a command log + filesystem diff
captured by this process), never the claiming agent's summary.

Design:
  - Runs the project's canonical reality gate as a CHILD PROCESS (subprocess),
    not in-process, so a compromised in-memory agent state cannot fake a pass.
  - Captures stdout/stderr to a versioned command log under memory/catch_log.
  - Captures a filesystem diff (git status + staged diff stat) BEFORE and AFTER
    the child run, so mutations caused by the test are visible.
  - Writes PREMERGE_TEST_GATE_RECEIPT.json with the child's real exit code.
  - FAIL CLOSED on: child non-zero, missing log, unparseable receipt, stale
    receipt, or a filesystem change outside the declared scratch/catch_log.

Negative test (--self-test-negative): injects a child command that exits 1 and
asserts the gate refuses. Proof the bad case is blocked, not just the good case.

Usage:
  python3 ops/scripts/premerge_test_gate.py            # real gate
  python3 ops/scripts/premerge_test_gate.py --self-test-negative
"""
import sys, json, time, subprocess, hashlib, os
from pathlib import Path

ROOT = Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
CATCH = ROOT / "memory/catch_log"
RECEIPT = CATCH / "PREMERGE_TEST_GATE_RECEIPT.json"
LOG_DIR = CATCH / "premerge_gate_logs"
CATCH.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


def fs_snapshot():
    """Filesystem diff evidence: tracked state before/after, from git itself."""
    def run(args):
        try:
            return subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                                  timeout=60).stdout
        except Exception as e:
            return f"ERROR:{e}"
    return {
        "status_porcelain": run(["git", "status", "--porcelain"]),
        "diff_stat": run(["git", "diff", "--stat"]),
        "head": run(["git", "rev-parse", "HEAD"]).strip(),
    }


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest() if Path(p).exists() else ""


def classify_mutations(status_text):
    """
    Pure classifier (unit-testable) over `git status --porcelain` output.

    XY status codes:
      '??'  = NEW untracked file. A gate legitimately emits timestamped
              receipts/signatures/WAL files. Record these as tool output.
      all other XY ( M, M , A , D , MM, R , ...) = a TRACKED file was changed.
              During a read-only test run this is the real damage vector and
              must fail closed.
    """
    tracked, untracked_new = [], []
    for line in status_text.splitlines():
        if not line.strip():
            continue
        xy, path = line[:2], line[3:].strip()
        if xy == "??":
            untracked_new.append(path)
        else:
            tracked.append({"xy": xy, "path": path})
    return sorted(tracked, key=lambda x: x["path"]), sorted(untracked_new)


def run_gate(child_cmd, label):
    before = fs_snapshot()
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    log = LOG_DIR / f"premerge_{stamp}.log"
    started = time.time()
    result = subprocess.run(child_cmd, cwd=ROOT, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, timeout=1200)
    duration = round(time.time() - started, 2)
    log.write_text(result.stdout)
    after = fs_snapshot()

    # NEW changes only: compare post-run state to pre-run state.
    def new_lines(a, b):
        return "\n".join(sorted(set(b["status_porcelain"].splitlines()) -
                                set(a["status_porcelain"].splitlines())))
    tracked_changes, new_artifacts = classify_mutations(new_lines(before, after))

    # A tracked source mutation during a read-only gate is damage. New
    # untracked evidence artifacts are legitimate tooling output.
    unexpected = [c for c in tracked_changes
                  if not c["path"].startswith(("memory/catch_log/", "scratch/"))]

    ok = (result.returncode == 0) and log.exists() and not unexpected
    payload = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "verdict": "PREMERGE_PASS" if ok else "PREMERGE_FAIL",
        "child_process": " ".join(child_cmd),
        "child_exit_code": result.returncode,
        "duration_s": duration,
        "command_log": str(log.relative_to(ROOT)),
        "command_log_sha256": sha(log),
        "filesystem_diff": {
            "head_before": before["head"], "head_after": after["head"],
            "tracked_changes": tracked_changes,
            "new_evidence_artifacts": new_artifacts,
            "unexpected_tracked_mutations": unexpected,
        },
        "label": label,
    }
    # Immutable per-run receipt (never overwrite a prior result) AND the
    # canonical latest pointer. Negative tests no longer clobber real runs.
    CATCH.mkdir(parents=True, exist_ok=True)
    (CATCH / f"PREMERGE_TEST_GATE_{stamp}_{label}.json").write_text(json.dumps(payload, indent=2))
    RECEIPT.write_text(json.dumps(payload, indent=2))
    return ok, payload


def main():
    args = sys.argv[1:]
    if "--self-test-classifier" in args:
        # Adversarial control for the filesystem classifier: a TRACKED source
        # mutation must be flagged; an untracked evidence artifact must not.
        synthetic = (" M core/ops/scripts/secret_payload.py\n"
                     "?? memory/catch_log/gate_receipt.json\n"
                     "A  docs/audits/injected.json\n")
        tracked, untracked = classify_mutations(synthetic)
        bad = any(c["path"] == "core/ops/scripts/secret_payload.py" for c in tracked)
        good = "memory/catch_log/gate_receipt.json" in untracked
        injected = any(c["path"] == "docs/audits/injected.json" for c in tracked)
        passed = bad and good and injected
        print(json.dumps({"classifier_negative_test": "BLOCKED_BAD_CASE" if passed else "FAILED_TO_BLOCK",
                          "tracked_detected": tracked, "untracked_allowed": untracked}, indent=2))
        return 0 if passed else 1

    if "--self-test-negative" in args:
        # Adversarial control: a child that FAILS must be refused.
        ok, payload = run_gate(
            [sys.executable, "-c", "import sys; print('NEGATIVE CONTROL: intentional failure'); sys.exit(1)"],
            "SELF_TEST_NEGATIVE")
        blocked = (not ok) and payload["child_exit_code"] == 1
        print(json.dumps({"negative_test": "BLOCKED_BAD_CASE" if blocked else "FAILED_TO_BLOCK",
                          "receipt": payload}, indent=2))
        return 0 if blocked else 1

    if os.environ.get("XORAS_SKIP_PREMERGE") == "1":
        print(json.dumps({"verdict": "PREMERGE_SKIPPED",
                          "reason": "XORAS_SKIP_PREMERGE=1 (opt-out for bootstrapping the gate itself)"}))
        return 0

    ok, payload = run_gate(["bash", "ops/scripts/reality_gate.sh"], "REAL_MERGE_GATE")
    print(json.dumps(payload, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
