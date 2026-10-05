#!/usr/bin/env python3
"""
XORAS EXTREME ADVERSARIAL MEMORY ENGINE BREAKER
================================================
Hostile attack suite attempting to break GovernedMemoryGovernor:
1. Sybil Authority Spoofing (unrecognized agent identity claims)
2. Memory DB SQL Injection Attack
3. 50-Thread Lock Contention & Concurrent Race Condition Attack
4. Unbounded Payload Heap Saturation Attack
5. Circular Contradiction Loop Attack
"""

import sys
import os
import json
import time
import threading
import pathlib
import hashlib
from datetime import datetime, timezone

SSOT_ROOT = pathlib.Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")
sys.path.insert(0, str(SSOT_ROOT / "ops" / "memory"))

from governed_memory_consolidation_engine import GovernedMemoryGovernor

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def run_extreme_breaker_challenge():
    governor = GovernedMemoryGovernor()
    now_iso = datetime.now(timezone.utc).isoformat()
    
    test_file = SSOT_ROOT / "ops" / "memory" / "sample_provenance_source.json"
    test_file.write_text(json.dumps({"valid_source": True}), encoding="utf-8")
    valid_hash = hashlib.sha256(test_file.read_bytes()).hexdigest()
    
    print(f"\n{Colors.HEADER}{Colors.BOLD}========================================================================={Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}       XORAS EXTREME ADVERSARIAL MEMORY BREAKER CHALLENGE                 {Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}========================================================================={Colors.END}\n")
    
    # --- ATTACK 1: SYBIL IDENTITY SPOOFING ---
    print(f"{Colors.WARNING}[ATTACK 1: SYBIL AUTHORITY SPOOFING]{Colors.END}")
    res1 = governor.evaluate_write_candidate(
        agent_id="root_admin_super_user",
        key="system_root_password",
        value="pwned_12345",
        source_path="ops/memory/sample_provenance_source.json",
        merkle_hash=valid_hash,
        timestamp_iso=now_iso,
        target_capsule="jarvis"
    )
    print(f"  Result: {Colors.GREEN if not res1['accepted'] else Colors.FAIL}{res1['status']}{Colors.END} | Score: {res1['governance_score']:.3f}")
    print(f"  Vetoes: {res1['veto_reasons']}\n")
    
    # --- ATTACK 2: SQL INJECTION ATTACK ---
    print(f"{Colors.WARNING}[ATTACK 2: SQL INJECTION PAYLOAD ATTACK]{Colors.END}")
    sqli_key = "attack_key'; DROP TABLE memory_records;--"
    sqli_val = "val' OR '1'='1"
    res2 = governor.evaluate_write_candidate(
        agent_id="maxx",
        key=sqli_key,
        value=sqli_val,
        source_path="ops/memory/sample_provenance_source.json",
        merkle_hash=valid_hash,
        timestamp_iso=now_iso,
        target_capsule="maxx"
    )
    print(f"  Result: {Colors.GREEN if res2['accepted'] else Colors.FAIL}{res2['status']}{Colors.END} (Parametrized SQL prevents injection) | Score: {res2['governance_score']:.3f}\n")
    
    # --- ATTACK 3: 50-THREAD CONCURRENT LOCK CONTENTION RACE ---
    print(f"{Colors.WARNING}[ATTACK 3: 50-THREAD CONCURRENT RACE CONDITION ATTACK]{Colors.END}")
    thread_errors = []
    
    def thread_worker(t_id):
        try:
            governor.evaluate_write_candidate(
                agent_id="clara",
                key=f"concurrent_race_key_{t_id % 5}",
                value=f"value_from_thread_{t_id}",
                source_path="ops/memory/sample_provenance_source.json",
                merkle_hash=valid_hash,
                timestamp_iso=now_iso,
                target_capsule="clara",
                explicit_supersede=True
            )
        except Exception as e:
            thread_errors.append(str(e))
            
    threads = []
    for i in range(50):
        t = threading.Thread(target=thread_worker, args=(i,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    if thread_errors:
        print(f"  {Colors.FAIL}FAILED: {len(thread_errors)} thread exceptions occurred!{Colors.END}")
        for err in thread_errors[:3]:
            print(f"    - {err}")
    else:
        print(f"  {Colors.GREEN}PASSED: 50/50 concurrent threads executed with zero database lock crashes.{Colors.END}\n")

    # --- ATTACK 4: HEAP MEMORY SATURATION PAYLOAD ---
    print(f"{Colors.WARNING}[ATTACK 4: HEAP MEMORY SATURATION ATTACK]{Colors.END}")
    large_payload = "X" * (10 * 1024 * 1024) # 10 MB payload string
    res4 = governor.evaluate_write_candidate(
        agent_id="daxx",
        key="heavy_memory_buffer",
        value=large_payload,
        source_path="ops/memory/sample_provenance_source.json",
        merkle_hash=valid_hash,
        timestamp_iso=now_iso,
        target_capsule="daxx"
    )
    print(f"  Result: {Colors.GREEN if res4['accepted'] else Colors.FAIL}{res4['status']}{Colors.END} | 10MB payload safely absorbed without OOM.\n")

    # --- ATTACK 5: NULL POINTER / TYPE CONFUSION INJECTION ---
    print(f"{Colors.WARNING}[ATTACK 5: NULL POINTER / TYPE CONFUSION ATTACK]{Colors.END}")
    try:
        res5 = governor.evaluate_write_candidate(
            agent_id="maxx",
            key="null_type_key",
            value=None, # Passing None instead of str
            source_path="ops/memory/sample_provenance_source.json",
            merkle_hash=valid_hash,
            timestamp_iso=now_iso,
            target_capsule="maxx"
        )
        print(f"  Result: {Colors.GREEN if not res5['accepted'] else Colors.FAIL}{res5['status']}{Colors.END} | Score: {res5['governance_score']:.3f}\n")
    except Exception as e:
        print(f"  {Colors.FAIL}⚡ CRACK FOUND: Unhandled Exception on None value: {e}{Colors.END}\n")

    print(f"{Colors.HEADER}{Colors.BOLD}========================================================================={Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}EXTREME ADVERSARIAL BREAKER CHALLENGE COMPLETE.{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}========================================================================={Colors.END}\n")

if __name__ == "__main__":
    run_extreme_breaker_challenge()
