#!/usr/bin/env python3
"""
Compilation script for Sovra-Nexus Pure Zig Sovereign Engine.
Compiles both native shared libraries (.dll/.so/.dylib) AND pure standalone native binaries (sovra_engine.exe).
"""

import sys
import os
import subprocess
import shutil
import platform
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
ZIG_DIR = SCRIPT_DIR / "zig"
BUILD_DIR = SCRIPT_DIR / "build"

def get_zig_cmd():
    # 1. Try python -m ziglang
    try:
        res = subprocess.run([sys.executable, "-m", "ziglang", "version"], capture_output=True, text=True)
        if res.returncode == 0:
            return [sys.executable, "-m", "ziglang"]
    except Exception:
        pass

    # 2. Try system `zig`
    zig_path = shutil.which("zig")
    if zig_path:
        return [zig_path]

    raise RuntimeError("Zig compiler not found. Install via `pip install ziglang` or add `zig` to PATH.")

def compile_all():
    print("==========================================================")
    print("      BUILDING SOVRA-NEXUS PURE ZIG NATIVE SUITE          ")
    print("==========================================================")

    zig_cmd = get_zig_cmd()
    print(f"[+] Found Zig compiler: {' '.join(zig_cmd)}")

    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    simd_source = ZIG_DIR / "sovra_simd.zig"
    main_source = ZIG_DIR / "main.zig"

    system = platform.system().lower()
    if system == "windows":
        lib_name = "sovra_simd.dll"
        exe_name = "sovra_engine.exe"
    elif system == "darwin":
        lib_name = "libsovra_simd.dylib"
        exe_name = "sovra_engine"
    else:
        lib_name = "libsovra_simd.so"
        exe_name = "sovra_engine"

    target_lib = BUILD_DIR / lib_name
    target_exe = BUILD_DIR / exe_name
    db_source = ZIG_DIR / "sovra_db.zig"
    db_name = "sovra_db.exe" if system == "windows" else "sovra_db"
    target_db = BUILD_DIR / db_name

    # 1. Build Shared Library
    print(f"\n[+] Compiling Shared Library: {target_lib.name}")
    cmd_lib = zig_cmd + [
        "build-lib",
        "-O", "ReleaseFast",
        "-dynamic",
        str(simd_source),
        f"-femit-bin={target_lib}"
    ]
    res_lib = subprocess.run(cmd_lib, capture_output=True, text=True)
    if res_lib.returncode != 0:
        print("[-] Library Compilation Failed:")
        print(res_lib.stderr)
        sys.exit(1)
    print(f"[OK] Library Built: {target_lib} ({target_lib.stat().st_size:,} bytes)")

    # 2. Build Standalone Native Executable
    print(f"\n[+] Compiling Pure Native Executable: {target_exe.name}")
    cmd_exe = zig_cmd + [
        "build-exe",
        "-O", "ReleaseFast",
        str(main_source),
        f"-femit-bin={target_exe}"
    ]
    res_exe = subprocess.run(cmd_exe, capture_output=True, text=True)
    if res_exe.returncode != 0:
        print("[-] Executable Compilation Failed:")
        print(res_exe.stderr)
        sys.exit(1)
    print(f"[OK] Executable Built: {target_exe} ({target_exe.stat().st_size:,} bytes)")

    # 3. Build Standalone Native Database (TonyDB)
    print(f"\n[+] Compiling Pure Native Database (TonyDB): {target_db.name}")
    cmd_db = zig_cmd + [
        "build-exe",
        "-O", "ReleaseFast",
        str(db_source),
        f"-femit-bin={target_db}"
    ]
    res_db = subprocess.run(cmd_db, capture_output=True, text=True)
    if res_db.returncode != 0:
        print("[-] Database Compilation Failed:")
        print(res_db.stderr)
        sys.exit(1)
    print(f"[OK] Database Built: {target_db} ({target_db.stat().st_size:,} bytes)")

    print("\n==========================================================")
    print("            ALL PURE ZIG TARGETS BUILT CLEANLY            ")
    print("==========================================================")

if __name__ == "__main__":
    compile_all()
