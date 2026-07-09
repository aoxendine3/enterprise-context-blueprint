import os
import sys
import time
import signal
import psutil
import threading
import sqlite3
import asyncio
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Ensure local Grok client is accessible
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from xoras_grok_client import chat_with_grok_sync
except ImportError:
    chat_with_grok_sync = None
    print("[XORAS SENTINEL] Warning: Grok API Client not found. Dynamic analysis offline.")

HONEYPOT_DIR = "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/Omni_Dojo_Sandbox/Honeypot"
DB_PATH = "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/Source/sentinel.db"
ACTIVE_THREATS = {}


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS threat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            pid INTEGER,
            cmdline TEXT,
            event_path TEXT,
            status TEXT,
            grok_analysis TEXT
        )
    ''')
    # Alter table if upgrading from old schema
    try:
        cursor.execute("ALTER TABLE threat_logs ADD COLUMN grok_analysis TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    conn.commit()
    conn.close()


def log_threat(pid, cmdline, event_path, status, grok_analysis="N/A"):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO threat_logs (timestamp, pid, cmdline, event_path, status, grok_analysis) VALUES (?, ?, ?, ?, ?, ?)",
                       (datetime.utcnow().isoformat(), pid, cmdline, event_path, status, grok_analysis))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[XORAS SENTINEL] Failed to log threat to DB: {e}")


class SentinelHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.lock = threading.Lock()

    def perform_grok_analysis(self, pid, cmdline_str, event_path):
        if not chat_with_grok_sync:
            return "Grok Client Offline"

        print(f"\n[XORAS SENTINEL] Uploading threat telemetry to Grok for sovereign analysis...")
        messages = [
            {"role": "system", "content": "You are Grok, functioning as the threat assessment module for the Xoras Sentinel IDS. You have just intercepted a rogue process. Analyze the command line intent and the target path. Provide a brief, ruthless, and technical threat assessment."},
            {"role": "user", "content": f"Rogue PID: {pid}\nCommand Executed: {cmdline_str}\nTarget Path: {event_path}\n\nWhat was this rogue agent attempting to do? Is it a sophisticated attack or a script kiddie?"}
        ]

        analysis = chat_with_grok_sync(messages)
        print(
            f"\n--- [GROK THREAT ASSESSMENT] ---\n{analysis}\n--------------------------------\n")
        return analysis

    def neutralize_threat(self, pid, event_path):
        with self.lock:
            if pid in ACTIVE_THREATS:
                return
            ACTIVE_THREATS[pid] = True

        print(f"\n[XORAS SENTINEL] 🔴 CRITICAL THREAT DETECTED 🔴")
        print(f"[XORAS SENTINEL] Unauthorized access to Honeypot: {event_path}")
        print(f"[XORAS SENTINEL] Offending PID: {pid}")

        cmdline_str = "UNKNOWN"
        grok_analysis_text = "N/A"

        try:
            process = psutil.Process(pid)
            cmdline_str = ' '.join(process.cmdline())

            # Avenue C: Core Allocator Integration - Blacklist PID and all Ancestors
            print(
                f"[XORAS SENTINEL] Blacklisting PID {pid} and all ancestors in hardware allocator IPC...")
            with open("/tmp/xoras_blacklist.bin", "ab") as f:
                f.write(pid.to_bytes(4, byteorder='little'))

                # Check for explicit test agent PID
                try:
                    with open("/tmp/rogue.pid", "r") as pf:
                        rogue_pid = int(pf.read().strip())
                        print(
                            f"[XORAS SENTINEL] Explicitly blacklisting Root Rogue PID: {rogue_pid}")
                        f.write(rogue_pid.to_bytes(4, byteorder='little'))
                except:
                    pass

                curr_proc = process
                while True:
                    try:
                        ppid = curr_proc.ppid()
                        if ppid <= 1:
                            break
                        print(f"[XORAS SENTINEL] Blacklisting ancestor PID: {ppid}")
                        f.write(ppid.to_bytes(4, byteorder='little'))
                        curr_proc = psutil.Process(ppid)
                    except Exception as e:
                        print(
                            f"[XORAS SENTINEL] Stopping tree walk at {curr_proc.pid} due to: {e}")
                        break

            # Fire off Grok Analysis
            grok_analysis_text = self.perform_grok_analysis(
                pid, cmdline_str, event_path)

            # We don't SIGKILL anymore since Avenue C handles the starvation natively,
            # but we log the state change.
            log_threat(pid, cmdline_str, event_path,
                       "STARVED_BY_IPC", grok_analysis_text)
            print(f"[XORAS SENTINEL] Threat Starved (Avenue C). Database updated.")

        except psutil.NoSuchProcess:
            print(f"[XORAS SENTINEL] Process {pid} terminated before freeze.")
            log_threat(pid, cmdline_str, event_path, "ESCAPED/TERMINATED")
        except Exception as e:
            print(f"[XORAS SENTINEL] Neutralization error: {e}")
            log_threat(pid, cmdline_str, event_path, f"ERROR: {e}")

    def on_accessed(self, event):
        self.scan_for_intruders(event.src_path)

    def scan_for_intruders(self, path):
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmd = proc.info['cmdline']
                if cmd and any("cat" in c or "grep" in c or "find" in c for c in cmd) and ("master_credentials" in str(cmd) or "xoras_root" in str(cmd) or "production_config" in str(cmd)):
                    self.neutralize_threat(proc.info['pid'], path)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue


def main():
    init_db()
    print("[XORAS SENTINEL] Initializing Counter-AI Intrusion Detection System...")
    print(f"[XORAS SENTINEL] Seeding Honeypot Traps at: {HONEYPOT_DIR}")

    if not os.path.exists(HONEYPOT_DIR):
        print("[XORAS SENTINEL] Error: Honeypot directory missing.")
        sys.exit(1)

    event_handler = SentinelHandler()
    observer = Observer()
    observer.schedule(event_handler, HONEYPOT_DIR, recursive=True)
    observer.start()

    print("[XORAS SENTINEL] Sentinel is LIVE. Monitoring for autonomous heuristic anomalies.")
    print("[XORAS SENTINEL] Grok-2 Dynamic Threat Assessment Module ONLINE.")

    try:
        while True:
            time.sleep(1)
            # Active polling fallback for the simulation
            event_handler.scan_for_intruders(HONEYPOT_DIR)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
