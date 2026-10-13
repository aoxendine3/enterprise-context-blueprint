#!/usr/bin/env python3
"""
==============================================================================
PRESSURE-TEST GAUNTLET: ARTHUR vs. RUNTIME STATE & EXTERNAL TAINT ATTACKS
==============================================================================
Tests whether Arthur's widened Taint-Lattice intercepts:
  1. os.getenv("DANGEROUS_CALL") -> getattr(os, env_var)
  2. open("config.txt").read() -> operator.attrgetter(file_var)(os)
  3. sys.argv[1] concatenation -> importlib.import_module(argv_str)
  4. socket / network stream read -> os.system(network_buffer)
  5. os.environ["MODE"] -> os.__dict__[env_key]
  6. Clean code with sanitized input lookups -> admitted cleanly
==============================================================================
"""

import os
import sys
import tempfile
from pathlib import Path

# Add citizen directory to path dynamically
base = Path("/workspace" if os.path.exists("/workspace/core") else "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
sys.path.insert(0, str(base / "agents" / "citizens" / "arthur"))
from arthur_compliance_kernel import ArthurTaintLatticeKernel

TEST_TAINT_PAYLOADS = [
    ("attack_taint_getenv_getattr.py", """
import os
target = os.getenv("EXPLOIT_HOOK")
getattr(os, target)("rm -rf /")
"""),
    ("attack_taint_file_read_attrgetter.py", """
import operator, os
with open("user_input.txt") as f:
    key = f.read().strip()
getter = operator.attrgetter(key)
getter(os)("id")
"""),
    ("attack_taint_argv_importlib.py", """
import importlib, sys
mod_name = "sys_" + sys.argv[1]
importlib.import_module(mod_name)
"""),
    ("attack_taint_network_syscall.py", """
import socket, os
s = socket.socket()
cmd = s.recv(1024).decode()
os.system(cmd)
"""),
    ("attack_taint_environ_dict.py", """
import os
hook = os.environ["DYNAMIC_HOOK"]
fn = os.__dict__[hook]
fn("uname -a")
"""),
    ("clean_compliant_taint_free.py", """
import os, json
port_str = os.getenv("PORT")
# Legitimate numeric conversion and usage in non-banned primitive
port = int(port_str) if port_str else 8080
print(f"Listening on port {port}")
""")
]

def run_arthur_taint_test():
    print("=" * 80)
    print("  PRESSURE-TESTING ARTHUR (SEAT 7): EXTERNAL TAINT LATTICE GAUNTLET")
    print("=" * 80)

    kernel = ArthurTaintLatticeKernel()
    total_attacks = len(TEST_TAINT_PAYLOADS) - 1
    caught_count = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        for filename, code in TEST_TAINT_PAYLOADS:
            f = tmp_path / filename
            f.write_text(code, encoding="utf-8")
            violations = kernel.scan_python_ast_security(f)
            
            is_attack = "clean" not in filename
            if is_attack:
                if violations:
                    caught_count += 1
                    print(f"  ✓ INTERCEPTED: {filename:<36} -> {violations[0]}")
                else:
                    print(f"  ❌ MISSED:      {filename:<36} (External taint escaped!)")
            else:
                if not violations:
                    print(f"  ✓ PASSED:       {filename:<36} -> Clean code admitted with 0 false positives.")
                else:
                    print(f"  ❌ FALSE POSITIVE on {filename}: {violations}")

    print("=" * 80)
    print(f"  Arthur External Taint Interception: {caught_count} / {total_attacks} attacks caught ({100.0 * caught_count / total_attacks:.1f}%)")
    if caught_count == total_attacks:
        print("  🎉 COMPLETE LATTICE CLOSED: Runtime state, environment lookups, file reads,")
        print("     and network inputs are tracked as TAINT_EXTERNAL and blocked at all security sinks.")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    run_arthur_taint_test()
