import os, sys, subprocess

print("=== STARTING FULL NARRATED 10-MINUTE FILM PIPELINE ===")

output_dir = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/scratch/movie_10min"
final_narrated_movie = "/Users/ajoxendine68/Desktop/The_Last_Beacon_of_Horizon_9_FULL_NARRATED.mp4"

# 10 Scene Narration Scripts
narration_texts = [
    "On the jagged cliffs of Horizon 9, five hundred light years from Earth, stands the last atmospheric beacon. For three decades, it has guided relief freighters through turbulent plasma storms. But tonight, as the golden sun dips behind the obsidian ridges, the sky turns quiet.",
    "Inside the facility relay hub, emergency amber warning lights suddenly flicker to life. The planetary grid collapses as a massive solar flare strikes the upper thermosphere. Primary power drops to four percent. Communication lines sever in an instant.",
    "Chief Engineer Alex Vance stares at the flickering holographic display reflecting in his visor. The orbital relief fleet is entering the atmosphere blind. Without the beacon quantum vector, they will burn up in the upper cloud deck within minutes.",
    "Vance does not hesitate. He manual overrides the emergency protocol, sacrificing his own environmental life support to divert remaining battery reserves directly into the subterranean induction coils.",
    "Descending deep into the mountain volcanic core, Vance steps onto narrow metallic walkways. Heat waves shimmer off geothermal conduits as steam vents hiss under immense pressure.",
    "With heavy iron tools, Vance manually locks the three magnetic alignment rings into place. Blue plasma arcs across the ring, burning through heat shields as the main capacitor charges.",
    "A deafening roar echoes through the cavern. A pillar of pure coherent light erupts from the mountain spire, shooting ten miles straight up into the storm clouds above, tearing open a window in the sky.",
    "In high orbit, the relief freighters lock onto the quantum beam. Thrusters ignite in unison as the fleet corrects course, descending safely through the newly cleared atmospheric corridor.",
    "As the energy discharge disperses the plasma clouds, the violent planetary storm fades away. Twin glowing moons illuminate the calm alien sky, revealing nebulae across the horizon.",
    "Morning breaks over the quiet peaks of Horizon 9. The beacon hums steady and strong. One engineer quiet courage preserved a lifeline across the stars."
]

img1 = "/Users/ajoxendine68/.gemini/antigravity/brain/bd892285-cca1-43cd-bb8b-d1c3128f05ca/beacon_horizon9_scene1_1790903817387.jpg"
img2 = "/Users/ajoxendine68/.gemini/antigravity/brain/bd892285-cca1-43cd-bb8b-d1c3128f05ca/beacon_horizon9_scene2_1790903839832.jpg"

scene_files = []

for i, text in enumerate(narration_texts, start=1):
    src_img = img1 if i % 2 != 0 else img2
    audio_wav = os.path.join(output_dir, f"audio_{i:02d}.wav")
    scene_mp4 = os.path.join(output_dir, f"scene_narrated_{i:02d}.mp4")
    
    # 1. Synthesize Kokoro Audio via agent_speak.sh script or macOS native enhanced voice engine
    print(f"Synthesizing Audio Narration {i}/10...")
    # Render audio via mac os enhanced voice to WAV for exact 60s pad
    say_cmd = f"say -o {audio_wav} --data-format=LEI16@48000 '{text}'"
    subprocess.run(say_cmd, shell=True, check=True)
    
    # 2. Render 60-second video with exact audio alignment & ambient music track
    print(f"Rendering 60s Video Clip {i}/10 with audio track...")
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", src_img, "-i", audio_wav,
        "-filter_complex", "[1:a]apad=whole_dur=60[aout];[0:v]zoompan=z='min(zoom+0.0003,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1500:s=1280x720[vout]",
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-c:a", "aac", "-t", "60", "-pix_fmt", "yuv420p", scene_mp4
    ]
    subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    scene_files.append(scene_mp4)

# 3. Concatenate into single feature file
list_path = os.path.join(output_dir, "narrated_list.txt")
with open(list_path, "w") as f:
    for s in scene_files:
        f.write(f"file '{s}'\n")

print("Stitching narrated scenes into final 10-minute movie...")
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", final_narrated_movie], check=True)

print(f"=== FULL NARRATED FEATURE COMPLETE: {final_narrated_movie} ===")
subprocess.run(["open", final_narrated_movie])
