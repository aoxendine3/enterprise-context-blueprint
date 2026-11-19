# Independent Audit — Rust AST FFI Changes (2026-11-19)

**Verdict: NO-GO for promotion to main as-is.** Level-2 dual-pillar audit
(independent agent context, no files modified). Scope: the uncommitted diff in
`core/ops/src/arthur_ast_rs/Cargo.toml`, `.../src/lib.rs`, and
`workspaces/xoras_agent_framework/xoras/ast_security.py`.

The security-code diff is therefore **left uncommitted** in the working tree.
It is not part of the pushed gate state (`3b215d6`), and remote CI will not
pick it up.

## Blocking findings

| Severity | Finding | Evidence |
|---|---|---|
| **P0** | Host crash on deeply nested untrusted input | `walk_and_verify` recurses without a depth bound; `extern "C" arthur_ast_scan_ffi` has no `catch_unwind`. Verified: 20,000 nested parens → SIGSEGV (`-11` direct, exit `139` via `scan_code(use_native_rust=True)`). |
| **P0** | Fail-open on malformed Python | `scan_source` never checks `root_node.has_error()`. Verified `def (:` and `eval(` → `rc=0` (SAFE), contradicting the FFI doc comment (`<0 = fail-closed parse/input error`). |
| **P1** | False-negative regression vs Python engine | `x = globals()['__builtins__']`: Rust `rc=0` (safe), Python `is_safe=False`. `scan_code()` fully delegates to native, dropping Python-only detections when enabled. |
| **P1** | Capability off by default and unavailable on fresh clone | `use_native_rust=False` default; both `.dylib` candidates are gitignored/untracked. No test covers the new symbols. |
| **P1** | FFI input contract not hardened | `from_raw_parts` trusts caller length; `v.len() as i32` truncates; `expect()` can panic across the C boundary. |
| **P2** | Regex prefilter redundancy / quadratic backtracking risk | Combined secret regex + per-pattern `re.search`; `([^"\']{8,})` can backtrack on repeated `api_key=` inputs. |

## Claim vs evidence

- The advertised bypass fix **does work** for the specific tested payloads:
  `getattr(__builtins__, ''.join(['ev','al']))('1+1')` → `rc=3`, as does the
  exact harness payload, tuple join, `x.__globals__`, and `import pickle`.
- But **no tracked test** covers it — the tracked parity harness
  (`core/ops/scripts/arthur_native_parity.py`) invokes the Rust **CLI** over 26
  payloads, none containing `.join([...])`; its 26/26 receipt does not exercise
  the FFI. The "0/500,000 false negatives" figure is an authored string in a
  scratch render script, not a committed assertion.
- The Python engine already caught the bypass before this diff
  (`use_native_rust=False` → `is_safe=False`), so the default gate gained no
  new coverage.

## Minimum remediation before any promotion

1. Input-size limits + panic isolation (or subprocess boundary) for the FFI.
2. Check `root_node.has_error()` and return a negative code.
3. Tracked tests for join/builtins payloads, deep nesting, and syntax errors.
4. Run parity through the FFI, not only the CLI.
5. Make the native path a strict superset of — or additive to — the Python checks.
6. Version/build the library at deploy time, or fail loudly when absent.

**Signed:** independent audit agent (Level 2), 2026-11-19. Worker ≠ reviewer.

---

## Final Re-Audit (same independent reviewer): **GO**

After remediation, the same reviewer verified each blocker closed by execution:
`eval_expression_d` depth-bound (20k/50k/200k/500k-term `+` chains → VETO,
host exit 0; >1 MiB → `-1`; 400k nested parens and 100k `.strip()` chains →
no crash); syntax errors → `-3`; native path runs Python checks first and
merges (superset), fails loudly when the library is absent; duplicate secret
pass removed; `tests/test_arthur_ast_ffi.py` staged with 7/7 tests passing.

Non-blocking: native mode remains opt-in and the `.dylib` is gitignored —
other hosts must build/distribute it; absent library now raises instead of
silently degrading.

Verdict: **GO — no remaining security blockers.** Promotion approved.
