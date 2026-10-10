#!/usr/bin/env python3
"""
XORAS SYSTEMS — VIBE CODING HIGHLIGHTS CINEMATIC VIDEO GENERATOR
Generates a fast-loading 3-minute high-impact 1080p showcase video with audio spectrum,
PIL overlays, telemetry backdrop, and Council call-to-action outro.
"""

import os
import sys
import subprocess
from PIL import Image, ImageDraw, ImageFont

SSOT_ROOT = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain"
PODCAST_AUDIO = "/Users/ajoxendine68/Downloads/Replacing_Vibe_Coding_with_MARS_Framework.m4a"
OUTPUT_DIR = os.path.join(SSOT_ROOT, "docs", "assets", "videos")
OUTPUT_VIDEO = os.path.join(OUTPUT_DIR, "vibe_coding_highlights_showcase.mp4")
OUTPUT_PREVIEW_GIF = os.path.join(OUTPUT_DIR, "vibe_coding_highlights_showcase.gif")

os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTRO_TEXT_MAXX = "This is Maxx, alongside Vance and Clara of the Lead 9 Council. If you are ready to move beyond fragile vibe coding and build production-grade, zero-trust sovereign AI swarms, smash that like button and subscribe to the channel."
OUTRO_TEXT_VANCE = "Now, we pose a direct challenge to every engineer and researcher watching: Drop your hardest code, concurrency, memory leak, or security exploit in the comments below."
OUTRO_TEXT_CLARA = "Give our swarm your worst. Our 14-Gate Blackbox Gauntlet is ready to audit, falsify, and dismantle it. Subscribe now and challenge the Council!"

def synthesize_speech(agent, text, out_file):
    cmd = [
        "python3",
        os.path.join(SSOT_ROOT, "ops", "scripts", "fullscreen_ui", "sync_stage_engine_kokoro.py"),
        agent,
        text
    ]
    subprocess.run(cmd, check=True)
    src = os.path.join(SSOT_ROOT, "ops", "scripts", "fullscreen_ui", "live_elevenlabs.mp3")
    if not os.path.exists(src):
        src = os.path.join(SSOT_ROOT, "ops", "scripts", "fullscreen_ui", "live_speech.wav")
    subprocess.run(["cp", src, out_file], check=True)

def build_highlight_audio():
    print("\n[STEP 1] Extracting 2.5-Minute Highlight Segment + Concatenating Council Outro...")
    highlight_audio = "/tmp/highlight_clip.mp3"
    # Extract first 2.5 minutes (150 seconds) of the podcast
    subprocess.run(["ffmpeg", "-y", "-ss", "00:00:00", "-t", "150", "-i", PODCAST_AUDIO, "-c:a", "libmp3lame", "-q:a", "2", highlight_audio], check=True)
    
    maxx_wav = "/tmp/outro_maxx.mp3"
    vance_wav = "/tmp/outro_vance.mp3"
    clara_wav = "/tmp/outro_clara.mp3"
    
    if not os.path.exists(maxx_wav): synthesize_speech("maxx", OUTRO_TEXT_MAXX, maxx_wav)
    if not os.path.exists(vance_wav): synthesize_speech("vance", OUTRO_TEXT_VANCE, vance_wav)
    if not os.path.exists(clara_wav): synthesize_speech("clara", OUTRO_TEXT_CLARA, clara_wav)

    concat_list = "/tmp/audio_concat.txt"
    with open(concat_list, "w") as f:
        f.write(f"file '{maxx_wav}'\n")
        f.write(f"file '{vance_wav}'\n")
        f.write(f"file '{clara_wav}'\n")

    outro_combined = "/tmp/outro_full.mp3"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", outro_combined], check=True)

    silence = "/tmp/silence_1s.mp3"
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "1.5", silence], check=True)

    final_audio = "/tmp/vibe_coding_highlight_audio.mp3"
    concat_master_list = "/tmp/highlight_master_concat.txt"
    with open(concat_master_list, "w") as f:
        f.write(f"file '{highlight_audio}'\n")
        f.write(f"file '{silence}'\n")
        f.write(f"file '{outro_combined}'\n")

    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_master_list, "-c:a", "libmp3lame", "-q:a", "2", final_audio], check=True)
    return final_audio

def render_overlay_images():
    img_header = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img_header)
    try:
        font_main = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 44)
        font_sub = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        font_outro = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
    except Exception:
        font_main = font_sub = font_outro = ImageFont.load_default()

    title_text = "REPLACING VIBE CODING WITH MARS FRAMEWORK"
    sub_text = "XORAS SOVEREIGN SYSTEMS LLC — 18,432-D POINCARÉ MEMORY & BARE-METAL HEXCELL TOPOLOGY"
    
    draw.text((962, 82), title_text, fill=(0, 0, 0, 255), font=font_main, anchor="mm")
    draw.text((960, 80), title_text, fill=(255, 255, 255, 255), font=font_main, anchor="mm")
    draw.text((962, 142), sub_text, fill=(0, 0, 0, 255), font=font_sub, anchor="mm")
    draw.text((960, 140), sub_text, fill=(0, 242, 254, 255), font=font_sub, anchor="mm")
    
    header_path = "/tmp/header_overlay.png"
    img_header.save(header_path)

    img_outro = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw_out = ImageDraw.Draw(img_outro)
    
    outro_text = "LIKE & SUBSCRIBE — CHALLENGE THE LEAD 9 COUNCIL IN THE COMMENTS BELOW"
    sub_outro = "Drop your hardest code, concurrency, or security challenge. Our 14-Gate Gauntlet is waiting!"
    
    draw_out.rectangle([160, 680, 1760, 820], fill=(7, 10, 18, 220), outline=(0, 230, 118, 255), width=3)
    draw_out.text((962, 722), outro_text, fill=(0, 0, 0, 255), font=font_outro, anchor="mm")
    draw_out.text((960, 720), outro_text, fill=(0, 230, 118, 255), font=font_outro, anchor="mm")
    draw_out.text((962, 772), sub_outro, fill=(0, 0, 0, 255), font=font_sub, anchor="mm")
    draw_out.text((960, 770), sub_outro, fill=(248, 250, 252, 255), font=font_sub, anchor="mm")
    
    outro_path = "/tmp/outro_overlay.png"
    img_outro.save(outro_path)
    return header_path, outro_path

def build_cinematic_video(audio_path, header_png, outro_png):
    bg_img = os.path.join(SSOT_ROOT, "docs", "assets", "images", "upgp_v4_ultra_telemetry_dashboard.jpg")
    probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path]
    duration = float(subprocess.check_output(probe_cmd).decode('utf-8').strip())

    outro_start = duration - 35.0
    
    filter_complex = (
        f"[0:v]scale=1920:1080,format=yuv420p,drawbox=x=0:y=0:w=1920:h=1080:color=black@0.65:t=fill[bg];"
        f"[bg][2:v]overlay=0:0[vbg];"
        f"[1:a]showwaves=s=1920x240:mode=line:colors=0x00f2fe|0x00e676:scale=sqrt,format=yuva420p[waves];"
        f"[vbg][waves]overlay=x=0:y=840[v1];"
        f"[v1][3:v]overlay=x=0:y=0:enable='between(t,{outro_start},{duration})'[v2]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", bg_img,
        "-i", audio_path,
        "-loop", "1", "-i", header_png,
        "-loop", "1", "-i", outro_png,
        "-filter_complex", filter_complex,
        "-map", "[v2]", "-map", "1:a",
        "-c:v", "h264_videotoolbox", "-b:v", "2000k", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        OUTPUT_VIDEO
    ]

    subprocess.run(cmd, check=True)
    print(f"  ✅ HIGHLIGHT RENDER COMPLETE: {OUTPUT_VIDEO}")

    gif_cmd = [
        "ffmpeg", "-y",
        "-ss", "00:00:10", "-t", "8",
        "-i", OUTPUT_VIDEO,
        "-filter_complex", "[0:v]fps=15,scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse",
        OUTPUT_PREVIEW_GIF
    ]
    subprocess.run(gif_cmd, check=True)
    print(f"  ✅ GIF PREVIEW COMPLETE: {OUTPUT_PREVIEW_GIF}")

def main():
    final_audio = build_highlight_audio()
    header_png, outro_png = render_overlay_images()
    build_cinematic_video(final_audio, header_png, outro_png)

if __name__ == "__main__":
    main()
