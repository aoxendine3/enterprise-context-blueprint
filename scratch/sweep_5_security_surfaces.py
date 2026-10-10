import os
import re
import json

WORKSPACE = os.path.expanduser("~/Desktop/SSOT_Agentic_Brain")

surfaces = {
    "1_cycle_accurate_timing": [
        "cntvct_el0", "rdtsc", "mach_absolute_time", "clock_gettime", "cycle_counter"
    ],
    "2_side_channel_probe_flush_reload": [
        "flush_reload", "prime_probe", "clflush", "cache_probe", "side_channel"
    ],
    "3_key_lifecycle_management": [
        "key_rotation", "secure_zero_memory", "explicit_bzero", "memset_s", "crypto_keys", "hmac_hardware_key.bin"
    ],
    "4_entropy_csprng_audit": [
        "csprng", "getrandom", "/dev/urandom", "entropy", "rng_audit", "fortuna", "hkdf"
    ],
    "5_formal_c_security_model": [
        "frama-c", "saw", "cbmc", "z3_c_model", "llvm_smt", "klee"
    ]
}

findings = {k: [] for k in surfaces}

for root, dirs, files in os.walk(WORKSPACE):
    if ".venv" in root or ".git" in root or "barn" in root:
        continue
    for f in files:
        if f.endswith(('.py', '.c', '.h', '.cpp', '.hpp', '.zig', '.rs', '.md', '.sovra', '.sh')):
            filepath = os.path.join(root, f)
            relpath = os.path.relpath(filepath, WORKSPACE)
            try:
                content = open(filepath, 'r', encoding='utf-8', errors='ignore').read()
                for cat, keywords in surfaces.items():
                    for kw in keywords:
                        if re.search(r'\b' + re.escape(kw) + r'\b', content, re.IGNORECASE):
                            findings[cat].append({
                                "file": relpath,
                                "matched_keyword": kw
                            })
                            break
            except Exception:
                pass

print(json.dumps(findings, indent=2))
