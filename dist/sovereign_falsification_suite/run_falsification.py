#!/usr/bin/env python3
"""
Sovereign Falsification Suite v2 -- clean-room verifier.

Differences from v1 (which could report success regardless of results):
  * Exit code is NON-ZERO if any expectation fails.
  * Z3 results are checked against EXPECTED values (unsat / sat / mutant sat).
  * Mechanical-recovery convergence is MEASURED by property tests against a
    reference implementation, not asserted.
  * A mutant implementation (overwrite instead of append) must be CAUGHT.
  * WAL growth is reported as a curve with autocheckpoint disabled, not one number.
  * The LLM baseline is NOT part of this suite. It has not been measured live.
"""
import json, os, platform, random, sqlite3, subprocess, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).parent
random.seed(1234)
FAILS = []


def expect(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name} {detail}")
    if not cond:
        FAILS.append(name)


def z3_status(path):
    try:
        import z3
        s = z3.Solver()
        s.from_file(str(path))
        return str(s.check())
    except ImportError:
        return subprocess.check_output(["z3", str(path)], text=True).split()[0]


# ---- 1. formal checks ------------------------------------------------------
def formal():
    print("[1/3] SMT2 checks (expected results are pre-declared)")
    res = {}
    res["mtpo"] = z3_status(HERE / "agm_mtpo_monotonicity.smt2")
    res["unconstrained"] = z3_status(HERE / "agm_unconstrained_violation.smt2")
    mut = (HERE / "agm_mtpo_monotonicity.smt2").read_text().replace(
        "(store H n (- (select H k)))", "(store H k (- (select H k)))")
    with tempfile.NamedTemporaryFile("w", suffix=".smt2", delete=False) as f:
        f.write(mut)
    res["mutant"] = z3_status(f.name)
    os.unlink(f.name)
    expect("MTPO model is unsat", res["mtpo"] == "unsat", res["mtpo"])
    expect("unconstrained contraction is sat", res["unconstrained"] == "sat", res["unconstrained"])
    expect("mutant (overwrite) is sat -> proof not vacuous", res["mutant"] == "sat", res["mutant"])
    return res


# ---- 2. property tests against a reference implementation -------------------
class Log:
    def __init__(self, destructive=False):
        self.h, self.destructive = [], destructive

    def expand(self, d):
        self.h.append(d)

    def contract(self, k):
        if self.destructive:
            self.h[k] = 0           # mutant: rewrites committed history
        else:
            self.h.append(-self.h[k])  # saga: append algebraic inverse


def net(h):
    return sum(h)


def run_props(trials, destructive):
    ok = 0
    for _ in range(trials):
        lg = Log(destructive)
        for _ in range(random.randint(1, 30)):
            lg.expand(random.randint(-9, 9))
        snap = list(lg.h)
        k = random.randrange(len(snap))
        before_net = net(lg.h)
        lg.contract(k)
        prefix_ok = lg.h[:len(snap)] == snap and len(lg.h) >= len(snap)
        # saga must also actually undo the entry's effect on the net state
        undone = (net(lg.h) == before_net - snap[k]) if not destructive else True
        ok += prefix_ok and undone
    return ok


def props():
    print("[2/3] Property tests vs reference implementation (measured, not asserted)")
    n = 5000
    good, bad = run_props(n, False), run_props(n, True)
    expect("saga impl: prefix-immutable + effect undone", good == n, f"{good}/{n}")
    expect("mutant impl is caught", bad < n, f"{bad}/{n} passed (must be < {n})")
    return {"saga_pass": good, "mutant_pass": bad, "trials": n}


# ---- 3. WAL curve ----------------------------------------------------------
def wal(n, mode):
    d = tempfile.mkdtemp(); p = os.path.join(d, "t.db")
    c = sqlite3.connect(p)
    c.execute("PRAGMA journal_mode=WAL"); c.execute("PRAGMA wal_autocheckpoint=0")
    if mode == "json":
        c.execute("CREATE TABLE d(id INTEGER PRIMARY KEY, x TEXT)")
        st = {}
        c.execute("INSERT INTO d VALUES(1,'{}')"); c.commit()
        base = os.path.getsize(p + "-wal")
        for i in range(n):
            st[f"k{i}"] = "x" * 64
            c.execute("UPDATE d SET x=? WHERE id=1", (json.dumps(st),)); c.commit()
    else:
        c.execute("CREATE TABLE l(s INT,t INT,ty INT,r INT,sig BLOB,PRIMARY KEY(s,t,ty)) WITHOUT ROWID")
        c.commit(); base = os.path.getsize(p + "-wal")
        for i in range(n):
            c.execute("INSERT OR REPLACE INTO l VALUES(?,?,?,?,?)", (1, i, 1, i, b"x" * 32)); c.commit()
    out = os.path.getsize(p + "-wal") - base
    c.close()
    return out


def wal_curve():
    print("[3/3] WAL growth curve (autocheckpoint off; ratio depends on workload size)")
    rows = []
    for n in (100, 500, 1000):
        j, t = wal(n, "json"), wal(n, "typed")
        rows.append({"n": n, "json_bytes": j, "typed_bytes": t, "ratio": round(j / t, 2),
                     "typed_bytes_per_commit": round(t / n)})
        print(f"      n={n:5d} json={j/1024:9.1f}KB typed={t/1024:8.1f}KB ratio={j/t:5.2f}x")
    expect("typed-link WAL smaller than monolithic JSON at every n",
           all(r["ratio"] > 1 for r in rows))
    return rows


def main():
    host = {"platform": platform.platform(), "arch": platform.machine(),
            "cpus": os.cpu_count(), "python": platform.python_version(),
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    print("=" * 72, "\nSOVEREIGN FALSIFICATION SUITE v2\n", host, "\n" + "=" * 72, sep="")
    rec = {"host": host, "formal": formal(), "props": props(), "wal_curve": wal_curve(),
           "failures": FAILS, "verdict": "PASS" if not FAILS else "FAIL",
           "not_measured": ["live LLM baseline", "sustained fault injection", "multi-writer contention"]}
    out = Path(f"cleanroom_receipt_v2_{host['arch']}_{int(time.time())}.json")
    out.write_text(json.dumps(rec, indent=2))
    print(f"\nVERDICT: {rec['verdict']}  receipt: {out}")
    sys.exit(0 if not FAILS else 1)


if __name__ == "__main__":
    main()
