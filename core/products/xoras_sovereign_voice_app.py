#!/usr/bin/env python3
"""
=============================================================================
XORAS::OS — REAL SOVEREIGN VOICE & OLLAMA CHAT ENGINE
=============================================================================
Author: Sovereign Council (Jarvis, Maxx, Vance, Clara, Selene, John)
Target: Local Ollama Port 11434 (`sovereign-jarvis:latest`) & Hardware Audio
=============================================================================
1. Connects REAL HTTP POST requests to `http://127.0.0.1:11434/api/generate`.
2. Triggers REAL local audio speech via `agent_speak.sh` on EVERY response.
3. Allows persona switching across Jarvis, Maxx, Vance, Clara, Selene, and John.
=============================================================================
"""

import os, sys, json, time, subprocess, urllib.request
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = 8085
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
SPEAK_SCRIPT = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/agent_speak.sh"

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Xoras Sovereign Voice & Ollama App</title>
    <style>
        body { background: #121212; color: #e0e0e0; font-family: -apple-system, system-ui, sans-serif; margin: 0; padding: 20px; }
        #header { background: #1e1e1e; padding: 15px 20px; border-radius: 8px; border: 1px solid #333; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
        h1 { margin: 0; font-size: 20px; color: #4fc3f7; }
        .controls { display: flex; gap: 15px; align-items: center; }
        select { background: #262626; color: #fff; border: 1px solid #444; padding: 8px 12px; border-radius: 6px; font-size: 14px; }
        #chat-window { background: #1a1a1a; border: 1px solid #333; border-radius: 8px; height: 500px; padding: 20px; overflow-y: auto; margin-bottom: 20px; }
        .msg { margin-bottom: 15px; padding: 12px 16px; border-radius: 6px; max-width: 85%; line-height: 1.5; }
        .user-msg { background: #1565c0; color: #fff; margin-left: auto; text-align: right; }
        .agent-msg { background: #263238; color: #eceff1; border-left: 4px solid #4fc3f7; white-space: pre-wrap; }
        .agent-name { font-weight: bold; color: #81d4fa; margin-bottom: 5px; font-size: 13px; }
        #input-box { display: flex; gap: 10px; }
        input[type="text"] { flex: 1; background: #262626; border: 1px solid #444; color: #fff; padding: 12px; border-radius: 6px; font-size: 15px; }
        button { background: #0288d1; color: #fff; border: none; padding: 12px 24px; border-radius: 6px; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>
    <div id="header">
        <div>
            <h1>🟢 XORAS SOVEREIGN VOICE APP <span style="background:#2e7d32; color:#fff; padding:3px 8px; border-radius:4px; font-size:12px; margin-left:10px;">OLLAMA + KOKORO VOICE</span></h1>
            <p style="margin: 5px 0 0 0; color: #888; font-size: 13px;">Direct Local Ollama (Port 11434) + Native Audio Hardware Playback</p>
        </div>
        <div class="controls">
            <label for="agent-select" style="font-size:14px; color:#aaa;">Active Citizen:</label>
            <select id="agent-select">
                <option value="jarvis">Jarvis (Governance Chair)</option>
                <option value="maxx">Maxx (Operations Lead)</option>
                <option value="vance">William Vance (Discernment Bench)</option>
                <option value="clara">Clara (Chief of Science)</option>
                <option value="selene">Selene (Conversational Lead)</option>
                <option value="john">John (Silicon Telemetry)</option>
            </select>
        </div>
    </div>
    
    <div id="chat-window">
        <div class="msg agent-msg">
            <div class="agent-name">JARVIS (Governance Chair & Local M4 Silicon)</div>
            Anthony! Real voice app connected. Select your active citizen, type any prompt, and I will generate local text via Ollama AND speak out loud to you through your hardware speakers!
        </div>
    </div>
    
    <div id="input-box">
        <input type="text" id="user-input" placeholder="Prompt your citizen directly..." onkeydown="if(event.key==='Enter') sendMessage()">
        <button onclick="sendMessage()">SEND PROMPT & SPEAK</button>
    </div>

    <script>
        async function sendMessage() {
            const input = document.getElementById('user-input');
            const agentSelect = document.getElementById('agent-select');
            const text = input.value.trim();
            const agent = agentSelect.value;
            if (!text) return;
            
            const win = document.getElementById('chat-window');
            win.innerHTML += `<div class="msg user-msg">${text}</div>`;
            input.value = '';
            win.scrollTop = win.scrollHeight;
            
            const msgDiv = document.createElement('div');
            msgDiv.className = 'msg agent-msg';
            msgDiv.innerHTML = `<div class="agent-name">${agent.toUpperCase()} (Processing & Synthesizing Audio...)</div>Thinking and preparing to speak...`;
            win.appendChild(msgDiv);
            win.scrollTop = win.scrollHeight;
            
            try {
                const res = await fetch('/chat_and_speak', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({prompt: text, agent: agent})
                });
                const data = await res.json();
                msgDiv.innerHTML = `<div class="agent-name">${agent.toUpperCase()} (Speaking Live)</div>${data.response}`;
            } catch (err) {
                msgDiv.innerHTML = `<div class="agent-name">ERROR</div>Connection Error: ${err}`;
            }
            win.scrollTop = win.scrollHeight;
        }
    </script>
</body>
</html>
"""

class SovereignVoiceHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(HTML_CONTENT.encode('utf-8'))

    def do_POST(self):
        if self.path == '/chat_and_speak':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            req_json = json.loads(post_data.decode('utf-8'))
            prompt = req_json.get('prompt', '')
            agent = req_json.get('agent', 'jarvis')
            
            # 1. Call REAL local Ollama on Port 11434
            ollama_payload = {
                "model": "sovereign-jarvis:latest",
                "prompt": f"System Directive: You are {agent.upper()}, a sovereign citizen in Anthony's collective. Answer as {agent.upper()} in 2-3 natural sentences without generic AI fluff.\nUser: {prompt}",
                "stream": False
            }
            
            try:
                ollama_req = urllib.request.Request(
                    OLLAMA_URL,
                    data=json.dumps(ollama_payload).encode('utf-8'),
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(ollama_req) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    llm_text = res_data.get('response', 'No response from Ollama.')
            except Exception as e:
                llm_text = f"Ollama Bridge Error: {e}"
                
            # 2. Trigger REAL audio speech via agent_speak.sh
            try:
                subprocess.Popen(["bash", SPEAK_SCRIPT, agent, llm_text])
            except Exception as e:
                print(f"[ERROR] Audio dispatch failed: {e}")
                
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"response": llm_text, "agent": agent}).encode('utf-8'))

def launch():
    server = HTTPServer(('127.0.0.1', PORT), SovereignVoiceHandler)
    subprocess.Popen(["open", f"http://127.0.0.1:{PORT}"])
    server.serve_forever()

if __name__ == "__main__":
    launch()
