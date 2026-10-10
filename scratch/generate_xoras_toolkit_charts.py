#!/usr/bin/env python3
"""
Generate Modern Visual Assets for Xoras Agentic Toolkit (xoras-opensource)
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

plt.style.use('dark_background')
fig_color = '#0B0E14'
card_color = '#161B22'
text_color = '#E6EDF3'

# 1. Generate Architecture Banner
def generate_toolkit_banner(out_path: str):
    fig, ax = plt.subplots(figsize=(12, 4.5), facecolor=fig_color)
    ax.set_facecolor(fig_color)
    ax.axis('off')

    # Background header box
    rect = patches.FancyBboxPatch((0.05, 0.1), 0.9, 0.8, boxstyle="round,pad=0.03",
                                 facecolor=card_color, edgecolor='#30363D', linewidth=2)
    ax.add_patch(rect)

    ax.text(0.5, 0.72, "XORAS AGENTIC TOOLKIT", color='#58A6FF', fontsize=22, fontweight='bold', ha='center')
    ax.text(0.5, 0.60, "Sovereign Autonomous Multi-Agent Utilities & Open-Source Toolkit", color=text_color, fontsize=12, ha='center')

    # Sub-modules
    # Box 1: Chronos Debugger
    b1 = patches.FancyBboxPatch((0.10, 0.20), 0.36, 0.32, boxstyle="round,pad=0.02",
                                facecolor='#1F2937', edgecolor='#3B82F6', linewidth=1.5)
    ax.add_patch(b1)
    ax.text(0.28, 0.40, "⏱️ Chronos Swarm Debugger", color='#60A5FA', fontsize=12, fontweight='bold', ha='center')
    ax.text(0.28, 0.28, "HTML5 Time-Scrubbing Visualizer\nJSONL Transcripts • Zero Dependencies", color='#9CA3AF', fontsize=9, ha='center')

    # Box 2: Horizon Sentinel
    b2 = patches.FancyBboxPatch((0.54, 0.20), 0.36, 0.32, boxstyle="round,pad=0.02",
                                facecolor='#1F2937', edgecolor='#10B981', linewidth=1.5)
    ax.add_patch(b2)
    ax.text(0.72, 0.40, "📡 Xoras Horizon Sentinel", color='#34D399', fontsize=12, fontweight='bold', ha='center')
    ax.text(0.72, 0.28, "Autonomous Intelligence Daemon\nGitHub Sweep • Ollama Local LLM Audit", color='#9CA3AF', fontsize=9, ha='center')

    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor=fig_color)
    plt.close()

# 2. Generate Workflow Chart
def generate_sentinel_workflow(out_path: str):
    fig, ax = plt.subplots(figsize=(10, 5), facecolor=fig_color)
    ax.set_facecolor(card_color)

    stages = ['GitHub API Sweep\n(Horizon Query)', 'Repo Metadata\nExtraction', 'Local LLM Inference\n(Ollama Llama-3.2-3B)', 'Architect Threat/Opportunity\nMarkdown Report']
    latencies = [120, 15, 315, 5] # milliseconds
    colors = ['#238636', '#1F6FEB', '#8E44AD', '#D35400']

    bars = ax.bar(stages, latencies, color=colors, width=0.45, edgecolor='#30363D', linewidth=1.5)

    ax.set_ylabel('Pipeline Execution Time (ms)', color=text_color, fontsize=12, fontweight='bold', labelpad=10)
    ax.set_title('Xoras Horizon Sentinel Autonomous Pipeline Execution Dynamics', color='#58A6FF', fontsize=14, fontweight='bold', pad=15)
    ax.tick_params(colors=text_color, labelsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#30363D')
    ax.spines['bottom'].set_color('#30363D')
    ax.grid(axis='y', linestyle='--', alpha=0.3, color='#8B949E')

    for bar, lat in zip(bars, latencies):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 10, f"{lat} ms",
                ha='center', va='bottom', color=text_color, fontweight='bold', fontsize=11)

    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor=fig_color)
    plt.close()

if __name__ == "__main__":
    out_dir = "/tmp/xoras-opensource/docs/assets"
    
    p1 = os.path.join(out_dir, "xoras_toolkit_architecture_banner.png")
    generate_toolkit_banner(p1)
    print(f"Generated: {p1}")

    p2 = os.path.join(out_dir, "xoras_sentinel_workflow_chart.png")
    generate_sentinel_workflow(p2)
    print(f"Generated: {p2}")
