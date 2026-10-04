#!/usr/bin/env python3
"""truth_verifier_native_wrapper.py – Cross-Platform Python CLI & JSON Adapter around Native SOVRA C-ABI Engine v3.0.

Cross-Platform Binary Resolution:
- macOS (darwin)   -> ops/scripts/libtruth_verifier.dylib
- Linux (linux)    -> ops/scripts/libtruth_verifier.so
- Windows (win32)  -> ops/scripts/libtruth_verifier.dll
"""

import json
import sys
import pathlib
import ctypes
import os
import hashlib
import datetime
from typing import Dict, Any, List

SCRIPT_PATH = pathlib.Path(__file__).resolve()
ROOT_DIR = SCRIPT_PATH.parents[2] if "ops/scripts" in str(SCRIPT_PATH) else SCRIPT_PATH.parents[1]
if not (ROOT_DIR / "knowledge_base.json").exists():
    ROOT_DIR = pathlib.Path("/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain")

if sys.platform.startswith("darwin"):
    DYLIB_NAME = "libtruth_verifier.dylib"
elif sys.platform.startswith("linux"):
    DYLIB_NAME = "libtruth_verifier.so"
elif sys.platform.startswith("win32") or os.name == "nt":
    DYLIB_NAME = "libtruth_verifier.dll"
else:
    DYLIB_NAME = "libtruth_verifier.so"

DYLIB_PATH = ROOT_DIR / "ops" / "scripts" / DYLIB_NAME
LOG_DIR = ROOT_DIR / "memory" / "catch_log"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "truth_verifier_advanced.log"

MAX_EVIDENCE_ITEMS = 16

class NativeVerificationResult(ctypes.Structure):
    _fields_ = [
        ("is_correct", ctypes.c_int),
        ("verdict_code", ctypes.c_int),
        ("verdict_name", ctypes.c_char_p),
        ("reason", ctypes.c_char_p),
        ("polarity_scope", ctypes.c_char_p),
        ("evidence_count", ctypes.c_size_t),
        ("evidence_ptrs", ctypes.c_char_p * MAX_EVIDENCE_ITEMS)
    ]

_native_lib = None
if DYLIB_PATH.exists():
    try:
        _native_lib = ctypes.CDLL(str(DYLIB_PATH))
        _native_lib.native_verify_truth_v3.argtypes = [
            ctypes.c_char_p, ctypes.c_size_t,
            ctypes.c_char_p, ctypes.c_size_t,
            ctypes.c_char_p, ctypes.c_size_t,
            ctypes.c_char_p, ctypes.c_size_t
        ]
        _native_lib.native_verify_truth_v3.restype = ctypes.POINTER(NativeVerificationResult)
    except Exception:
        _native_lib = None

def log_receipt(entry: dict, status: str = "success") -> str:
    prev_hash = ""
    if LOG_FILE.exists():
        try:
            with LOG_FILE.open("r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
                if lines:
                    last = json.loads(lines[-1])
                    prev_hash = last.get("chain_hash", "")
        except Exception:
            prev_hash = ""

    entry_copy = entry.copy()
    entry_copy["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    entry_copy["status"] = status
    
    payload_str = json.dumps({k: entry_copy[k] for k in sorted(entry_copy) if k != "chain_hash"}, sort_keys=True)
    sha256_val = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
    chain_hash = hashlib.sha256((prev_hash + sha256_val).encode("utf-8")).hexdigest()
    
    entry_copy["sha256"] = sha256_val
    entry_copy["chain_hash"] = chain_hash

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry_copy, ensure_ascii=False) + "\n")

    return chain_hash

def verify_native(question: str, answer: str, expected_answer: str, domain: str = "France") -> Dict[str, Any]:
    if _native_lib is not None:
        q_bytes = question.encode("utf-8")
        ans_bytes = answer.encode("utf-8")
        exp_bytes = expected_answer.encode("utf-8")
        dom_bytes = domain.encode("utf-8")

        ptr = _native_lib.native_verify_truth_v3(
            q_bytes, len(q_bytes),
            ans_bytes, len(ans_bytes),
            exp_bytes, len(exp_bytes),
            dom_bytes, len(dom_bytes)
        )

        res_struct = ptr.contents
        is_corr = bool(res_struct.is_correct)
        verdict_str = res_struct.verdict_name.decode("utf-8") if res_struct.verdict_name else "UNKNOWN"
        reason_str = res_struct.reason.decode("utf-8") if res_struct.reason else ""
        pol_scope = res_struct.polarity_scope.decode("utf-8") if res_struct.polarity_scope else ""

        evidence_items: List[str] = []
        count = min(res_struct.evidence_count, MAX_EVIDENCE_ITEMS)
        for i in range(count):
            item_ptr = res_struct.evidence_ptrs[i]
            if item_ptr:
                evidence_items.append(item_ptr.decode("utf-8"))

        res = {
            "question": question,
            "is_correct": is_corr,
            "verdict": verdict_str,
            "polarity_scope": pol_scope,
            "reason": reason_str,
            "execution_engine": f"SOVRA_NATIVE_C_STRUCT_ENGINE ({DYLIB_NAME})",
            "evidence_chain": evidence_items
        }

        log_receipt({"action": "verify", "question": question, "verdict": verdict_str, "engine": f"SOVRA_NATIVE_{DYLIB_NAME}"}, status="success" if is_corr else "failure")
        return res

    # Fallback to python advanced verifier if dylib not available
    import truth_verifier_advanced
    kb = truth_verifier_advanced.load_kb()
    return truth_verifier_advanced.verify(question, answer, kb)

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception as e:
        err = {"error": f"invalid JSON input: {e}"}
        print(json.dumps(err), file=sys.stderr)
        sys.exit(1)

    question = payload.get("question")
    answer = payload.get("answer")
    expected = payload.get("expected", "Paris")
    domain = payload.get("domain", "France")

    if not question or not answer:
        err = {"error": "both 'question' and 'answer' fields required"}
        print(json.dumps(err), file=sys.stderr)
        sys.exit(1)

    res = verify_native(question, answer, expected, domain)
    print(json.dumps(res, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
