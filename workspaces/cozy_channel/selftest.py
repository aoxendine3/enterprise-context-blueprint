#!/usr/bin/env python3
"""
selftest.py — prove the cozy pipeline end to end with synthetic assets.

Generates CC0-marked test media, registers them in a throwaway ledger,
renders a 60-second master, verifies duration + receipt, then exercises
the three refusal paths (unregistered / hash drift / bad license) and the
seamless-loop prepper. Writes memory/catch_log/COZY_PIPELINE_SELFTEST_RECEIPT.json.
"""

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def gen_assets(work: Path) -> dict:
    visual = work / "visual_loop.mp4"
    ambient = work / "fireplace_ambient.wav"
    music = work / "music"
    music.mkdir(exist_ok=True)
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=25:duration=12",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", str(visual)])
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-f", "lavfi", "-i", "sine=frequency=220:duration=10",
         "-c:a", "pcm_s16le", str(ambient)])
    for i, freq in enumerate((440, 523, 659), 1):
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
             "-f", "lavfi", "-i", f"sine=frequency={freq}:duration=20",
             "-c:a", "libmp3lame", "-b:a", "128k",
             str(music / f"track_{i:02d}.mp3")])
    return {"visual": visual, "ambient": ambient, "music": music}


def register(work: Path, ledger_path: Path, assets: dict) -> None:
    entries = {}
    paths = [assets["visual"], assets["ambient"]] + sorted(assets["music"].iterdir())
    for p in paths:
        entries[str(p.resolve())] = {
            "source_url": "synthetic://selftest",
            "license": "CC0",
            "author": "selftest generator",
            "retrieved_utc": "2026-11-17T00:00:00+00:00",
            "sha256": sha256_of(p),
            "notes": "synthetic pipeline self-test asset",
        }
    ledger_path.write_text(json.dumps(
        {"schema": "xoras.cozy-asset-ledger.v1", "assets": entries},
        indent=2), encoding="utf-8")


def probe_duration(p: Path) -> float:
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "csv=p=0", str(p)])
    return float(out.stdout.strip())


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="cozy_selftest_"))
    receipt = {
        "schema": "xoras.cozy-pipeline-selftest.v1",
        "checks": [],
    }

    def check(name, ok, detail=""):
        receipt["checks"].append({"name": name, "ok": bool(ok), "detail": detail})
        print(f"  {'PASS' if ok else 'FAIL'}  {name} {detail}")
        return ok

    ok = True
    try:
        assets = gen_assets(work)
        ledger = work / "ledger.json"
        register(work, ledger, assets)

        # 1. seamless loop prepper
        loop_out = work / "seamless.mp4"
        r = run([sys.executable, str(HERE / "make_seamless_loop.py"),
                 "--input", str(assets["visual"]), "--output", str(loop_out)])
        ok &= check("make_seamless_loop runs", r.returncode == 0, r.stderr[-200:])
        if loop_out.exists():
            d = probe_duration(loop_out)
            ok &= check("loop length = 12s - 2s tail", abs(d - 10) < 0.5, f"{d:.1f}s")

        # 2. real render at self-test scale
        out = work / "master_60s.mp4"
        r = run([sys.executable, str(HERE / "build_loop.py"),
                 "--duration", "60", "--ledger", str(ledger),
                 "--visual", str(assets["visual"]),
                 "--ambient", str(assets["ambient"]),
                 "--music-dir", str(assets["music"]),
                 "--output", str(out), "--preset", "ultrafast", "--crf", "30"])
        ok &= check("build_loop renders", r.returncode == 0, r.stderr[-300:])
        if out.exists():
            d = probe_duration(out)
            ok &= check("master duration ~60s", abs(d - 60) < 3, f"{d:.1f}s")
        rp = REPO / "memory" / "catch_log" / "COZY_BUILD_RECEIPT.json"
        ok &= check("build receipt written", rp.exists(), str(rp))

        # 3. refusal paths (fail closed)
        r = run([sys.executable, str(HERE / "build_loop.py"),
                 "--duration", "60", "--ledger", str(work / "nope.json"),
                 "--visual", str(assets["visual"]),
                 "--ambient", str(assets["ambient"]),
                 "--music-dir", str(assets["music"]),
                 "--output", str(work / "x.mp4")])
        ok &= check("missing ledger refuses", r.returncode == 2 and
                    "PLACEHOLDER_NO_LEDGER" in r.stderr)

        bad = json.loads(ledger.read_text())
        vkey = str(assets["visual"].resolve())
        bad["assets"][vkey]["sha256"] = "0" * 64
        drift = work / "ledger_drift.json"
        drift.write_text(json.dumps(bad), encoding="utf-8")
        r = run([sys.executable, str(HERE / "build_loop.py"),
                 "--duration", "60", "--ledger", str(drift),
                 "--visual", str(assets["visual"]),
                 "--ambient", str(assets["ambient"]),
                 "--music-dir", str(assets["music"]),
                 "--output", str(work / "x.mp4")])
        ok &= check("hash drift refuses", r.returncode == 2 and
                    "PLACEHOLDER_HASH_DRIFT" in r.stderr)

        bad["assets"][vkey]["license"] = "ALL-RIGHTS-RESERVED"
        lic = work / "ledger_license.json"
        lic.write_text(json.dumps(bad), encoding="utf-8")
        r = run([sys.executable, str(HERE / "build_loop.py"),
                 "--duration", "60", "--ledger", str(lic),
                 "--visual", str(assets["visual"]),
                 "--ambient", str(assets["ambient"]),
                 "--music-dir", str(assets["music"]),
                 "--output", str(work / "x.mp4")])
        ok &= check("disallowed license refuses", r.returncode == 2 and
                    "PLACEHOLDER_LICENSE" in r.stderr)

        # 4. dry-run prints argv without rendering
        r = run([sys.executable, str(HERE / "build_loop.py"),
                 "--duration", "60", "--ledger", str(ledger),
                 "--visual", str(assets["visual"]),
                 "--ambient", str(assets["ambient"]),
                 "--music-dir", str(assets["music"]),
                 "--output", str(work / "y.mp4"), "--dry-run"])
        ok &= check("dry-run refuses render", r.returncode == 0 and
                    "[DRY-RUN]" in r.stdout)
    finally:
        receipt["verdict"] = "SELFTEST_PASS" if ok else "SELFTEST_FAIL"
        rp = REPO / "memory" / "catch_log" / "COZY_PIPELINE_SELFTEST_RECEIPT.json"
        rp.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
        shutil.rmtree(work, ignore_errors=True)
        print(f"[receipt] {rp}  {receipt['verdict']}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
