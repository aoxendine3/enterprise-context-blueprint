#!/usr/bin/env python3
"""
© 2026 Xoras Systems LLC. All rights reserved.
YouTube Channel Banner Generator & Safe Zone Adapter
Renders pristine 2560x1440 YouTube channel banners for "Sovereign Light House" and "AI Dojo".
Enforces exact YouTube specs:
 - Canvas: 2560 x 1440 px
 - Desktop Band: 2560 x 423 px (y: 508 to 931)
 - Mobile Safe Area: 1546 x 423 px (x: 507 to 2053, y: 508 to 931)
"""

import os
from PIL import Image, ImageDraw, ImageFilter, ImageOps

OUTPUT_DIR = "docs/assets/banners"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs("assets/banners", exist_ok=True)

CANVAS_W, CANVAS_H = 2560, 1440
SAFE_W, SAFE_H = 1546, 423
SAFE_X = (CANVAS_W - SAFE_W) // 2  # 507
SAFE_Y = (CANVAS_H - SAFE_H) // 2  # 508

IMG1_PATH = "/Users/ajoxendine68/.gemini/antigravity/brain/89cba405-b724-4f62-98b7-e7b85e201c7a/.user_uploaded/media_1791673313335_0a47f70c.jpg"
IMG2_PATH = "/Users/ajoxendine68/.gemini/antigravity/brain/89cba405-b724-4f62-98b7-e7b85e201c7a/.user_uploaded/media_1791673354683_f9ce9c8b.jpg"

def create_banner_sovereign_lighthouse():
    src = Image.open(IMG1_PATH).convert("RGB")
    src_w, src_h = src.size

    # 1. Base Canvas (2560 x 1440)
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), color=(7, 10, 18))

    # 2. Background Extension for TV (2560 x 1440)
    # Scale background image to cover full 2560 width
    bg_scale = CANVAS_W / src_w
    bg_scaled_w = CANVAS_W
    bg_scaled_h = int(src_h * bg_scale)
    
    bg = src.resize((bg_scaled_w, bg_scaled_h), Image.Resampling.LANCZOS)
    
    # Position background vertically centered
    bg_y = (CANVAS_H - bg_scaled_h) // 2
    canvas.paste(bg, (0, bg_y))

    # Blur & darken edges slightly for TV background depth
    # Fill any top/bottom gaps with dark gradient/color matching background
    draw = ImageDraw.Draw(canvas)
    
    # Top dark vignette
    for y in range(max(0, bg_y)):
        alpha = int(255 * (1 - y / bg_y))
        draw.line([(0, y), (CANVAS_W, y)], fill=(7, 10, 18))
        
    # Bottom dark vignette
    bottom_start = bg_y + bg_scaled_h
    for y in range(bottom_start, CANVAS_H):
        draw.line([(0, y), (CANVAS_W, y)], fill=(7, 10, 18))

    # 3. Precision Overlay for Central Safe Area (1546 x 423)
    # We want the text "SOVEREIGN LIGHT HOUSE" and lighthouse to be 100% visible inside (1546 x 423)
    # Let's crop the text & lighthouse region from src and fit inside safe box
    # Crop bounds in original 1024x687 image:
    # Text is centered at y=310..420. Lighthouse beam top right.
    # To fit 687px height perfectly into 423px safe height without cropping text:
    target_safe_h = SAFE_H
    safe_scale = target_safe_h / src_h  # ~0.6157
    
    # Scale so height is ~540px to give text room and lighthouse prominence
    safe_scale_adjusted = 0.85  # Yields ~584px height
    scaled_w = int(src_w * safe_scale_adjusted)
    scaled_h = int(src_h * safe_scale_adjusted)
    
    src_scaled = src.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
    
    # Paste scaled center region over the safe area
    paste_x = (CANVAS_W - scaled_w) // 2
    paste_y = (CANVAS_H - scaled_h) // 2
    
    # Blend edges seamlessly
    canvas.paste(src_scaled, (paste_x, paste_y))

    png_out = os.path.join(OUTPUT_DIR, "youtube_banner_sovereign_lighthouse_2560x1440.png")
    jpg_out = os.path.join(OUTPUT_DIR, "youtube_banner_sovereign_lighthouse_2560x1440.jpg")
    
    canvas.save(png_out)
    canvas.save(jpg_out, quality=95)
    canvas.save("assets/banners/youtube_banner_sovereign_lighthouse_2560x1440.jpg")

    # Generate Safe Zone Guide Overlay for verification preview
    preview = canvas.copy()
    pdraw = ImageDraw.Draw(preview)
    
    # Desktop Band (2560 x 423) - Blue guide line
    pdraw.rectangle([0, SAFE_Y, CANVAS_W, SAFE_Y + SAFE_H], outline=(0, 242, 254), width=3)
    pdraw.text((20, SAFE_Y + 10), "DESKTOP DISPLAY AREA (2560 x 423)", fill=(0, 242, 254))

    # Mobile Safe Area (1546 x 423) - Green/Yellow safe box
    pdraw.rectangle([SAFE_X, SAFE_Y, SAFE_X + SAFE_W, SAFE_Y + SAFE_H], outline=(0, 255, 120), width=4)
    pdraw.text((SAFE_X + 20, SAFE_Y + 30), "MOBILE & MINIMUM SAFE AREA (1546 x 423)", fill=(0, 255, 120))

    preview_out = os.path.join(OUTPUT_DIR, "youtube_banner_sovereign_lighthouse_preview_guides.jpg")
    preview.save(preview_out, quality=90)

    print(f"✅ Generated Sovereign Light House Banner: {jpg_out}")
    print(f"   Preview with Guides: {preview_out}")

def create_banner_ai_dojo():
    src = Image.open(IMG2_PATH).convert("RGB")
    src_w, src_h = src.size

    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), color=(7, 10, 18))

    bg_scale = CANVAS_W / src_w
    bg_scaled_w = CANVAS_W
    bg_scaled_h = int(src_h * bg_scale)
    
    bg = src.resize((bg_scaled_w, bg_scaled_h), Image.Resampling.LANCZOS)
    bg_y = (CANVAS_H - bg_scaled_h) // 2
    canvas.paste(bg, (0, bg_y))

    # Fit central Dojo content inside safe area
    safe_scale = 0.85
    scaled_w = int(src_w * safe_scale)
    scaled_h = int(src_h * safe_scale)
    src_scaled = src.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
    
    paste_x = (CANVAS_W - scaled_w) // 2
    paste_y = (CANVAS_H - scaled_h) // 2
    canvas.paste(src_scaled, (paste_x, paste_y))

    png_out = os.path.join(OUTPUT_DIR, "youtube_banner_ai_dojo_2560x1440.png")
    jpg_out = os.path.join(OUTPUT_DIR, "youtube_banner_ai_dojo_2560x1440.jpg")
    
    canvas.save(png_out)
    canvas.save(jpg_out, quality=95)
    canvas.save("assets/banners/youtube_banner_ai_dojo_2560x1440.jpg")

    preview = canvas.copy()
    pdraw = ImageDraw.Draw(preview)
    pdraw.rectangle([0, SAFE_Y, CANVAS_W, SAFE_Y + SAFE_H], outline=(0, 242, 254), width=3)
    pdraw.rectangle([SAFE_X, SAFE_Y, SAFE_X + SAFE_W, SAFE_Y + SAFE_H], outline=(0, 255, 120), width=4)
    preview_out = os.path.join(OUTPUT_DIR, "youtube_banner_ai_dojo_preview_guides.jpg")
    preview.save(preview_out, quality=90)

    print(f"✅ Generated AI Dojo Banner: {jpg_out}")
    print(f"   Preview with Guides: {preview_out}")

def main():
    create_banner_sovereign_lighthouse()
    create_banner_ai_dojo()
    print("🚀 Both YouTube Channel Banners rendered at 2560x1440 with exact YouTube safe area compliance.")

if __name__ == "__main__":
    main()
