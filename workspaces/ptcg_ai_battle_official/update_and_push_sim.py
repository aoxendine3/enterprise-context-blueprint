#!/usr/bin/env python3
"""
XORAS Systems LLC — Official Kaggle PTCG AI Battle Simulation Notebook Pusher
Target Competition: the-pokemon-company-ptcg-ai-battle-challenge-playground
"""

import json
import os
import subprocess
import base64

def update_and_push():
    sim_dir = "workspaces/ptcg_ai_battle_official/pulled_sim_kernel"
    
    # Read 2.1 MB official submission.tar.gz and convert to base64
    tarball_path = "workspaces/ptcg_ai_battle_official/submission.tar.gz"
    with open(tarball_path, "rb") as f:
        tarball_b64 = base64.b64encode(f.read()).decode("utf-8")

    cells = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# The Pokémon Company — PTCG AI Battle Challenge Playground (Official Master Entry)\n",
                "**Engine Architecture**: Native C++ Game Engine (`libcg-arm64.so`) with 4-Layer MCTS Priority Evaluator & Zero-Network Offline Packaging\n",
                "**Developed by**: XORAS Systems LLC & Lead 9 Council\n"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Cell 1: Extract Official Submission Package (2.1 MB Engine + Deck + API)\n",
                "import base64\n",
                "import os\n",
                "import tarfile\n",
                "\n",
                "SUBMISSION_B64 = '''" + tarball_b64 + "'''\n",
                "\n",
                "tar_bytes = base64.b64decode(SUBMISSION_B64)\n",
                "with open('submission.tar.gz', 'wb') as f:\n",
                "    f.write(tar_bytes)\n",
                "\n",
                "print(f'Successfully wrote submission.tar.gz ({len(tar_bytes):,} bytes).')\n",
                "\n",
                "# Extract for validation test run\n",
                "os.makedirs('submission_ext', exist_ok=True)\n",
                "with tarfile.open('submission.tar.gz', 'r:gz') as tar:\n",
                "    tar.extractall('submission_ext')\n",
                "print('Extracted submission contents:', os.listdir('submission_ext'))\n"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Cell 2: Run Live Match Verification via Official C++ Engine\n",
                "import sys\n",
                "import os\n",
                "import random\n",
                "\n",
                "sys.path.insert(0, 'submission_ext')\n",
                "from cg.game import battle_start, battle_select, battle_finish, visualize_data\n",
                "from cg.api import to_observation_class, Observation\n",
                "\n",
                "def read_deck():\n",
                "    with open('submission_ext/deck.csv', 'r') as f:\n",
                "        return [int(x.strip()) for x in f.readlines() if x.strip()][:60]\n",
                "\n",
                "deck0 = read_deck()\n",
                "deck1 = read_deck()\n",
                "\n",
                "print(f'Starting official PTCG validation match with 60-card decks...')\n",
                "obs_dict, start_data = battle_start(deck0, deck1)\n",
                "step = 0\n",
                "while obs_dict and 'winner' not in obs_dict:\n",
                "    step += 1\n",
                "    obs = to_observation_class(obs_dict)\n",
                "    if obs.select is None:\n",
                "        break\n",
                "    options = obs.select.option\n",
                "    choice = random.sample(list(range(len(options))), min(obs.select.maxCount, len(options)))\n",
                "    obs_dict = battle_select(choice)\n",
                "\n",
                "print(f'Validation match completed in {step} turns cleanly!')\n",
                "viz = visualize_data()\n",
                "print(f'Engine visualization log size: {len(viz):,} bytes.')\n",
                "battle_finish()\n"
            ]
        }
    ]

    nb_content = {
        "cells": cells,
        "metadata": {
            "language_info": {"name": "python"}
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }

    nb_path = os.path.join(sim_dir, "ptcg-ai-battle-simulation-submission.ipynb")
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb_content, f, indent=2)

    meta_content = {
        "id": "anthonyoxendine/ptcg-ai-battle-simulation-submission",
        "title": "ptcg-ai-battle-simulation-submission",
        "code_file": "ptcg-ai-battle-simulation-submission.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": False,
        "enable_gpu": False,
        "enable_tpu": False,
        "enable_internet": False,
        "dataset_sources": [],
        "kernel_sources": [],
        "competition_sources": ["the-pokemon-company-ptcg-ai-battle-challenge-playground"]
    }

    meta_path = os.path.join(sim_dir, "kernel-metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_content, f, indent=2)

    print("Updated simulation kernel files with boolean JSON. Pushing to Kaggle...")
    res = subprocess.run(["kaggle", "kernels", "push", "-p", sim_dir], capture_output=True, text=True)
    print("Kaggle Push Output:")
    print(res.stdout)
    if res.stderr:
        print("Kaggle Push Error:")
        print(res.stderr)

if __name__ == "__main__":
    update_and_push()
