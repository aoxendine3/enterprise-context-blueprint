import urllib.request
import json

base = "http://127.0.0.1:8085"

# 1. Index page
with urllib.request.urlopen(f"{base}/", timeout=3) as r:
    html = r.read().decode("utf-8")
    print(f"[1] Index page OK, size: {len(html)} bytes, contains XORAS: {'XORAS // XMARS.os' in html}")

# 2. Workspace Tree
with urllib.request.urlopen(f"{base}/api/workspace/tree", timeout=3) as r:
    data = json.loads(r.read().decode("utf-8"))
    print(f"[2] Workspace Tree OK, root items: {len(data.get('tree', []))}")

# 3. Workspace Read
with urllib.request.urlopen(f"{base}/api/workspace/read?path=products/xmars_os/server.py", timeout=3) as r:
    data = json.loads(r.read().decode("utf-8"))
    print(f"[3] Workspace Read OK, lines: {data.get('lines')}, size: {data.get('size')} bytes")

# 4. Terminal Exec
req = urllib.request.Request(
    f"{base}/api/terminal/exec",
    data=json.dumps({"command": "git branch --show-current"}).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req, timeout=5) as r:
    data = json.loads(r.read().decode("utf-8"))
    print(f"[4] Terminal Exec OK, branch: {data.get('stdout').strip()}")

# 5. Preview Render
req = urllib.request.Request(
    f"{base}/api/preview/render",
    data=json.dumps({"html": "<div id='app'><h1>Sovereign Stage</h1></div>"}).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req, timeout=5) as r:
    data = json.loads(r.read().decode("utf-8"))
    print(f"[5] Preview Render OK, url: {data.get('preview_url')}")

print("\n[ALL 5 NEW WORKSPACE & LOVABLE APIS VERIFIED FLUID & OPERATIONAL]")
