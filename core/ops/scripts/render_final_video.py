import os
import subprocess

IMAGE_DIR = "/Users/ajoxendine68/.gemini/antigravity/brain/89cba405-b724-4f62-98b7-e7b85e201c7a"

SCENES = [
    {"img": f"{IMAGE_DIR}/scene1_context_collapse_1791395729677.jpg", "dur": 27.8},
    {"img": f"{IMAGE_DIR}/scene2_kv_cache_bloat_1791395751171.jpg", "dur": 33.7},
    {"img": f"{IMAGE_DIR}/scene3_clinical_telemetry_1791395766151.jpg", "dur": 36.9},
    {"img": f"{IMAGE_DIR}/scene4_blackbox_gauntlet_1791395830786.jpg", "dur": 31.3},
    {"img": f"{IMAGE_DIR}/scene5_poincare_manifold_1791395846620.jpg", "dur": 33.9},
    {"img": f"{IMAGE_DIR}/scene6_hexcell_lattice_1791395870253.jpg", "dur": 31.3},
    {"img": f"{IMAGE_DIR}/telecom_architecture_diagram_1791318742742.jpg", "dur": 18.3}
]

TEMP_DIR = "memory/agent_logs/video_segments"
os.makedirs(TEMP_DIR, exist_ok=True)

segment_files = []
for idx, scene in enumerate(SCENES, 1):
    img = scene["img"]
    dur = scene["dur"]
    seg_output = os.path.join(TEMP_DIR, f"segment_{idx:02d}.mp4")
    
    # FFmpeg command to turn static image into 1080p video clip with subtle Ken Burns zoom effect
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", img,
        "-vf", f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z='min(zoom+0.0005,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(dur*25)}:s=1920x1080",
        "-t", str(dur), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "25",
        seg_output
    ]
    print(f"[RENDERING SEGMENT {idx:02d}] Duration {dur}s: {img}")
    subprocess.run(cmd, check=True)
    segment_files.append(seg_output)

# Write concat file
concat_path = os.path.join(TEMP_DIR, "video_concat.txt")
with open(concat_path, "w") as f:
    for sf in segment_files:
        f.write(f"file '{os.path.abspath(sf)}'\n")

temp_video = os.path.join(TEMP_DIR, "temp_video_no_audio.mp4")
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_path, "-c", "copy", temp_video], check=True)

AUDIO_TRACK = "memory/agent_logs/collective_master_narration_multiagent.mp3"
FINAL_VIDEO = "memory/agent_logs/XORAS_Context_Collapse_Master_Video.mp4"

# Merge video and multi-agent audio track into final master MP4
merge_cmd = [
    "ffmpeg", "-y", "-i", temp_video, "-i", AUDIO_TRACK,
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
    FINAL_VIDEO
]
subprocess.run(merge_cmd, check=True)

print(f"\n[SUCCESS] MASTER VIDEO COMPLETED & RENDERED: {FINAL_VIDEO}")
