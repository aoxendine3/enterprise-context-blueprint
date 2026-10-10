#!/usr/bin/env python3
"""
© 2026 Xoras Systems LLC. All rights reserved.
Un-mocked Verification Harness for Cinematic Video Synthesis & Movie Condensation Engine
Writes receipts to memory/catch_log/cinematic_video_engine.log.
"""

import os
import sys
import json
import time

# Ensure repo root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core.products.cinematic_video_engine import (
    MovieShortenerEngine,
    CinematicShortsEngine,
    DeepDiveScriptEngine,
    MARSAtlanAuditGate
)

LOG_DIR = os.path.join(REPO_ROOT, "memory/catch_log")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "cinematic_video_engine.log")

def main():
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

    # 1. Script Generation
    script_engine = DeepDiveScriptEngine()
    script = script_engine.compile_high_retention_script("Sovereign AI Swarm Architecture", 600.0)
    val = script_engine.validate_atlan_groundedness(script, ["AGENTS.md", "SOVRA_SPEC.md"])

    assert val["groundedness_passed"], "Atlan Groundedness failed (< 95%)"
    assert val["fin_hallucination_passed"], "Fin Hallucination failed (>= 1.0%)"

    # 2. Movie Condensation
    movie_engine = MovieShortenerEngine()
    frames = movie_engine.sample_multimodal_frames("feature_film.mp4", 7200.0) # 2 hours
    transcript = movie_engine.index_dialogue_whisper("dialogue.mp3")
    scene_graph = movie_engine.build_temporal_scene_graph(frames, transcript)
    edl = movie_engine.generate_ffmpeg_edl("Feature Film Sovereign Cut", 7200.0, scene_graph)

    assert len(edl["scenes"]) > 0, "No scenes extracted for EDL cut sheet"
    assert edl["condensed_duration_sec"] < 7200.0, "Movie condensation failed to compress timeline"

    # 3. Cinematic Shorts Chaining
    shorts_engine = CinematicShortsEngine()
    chain = shorts_engine.compile_scene_chain("Hyperbolic Poincaré Manifold Visualization", 4)

    assert len(chain) == 4, "Scene chain length mismatch"
    assert chain[1]["seed_reference"] == "scene_01_final_frame.png", f"Frame-seeded continuity failed: got {chain[1]['seed_reference']}"

    # 4. MARS Atlan Audit Gate
    gate = MARSAtlanAuditGate()
    audit = gate.execute_4_layer_audit({"script": script, "edl": edl, "chain": chain})

    assert audit["gate_disposition"] == "APPROVED_FOR_PRODUCTION", "MARS Audit Gate rejected payload"

    log_entry = (
        f"[{timestamp}] XORAS CINEMATIC VIDEO SYNTHESIS ENGINE AUDIT SUCCESS\n"
        f" - Atlan Groundedness Score: {val['groundedness_score']}%\n"
        f" - Fin Hallucination Rate: {val['fin_hallucination_rate']}%\n"
        f" - Movie Condensation: 120.0m -> {edl['condensed_duration_sec']}s ({edl['compression_ratio']})\n"
        f" - Shorts Frame-Seeded Chain: {len(chain)} scenes compiled\n"
        f" - MARS 4-Layer Gate: {audit['gate_disposition']}\n"
        f" - Ed25519 Signature: {audit['layer_2_sast_ed25519']['signature']}\n\n"
    )

    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

    print(log_entry)
    print("🚀 All 3 Video Synthesis & Condensation Pipelines Verified 100% PASS.")

if __name__ == "__main__":
    main()
