#!/usr/bin/env python3
"""
© 2026 Xoras Systems LLC. All rights reserved.
YouTube Thumbnail CTR V2 Generator Script
Generates 3 high-contrast 1280x720 YouTube Studio Test & Compare thumbnail variants based on XORAS-SPEC-THUMBNAIL-CTR-V2.
"""

import os
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = "docs/assets/thumbnails"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs("assets/thumbnails", exist_ok=True)

WIDTH, HEIGHT = 1280, 720

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

def draw_background(draw):
    for y in range(HEIGHT):
        r = int(7 + (y / HEIGHT) * 10)
        g = int(10 + (y / HEIGHT) * 12)
        b = int(18 + (y / HEIGHT) * 20)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
        
    mid_x = WIDTH // 2
    for y in range(80, HEIGHT - 180):
        alpha = int(180 * (1 - abs(y - (HEIGHT - 100) / 2) / (HEIGHT / 2)))
        draw.line([(mid_x, y), (mid_x, y+1)], fill=(40, 60, 90, alpha))

def draw_left_problem(draw, font_lg, font_md):
    draw.rectangle([100, 160, 340, 240], fill=(255, 69, 0, 40), outline=(255, 69, 0), width=3)
    draw.text((120, 185), "AGENT ALPHA", fill=(255, 120, 80), font=font_md)
    draw.text((120, 210), "Write: state.val=42", fill=(200, 200, 200), font=font_md)

    draw.rectangle([100, 320, 340, 400], fill=(255, 69, 0, 40), outline=(255, 69, 0), width=3)
    draw.text((120, 345), "AGENT BETA", fill=(255, 120, 80), font=font_md)
    draw.text((120, 370), "Write: state.val=99", fill=(200, 200, 200), font=font_md)

    draw.line([(340, 200), (450, 280)], fill=(255, 0, 0), width=4)
    draw.line([(340, 360), (450, 280)], fill=(255, 0, 0), width=4)

    draw.ellipse([430, 240, 530, 320], fill=(200, 0, 0), outline=(255, 255, 255), width=3)
    draw.text((455, 252), "✖", fill=(255, 255, 255), font=font_lg)

    draw.text((130, 430), "RACE CONDITION! [OVERWRITE]", fill=(255, 60, 60), font=font_md)

def draw_right_solution(draw, font_lg, font_md):
    start_x = 680
    y_center = 280

    nodes = ["σ₀", "σ₁", "σ₂"]
    for i, node in enumerate(nodes):
        nx = start_x + i * 160
        draw.rectangle([nx, y_center - 40, nx + 100, y_center + 40], fill=(0, 242, 254, 30), outline=(0, 242, 254), width=3)
        draw.text((nx + 35, y_center - 15), node, fill=(0, 242, 254), font=font_lg)

        if i < len(nodes) - 1:
            draw.line([(nx + 100, y_center), (nx + 160, y_center)], fill=(0, 242, 254), width=4)
            draw.polygon([(nx + 155, y_center - 6), (nx + 165, y_center), (nx + 155, y_center + 6)], fill=(0, 242, 254))

    draw.ellipse([1140, 240, 1220, 320], fill=(0, 200, 100), outline=(255, 255, 255), width=3)
    draw.text((1162, 252), "✔", fill=(255, 255, 255), font=font_lg)

    draw.text((700, 430), "PRE-ORDERED MERKLE LINEAGE", fill=(0, 242, 254), font=font_md)

def draw_headline_text(draw, text, font_xl):
    bbox = font_xl.getbbox(text)
    text_w = bbox[2] - bbox[0]
    x = (WIDTH - text_w) // 2
    y = 540

    for dx, dy in [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, 4)]:
        draw.text((x + dx, y + dy), text, fill=(0, 0, 0), font=font_xl)
    
    draw.text((x, y), text, fill=(255, 215, 0), font=font_xl)

def draw_corner_badge(draw, font_md):
    draw.rectangle([1060, 20, 1240, 60], fill=(20, 30, 50), outline=(0, 242, 254), width=2)
    draw.text((1075, 32), "MTPO v4.0", fill=(0, 242, 254), font=font_md)

def build_variant(variant_name, headline_text):
    font_xl = get_font(72, bold=True)
    font_lg = get_font(40, bold=True)
    font_md = get_font(22, bold=True)

    img = Image.new("RGB", (WIDTH, HEIGHT), color=(7, 10, 18))
    draw = ImageDraw.Draw(img)

    draw_background(draw)
    draw_left_problem(draw, font_lg, font_md)
    draw_right_solution(draw, font_lg, font_md)
    draw_headline_text(draw, headline_text, font_xl)
    draw_corner_badge(draw, font_md)

    png_path = os.path.join(OUTPUT_DIR, f"{variant_name}.png")
    jpg_path = os.path.join(OUTPUT_DIR, f"{variant_name}.jpg")

    img.save(png_path)
    img.save(jpg_path, quality=95)

    img.save(f"assets/thumbnails/{variant_name}.png")
    img.save(f"assets/thumbnails/{variant_name}.jpg")

    print(f"✅ Generated Thumbnail: {png_path} & {jpg_path}")

def main():
    variants = [
        ("thumbnail_v2_variant_a", "STOP THE OVERWRITE"),
        ("thumbnail_v2_variant_b", "NO MORE COLLISIONS"),
        ("thumbnail_v2_variant_c", "ZERO STATE BLEED"),
    ]

    for var_id, text in variants:
        build_variant(var_id, text)

    print("🚀 All 3 YouTube Studio Test & Compare thumbnails generated successfully.")

if __name__ == "__main__":
    main()
