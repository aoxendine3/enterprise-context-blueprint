import os
import subprocess
import http.server
import socketserver
import webbrowser
import threading

PORT = 8080
DIRECTORY = r"C:\Users\admin\Desktop\SSOT_Agentic_Brain\ops\scripts\fullscreen_ui"

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

def launch_visual_dashboard(url):
    try:
        webbrowser.open(url)
    except Exception:
        pass
    if os.name == 'nt':
        try:
            subprocess.Popen(f'start {url}', shell=True)
        except Exception:
            pass

def run_server():
    os.chdir(DIRECTORY)
    socketserver.TCPServer.allow_reuse_address = True
    url = f"http://127.0.0.1:{PORT}/customer_app.html"
    print(f"XORAS Sovereign Stage serving live across LAN on {url}")
    # Launch browser after slight delay to ensure server binding
    threading.Timer(0.8, lambda: launch_visual_dashboard(url)).start()
    with socketserver.TCPServer(("0.0.0.0", PORT), CustomHandler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    import sys, ctypes
    if os.name == 'nt' or sys.platform == 'win32':
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Global\\StageServerSingleInstance")
        if ctypes.windll.kernel32.GetLastError() == 183:
            print("[STAGE SERVER] Stage server process already running. Exiting duplicate instance.")
            sys.exit(0)
    run_server()
