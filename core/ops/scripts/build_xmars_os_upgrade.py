#!/usr/bin/env python3
"""
ops/scripts/build_xmars_os_upgrade.py
Compiles the adult, elite-grade XMARS.os Sovereign Command Center:
Unifying Hermes (Deep Cognitive Reasoning & Neural Voice),
Cursor (Workspace File Explorer, Code Editor & Terminal Executor),
and Lovable (Real-Time Interactive Visual Canvas & Sandbox Preview).
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(r"C:\Users\admin\Desktop\SSOT_Agentic_Brain")
XMARS_DIR = REPO_ROOT / "products" / "xmars_os"
STATIC_DIR = XMARS_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

print("[*] Upgrading XMARS.os to Hermes + Cursor + Lovable Sovereign Suite...")

# -----------------------------------------------------------------------------
# 1. PREVIEW SANDBOX (Initial Interactive Dashboard)
# -----------------------------------------------------------------------------
preview_sandbox_html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>XORAS Live Visual Canvas</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: radial-gradient(circle at 50% 20%, #111827 0%, #030712 100%);
      color: #f3f4f6;
      font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 24px;
      overflow-x: hidden;
    }
    .hud-card {
      background: rgba(17, 24, 39, 0.7);
      backdrop-filter: blur(16px);
      border: 1px solid rgba(6, 182, 212, 0.3);
      border-radius: 16px;
      padding: 32px;
      max-width: 640px;
      width: 100%;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6), 0 0 30px rgba(6, 182, 212, 0.15);
      text-align: center;
      animation: fadeIn 0.6s ease-out;
    }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
    .badge {
      display: inline-block;
      padding: 4px 12px;
      background: rgba(6, 182, 212, 0.15);
      border: 1px solid #06b6d4;
      border-radius: 9999px;
      color: #38bdf8;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 1px;
      text-transform: uppercase;
      margin-bottom: 16px;
    }
    h1 { font-size: 26px; font-weight: 800; margin-bottom: 8px; background: linear-gradient(135deg, #fff, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    p { font-size: 13px; color: #94a3b8; line-height: 1.6; margin-bottom: 24px; }
    .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 24px; }
    .metric-box { background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 14px; text-align: center; }
    .metric-value { font-size: 18px; font-weight: 800; color: #00f0ff; font-family: monospace; }
    .metric-label { font-size: 10px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }
    .action-btn {
      background: linear-gradient(135deg, #06b6d4, #3b82f6);
      color: #fff;
      border: none;
      padding: 10px 24px;
      border-radius: 8px;
      font-weight: 600;
      font-size: 13px;
      cursor: pointer;
      transition: all 0.2s;
    }
    .action-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 20px rgba(6, 182, 212, 0.4); }
  </style>
</head>
<body>
  <div class="hud-card">
    <div class="badge">Lovable Live Visual Sandbox</div>
    <h1>XORAS Visual Stage Active</h1>
    <p>Ask Maxx or any Lead 9 agent to generate an application, component, dashboard, or UI layout. The live interactive app will instantly render right here in real-time.</p>
    <div class="grid">
      <div class="metric-box">
        <div class="metric-value">4096</div>
        <div class="metric-label">Context Bound</div>
      </div>
      <div class="metric-box">
        <div class="metric-value">0%</div>
        <div class="metric-label">Cloud Leak</div>
      </div>
      <div class="metric-box">
        <div class="metric-value">60 FPS</div>
        <div class="metric-label">DOM Pipeline</div>
      </div>
    </div>
    <button class="action-btn" onclick="triggerEffect()">Pulse Visual Wave</button>
  </div>
  <script>
    function triggerEffect() {
      const card = document.querySelector('.hud-card');
      card.style.transform = 'scale(0.98)';
      setTimeout(() => { card.style.transform = 'scale(1)'; }, 150);
      window.parent.postMessage({ type: 'xmars_event', message: 'Sandbox pulse triggered' }, '*');
    }
  </script>
</body>
</html>
"""
(STATIC_DIR / "preview_sandbox.html").write_text(preview_sandbox_html, encoding="utf-8")
print("[+] Wrote static/preview_sandbox.html")

print("[OK] Finished generating base sandbox.")
"""
(REPO_ROOT / "ops" / "scripts" / "build_xmars_os_upgrade.py").write_text(content, encoding="utf-8")
"""
