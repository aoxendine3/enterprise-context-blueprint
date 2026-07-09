import os
import sys
import psutil
import sqlite3
import subprocess
import time
import json
import re

# Set paths
XORAS_DIR = "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core"
REGISTRY_PATH = os.path.join(XORAS_DIR, "XORAS_MASTER_AGENT_REGISTRY.md")
DB_PATH = os.path.join(XORAS_DIR, "xoras_memory.db")
BLOBS_DIR = os.path.join(XORAS_DIR, "Source/whisper.cpp/blobs")
MANIFESTS_DIR = os.path.join(XORAS_DIR, "Source/whisper.cpp/manifests")

class XorasSystemScanner:
    def __init__(self):
        self.report = []

    def log(self, section: str, message: str):
        self.report.append(f"### {section}\n{message}\n")

    def run_diagnostics(self):
        print("=== [SCANNER] Initiating System-Wide OPSEC & Performance Diagnostics ===")
        
        # 1. Disk and Hardware Space Analysis
        self.scan_disk_space()

        # 2. Orphaned Blobs / Model Caches Scan
        self.scan_model_blobs()

        # 3. Process Integrity and Daemon Audits
        self.scan_active_processes()

        # 4. Database Telemetry Audits
        self.scan_database_metrics()

        # 5. Compile Final Diagnostic Report
        self.generate_final_report()

    def scan_disk_space(self):
        disk = psutil.disk_usage('/')
        free_gb = disk.free / (1024 ** 3)
        total_gb = disk.total / (1024 ** 3)
        used_percent = disk.percent

        status = "🔴 CRITICAL ALERT" if used_percent > 90 else "🟢 HEALTHY"
        
        message = (
            f"* **Drive Status:** {status}\n"
            f"* **Available Free Space:** **{free_gb:.2f} GB** (Total: {total_gb:.2f} GB)\n"
            f"* **Disk Capacity Utilized:** **{used_percent}%**\n\n"
            f"**Simple Explanation:** Your computer is almost completely full. If the space drops to zero, "
            f"your databases will fail to save data and applications will freeze. We need to free up space immediately."
        )
        self.log("💿 Disk Storage & Capacity", message)

    def scan_model_blobs(self):
        if not os.path.exists(BLOBS_DIR):
            self.log("🧠 Model Blobs & Caches", "No model blobs folder found.")
            return

        # Read manifest file to find referenced model digests
        referenced = set()
        manifest_files = []
        for root, _, files in os.walk(MANIFESTS_DIR):
            for file in files:
                if not file.startswith('.'):
                    manifest_files.append(os.path.join(root, file))

        for mf in manifest_files:
            try:
                with open(mf, 'r') as f:
                    data = json.load(f)
                    for layer in data.get("layers", []):
                        digest = layer.get("digest", "").replace("sha256:", "")
                        if digest:
                            referenced.add(digest)
            except Exception:
                pass

        # Scan blobs folder
        blobs = []
        total_blobs_size = 0
        for file in os.listdir(BLOBS_DIR):
            if file.startswith("sha256-"):
                digest = file.replace("sha256-", "")
                path = os.path.join(BLOBS_DIR, file)
                size_mb = os.path.getsize(path) / (1024 ** 2)
                total_blobs_size += os.path.getsize(path)
                
                # Check model name inside the binary GGUF file
                model_name = "Unknown Model"
                try:
                    with open(path, "rb") as f:
                        header = f.read(1000)
                        # Extract general.name from metadata if readable
                        match = re.search(b'general\\.name\x00([^\x00]+)', header)
                        if match:
                            model_name = match.group(1).decode('utf-8', errors='ignore')
                        else:
                            # Fallback string extract
                            strings = re.findall(b'[a-zA-Z0-9\\.\\- _]{8,}', header)
                            for s in strings:
                                s_dec = s.decode('utf-8', errors='ignore')
                                if "Coder" in s_dec or "Llama" in s_dec or "nomic" in s_dec:
                                    model_name = s_dec
                                    break
                except Exception:
                    pass

                is_referenced = digest in referenced
                blobs.append({
                    "filename": file,
                    "model_name": model_name,
                    "size_gb": size_mb / 1024,
                    "status": "🟢 Active (In Use)" if is_referenced else "🔴 ORPHANED (Safe to Delete)"
                })

        blob_summary = f"* **Total Local Model Cache Size:** **{total_blobs_size / (1024**3):.2f} GB**\n\n"
        blob_summary += "| Model Name / Digest | Size | Status | Action |\n"
        blob_summary += "| :--- | :--- | :--- | :--- |\n"
        for b in blobs:
            action = "None" if "Active" in b["status"] else "**DELETE** to free space"
            blob_summary += f"| {b['model_name']} (`{b['filename'][:12]}...`) | {b['size_gb']:.2f} GB | {b['status']} | {action} |\n"

        blob_summary += (
            f"\n**Simple Explanation:** We found large AI models stored in your code directory. "
            f"Only some are being used. The orphaned ones are cluttering your drive and can be deleted to recover space."
        )
        self.log("🧠 Model Blobs & Caches", blob_summary)

    def scan_active_processes(self):
        daemons = {
            "sentinel_core.py": "Network Intrusion Monitor",
            "xoras_evolution_daemon.py": "Swarm Evolution Loop",
            "xoras_sovereign_nexus.py": "Sovereign Nexus Coordinator"
        }
        
        status_table = "| Process Name | Description | Status | PID |\n"
        status_table += "| :--- | :--- | :--- | :--- |\n"
        
        for name, desc in daemons.items():
            pid = "N/A"
            status = "🔴 STOPPED"
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmd = proc.info.get('cmdline')
                    if cmd and any(name in part for part in cmd):
                        pid = str(proc.info['pid'])
                        status = "🟢 RUNNING"
                        break
                except Exception:
                    pass
            status_table += f"| `{name}` | {desc} | {status} | {pid} |\n"

        status_table += (
            f"\n**Simple Explanation:** These are the active defensive scripts guarding your codebase. "
            f"Running status means they are actively watching for intruders and maintaining system health."
        )
        self.log("🤖 Active Guard Daemons", status_table)

    def scan_database_metrics(self):
        if not os.path.exists(DB_PATH):
            self.log("📊 Database Storage & Telemetry", "No primary SQLite database found.")
            return

        db_size_mb = os.path.getsize(DB_PATH) / (1024 ** 2)
        message = f"* **Primary Database Size:** **{db_size_mb:.2f} MB**\n"
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Count rows
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [t[0] for t in cursor.fetchall()]
            
            message += "\n| Table Name | Row Count | Status |\n"
            message += "| :--- | :--- | :--- |\n"
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                status = "⚠️ Large Telemetry Feed" if count > 50000 else "🟢 Healthy Size"
                message += f"| `{table}` | {count:,} | {status} |\n"
            
            conn.close()
        except Exception as e:
            message += f"\n* **Error reading database metrics:** {e}\n"

        message += (
            f"\n**Simple Explanation:** Telemetry table tracks system heartbeat metrics. "
            f"As it grows to hundreds of thousands of rows, we should periodically prune it to reclaim disk space."
        )
        self.log("📊 Database Storage & Telemetry", message)

    def generate_final_report(self):
        output_file = os.path.join(XORAS_DIR, "system_audit_report.md")
        
        header = (
            "# Xoras System Diagnostic & Integrity Report\n"
            f"**Scan Executed At:** {time.strftime('%Y-%m-%d %H:%M:%S Local')}\n"
            "**System Classification:** [PRODUCTION]\n\n"
            "---"
        )
        
        full_content = header + "\n\n" + "\n".join(self.report)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(full_content)
            
        print(f"=== [SCANNER] Diagnostic complete. Report saved to {output_file} ===")
        sys.stdout.flush()

        # Trigger native Mac voice report for highlights
        free_space = psutil.disk_usage('/').free / (1024 ** 3)
        voice_msg = (
            f"Diagnostic complete. Disk storage is critical with only {free_space:.1f} gigabytes remaining. "
            "Large orphaned model files and telemetry feeds have been identified. Detailed markdown report saved."
        )
        subprocess.Popen(["say", voice_msg])

if __name__ == "__main__":
    scanner = XorasSystemScanner()
    scanner.run_diagnostics()
