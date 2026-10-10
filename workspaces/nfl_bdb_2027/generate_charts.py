#!/usr/bin/env python3
"""
XORAS Systems LLC — Visual Analytics Chart Generator for NFL Big Data Bowl 2027
Generates broadcast-grade data visualizations for player physical combine tracking metrics.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def generate_charts():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    players_df = pd.read_csv(os.path.join(base_dir, "players.csv"))
    combine_df = pd.read_csv(os.path.join(base_dir, "combine_results.csv"))
    merged = pd.merge(players_df, combine_df, on="nfl_id")

    numeric_cols = ["forty", "ten_yd_split", "vertical", "broad_jump", "ngs_athleticism_score"]
    for col in numeric_cols:
        merged[col] = pd.to_numeric(merged[col], errors='coerce')

    merged['aei_score'] = (merged['vertical'] / (merged['forty'] + 1e-5)) + (merged['broad_jump'] / (merged['ten_yd_split'] * 10 + 1e-5))
    merged = merged.dropna(subset=['forty', 'vertical', 'aei_score'])

    plt.style.use('dark_background')
    
    # 1. Scatter Plot: 40-Yard Dash vs Vertical Jump
    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
    scatter = ax.scatter(
        merged['forty'], 
        merged['vertical'], 
        c=merged['aei_score'], 
        cmap='plasma', 
        alpha=0.85, 
        s=60
    )
    
    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label('Athletic Explosiveness Index (AEI)', color='white')
    
    ax.set_title("NFL Combine 2023-2025: 40-Yard Dash vs. Vertical Jump Velocity", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("40-Yard Dash Time (Seconds)", fontsize=11)
    ax.set_ylabel("Vertical Jump (Inches)", fontsize=11)
    ax.grid(True, linestyle='--', alpha=0.2)
    plt.tight_layout()
    
    chart1_path = os.path.join(base_dir, "forty_vs_vertical.png")
    plt.savefig(chart1_path, dpi=150)
    plt.close()
    print(f"Generated chart 1 at '{chart1_path}'")

    # 2. Bar Chart: Mean AEI Score by Position
    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
    avg_aei = merged.groupby('nfl_position')['aei_score'].mean().sort_values(ascending=True)
    
    bars = ax.barh(avg_aei.index, avg_aei.values, color='#3b82f6', edgecolor='#60a5fa', alpha=0.85)
    ax.set_title("Mean Athletic Explosiveness Index (AEI) by Position Group", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Mean AEI Score", fontsize=11)
    ax.set_ylabel("Position Group", fontsize=11)
    ax.grid(True, linestyle='--', alpha=0.2)
    plt.tight_layout()

    chart2_path = os.path.join(base_dir, "position_aei_leaderboard.png")
    plt.savefig(chart2_path, dpi=150)
    plt.close()
    print(f"Generated chart 2 at '{chart2_path}'")

if __name__ == "__main__":
    generate_charts()
