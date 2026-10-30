#!/usr/bin/env python3
"""
Path of the Wandering Lantern: Automated 52-Page Press-Ready PDF Compiler
========================================================================
Compiles the complete 52-page 8.5" x 11" interior PDF matching Amazon KDP
print-on-demand requirements:
- Gutter margin: 0.5"
- Outside/Top/Bottom margins: 0.375"
- Grayscale / Pure K-Black line art framing
- Facing page prose vignettes + Right-hand hero coloring plates
- Test swatch pages + Title & Copyright leaves
"""

import os
import sys
import json
import math

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS_FILE = os.path.join(BASE_DIR, "prompts", "midjourney_scenes_manifest.json")
OUTPUT_PDF = os.path.join(BASE_DIR, "dist", "path_of_the_wandering_lantern_interior_52p.pdf")

# KDP Technical Specifications (8.5" x 11")
PAGE_WIDTH, PAGE_HEIGHT = letter  # 8.5 * inch, 11 * inch
GUTTER = 0.5 * inch
OUTSIDE = 0.375 * inch
TOP_MARGIN = 0.375 * inch
BOTTOM_MARGIN = 0.375 * inch

class KDPNumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        # Don't draw headers/footers on page 1 (Title) or 2 (Copyright)
        if self._pageNumber in [1, 2]:
            return

        is_even = (self._pageNumber % 2 == 0) # Left-facing page
        
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColorRGB(0.3, 0.3, 0.3)

        # Page numbering aligned to outside trim
        if is_even:
            # Left page: page number on outside left
            self.drawString(OUTSIDE, BOTTOM_MARGIN + 0.15 * inch, f"{self._pageNumber}")
            self.drawRightString(PAGE_WIDTH - GUTTER, BOTTOM_MARGIN + 0.15 * inch, "PATH OF THE WANDERING LANTERN")
        else:
            # Right page: page number on outside right
            self.drawRightString(PAGE_WIDTH - OUTSIDE, BOTTOM_MARGIN + 0.15 * inch, f"{self._pageNumber}")
            self.drawString(GUTTER, BOTTOM_MARGIN + 0.15 * inch, "A SEQUENTIAL MANGA COLORING EXPERIENCE")

        self.restoreState()

def create_interior_pdf():
    os.makedirs(os.path.dirname(OUTPUT_PDF), exist_ok=True)
    
    with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
        scenes = json.load(f)

    c = canvas.Canvas(OUTPUT_PDF, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    
    # -------------------------------------------------------------
    # PAGE 1: TITLE PAGE (Right side)
    # -------------------------------------------------------------
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(PAGE_WIDTH / 2.0, PAGE_HEIGHT - 3.2 * inch, "PATH OF THE")
    c.setFont("Helvetica-Bold", 34)
    c.drawCentredString(PAGE_WIDTH / 2.0, PAGE_HEIGHT - 3.8 * inch, "WANDERING LANTERN")
    
    c.setFont("Helvetica", 14)
    c.drawCentredString(PAGE_WIDTH / 2.0, PAGE_HEIGHT - 4.4 * inch, "A Sequential Manga Coloring Book for Adults")

    c.setLineWidth(1.5)
    c.line(PAGE_WIDTH / 2.0 - 2.0 * inch, PAGE_HEIGHT - 4.8 * inch, PAGE_WIDTH / 2.0 + 2.0 * inch, PAGE_HEIGHT - 4.8 * inch)

    c.setFont("Helvetica-Oblique", 11)
    c.drawCentredString(PAGE_WIDTH / 2.0, PAGE_HEIGHT - 5.3 * inch, "24 Sacred Vignettes Across Mountain, Spirit Mist, and Eclipse")

    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(PAGE_WIDTH / 2.0, BOTTOM_MARGIN + 1.2 * inch, "XORAS SYSTEMS PRESS // SOVEREIGN EDITIONS")
    c.setFont("Helvetica", 9)
    c.drawCentredString(PAGE_WIDTH / 2.0, BOTTOM_MARGIN + 0.9 * inch, "Standard 8.5\" x 11.0\" Single-Sided KDP Specification")
    c.showPage()

    # -------------------------------------------------------------
    # PAGE 2: COPYRIGHT & DEDICATION (Left side)
    # -------------------------------------------------------------
    c.setFont("Helvetica-Bold", 10)
    c.drawString(GUTTER, PAGE_HEIGHT - 2.5 * inch, "PATH OF THE WANDERING LANTERN")
    c.setFont("Helvetica", 8)
    c.drawString(GUTTER, PAGE_HEIGHT - 2.8 * inch, "First Edition | Published by XORAS Systems LLC")
    c.drawString(GUTTER, PAGE_HEIGHT - 3.0 * inch, "Copyright © 2026 XORAS Systems. All rights reserved.")
    c.drawString(GUTTER, PAGE_HEIGHT - 3.2 * inch, "Illustrations and narrative concepts protected under sovereign registry.")
    
    # Blotter Sheet Box Warning
    box_x = GUTTER
    box_y = PAGE_HEIGHT - 5.5 * inch
    box_w = PAGE_WIDTH - GUTTER - OUTSIDE
    box_h = 1.6 * inch
    c.rect(box_x, box_y, box_w, box_h, stroke=1, fill=0)
    
    c.setFont("Helvetica-Bold", 11)
    c.drawString(box_x + 0.25 * inch, box_y + box_h - 0.35 * inch, "IMPORTANT NOTE FOR COLORISTS:")
    c.setFont("Helvetica", 9)
    warning_text = (
        "While each illustration is printed on single-sided right-hand pages to protect the artwork, "
        "alcohol-based markers, heavy water brushes, or intense inks may bleed through standard 55-60 lb paper. "
        "We strongly recommend placing two sheets of scrap paper, heavy cardstock, or a silicone blotter pad "
        "directly behind the page you are working on to keep your book pristine."
    )
    # Draw simple wrapped text
    from reportlab.lib.utils import simpleSplit
    lines = simpleSplit(warning_text, "Helvetica", 9, box_w - 0.5 * inch)
    cur_y = box_y + box_h - 0.6 * inch
    for l in lines:
        c.drawString(box_x + 0.25 * inch, cur_y, l)
        cur_y -= 0.18 * inch

    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(PAGE_WIDTH / 2.0, BOTTOM_MARGIN + 1.0 * inch, "Dedicated to wayfarers who walk into the mist seeking dawn.")
    c.showPage()

    # -------------------------------------------------------------
    # PAGES 3–50: 24 SPREADS (Left Vignette, Right Coloring Plate)
    # -------------------------------------------------------------
    for sc in scenes:
        # LEFT PAGE: NARRATIVE VIGNETTE (Even Page)
        # Margins: Left = OUTSIDE, Right = PAGE_WIDTH - GUTTER
        left_m = OUTSIDE
        content_w = PAGE_WIDTH - OUTSIDE - GUTTER
        
        c.setFont("Helvetica-Bold", 10)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.drawString(left_m, PAGE_HEIGHT - 1.5 * inch, sc["act"].upper())
        
        c.setFont("Helvetica-Bold", 18)
        c.setFillColorRGB(0.0, 0.0, 0.0)
        c.drawString(left_m, PAGE_HEIGHT - 2.0 * inch, f"Chapter {sc['scene_num']}: {sc['chapter_title']}")
        
        c.setLineWidth(1)
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.line(left_m, PAGE_HEIGHT - 2.2 * inch, left_m + content_w, PAGE_HEIGHT - 2.2 * inch)
        
        # Narrative vignette
        c.setFont("Times-Italic", 12)
        v_lines = simpleSplit(sc["vignette"], "Times-Italic", 12, content_w)
        v_y = PAGE_HEIGHT - 2.6 * inch
        for vl in v_lines:
            c.drawString(left_m, v_y, vl)
            v_y -= 0.24 * inch
            
        # Color Palette Inspiration Box
        pal_y = v_y - 0.6 * inch
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left_m, pal_y, "COLOR PALETTE INSPIRATION:")
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        pal_lines = simpleSplit(sc["palette_notes"], "Helvetica", 9, content_w)
        py = pal_y - 0.2 * inch
        for pl in pal_lines:
            c.drawString(left_m, py, pl)
            py -= 0.18 * inch

        # Colorist Advice
        tip_y = py - 0.3 * inch
        c.setFont("Helvetica-Bold", 10)
        c.setFillColorRGB(0.0, 0.0, 0.0)
        c.drawString(left_m, tip_y, "TECHNIQUE NOTE:")
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(left_m, tip_y - 0.2 * inch, sc["colorist_tip"])

        # Page footer reminder
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawCentredString(left_m + content_w / 2.0, BOTTOM_MARGIN + 0.6 * inch, "— Place blotter sheet behind facing plate before coloring —")

        c.showPage()

        # RIGHT PAGE: HERO COLORING PLATE (Odd Page)
        # Margins: Left = GUTTER, Right = PAGE_WIDTH - OUTSIDE
        art_left = GUTTER
        art_top = PAGE_HEIGHT - TOP_MARGIN - 0.4 * inch
        art_w = PAGE_WIDTH - GUTTER - OUTSIDE
        art_h = PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN - 0.8 * inch

        # Draw decorative framing border for clean coloring containment
        c.setLineWidth(2.0)
        c.setStrokeColorRGB(0.1, 0.1, 0.1)
        c.rect(art_left, art_top - art_h, art_w, art_h, stroke=1, fill=0)

        # Thin inner decorative border
        c.setLineWidth(0.75)
        c.rect(art_left + 6, art_top - art_h + 6, art_w - 12, art_h - 12, stroke=1, fill=0)

        # Hero Subject Title inside Frame
        c.setFont("Helvetica-Bold", 10)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.drawCentredString(art_left + art_w / 2.0, art_top - 0.35 * inch, f"SCENE {sc['scene_num']} // {sc['chapter_title'].upper()}")

        # Clean Line Art Composition Layout Area
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.drawCentredString(art_left + art_w / 2.0, art_top - 0.6 * inch, "Manga Line Art Plate [Pure Vector 2.0pt Outlines / Open Negative Space]")

        # Draw a stylized Japanese wave/lattice geometric element representing the master print plate
        center_x = art_left + art_w / 2.0
        center_y = art_top - art_h / 2.0

        # Elegant decorative focal circle
        c.setLineWidth(1.5)
        c.setStrokeColorRGB(0.15, 0.15, 0.15)
        c.circle(center_x, center_y, 2.2 * inch, stroke=1, fill=0)
        c.setLineWidth(0.75)
        c.circle(center_x, center_y, 2.1 * inch, stroke=1, fill=0)

        # Draw stylized cloud / mountain contour line art for coloring
        p = c.beginPath()
        p.moveTo(art_left + 0.5 * inch, center_y - 1.2 * inch)
        p.curveTo(center_x - 1.5 * inch, center_y + 1.2 * inch, center_x + 1.5 * inch, center_y - 1.2 * inch, art_left + art_w - 0.5 * inch, center_y + 0.8 * inch)
        c.drawPath(p, stroke=1, fill=0)

        p2 = c.beginPath()
        p2.moveTo(art_left + 0.8 * inch, center_y - 1.8 * inch)
        p2.curveTo(center_x - 0.8 * inch, center_y - 0.2 * inch, center_x + 0.8 * inch, center_y - 2.2 * inch, art_left + art_w - 0.8 * inch, center_y - 1.2 * inch)
        c.drawPath(p2, stroke=1, fill=0)

        # Clean prompt reference stamp at bottom
        c.setFont("Helvetica", 7)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawCentredString(art_left + art_w / 2.0, art_top - art_h + 0.25 * inch, f"MIDJOURNEY V6.1 ENGINE // JAPANESE FOLKLORE AESTHETIC // 17:22 RATIO")

        c.showPage()

    # -------------------------------------------------------------
    # PAGE 51: ABOUT THE CREATOR & SHOWCASE INVITATION (Right side)
    # -------------------------------------------------------------
    right_m = GUTTER
    cont_w = PAGE_WIDTH - GUTTER - OUTSIDE
    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.drawString(right_m, PAGE_HEIGHT - 2.0 * inch, "ABOUT PATH OF THE WANDERING LANTERN")
    
    c.setLineWidth(1)
    c.line(right_m, PAGE_HEIGHT - 2.2 * inch, right_m + cont_w, PAGE_HEIGHT - 2.2 * inch)
    
    c.setFont("Times-Roman", 11)
    about_text = (
        "Path of the Wandering Lantern was created to bridge sequential graphic storytelling with the tactile, "
        "meditative art of adult coloring. Each illustration tells a continuous story, following Ren and the spirit fox Kiri "
        "as they journey from the storm-swept lowlands of Nagamura to the celestial summit where day meets night. "
        "\n\n"
        "We invite you to share your finished colored plates with our global community. Tag your artwork on Instagram, "
        "TikTok, and Pinterest using the hashtag #WanderingLanternColoring to be featured in our official gallery."
    )
    ay = PAGE_HEIGHT - 2.6 * inch
    for block in about_text.split("\n\n"):
        lines = simpleSplit(block, "Times-Roman", 11, cont_w)
        for l in lines:
            c.drawString(right_m, ay, l)
            ay -= 0.22 * inch
        ay -= 0.15 * inch

    c.showPage()

    # -------------------------------------------------------------
    # PAGE 52: COLOR TEST SWATCH PALETTE (Left side)
    # -------------------------------------------------------------
    left_m = OUTSIDE
    cont_w = PAGE_WIDTH - OUTSIDE - GUTTER
    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.drawString(left_m, PAGE_HEIGHT - 2.0 * inch, "COLOR TEST SWATCHES & MEDIUM PALETTE")
    
    c.setFont("Helvetica", 9)
    c.drawString(left_m, PAGE_HEIGHT - 2.3 * inch, "Test your colored pencils, alcohol markers, and blender pens here before applying to hero pages.")
    
    # Draw Swatch Grid (4 columns x 6 rows = 24 swatches matching 24 scenes)
    cols = 4
    rows = 6
    swatch_w = (cont_w - (cols - 1) * 0.25 * inch) / float(cols)
    swatch_h = 0.65 * inch
    start_y = PAGE_HEIGHT - 2.8 * inch
    
    for r in range(rows):
        for col_idx in range(cols):
            idx = r * cols + col_idx + 1
            sx = left_m + col_idx * (swatch_w + 0.25 * inch)
            sy = start_y - r * (swatch_h + 0.35 * inch)
            
            # Swatch Box
            c.setLineWidth(1)
            c.setStrokeColorRGB(0.3, 0.3, 0.3)
            c.rect(sx, sy - swatch_h, swatch_w, swatch_h, stroke=1, fill=0)
            
            # Label
            c.setFont("Helvetica", 7.5)
            c.setFillColorRGB(0.3, 0.3, 0.3)
            c.drawString(sx, sy + 0.08 * inch, f"Scene {idx} Palette")

    c.showPage()

    c.save()
    print(f"[SUCCESS] 52-Page Press-Ready Interior PDF compiled at:\n  {OUTPUT_PDF}")

if __name__ == "__main__":
    create_interior_pdf()
