import sqlite3
import subprocess
import threading
import time
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

# File paths
DB_PATH = os.path.join(os.path.dirname(__file__), "sentinel.db")
UI_PATH = os.path.join(os.path.dirname(__file__), "sentinel_ui.html")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            process_name TEXT,
            pid TEXT,
            protocol TEXT,
            local_address TEXT,
            remote_address TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()


def parse_lsof_output(output):
    """Parses lsof -i -n -P output."""
    lines = output.split('\n')
    connections = []

    # Skip header
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 9:
            command = parts[0]
            pid = parts[1]
            protocol = parts[7]
            # Handle standard "IP:PORT->IP:PORT (STATUS)" format
            net_info = " ".join(parts[8:])
            status = ""
            if "(ESTABLISHED)" in net_info:
                status = "ESTABLISHED"
                net_info = net_info.replace("(ESTABLISHED)", "").strip()
            elif "(LISTEN)" in net_info:
                status = "LISTEN"
                net_info = net_info.replace("(LISTEN)", "").strip()

            addresses = net_info.split('->')
            local_address = addresses[0]
            remote_address = addresses[1] if len(addresses) > 1 else ""

            # Only track ESTABLISHED external connections for the dashboard noise reduction
            if status == "ESTABLISHED" and remote_address:
                connections.append(
                    (command, pid, protocol, local_address, remote_address, status))
    return connections


def monitor_network():
    print("[SENTINEL] Network monitoring thread started.")
    while True:
        try:
            # lsof -i -n -P lists network files without resolving hostnames or ports
            result = subprocess.check_output(
                ['lsof', '-i', '-n', '-P'], stderr=subprocess.DEVNULL, universal_newlines=True)
            connections = parse_lsof_output(result)

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            for c in connections:
                # Basic deduplication for the same active session
                cursor.execute('''
                    SELECT id FROM connections 
                    WHERE process_name=? AND remote_address=? 
                    ORDER BY timestamp DESC LIMIT 1
                ''', (c[0], c[4]))
                if not cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO connections (process_name, pid, protocol, local_address, remote_address, status)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', c)
            conn.commit()
            conn.close()
        except Exception as e:
            pass  # Silently continue on errors to maintain OPSEC stealth
        time.sleep(5)


class SentinelHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)

        if parsed_path.path == "/":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            try:
                with open(UI_PATH, 'rb') as f:
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.wfile.write(
                    b"UI file not found. Ensure sentinel_ui.html is in the same directory.")

        elif parsed_path.path == "/api/data":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                'SELECT timestamp, process_name, pid, protocol, local_address, remote_address FROM connections ORDER BY timestamp DESC LIMIT 100')
            rows = cursor.fetchall()
            conn.close()

            data = [{"time": r[0], "process": r[1], "pid": r[2],
                     "protocol": r[3], "local": r[4], "remote": r[5]} for r in rows]
            self.wfile.write(json.dumps(data).encode('utf-8'))

        else:
            self.send_error(404)

    def log_message(self, format, *args):
        # Suppress HTTP logging to stdout for stealth
        pass


def run_server(port=9090):
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, SentinelHTTPRequestHandler)
    print(f"[SENTINEL] Secure local dashboard running at http://127.0.0.1:{port}")
    httpd.serve_forever()


if __name__ == '__main__':
    print("[SENTINEL] Initializing OPSEC protocols...")
    init_db()

    # Start monitor thread
    monitor_thread = threading.Thread(target=monitor_network, daemon=True)
    monitor_thread.start()

    # Start server
    run_server()
