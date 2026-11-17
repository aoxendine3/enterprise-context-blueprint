#!/usr/bin/env python3
"""
build_loop.py — Cozy Channel master renderer (FFmpeg, receipt-tracked).

Renders a seamless long-form master (1h / 3h / 8h, parameterized) from:
  - one short seamless visual loop (video)
  - one seamless ambient loop (fireplace crackle / rain / wind)
  - a folder of music tracks (jazz / piano / ambient)

Doctrine:
  FAIL-CLOSED LICENSE GATE: every input must have a ledger entry in
  asset_ledger.json with an allowed license AND a matching sha256.
  Unlicensed or hash-drifted assets refuse the build (exit 2) — nothing
  renders without provenance.
  RECEIPT: every build writes memory/catch_log/COZY_BUILD_RECEIPT.json
  with input hashes, the exact ffmpeg argv, output hash, and duration.

Usage:
  python3 build_loop.py --duration 1h
  python3 build_loop.py --duration 8h --output cozy_8hr_master.mp4
  python3 build_loop.py --duration 60 --dry-run    # self-test scale (seconds)
"""

import argparse
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent

# --- fail-closed license policy ------------------------------------------
ALLOWED_LICENSES = {
    "CC0", "CC0-1.0", "CC0-1.0-US", "PUBLIC-DOMAIN", "PDM",
    "YOUTUBE-AUDIO-LIBRARY", "CC-BY", "CC-BY-4.0", "CC-BY-3.0",
    # Owner-generated footage: the operator generated it (Runway/Sora/Pika),
    # so full rights are held in-house. Not a third-party license — provenance
    # still requires source_url recording the generator and prompt.
    "OWNER-GENERATED",
}
AUDIO_EXT = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"}
VIDEO_EXT = {".mp4", ".mov", ".mkv", ".webm"}


class BuildRefusal(Exception):
    """Structured, fail-closed refusal. Never a silent crash."""


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_ledger(ledger_path: Path) -> dict:
    if not ledger_path.exists():
        raise BuildRefusal(
            "PLACEHOLDER_NO_LEDGER: asset_ledger.json missing. Create it and "
            "record every asset with source URL, license, author, and sha256."
        )
    return json.loads(ledger_path.read_text(encoding="utf-8"))


def verify_asset(path: Path, ledger: dict, kind: str) -> dict:
    """Fail-closed: the asset must be in the ledger, licensed, hash-matched."""
    if not path.exists():
        raise BuildRefusal(f"PLACEHOLDER_MISSING_{kind.upper()}: {path}")
    actual = sha256_of(path)
    assets = ledger.get("assets", {})
    # macOS /var vs /private/var symlink normalization: accept either key form.
    entry = assets.get(str(path)) or assets.get(str(path.resolve()))
    if entry is None:
        raise BuildRefusal(
            f"PLACEHOLDER_UNREGISTERED_{kind.upper()}: {path.name} has no "
            "ledger entry. Register it (source_url, license, author, sha256)."
        )
    license_id = str(entry.get("license", "")).upper()
    if license_id not in ALLOWED_LICENSES:
        raise BuildRefusal(
            f"PLACEHOLDER_LICENSE_{kind.upper()}: {path.name} license "
            f"'{entry.get('license')}' is not in the allowed set {sorted(ALLOWED_LICENSES)}."
        )
    if entry.get("sha256") != actual:
        raise BuildRefusal(
            f"PLACEHOLDER_HASH_DRIFT_{kind.upper()}: {path.name} sha256 "
            f"mismatch. ledger={entry.get('sha256')} actual={actual}. "
            "File changed since registration — re-verify or re-register."
        )
    return {**entry, "sha256": actual}


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def parse_duration(spec: str) -> int:
    spec = spec.strip().lower()
    if spec.endswith("h"):
        return int(float(spec[:-1]) * 3600)
    if spec.endswith("m"):
        return int(float(spec[:-1]) * 60)
    return int(spec)  # bare seconds


def build_playlist(music_dir: Path, seed: int) -> Path:
    tracks = sorted(p for p in music_dir.iterdir()
                    if p.suffix.lower() in AUDIO_EXT)
    if not tracks:
        raise BuildRefusal("PLACEHOLDER_NO_MUSIC: no audio tracks in music dir.")
    rng = random.Random(seed)
    order = tracks[:]
    rng.shuffle(order)
    # Repeat shuffled passes until comfortably past any target length.
    playlist = tempfile.NamedTemporaryFile(
        "w", suffix=".txt", delete=False, encoding="utf-8")
    with playlist as f:
        for _ in range(64):
            for t in order:
                f.write(f"file '{t.resolve()}'\n")
    return Path(playlist.name)


def render(args) -> dict:
    duration = parse_duration(args.duration)
    visual = Path(args.visual).resolve()
    ambient = Path(args.ambient).resolve()
    music_dir = Path(args.music_dir).resolve()
    output = Path(args.output).resolve()

    ledger = load_ledger(Path(args.ledger).resolve())
    v_rec = verify_asset(visual, ledger, "visual")
    a_rec = verify_asset(ambient, ledger, "ambient")
    tracks = sorted(p for p in music_dir.iterdir()
                    if p.suffix.lower() in AUDIO_EXT)
    if not tracks:
        raise BuildRefusal("PLACEHOLDER_NO_MUSIC: no audio tracks in music dir.")
    music_recs = [verify_asset(t, ledger, "music") for t in tracks]

    seed = args.seed if args.seed is not None else random.randrange(2**32)
    playlist = build_playlist(music_dir, seed)

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-stream_loop", "-1", "-i", str(visual),
        "-f", "concat", "-safe", "0", "-i", str(playlist),
        "-stream_loop", "-1", "-i", str(ambient),
        "-filter_complex",
        f"[1:a]volume={args.music_volume}[music];"
        f"[2:a]volume={args.ambient_volume}[ambient];"
        "[music][ambient]amix=inputs=2:duration=longest,"
        "aformat=sample_rates=48000:channel_layouts=stereo[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "libx264", "-preset", args.preset, "-crf", str(args.crf),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        "-t", str(duration),
        str(output),
    ]

    if args.dry_run:
        print("[DRY-RUN] refusing to render; would execute:")
        print(" \\\n  ".join(cmd))
        playlist.unlink(missing_ok=True)
        return {"dry_run": True, "argv": cmd}

    print(f"[render] target={duration}s  seed={seed}  -> {output.name}")
    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True)
    playlist.unlink(missing_ok=True)
    if proc.returncode != 0:
        raise BuildRefusal(
            f"PLACEHOLDER_FFMPEG_EXIT_{proc.returncode}: {proc.stderr[-2000:]}"
        )

    got = probe_duration(output)
    if abs(got - duration) > 5:
        raise BuildRefusal(
            f"PLACEHOLDER_DURATION_DRIFT: expected {duration}s, got {got:.1f}s"
        )
    out_hash = sha256_of(output)
    receipt = {
        "schema": "xoras.cozy-build-receipt.v1",
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "duration_target_sec": duration,
        "duration_actual_sec": round(got, 2),
        "seed": seed,
        "argv": cmd,
        "inputs": {
            "visual": v_rec, "ambient": a_rec, "music": music_recs,
        },
        "output": {
            "path": str(output), "sha256": out_hash,
            "bytes": output.stat().st_size,
        },
        "render_seconds": round(time.time() - t0, 1),
        "verdict": "OK",
    }
    receipt_path = REPO / "memory" / "catch_log" / "COZY_BUILD_RECEIPT.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
    print(f"[done] {output.name}  {got:.0f}s  {receipt['render_seconds']}s render")
    print(f"[receipt] {receipt_path}")
    return receipt


def main() -> int:
    ap = argparse.ArgumentParser(description="Cozy Channel master renderer")
    ap.add_argument("--visual", default=str(HERE / "visual_loop.mp4"))
    ap.add_argument("--ambient", default=str(HERE / "fireplace_ambient.wav"))
    ap.add_argument("--music-dir", default=str(HERE / "music"))
    ap.add_argument("--output", default=str(HERE / "cozy_master.mp4"))
    ap.add_argument("--duration", default="3h",
                    help="1h | 3h | 8h | bare seconds (self-test scale)")
    ap.add_argument("--music-volume", default="0.85")
    ap.add_argument("--ambient-volume", default="0.35")
    ap.add_argument("--preset", default="fast")
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--seed", type=int, default=None,
                    help="shuffle seed (recorded in receipt for reproducibility)")
    ap.add_argument("--ledger", default=str(HERE / "asset_ledger.json"),
                    help="asset license ledger (default: workspace ledger)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    try:
        render(args)
        return 0
    except BuildRefusal as e:
        print(f"[REFUSED] {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
