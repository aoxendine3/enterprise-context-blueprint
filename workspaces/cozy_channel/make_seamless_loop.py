#!/usr/bin/env python3
"""
make_seamless_loop.py — turn a raw clip into a true seamless loop.

Takes the last `--tail` seconds of the clip and crossfades them into the
final `--fade` seconds of the head, so the restart is invisible. Output
length = duration - tail.

Usage:
  python3 make_seamless_loop.py --input raw_clip.mp4 --output visual_loop.mp4
  python3 make_seamless_loop.py --input raw_clip.mp4 --tail 2 --fade 2
"""

import argparse
import subprocess
import sys
from pathlib import Path


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def main() -> int:
    ap = argparse.ArgumentParser(description="Seamless-loop crossfade prepper")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", default="visual_loop.mp4")
    ap.add_argument("--tail", type=float, default=2.0,
                    help="seconds trimmed off the end to use as the crossfade tail")
    ap.add_argument("--fade", type=float, default=None,
                    help="crossfade duration (default = tail)")
    args = ap.parse_args()

    fade = args.fade if args.fade is not None else args.tail
    dur = probe_duration(Path(args.input))
    main_len = dur - args.tail
    if main_len <= fade:
        print(f"[REFUSED] clip {dur:.1f}s too short for tail={args.tail}s "
              f"fade={fade}s", file=sys.stderr)
        return 2
    offset = main_len - fade

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", args.input,
        "-filter_complex",
        f"[0:v]trim=0:{main_len},setpts=PTS-STARTPTS[main];"
        f"[0:v]trim={main_len}:{dur},setpts=PTS-STARTPTS[tail];"
        f"[main][tail]xfade=transition=fade:duration={fade}:offset={offset}[out]",
        "-map", "[out]", "-an",
        "-c:v", "libx264", "-preset", "slow", "-crf", "16",
        "-pix_fmt", "yuv420p",
        args.output,
    ]
    print(f"[loop] {dur:.1f}s -> {main_len:.1f}s seamless "
          f"(tail={args.tail}s fade={fade}s offset={offset:.1f}s)")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"[REFUSED] PLACEHOLDER_FFMPEG_EXIT_{proc.returncode}: "
              f"{proc.stderr[-2000:]}", file=sys.stderr)
        return 2
    print(f"[done] {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
