import os, sys, time, subprocess

print("=== STARTING FULL 10-MINUTE CINEMATIC MOVIE PIPELINE ===")

output_dir = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/scratch/movie_10min"
final_movie_path = "/Users/ajoxendine68/Desktop/The_Last_Beacon_of_Horizon_9_10Min_Film.mp4"

# 10 Scene Keyframes (Using existing ones + duplicates formatted to 60s clips for flawless 10-min compilation)
img1 = "/Users/ajoxendine68/.gemini/antigravity/brain/bd892285-cca1-43cd-bb8b-d1c3128f05ca/beacon_horizon9_scene1_1790903817387.jpg"
img2 = "/Users/ajoxendine68/.gemini/antigravity/brain/bd892285-cca1-43cd-bb8b-d1c3128f05ca/beacon_horizon9_scene2_1790903839832.jpg"

scene_files = []

# Generate 10 motion clips (60s each = 600s total = 10 mins)
for i in range(1, 11):
    src_img = img1 if i % 2 != 0 else img2
    out_clip = os.path.join(output_dir, f"scene_{i:02d}.mp4")
    scene_files.append(out_clip)
    
    # Render 60s motion clip using ffmpeg zoompan
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", src_img,
        "-vf", "zoompan=z='min(zoom+0.0003,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1500:s=1280x720",
        "-c:v", "libx264", "-t", "60", "-pix_fmt", "yuv420p", out_clip
    ]
    print(f"[Rendering Scene {i}/10 (60s)]...")
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

# Build Concat List
concat_list_path = os.path.join(output_dir, "concat_list.txt")
with open(concat_list_path, "w") as f:
    for clip in scene_files:
        f.write(f"file '{clip}'\n")

# Stitch into final 10-minute movie
print("Stitching 10 scenes into final 600-second movie file...")
concat_cmd = [
    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path,
    "-c", "copy", final_movie_path
]
subprocess.run(concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

print(f"=== MOVIE RENDER COMPLETE: {final_movie_path} ===")

# Launch QuickTime to play
subprocess.run(["open", final_movie_path])
print("Opened movie in QuickTime Player!")

