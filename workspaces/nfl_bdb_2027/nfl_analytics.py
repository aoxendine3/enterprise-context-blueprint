#!/usr/bin/env python3
"""
XORAS Systems LLC — NFL Big Data Bowl 2027 Feature Engineering & Predictive Pipeline
Analyzes player combine physical tracking metrics, Next Gen Stats athleticism, and career success trajectories.
"""

import pandas as pd
import numpy as np
import os
import json

def load_and_preprocess():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    players_df = pd.read_csv(os.path.join(base_dir, "players.csv"))
    combine_df = pd.read_csv(os.path.join(base_dir, "combine_results.csv"))
    success_df = pd.read_csv(os.path.join(base_dir, "player_career_successes.csv"))
    games_df = pd.read_csv(os.path.join(base_dir, "games.csv"))

    print(f"Loaded {len(players_df)} players, {len(combine_df)} combine records, {len(success_df)} success metrics, {len(games_df)} games.")

    # Merge players and combine results on nfl_id
    merged = pd.merge(players_df, combine_df, on="nfl_id", how="inner", suffixes=('', '_combine'))
    merged = pd.merge(merged, success_df, on="nfl_id", how="left")

    # Clean numeric columns
    numeric_cols = ["forty", "ten_yd_split", "vertical", "broad_jump", "three_cone", "short_shuttle", "bench_reps", "ngs_athleticism_score"]
    for col in numeric_cols:
        if col in merged.columns:
            merged[col] = pd.to_numeric(merged[col], errors='coerce')

    # Compute custom Athletic Explosiveness Index (AEI)
    # AEI = (Vertical / Forty) + (Broad Jump / (Ten Yd Split * 10))
    merged['aei_score'] = (merged['vertical'] / (merged['forty'] + 1e-5)) + (merged['broad_jump'] / (merged['ten_yd_split'] * 10 + 1e-5))
    merged['aei_score'] = merged['aei_score'].fillna(merged['aei_score'].median())

    # Rank players by position
    merged['position_rank'] = merged.groupby('nfl_position')['aei_score'].rank(ascending=False, method='min')

    print(f"Computed AEI score for {len(merged)} matched player records.")
    
    # Generate submission dataframe
    submission_df = merged[['nfl_id', 'display_name', 'nfl_position', 'aei_score', 'position_rank']].copy()
    submission_path = os.path.join(base_dir, "submission.csv")
    submission_df.to_csv(submission_path, index=False)
    print(f"Successfully generated submission CSV at '{submission_path}' ({len(submission_df)} rows).")

    return merged

if __name__ == "__main__":
    load_and_preprocess()
