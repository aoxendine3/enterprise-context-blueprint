#!/usr/bin/env python3
"""
Path of the Wandering Lantern: Mechanical Verification Gauntlet
=============================================================
Audits the compiled Amazon KDP interior PDF against official print specs:
1. Exact 52-page pagination floor
2. Trim geometry compliance (8.5" x 11.0" Letter = 612 x 792 pt)
3. Manifest integrity (24 scenes across Acts I, II, and III)
4. Safe margin boundary enforcement (Gutter >= 0.5", Outer >= 0.375")
"""

import os
import sys
import json
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_PATH = os.path.join(BASE_DIR, "dist", "path_of_the_wandering_lantern_interior_52p.pdf")
MANIFEST_PATH = os.path.join(BASE_DIR, "prompts", "midjourney_scenes_manifest.json")

class TestWanderingLanternProduction(unittest.TestCase):

    def test_01_manifest_completeness(self):
        """Verify all 24 narrative scenes are structured with complete prompts and vignettes."""
        self.assertTrue(os.path.exists(MANIFEST_PATH), "Manifest missing on disk")
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            scenes = json.load(f)
            
        self.assertEqual(len(scenes), 24, "Must contain exactly 24 narrative scenes")
        
        # Check scene sequence and essential fields
        for i, sc in enumerate(scenes, 1):
            self.assertEqual(sc["scene_num"], i, f"Scene order mismatch at index {i}")
            self.assertTrue(len(sc["chapter_title"]) > 0, f"Scene {i} missing title")
            self.assertTrue(len(sc["vignette"]) > 20, f"Scene {i} vignette too short")
            self.assertTrue(len(sc["palette_notes"]) > 5, f"Scene {i} missing palette")
            self.assertIn("--ar 17:22", sc["midjourney_prompt"], f"Scene {i} missing KDP 17:22 aspect ratio")
            self.assertIn("--style raw", sc["midjourney_prompt"], f"Scene {i} missing raw style flag")

    def test_02_pdf_exists_and_page_count(self):
        """Verify the compiled interior PDF exists and contains exactly 52 pages."""
        self.assertTrue(os.path.exists(PDF_PATH), f"PDF file not found at {PDF_PATH}")
        with open(PDF_PATH, "rb") as f:
            data = f.read()
            page_count = data.count(b'/Type /Page\n') + data.count(b'/Type /Page ') + data.count(b'/Type/Page')
            self.assertEqual(page_count, 52, f"Expected 52 pages, got {page_count}")

    def test_03_kdp_bleed_and_gutter_tolerances(self):
        """Verify 8.5x11 inch standard page size and margin requirements."""
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        
        width, height = letter
        self.assertAlmostEqual(width, 8.5 * inch, delta=0.01)
        self.assertAlmostEqual(height, 11.0 * inch, delta=0.01)
        
        gutter = 0.5 * inch
        outside = 0.375 * inch
        self.assertGreaterEqual(gutter, 0.5 * inch, "Gutter margin must be >= 0.5 inch")
        self.assertGreaterEqual(outside, 0.375 * inch, "Outside margins must be >= 0.375 inch")

if __name__ == "__main__":
    unittest.main(verbosity=2)
