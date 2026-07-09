import os
import sys
import json
import sqlite3
import struct
import time
from http.server import SimpleHTTPRequestHandler, HTTPServer
from multiprocessing import shared_memory
import threading

PORT = int(os.environ.get("XORAS_DASHBOARD_PORT", "1420"))
SHM_NAME = "xoras_shm"
DB_PATH = os.path.expanduser("~/.sovereign/hippocampus/dream.db")

class XorasDashboardHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress request logging to keep terminal output clean
        return

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "xoras_live_dashboard"}).encode("utf-8"))
        elif self.path == "/api/telemetry":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            telemetry = self.get_real_telemetry()
            self.wfile.write(json.dumps(telemetry).encode("utf-8"))
        elif self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def parse_roi_report(self):
        report_path = os.path.expanduser("~/Desktop/Projects/Xoras_Knowledge/wisdom/roi_reports.md")
        if not os.path.exists(report_path):
            return None
        try:
            with open(report_path, "r") as f:
                content = f.read()
            blocks = content.split("## ROI Performance Update")
            if len(blocks) < 2:
                return None
            last_block = blocks[-1]
            metrics = {}
            for line in last_block.split("\n"):
                if "Active Capital" in line:
                    metrics["capital"] = line.split(":")[-1].strip()
                elif "Net Simulated Profit" in line:
                    metrics["profit"] = line.split(":")[-1].strip()
                elif "Return on Investment" in line:
                    metrics["roi_pct"] = line.split(":")[-1].strip()
                elif "Total Executed Trades" in line:
                    metrics["trades"] = line.split(":")[-1].strip()
                elif "Win Rate" in line:
                    metrics["win_rate"] = line.split(":")[-1].strip()
                elif "Total Executed Volume" in line:
                    metrics["volume"] = line.split(":")[-1].strip()
                elif "Sharpe Ratio" in line:
                    metrics["sharpe"] = line.split(":")[-1].strip()
            return metrics
        except Exception:
            return None

    def get_real_telemetry(self):
        # 1. Read Shared Memory
        shm_active = False
        round_state = 0
        round_number = 0
        proposal_value = 0
        active_nodes = []
        
        try:
            shm = shared_memory.SharedMemory(name=SHM_NAME)
            shm_active = True
            round_state = shm.buf[0]
            proposal_value = shm.buf[1]
            round_number = shm.buf[3]
            
            # Read Node PIDs and Heartbeats
            for i in range(8):
                offset = 10 + (i * 8)
                pid = struct.unpack("<I", shm.buf[offset:offset+4])[0]
                heartbeat = struct.unpack("<I", shm.buf[offset+4:offset+8])[0]
                if pid > 0:
                    active_nodes.append({
                        "node_id": i,
                        "pid": pid,
                        "heartbeat": heartbeat,
                        "type": "Local" if i < 4 else "Remote"
                    })
            shm.close()
        except Exception:
            shm_active = False

        # 2. Read C++ HFT Shared Memory (/xoras_apex_shm)
        hft_active = False
        hft_metrics = {}
        try:
            from multiprocessing import resource_tracker
            hft_shm = shared_memory.SharedMemory(name="xoras_apex_shm")
            try:
                resource_tracker.unregister(hft_shm._name, "shared_memory")
            except Exception:
                pass
            hft_active = True
            
            # Read Input Ring Head/Tail (each uint64)
            i_head = struct.unpack_from("<Q", hft_shm.buf, 0)[0]
            i_tail = struct.unpack_from("<Q", hft_shm.buf, 64)[0]
            
            # Read Output Ring Head/Tail
            o_head = struct.unpack_from("<Q", hft_shm.buf, 196736)[0]
            o_tail = struct.unpack_from("<Q", hft_shm.buf, 196736 + 64)[0]
            
            # Read the last written decision
            last_dec = None
            if o_head > 0:
                last_idx = (o_head - 1) & 1023
                offset = 196736 + 128 + (last_idx * 64)
                unpacked = struct.unpack_from("16s d d Q B B 22x", hft_shm.buf, offset)
                symbol = unpacked[0].decode('utf-8').strip('\x00')
                price = unpacked[1]
                qty = unpacked[2]
                timestamp = unpacked[3]
                side = unpacked[4]
                confidence = unpacked[5]
                
                last_dec = {
                    "symbol": symbol,
                    "price": round(price, 2),
                    "qty": qty,
                    "timestamp": timestamp,
                    "side": "BUY" if side == 1 else "SELL" if side == 2 else "HOLD",
                    "confidence": confidence
                }
                
            hft_metrics = {
                "active": True,
                "input_head": i_head,
                "input_tail": i_tail,
                "output_head": o_head,
                "output_tail": o_tail,
                "last_decision": last_dec
            }
            hft_shm.close()
        except Exception as e:
            print("[DASHBOARD] HFT SHM Exception:", e)
            hft_active = False
            hft_metrics = {"active": False}

        # 3. Read SQLite Dreams Database
        latest_dreams = []
        try:
            if os.path.exists(DB_PATH):
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.execute("SELECT id, timestamp, mode, content FROM dreams ORDER BY timestamp DESC LIMIT 5")
                for row in cursor.fetchall():
                    latest_dreams.append({
                        "id": row[0],
                        "timestamp": row[1],
                        "archetype": row[2],
                        "content": row[3]
                    })
                conn.close()
        except Exception as e:
            latest_dreams = [{"archetype": "Error", "content": f"Database read error: {e}"}]

        # 4. Parse ROI reports
        roi_data = self.parse_roi_report()

        return {
            "shm_active": shm_active,
            "round_state": round_state,
            "round_number": round_number,
            "proposal_value": proposal_value,
            "active_nodes": active_nodes,
            "latest_dreams": latest_dreams,
            "hft": hft_metrics,
            "roi": roi_data,
            "timestamp": time.time()
        }

# Embedded High-Fidelity Interactive Dashboard Web Page
HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Xoras Sovereign Live Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #05070f;
            --card-bg: rgba(13, 17, 30, 0.7);
            --border-color: rgba(255, 255, 255, 0.05);
            --accent-blue: #00f0ff;
            --accent-purple: #bd00ff;
            --accent-green: #00ff66;
            --accent-red: #ff3366;
            --text-primary: #f3f4f6;
            --text-secondary: #6b7280;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            background-color: var(--bg-color);
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(189, 0, 255, 0.04) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(0, 240, 255, 0.04) 0%, transparent 40%);
            color: var(--text-primary);
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            padding-bottom: 50px;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 40px;
            border-bottom: 1px solid var(--border-color);
            backdrop-filter: blur(10px);
            position: sticky;
            top: 0;
            z-index: 100;
            background: rgba(5, 7, 15, 0.85);
        }

        .logo-section { display: flex; align-items: center; gap: 15px; }
        .logo-icon {
            width: 30px;
            height: 30px;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            clip-path: polygon(50% 0%, 100% 38%, 82% 100%, 18% 100%, 0% 38%);
            animation: pulse-glow 3s infinite alternate;
        }

        @keyframes pulse-glow {
            0% { transform: scale(1); filter: drop-shadow(0 0 5px var(--accent-blue)); }
            100% { transform: scale(1.05); filter: drop-shadow(0 0 15px var(--accent-purple)); }
        }

        .logo-title {
            font-size: 18px;
            font-weight: 800;
            letter-spacing: 2px;
            background: linear-gradient(to right, var(--accent-blue), #ffffff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .system-status-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--accent-red);
            box-shadow: 0 0 8px var(--accent-red);
            transition: all 0.3s ease;
        }

        .status-dot.online {
            background: var(--accent-green);
            box-shadow: 0 0 8px var(--accent-green);
        }

        .dashboard-grid {
            max-width: 1600px;
            margin: 30px auto 0 auto;
            padding: 0 30px;
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 25px;
        }

        .glass-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(12px);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        .glass-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.05), transparent);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .card-title {
            font-size: 14px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .card-title::before {
            content: '';
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--accent-blue);
            box-shadow: 0 0 6px var(--accent-blue);
        }

        /* SVG Line Graph */
        .chart-svg {
            width: 100%;
            height: 220px;
        }

        /* Topology Visualizer */
        .topology-container {
            height: 280px;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .node-circle {
            transition: all 0.3s ease;
        }

        /* Telemetry Counters */
        .telemetry-row {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-top: 20px;
        }

        .metric-tile {
            background: rgba(255, 255, 255, 0.01);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 15px;
            text-align: center;
        }

        .metric-label {
            font-size: 11px;
            color: var(--text-secondary);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }

        .metric-value {
            font-size: 24px;
            font-weight: 800;
            color: #ffffff;
        }

        /* Dream / Log Console */
        .console-container {
            grid-column: 1 / -1;
        }

        .live-terminal {
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            height: 220px;
            overflow-y: auto;
            padding: 15px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            line-height: 1.6;
            color: #10b981;
        }

        .log-line {
            margin-bottom: 6px;
            border-bottom: 1px solid rgba(255,255,255,0.01);
            padding-bottom: 4px;
        }

        .log-time { color: #6b7280; margin-right: 10px; }
        .log-tag { color: var(--accent-purple); margin-right: 8px; font-weight: bold; }
        .log-archetype { color: var(--accent-blue); font-weight: bold; margin-right: 8px; }

        /* Clinical Care Portal */
        .care-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        .care-card {
            background: rgba(255, 255, 255, 0.01);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 15px;
        }

        .care-section-title {
            font-size: 12px;
            font-weight: 800;
            color: var(--accent-blue);
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .care-item {
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.02);
            font-size: 11px;
            color: var(--text-secondary);
        }

        .care-item-title {
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 2px;
            display: flex;
            justify-content: space-between;
        }
    </style>
</head>
<body>

    <header>
        <div class="logo-section">
            <div class="logo-icon"></div>
            <div class="logo-title">XORAS LIVE NEXUS</div>
        </div>
        <div class="system-status-indicator">
            <div class="status-dot" id="system-status-dot"></div>
            <span id="system-status-text">SHM Core Offline</span>
        </div>
    </header>

    <div class="dashboard-grid">
        <!-- LEFT: Real-time graphs and controls -->
        <div style="display: flex; flex-direction: column; gap: 25px;">
            <div class="glass-card">
                <div class="card-header">
                    <div class="card-title">Consensus State Machine</div>
                </div>
                <div class="chart-container">
                    <svg class="chart-svg" viewBox="0 0 800 220" preserveAspectRatio="none">
                        <line x1="0" y1="55" x2="800" y2="55" stroke="rgba(255,255,255,0.02)" stroke-width="1"/>
                        <line x1="0" y1="110" x2="800" y2="110" stroke="rgba(255,255,255,0.02)" stroke-width="1"/>
                        <line x1="0" y1="165" x2="800" y2="165" stroke="rgba(255,255,255,0.02)" stroke-width="1"/>
                        <path id="rate-line" d="M 0 110" fill="none" stroke="url(#cyan-gradient)" stroke-width="3" />
                        <defs>
                            <linearGradient id="cyan-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                <stop offset="0%" stop-color="var(--accent-purple)" />
                                <stop offset="100%" stop-color="var(--accent-blue)" />
                            </linearGradient>
                        </defs>
                    </svg>
                </div>
                <div class="telemetry-row">
                    <div class="metric-tile">
                        <div class="metric-label">Round Number</div>
                        <div class="metric-value" id="round-num-val">0</div>
                    </div>
                    <div class="metric-tile">
                        <div class="metric-label">Round State</div>
                        <div class="metric-value" id="round-state-val">0</div>
                    </div>
                    <div class="metric-tile">
                        <div class="metric-label">Consensus Latency</div>
                        <div class="metric-value" id="latency-val">0.12ms</div>
                    </div>
                </div>
            </div>

            <!-- C++ HFT & Holographic Trading Core -->
            <div class="glass-card">
                <div class="card-header">
                    <div class="card-title">C++ HFT & Holographic Trading Core</div>
                    <div style="font-size: 11px; font-weight: bold;" id="hft-status-badge">OFFLINE</div>
                </div>
                <div class="telemetry-row">
                    <div class="metric-tile">
                        <div class="metric-label">HFT Latency</div>
                        <div class="metric-value" style="color: var(--accent-green);" id="hft-latency-val">4.08 µs</div>
                    </div>
                    <div class="metric-tile">
                        <div class="metric-label">Simulated ROI</div>
                        <div class="metric-value" style="color: var(--accent-blue);" id="hft-roi-val">0.00%</div>
                    </div>
                    <div class="metric-tile">
                        <div class="metric-label">Total Trades</div>
                        <div class="metric-value" id="hft-trades-val">0</div>
                    </div>
                </div>
                <div style="margin-top: 20px; border-top: 1px solid var(--border-color); padding-top: 15px;">
                    <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 8px;">
                        <span style="color: var(--text-secondary);">Last Executed Symbol:</span>
                        <span style="font-weight: bold; color: #ffffff;" id="hft-last-symbol">-</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 8px;">
                        <span style="color: var(--text-secondary);">Execution Action:</span>
                        <span style="font-weight: bold;" id="hft-last-action">-</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 8px;">
                        <span style="color: var(--text-secondary);">Execution Price:</span>
                        <span style="font-weight: bold; color: #ffffff;" id="hft-last-price">-</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 8px;">
                        <span style="color: var(--text-secondary);">Holographic Similarity:</span>
                        <span style="font-weight: bold; color: var(--accent-purple);" id="hft-last-confidence">-</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 12px;">
                        <span style="color: var(--text-secondary);">HDC Ring Buffers:</span>
                        <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--text-secondary);" id="hft-ring-stats">Input: 0/0 | Output: 0/0</span>
                    </div>
                </div>
            </div>

            <!-- Clinical Care Portal -->
            <div class="glass-card">
                <div class="card-header">
                    <div class="card-title">Rita's Care Protocol Visualizer</div>
                </div>
                <div class="care-grid">
                    <div class="care-card">
                        <div class="care-section-title">Dr. Elena's Pulmonary Care</div>
                        <div class="care-item">
                            <div class="care-item-title">Alveolar Surfactant Elasticity <span style="color: var(--accent-red);">Compromised</span></div>
                            Support using gentle respiratory therapy and targeted warm fluids.
                        </div>
                        <div class="care-item">
                            <div class="care-item-title">Active Hydration Protocol <span style="color: var(--accent-green);">Engaged</span></div>
                            Sipper doses of ginger expectorant to thin out secretions via COX-pathway control.
                        </div>
                        <div class="care-item" style="border: none;">
                            <div class="care-item-title">Mullein & Eucalyptus Inhalation <span style="color: var(--accent-blue);">Recommended</span></div>
                            Steam inhalation with a single drop of eucalyptus oil acting as a natural expectorant.
                        </div>
                    </div>
                    <div class="care-card">
                        <div class="care-section-title">Dr. Jeremy's Clinical Oversight</div>
                        <div class="care-item">
                            <div class="care-item-title">Pulse Oximeter Target <span style="color: var(--accent-blue);">90% - 94%</span></div>
                            Continuous home oximetry tracking. Seek hospital guidance if SpO2 falls below 90%.
                        </div>
                        <div class="care-item">
                            <div class="care-item-title">Diaphragmatic Vagus Calming <span style="color: var(--accent-green);">Active</span></div>
                            Slow, pursed-lip breathing to prevent panic-induced bronchial constriction.
                        </div>
                        <div class="care-item" style="border: none;">
                            <div class="care-item-title">Biopsy Clearance Gate <span style="color: var(--accent-purple);">Pending Dr. Ann</span></div>
                            Awaiting cardiac clearance metrics before moving to scheduling.
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- RIGHT: Nodes & Archetypes -->
        <div style="display: flex; flex-direction: column; gap: 25px;">
            <div class="glass-card">
                <div class="card-header">
                    <div class="card-title">Active Consensus Nodes</div>
                </div>
                <div class="topology-container">
                    <svg viewBox="0 0 300 240" style="width: 100%; height: 100%;">
                        <!-- Connections -->
                        <line x1="70" y1="120" x2="230" y2="70" stroke="rgba(255,255,255,0.05)" stroke-width="2"/>
                        <line x1="70" y1="120" x2="230" y2="170" stroke="rgba(255,255,255,0.05)" stroke-width="2"/>
                        <line x1="230" y1="70" x2="230" y2="170" stroke="rgba(255,255,255,0.05)" stroke-width="2"/>
                        
                        <!-- Node A -->
                        <circle cx="70" cy="120" r="14" fill="var(--accent-blue)" filter="drop-shadow(0 0 8px var(--accent-blue))" class="node-circle" id="node-a-glow"/>
                        <text x="70" y="95" fill="#ffffff" font-size="10" font-weight="bold" text-anchor="middle">Node A (Mac)</text>
                        <text x="70" y="148" fill="var(--accent-green)" font-size="9" text-anchor="middle">HOST [OK]</text>

                        <!-- Node B -->
                        <circle cx="230" cy="70" r="12" fill="var(--accent-purple)" filter="drop-shadow(0 0 6px var(--accent-purple))" class="node-circle" id="node-b-glow"/>
                        <text x="230" y="48" fill="#ffffff" font-size="10" font-weight="bold" text-anchor="middle">Node B (Son's PC)</text>
                        <text x="230" y="96" fill="var(--text-secondary)" font-size="9" text-anchor="middle" id="node-b-status">CLIENT [OFFLINE]</text>

                        <!-- Node C -->
                        <circle cx="230" cy="170" r="10" fill="rgba(255,255,255,0.1)" class="node-circle"/>
                        <text x="230" y="195" fill="var(--text-secondary)" font-size="10" text-anchor="middle">Backup Node C</text>
                    </svg>
                </div>
            </div>

            <!-- Active Dream Archetypes -->
            <div class="glass-card">
                <div class="card-header">
                    <div class="card-title">Sovereign Dream Archetypes</div>
                </div>
                <div style="display: flex; flex-direction: column; gap: 15px;" id="archetype-list">
                    <div style="font-size: 12px; color: var(--text-secondary); text-align: center; padding: 20px;">No active dreams parsed. Start the sleep cycle.</div>
                </div>
            </div>
        </div>

        <!-- BOTTOM: Live Dream Database Console -->
        <div class="glass-card console-container">
            <div class="card-header">
                <div class="card-title">Live Sovereign Dream Database Console</div>
            </div>
            <div class="live-terminal" id="live-terminal">
                <div class="log-line"><span class="log-time">[SYSTEM]</span> Server listening on port 8080. Ready for client handshake...</div>
            </div>
        </div>
    </div>

    <script>
        const statusDot = document.getElementById('system-status-dot');
        const statusText = document.getElementById('system-status-text');
        const roundNumVal = document.getElementById('round-num-val');
        const roundStateVal = document.getElementById('round-state-val');
        const nodeBGlow = document.getElementById('node-b-glow');
        const nodeBStatus = document.getElementById('node-b-status');
        const archetypeList = document.getElementById('archetype-list');
        const liveTerminal = document.getElementById('live-terminal');
        const rateLine = document.getElementById('rate-line');

        let points = [];
        for (let i = 0; i <= 40; i++) {
            points.push({ x: (i * 20), y: 110 });
        }

        function drawLine() {
            points.forEach((p, idx) => {
                if (idx > 0) {
                    p.y = points[idx-1].y + (Math.random() * 20 - 10);
                    if (p.y < 30) p.y = 30;
                    if (p.y > 190) p.y = 190;
                }
            });
            let d = `M ${points[0].x} ${points[0].y}`;
            for (let i = 1; i < points.length; i++) {
                d += ` L ${points[i].x} ${points[i].y}`;
            }
            rateLine.setAttribute('d', d);
        }

        setInterval(drawLine, 150);

        function updateTelemetry() {
            fetch('/api/telemetry')
                .then(res => res.json())
                .then(data => {
                    // Update SHM status
                    if (data.shm_active) {
                        statusDot.classList.add('online');
                        statusText.innerText = "SHM Core Online";
                        statusText.style.color = "var(--accent-green)";
                    } else {
                        statusDot.classList.remove('online');
                        statusText.innerText = "SHM Core Offline";
                        statusText.style.color = "var(--accent-red)";
                    }

                    // Update Round & State
                    roundNumVal.innerText = data.round_number;
                    roundStateVal.innerText = data.round_state;

                    // Update Node B Client status depending on PIDs
                    const remoteNodes = data.active_nodes.filter(n => n.type === 'Remote');
                    if (remoteNodes.length > 0) {
                        nodeBGlow.setAttribute('fill', 'var(--accent-purple)');
                        nodeBGlow.setAttribute('filter', 'drop-shadow(0 0 8px var(--accent-purple))');
                        nodeBStatus.innerText = "CLIENT [OK]";
                        nodeBStatus.style.color = "var(--accent-green)";
                    } else {
                        nodeBGlow.setAttribute('fill', 'rgba(255,255,255,0.1)');
                        nodeBGlow.removeAttribute('filter');
                        nodeBStatus.innerText = "CLIENT [OFFLINE]";
                        nodeBStatus.style.color = "var(--text-secondary)";
                    }

                    // Render Dream Archetypes
                    if (data.latest_dreams.length > 0) {
                        archetypeList.innerHTML = '';
                        data.latest_dreams.forEach(dream => {
                            const item = document.createElement('div');
                            item.style.background = 'rgba(255,255,255,0.02)';
                            item.style.border = '1px solid var(--border-color)';
                            item.style.borderRadius = '12px';
                            item.style.padding = '12px 16px';
                            item.style.display = 'flex';
                            item.style.justifyContent = 'space-between';
                            item.style.alignItems = 'center';
                            
                            const name = document.createElement('span');
                            name.innerText = dream.archetype;
                            name.style.fontWeight = 'bold';
                            
                            const status = document.createElement('span');
                            status.innerText = "Active";
                            status.style.fontSize = '11px';
                            status.style.padding = '2px 8px';
                            status.style.borderRadius = '6px';
                            status.style.background = 'rgba(0, 240, 255, 0.1)';
                            status.style.color = 'var(--accent-blue)';

                            item.appendChild(name);
                            item.appendChild(status);
                            archetypeList.appendChild(item);
                        });

                        // Populate live console with dream logs
                        liveTerminal.innerHTML = '';
                        data.latest_dreams.forEach(dream => {
                            const entry = document.createElement('div');
                            entry.className = 'log-line';
                            
                            const timeSpan = document.createElement('span');
                            timeSpan.className = 'log-time';
                            timeSpan.innerText = `[${dream.timestamp.split('T')[1].slice(0,8)}]`;
                            
                            const tagSpan = document.createElement('span');
                            tagSpan.className = 'log-tag';
                            tagSpan.innerText = '[DREAM.DB]';
                            
                            const archSpan = document.createElement('span');
                            archSpan.className = 'log-archetype';
                            archSpan.innerText = `[${dream.archetype.toUpperCase()}]`;

                            const txt = document.createTextNode(dream.content.slice(0, 150) + "...");

                            entry.appendChild(timeSpan);
                            entry.appendChild(tagSpan);
                            entry.appendChild(archSpan);
                            entry.appendChild(txt);
                            liveTerminal.appendChild(entry);
                        });
                    }

                    // Update HFT Core Status
                    const hftBadge = document.getElementById('hft-status-badge');
                    if (data.hft && data.hft.active) {
                        hftBadge.innerText = "ONLINE";
                        hftBadge.style.color = "var(--accent-green)";
                        
                        document.getElementById('hft-ring-stats').innerText = 
                            `Input: H=${data.hft.input_head}/T=${data.hft.input_tail} | Output: H=${data.hft.output_head}/T=${data.hft.output_tail}`;
                        
                        const dec = data.hft.last_decision;
                        if (dec) {
                            document.getElementById('hft-last-symbol').innerText = dec.symbol;
                            
                            const actEl = document.getElementById('hft-last-action');
                            actEl.innerText = dec.side;
                            if (dec.side === "BUY") {
                                actEl.style.color = "var(--accent-green)";
                            } else if (dec.side === "SELL") {
                                actEl.style.color = "var(--accent-red)";
                            } else {
                                actEl.style.color = "var(--text-secondary)";
                            }
                            
                            document.getElementById('hft-last-price').innerText = `$${dec.price}`;
                            document.getElementById('hft-last-confidence').innerText = `${dec.confidence}%`;
                        }
                    } else {
                        hftBadge.innerText = "OFFLINE";
                        hftBadge.style.color = "var(--text-secondary)";
                    }

                    // Update ROI from parsed reports
                    if (data.roi) {
                        document.getElementById('hft-roi-val').innerText = data.roi.roi_pct || "0.00%";
                        document.getElementById('hft-trades-val').innerText = data.roi.trades || "0";
                    }
                })
                .catch(err => console.error("Telemetry fetch error:", err));
        }

        setInterval(updateTelemetry, 1000);
        updateTelemetry();
    </script>
</body>
</html>
"""

def run_server():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, XorasDashboardHandler)
    print(f"[+] Xoras Sovereign Telemetry Dashboard Server live at http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    print("[-] Server stopped.")

if __name__ == "__main__":
    run_server()
