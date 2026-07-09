#!/usr/bin/env python3
"""Xoras elite scheduler — status, start/stop, and cron next-run for scheduled agents."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None

ROOT = pathlib.Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
SCHEDULES_YAML = PROJECT / "xoras-config" / "schedules.yaml"
PID_DIR = ROOT / ".xoras_schedule_pids"
STATUS_FILE = ROOT / ".xoras_schedules_status.json"
STACK_STATUS = ROOT / ".xoras_stack_status.json"
PERSONA_API = os.environ.get("XORAS_PERSONA_API", "http://127.0.0.1:8787")


def _load_schedules() -> List[Dict[str, Any]]:
    if not SCHEDULES_YAML.exists():
        return []
    raw = SCHEDULES_YAML.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(raw) or {}
        return list(data.get("schedules") or [])
    # Minimal fallback if PyYAML missing
    return []


def _pid_file(task_id: str) -> pathlib.Path:
    PID_DIR.mkdir(parents=True, exist_ok=True)
    return PID_DIR / f"{task_id}.pid"


def _read_pid(task_id: str) -> Optional[int]:
    path = _pid_file(task_id)
    if not path.exists():
        return None
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except ValueError:
        return None


def _is_alive(pid: Optional[int]) -> bool:
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _pgrep_script(script: str) -> Optional[int]:
    try:
        out = subprocess.check_output(
            ["pgrep", "-f", script],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        if out:
            return int(out.split("\n")[0])
    except (subprocess.CalledProcessError, ValueError):
        pass
    return None


def _probe_http(url: str) -> bool:
    try:
        import urllib.request

        with urllib.request.urlopen(url, timeout=3) as resp:
            return 200 <= resp.status < 300
    except Exception:
        return False


def _cron_next(cron_expr: str) -> Optional[str]:
    """Best-effort next run for simple daily cron (M H * * *)."""
    parts = cron_expr.split()
    if len(parts) != 5:
        return None
    minute, hour = parts[0], parts[1]
    if not minute.isdigit() or not hour.isdigit():
        return None
    now = datetime.now()
    target = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target.isoformat(timespec="seconds")


def _task_status(task: Dict[str, Any]) -> Dict[str, Any]:
    task_id = task["id"]
    script = task.get("script", "")
    pid = _read_pid(task_id)
    if not _is_alive(pid):
        pid = _pgrep_script(script)
    running = _is_alive(pid)

    health_ok = False
    port = task.get("port")
    health_path = task.get("health_path", "/health")
    if port:
        health_ok = _probe_http(f"http://127.0.0.1:{port}{health_path}")

    interval = task.get("interval_seconds")
    next_run = None
    if task.get("kind") == "cron" and task.get("cron"):
        next_run = _cron_next(task["cron"])
    elif running and interval and int(interval) > 0:
        next_run = (datetime.now() + timedelta(seconds=int(interval))).isoformat(timespec="seconds")

    status = "running" if (running or health_ok) else "stopped"
    if running and port and not health_ok:
        status = "starting"

    return {
        "id": task_id,
        "label": task.get("label", task_id),
        "agent": task.get("agent", "Maxx"),
        "script": script,
        "kind": task.get("kind", "daemon"),
        "description": task.get("description", ""),
        "interval_seconds": interval,
        "cron": task.get("cron"),
        "autostart": bool(task.get("autostart")),
        "status": status,
        "pid": pid,
        "health_ok": health_ok,
        "next_run": next_run,
        "last_checked": datetime.now().isoformat(timespec="seconds"),
    }


def status_payload() -> Dict[str, Any]:
    tasks = [_task_status(t) for t in _load_schedules()]
    stack = {}
    if STACK_STATUS.exists():
        try:
            stack = json.loads(STACK_STATUS.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            stack = {}
    payload = {
        "timestamp": time.time(),
        "schedules": tasks,
        "stack": stack,
        "persona_api": PERSONA_API,
        "source": str(ROOT),
    }
    STATUS_FILE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def start_task(task_id: str) -> Dict[str, Any]:
    tasks = {t["id"]: t for t in _load_schedules()}
    task = tasks.get(task_id)
    if not task:
        return {"ok": False, "error": f"Unknown schedule: {task_id}"}
    script = task.get("script")
    if not script:
        return {"ok": False, "error": "No script configured"}
    script_path = ROOT / script
    if not script_path.exists():
        return {"ok": False, "error": f"Script not found: {script_path}"}

    existing = _pgrep_script(script)
    if _is_alive(existing):
        return {"ok": True, "pid": existing, "message": "Already running"}

    proc = subprocess.Popen(
        [sys.executable, script],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    _pid_file(task_id).write_text(str(proc.pid), encoding="utf-8")
    return {"ok": True, "pid": proc.pid, "message": f"Started {task_id}"}


def stop_task(task_id: str) -> Dict[str, Any]:
    tasks = {t["id"]: t for t in _load_schedules()}
    task = tasks.get(task_id)
    if not task:
        return {"ok": False, "error": f"Unknown schedule: {task_id}"}

    pid = _read_pid(task_id) or _pgrep_script(task.get("script", ""))
    if not _is_alive(pid):
        _pid_file(task_id).unlink(missing_ok=True)
        return {"ok": True, "message": "Already stopped"}

    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(0.5)
        if _is_alive(pid):
            os.kill(pid, signal.SIGKILL)
    except OSError as exc:
        return {"ok": False, "error": str(exc)}

    _pid_file(task_id).unlink(missing_ok=True)
    return {"ok": True, "message": f"Stopped {task_id} (pid={pid})"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Xoras scheduler")
    parser.add_argument("command", choices=["status", "start", "stop", "run"])
    parser.add_argument("task_id", nargs="?", default="")
    args = parser.parse_args()

    if args.command == "status":
        print(json.dumps(status_payload(), indent=2))
    elif args.command == "start":
        print(json.dumps(start_task(args.task_id), indent=2))
    elif args.command == "stop":
        print(json.dumps(stop_task(args.task_id), indent=2))
    elif args.command == "run":
        # Lightweight daemon: refresh status every 15s
        while True:
            status_payload()
            time.sleep(15)


if __name__ == "__main__":
    main()
