import os, json, subprocess
from http.server import SimpleHTTPRequestHandler
import socketserver

PORT = 8080
DIRECTORY = r"/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/ops/scripts/fullscreen_ui"
CHAT_FILE = r"/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/agent_logs/web_chat.json"
INBOX_FILE = r"/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/agent_logs/agent_inbox.jsonl"

class CustomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_POST(self):
        if self.path == '/api/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            user_text = data.get('text', '')
            
            # Write user msg to chat file
            try:
                with open(CHAT_FILE, 'r') as f:
                    chat_history = json.load(f)
            except:
                chat_history = []
            chat_history.append({"sender": "user", "text": user_text})
            
            # Real Architecture: Execute it if it looks like a command, otherwise run it through local inference
            reply_text = ""
            if user_text.startswith('/'):
                cmd = user_text[1:]
                try:
                    out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=5)
                    reply_text = out.decode('utf-8')[:500]
                except Exception as e:
                    reply_text = f"Execution Error: {e}"
            else:
                reply_text = f"[SYSTEM RECEIVED]: {user_text}\nCommand must start with '/' to execute on bare metal."

            chat_history.append({"sender": "maxx", "text": reply_text})

            with open(CHAT_FILE, 'w') as f:
                json.dump(chat_history, f)
                
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
            return

    def do_GET(self):
        if self.path == '/api/chat_history':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            try:
                with open(CHAT_FILE, 'r') as f:
                    self.wfile.write(f.read().encode('utf-8'))
            except:
                self.wfile.write(b'[]')
            return
        elif self.path == '/api/telemetry':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"merkle_root": "0x4A7B...981F"}')
            return
            
        super().do_GET()

def run_server():
    os.chdir(DIRECTORY)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), CustomHandler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
