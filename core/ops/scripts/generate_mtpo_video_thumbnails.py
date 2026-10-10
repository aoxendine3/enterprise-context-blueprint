#!/usr/bin/env python3
"""
© 2026 Xoras Systems LLC. All rights reserved.
Specific Thumbnail Generator for "How_MTPO_Stops_AI_Agents_From_Clashing.mp4"
Generates both 9:16 Vertical (1080x1920) and 16:9 Landscape (1280x720) YouTube thumbnails.
"""

import os
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = "docs/assets/thumbnails"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs("assets/thumbnails", exist_ok=True)

def get_font(size, bold=True):
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSMono.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size, index=0 if bold else 0)
            except Exception:
                pass
    return ImageFont.load_default()

def generate_landscape_16x9():
    width, height = 1280, 720
    img = Image.new("RGB", (width, height), color=(7, 10, 18))
    draw = ImageDraw.Draw(img)

    # Background gradient
    for y in range(height):
        r = int(7 + (y / height) * 12)
        g = int(10 + (y / height) * 15)
        b = int(18 + (y / height) * 22)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    font_xl = get_font(76, bold=True)
    font_lg = get_font(38, bold=True)
    font_md = get_font(22, bold=True)

    # Split visual
    mid_x = width // 2
    draw.line([(mid_x, 80), (mid_x, height - 180)], fill=(40, 60, 90))

    # Left: Agent Collision
    draw.rectangle([80, 150, 320, 230], fill=(255, 69, 0, 40), outline=(255, 69, 0), width=3)
    draw.text((100, 175), "AGENT A", fill=(255, 120, 80), font=font_lg)
    draw.text((100, 205), "Write: file.py", fill=(200, 200, 200), font=font_md)

    draw.rectangle([80, 310, 320, 390], fill=(255, 69, 0, 40), outline=(255, 69, 0), width=3)
    draw.text((100, 335), "AGENT B", fill=(255, 120, 80), font=font_lg)
    draw.text((100, 365), "Write: file.py", fill=(200, 200, 200), font=font_md)

    draw.ellipse([420, 230, 520, 310], fill=(200, 0, 0), outline=(255, 255, 255), width=3)
    draw.text((447, 243), "✖", fill=(255, 255, 255), font=font_lg)

    draw.text((120, 420), "RACE CONDITION OVERWRITE", fill=(255, 60, 60), font=font_md)

    # Right: MTPO Pre-ordered Chain
    start_x = 680
    y_center = 270
    nodes = ["σ₀", "σ₁", "σ₂"]
    for i, node in enumerate(nodes):
        nx = start_x + i * 160
        draw.rectangle([nx, y_center - 40, nx + 100, y_center + 40], fill=(0, 242, 254, 30), outline=(0, 242, 254), width=3)
        draw.text((nx + 35, y_center - 15), node, fill=(0, 242, 254), font=font_lg)
        if i < len(nodes) - 1:
            draw.line([(nx + 100, y_center), (nx + 160, y_center)], fill=(0, 242, 254), width=4)
            draw.polygon([(nx + 155, y_center - 6), (nx + 165, y_center), (nx + 155, y_center + 6)], fill=(0, 242, 254))

    draw.ellipse([1140, 230, 1220, 310], fill=(0, 200, 100), outline=(255, 255, 255), width=3)
    draw.text((1162, 243), "✔", fill=(255, 255, 255), font=font_lg)

    draw.text((720, 420), "PRE-ORDERED MERKLE LINEAGE", fill=(0, 242, 254), font=font_md)

    # Text Headline
    text = "NO MORE AGENT CLASHES"
    bbox = font_xl.getbbox(text)
    text_w = bbox[2] - bbox[0]
    x = (width - text_w) // 2
    y = 540

    for dx, dy in [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, 4)]:
        draw.text((x + dx, y + dy), text, fill=(0, 0, 0), font=font_xl)
    draw.text((x, y), text, fill=(255, 215, 0), font=font_xl)

    # Badge
    draw.rectangle([1040, 20, 1240, 60], fill=(20, 30, 50), outline=(0, 242, 254), width=2)
    draw.text((1060, 32), "MTPO ENGINE", fill=(0, 242, 254), font=font_md)

    png_path = os.path.join(OUTPUT_DIR, "how_mtpo_stops_clashing_standard_16x9.png")
    jpg_path = os.path.join(OUTPUT_DIR, "how_mtpo_stops_clashing_standard_16x9.jpg")
    img.save(png_path)
    img.save(jpg_path, quality=95)
    img.save("assets/thumbnails/how_mtpo_stops_clashing_standard_16x9.jpg")
    print(f"✅ Generated 16:9 Thumbnail: {png_path}")

def generate_portrait_9x16():
    width, height = 1080, 1920
    img = Image.new("RGB", (width, height), color=(7, 10, 18))
    draw = ImageDraw.Draw(img)

    for y in range(height):
        r = int(7 + (y / height) * 15)
        g = int(10 + (y / height) * 20)
        b = int(18 + (y / height) * 30)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    font_xl = get_font(90, bold=True)
    font_sub = get_font(52, bold=True)
    font_lg = get_font(42, bold=True)
    font_md = get_font(32, bold=True)

    # Top Header Badge
    draw.rectangle([240, 100, 840, 180], fill=(20, 30, 50), outline=(0, 242, 254), width=4)
    draw.text((320, 120), "XORAS SYSTEMS", fill=(0, 242, 254), font=font_lg)

    # Headline (3 words max)
    text1 = "STOP AGENT"
    text2 = "CLASHES!"
    
    bbox1 = font_xl.getbbox(text1)
    w1 = bbox1[2] - bbox1[0]
    bbox2 = font_xl.getbbox(text2)
    w2 = bbox2[2] - bbox2[0]

    y_pos = 280
    for dx, dy in [(-4, -4), (4, -4), (-4, 4), (4, 4), (0, 5)]:
        draw.text(((width - w1)//2 + dx, y_pos + dy), text1, fill=(0, 0, 0), font=font_xl)
        draw.text(((width - w2)//2 + dx, y_pos + 110 + dy), text2, fill=(0, 0, 0), font=font_xl)

    draw.text(((width - w1)//2, y_pos), text1, fill=(255, 215, 0), font=font_xl)
    draw.text(((width - w2)//2, y_pos + 110), text2, fill=(255, 69, 0), font=font_xl)

    # Section 1: Problem Box
    draw.rectangle([100, 580, 980, 960], fill=(255, 69, 0, 30), outline=(255, 69, 0), width=4)
    draw.text((140, 610), "THE PROBLEM: AGENT OVERWRITE", fill=(255, 120, 80), font=font_lg)
    draw.text((140, 680), "✖ Agent A & B edit same file", fill=(220, 220, 220), font=font_md)
    draw.text((140, 740), "✖ Database locks freeze swarm", fill=(220, 220, 220), font=font_md)
    draw.text((140, 800), "✖ Traditional state crashes", fill=(220, 220, 220), font=font_md)
    draw.text((140, 860), "✖ LLM context degraded", fill=(255, 100, 100), font=font_md)

    # Arrow Down
    draw.polygon([(540, 1040), (500, 990), (580, 990)], fill=(0, 242, 254))

    # Section 2: Solution Box
    draw.rectangle([100, 1080, 980, 1500], fill=(0, 242, 254, 30), outline=(0, 242, 254), width=4)
    draw.text((140, 1110), "THE FIX: MTPO ENGINE", fill=(0, 242, 254), font=font_lg)
    draw.text((140, 1180), "✔ Pre-ordered σ Merkle Timeline", fill=(255, 255, 255), font=font_md)
    draw.text((140, 1240), "✔ Non-blocking advisory pulse", fill=(255, 255, 255), font=font_md)
    draw.text((140, 1300), "✔ Autonomous on-the-fly patching", fill=(255, 255, 255), font=font_md)
    draw.text((140, 1360), "✔ Deterministic SAGA reordering", fill=(255, 255, 255), font=font_md)

    # Call to Action Box
    draw.rectangle([100, 1560, 980, 1780], fill=(20, 50, 40), outline=(0, 255, 120), width=4)
    draw.text((160, 1600), "100% SOVEREIGN & BARE-METAL", fill=(0, 255, 120), font=font_sub)
    draw.text((220, 1690), "SUBSCRIBE FOR THE FULL AUDIT", fill=(255, 255, 255), font=font_md)

    png_path = os.path.join(OUTPUT_DIR, "how_mtpo_stops_clashing_short_9x16.png")
    jpg_path = os.path.join(OUTPUT_DIR, "how_mtpo_stops_clashing_short_9x16.jpg")
    img.save(png_path)
    img.save(jpg_path, quality=95)
    img.save("assets/thumbnails/how_mtpo_stops_clashing_short_9x16.jpg")
    print(f"✅ Generated 9:16 Shorts Thumbnail: {png_path}")

def main():
    generate_landscape_16x9()
    generate_portrait_9x16()
    print("🚀 Video thumbnails generated for 'How_MTPO_Stops_AI_Agents_From_Clashing.mp4'.")

if __name__ == "__main__":
    main()
