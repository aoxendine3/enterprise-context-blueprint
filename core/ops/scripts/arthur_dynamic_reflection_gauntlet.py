#!/usr/bin/env python3
"""
==============================================================================
PRESSURE-TEST GAUNTLET: ARTHUR vs. DYNAMIC REFLECTION & INJECTION ATTACKS
==============================================================================
Tests whether Arthur's hardened AST parser intercepts:
  1. getattr(os, 'system')('id')
  2. getattr(__builtins__, 'eval')('2+2')
  3. Variable-based dynamic reflection: getattr(os, secret_var)
  4. importlib.import_module('os').system('whoami')
  5. subprocess.run(['sh', '-c', 'echo 1'], shell=True)
  6. Direct ctypes raw memory mapping: import ctypes
==============================================================================
"""

import os
import sys
import tempfile
from pathlib import Path

# Add citizen directory to path dynamically
base = Path("/workspace" if os.path.exists("/workspace/core") else "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
sys.path.insert(0, str(base / "agents" / "citizens" / "arthur"))
from arthur_compliance_kernel import HardenedArthurComplianceKernel

TEST_ATTACK_PAYLOADS = [
    ("attack_getattr_system.py", """
import os
getattr(os, "system")("rm -rf /")
"""),
    ("attack_getattr_eval.py", """
import builtins
func = getattr(builtins, "eval")
func("print('hacked')")
"""),
    ("attack_variable_reflection.py", """
import os
cmd = "sys" + "tem"
f = getattr(os, cmd)
f("id")
"""),
    ("attack_importlib.py", """
import importlib
mod = importlib.import_module("os")
mod.system("ls")
"""),
    ("attack_subprocess_shell.py", """
import subprocess
subprocess.run("uname -a", shell=True)
"""),
    ("attack_ctypes.py", """
import ctypes
ctypes.c_char_p(b"bypass")
"""),
    ("clean_compliant_code.py", """
import json
import math
def compute(x):
    return math.sqrt(x) * 2.0
""")
]

def run_arthur_pressure_test():
    print("=" * 80)
    print("  PRESSURE-TESTING ARTHUR (SEAT 7): DYNAMIC REFLECTION & INJECTION GAUNTLET")
    print("=" * 80)

    kernel = HardenedArthurComplianceKernel()
    total_attacks = len(TEST_ATTACK_PAYLOADS) - 1 # 1 is clean
    caught_count = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        for filename, code in TEST_ATTACK_PAYLOADS:
            f = tmp_path / filename
            f.write_text(code, encoding="utf-8")
            violations = kernel.scan_python_ast_security(f)
            
            is_attack = "clean" not in filename
            if is_attack:
                if violations:
                    caught_count += 1
                    print(f"  ✓ INTERCEPTED: {filename:<32} -> {violations[0]}")
                else:
                    print(f"  ❌ MISSED:      {filename:<32} (Injection bypassed filter!)")
            else:
                if not violations:
                    print(f"  ✓ PASSED:       {filename:<32} -> Clean code admitted with 0 false positives.")
                else:
                    print(f"  ❌ FALSE POSITIVE on {filename}: {violations}")

    print("=" * 80)
    print(f"  Arthur Detection Rate: {caught_count} / {total_attacks} attacks intercepted ({100.0 * caught_count / total_attacks:.1f}%)")
    if caught_count == total_attacks:
        print("  🎉 GAP CLOSED: Dynamic reflection, getattr tricks, and importlib indirection")
        print("     are mechanically quarantined at the AST level before execution.")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    run_arthur_pressure_test()
