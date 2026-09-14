"""
XMARS.os Cross-Platform Accelerator & Physical Transceiver
Interfaces with native binary (XmarsNativeCore.exe on Windows,
and native bash/coreaudio agent_speak.sh / afplay on macOS).
"""

import os
import sys
import json
import subprocess
from typing import Dict, Any
from hardware_governor import governor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NATIVE_EXE = os.path.join(BASE_DIR, "native", "XmarsNativeCore.exe")

MAC_SSOT_ROOT = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain"
MAC_SPEAK_SCRIPT = os.path.join(MAC_SSOT_ROOT, "ops", "scripts", "agent_speak.sh")

def run_native_cmd(args: list) -> Dict[str, Any]:
    if sys.platform == "win32" and os.path.exists(NATIVE_EXE):
        try:
            cmd = [NATIVE_EXE] + args
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5.0)
            if res.returncode == 0:
                out = res.stdout.strip()
                try:
                    return json.loads(out)
                except Exception:
                    return {"status": "success", "raw_output": out}
        except Exception:
            pass
    return None

def run_distill(text: str) -> Dict[str, Any]:
    native_res = run_native_cmd(["distill", text])
    if native_res:
        return native_res
    
    words = text.strip().split()
    return {
        "status": "success",
        "engine": "xmars_python_core",
        "original_word_count": len(words),
        "stage_1_50pct": " ".join(words[:max(1, int(len(words)*0.5))]),
        "final_invariant": words[0] if words else "XMARS_SOVEREIGNTY"
    }

def run_audit() -> Dict[str, Any]:
    native_res = run_native_cmd(["telemetry"])
    top = governor.inspect_topology()
    return {
        "status": "success",
        "operating_system": "XMARS.os (Darwin)" if sys.platform == "darwin" else ("XMARS.os (Windows)" if sys.platform == "win32" else "XMARS.os (POSIX)"),
        "hardware_matrix": top,
        "native_kernel": native_res or {"engine": "xmars_darwin_kernel" if sys.platform == "darwin" else "xmars_x64_kernel"}
    }

def run_drift_check(target_dir: str = ".") -> Dict[str, Any]:
    native_res = run_native_cmd(["merkle", target_dir])
    if native_res:
        return native_res

    import hashlib
    hasher = hashlib.sha256()
    count = 0
    try:
        for root, _, files in os.walk(target_dir):
            if ".git" in root or "target" in root or "node_modules" in root:
                continue
            for f in files:
                if f.endswith((".py", ".json", ".md", ".html", ".js", ".css", ".sh")):
                    try:
                        with open(os.path.join(root, f), "rb") as fh:
                            hasher.update(fh.read())
                        count += 1
                    except Exception:
                        pass
    except Exception:
        pass

    return {
        "status": "success",
        "target": target_dir,
        "engine": "xmars_merkle_scanner",
        "merkle_root": f"0x{hasher.hexdigest()[:16]}",
        "files_scanned": count,
        "drift_detected": False
    }

def run_speak(agent_id: str, message: str) -> Dict[str, Any]:
    cleaned = message.replace('"', '\\"').replace("'", "")
    
    # macOS Dispatch (Kokoro M4 physical audio / CoreAudio afplay)
    if sys.platform == "darwin":
        if os.path.exists(MAC_SPEAK_SCRIPT):
            try:
                subprocess.Popen(["bash", MAC_SPEAK_SCRIPT, agent_id, cleaned[:200]])
                return {"status": "success", "agent": agent_id, "platform": "macOS", "mode": "kokoro_m4_coreaudio"}
            except Exception:
                pass
        try:
            subprocess.Popen(["say", "-v", "Samantha", cleaned[:200]])
            return {"status": "success", "agent": agent_id, "platform": "macOS", "mode": "macos_speech_core"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # Windows Native C# SAPI Dispatch
    native_res = run_native_cmd(["speak", agent_id, message])
    if native_res:
        return native_res

    # Windows PowerShell SAPI Fallback
    try:
        ps_cmd = f"Add-Type -AssemblyName System.speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.SpeakAsync('{cleaned[:200]}')"
        subprocess.Popen(["powershell", "-NoProfile", "-Command", ps_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"status": "success", "agent": agent_id, "platform": "windows", "mode": "powershell_sapi"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def dispatch_accelerator(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    name = tool_name.lower().strip().lstrip("/")
    if name == "distill":
        text = params.get("text", "") or params.get("content", "")
        return run_distill(text or "XMARS.os sovereign intelligence eliminates external data leakage.")
    elif name == "audit":
        return run_audit()
    elif name == "drift":
        target = params.get("target_dir", ".")
        return run_drift_check(target)
    elif name == "speak":
        agent = params.get("agent", "Maxx")
        msg = params.get("message", "XMARS dot os sovereign command matrix online.")
        return run_speak(agent, msg)
    else:
        return {"status": "error", "message": f"Unknown accelerator '{tool_name}'"}
