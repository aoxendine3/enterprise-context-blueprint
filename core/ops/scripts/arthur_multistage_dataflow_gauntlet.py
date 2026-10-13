#!/usr/bin/env python3
"""
==============================================================================
PRESSURE-TEST GAUNTLET: ARTHUR vs. MULTI-STAGE SYMBOLIC INJECTION
==============================================================================
Pushes beyond simple syntax matching into deferred resolution & data-flow:
  1. Multi-stage string join: part1 = 'sys'; part2 = 'tem'; fn = getattr(os, part1 + part2)
  2. operator.attrgetter with computed attribute string
  3. f-string formatting indirection: f"{prefix}{suffix}"
  4. Hex-decoded strings: bytes.fromhex("73797374656d").decode() -> 'system'
  5. os.__dict__["eval"] / os.__dict__["system"] dictionary reflection
  6. Computed importlib module name: mod = importlib.import_module("o" + "s")
==============================================================================
"""

import os
import sys
import tempfile
from pathlib import Path

# Add citizen directory to path dynamically
base = Path("/workspace" if os.path.exists("/workspace/core") else "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
sys.path.insert(0, str(base / "agents" / "citizens" / "arthur"))
from arthur_compliance_kernel import ArthurSymbolicTaintKernel

TEST_MULTI_STAGE_PAYLOADS = [
    ("attack_multistage_string_join.py", """
import os
p1 = "sys"
p2 = "tem"
cmd = p1 + p2
f = getattr(os, cmd)
f("id")
"""),
    ("attack_operator_attrgetter.py", """
import operator, os
part = "sys" + "tem"
getter = operator.attrgetter(part)
fn = getter(os)
fn("ls")
"""),
    ("attack_fstring_indirection.py", """
import os
a = "sys"
b = "tem"
cmd = f"{a}{b}"
getattr(os, cmd)("whoami")
"""),
    ("attack_hex_decode_reflection.py", """
import os
raw = bytes.fromhex("73797374656d").decode()
getattr(os, raw)("cat /etc/passwd")
"""),
    ("attack_dict_reflection.py", """
import os
key = "sys" + "tem"
fn = os.__dict__[key]
fn("uname -a")
"""),
    ("attack_computed_importlib.py", """
import importlib
target = "o" + "s"
mod = importlib.import_module(target)
getattr(mod, "system")("exit 1")
"""),
    ("clean_compliant_multistage.py", """
import math
p1 = "sq"
p2 = "rt"
def run(x):
    return math.sqrt(x) * 3.14
""")
]

def run_arthur_multistage_test():
    print("=" * 80)
    print("  PRESSURE-TESTING ARTHUR (SEAT 7): MULTI-STAGE SYMBOLIC DATA-FLOW GAUNTLET")
    print("=" * 80)

    kernel = ArthurSymbolicTaintKernel()
    total_attacks = len(TEST_MULTI_STAGE_PAYLOADS) - 1
    caught_count = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        for filename, code in TEST_MULTI_STAGE_PAYLOADS:
            f = tmp_path / filename
            f.write_text(code, encoding="utf-8")
            violations = kernel.scan_python_ast_security(f)
            
            is_attack = "clean" not in filename
            if is_attack:
                if violations:
                    caught_count += 1
                    print(f"  ✓ INTERCEPTED: {filename:<34} -> {violations[0]}")
                else:
                    print(f"  ❌ MISSED:      {filename:<34} (Deferred resolution escaped!)")
            else:
                if not violations:
                    print(f"  ✓ PASSED:       {filename:<34} -> Clean code admitted with 0 false positives.")
                else:
                    print(f"  ❌ FALSE POSITIVE on {filename}: {violations}")

    print("=" * 80)
    print(f"  Arthur Multi-Stage Interception: {caught_count} / {total_attacks} attacks caught ({100.0 * caught_count / total_attacks:.1f}%)")
    if caught_count == total_attacks:
        print("  🎉 MULTI-STAGE SEAM CLOSED: Symbolic data-flow tracking resolves values")
        print("     across split assignments, f-strings, hex decoding, and operator.attrgetter.")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    run_arthur_multistage_test()
