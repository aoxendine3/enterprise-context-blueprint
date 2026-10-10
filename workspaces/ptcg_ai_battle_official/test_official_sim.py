import sys
import os
import random

# Add sample_submission directory to PYTHONPATH
sample_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_submission", "sample_submission", "sample_submission")
sys.path.insert(0, sample_dir)

from cg.game import battle_start, battle_select, battle_finish, visualize_data
from cg.api import to_observation_class, Observation

def read_deck() -> list[int]:
    deck_path = os.path.join(sample_dir, "deck.csv")
    with open(deck_path, "r") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    return [int(x) for x in lines[:60]]

def run_match():
    deck0 = read_deck()
    deck1 = read_deck()
    
    print(f"Starting official PTCG battle with deck size: {len(deck0)}...")
    obs_dict, start_data = battle_start(deck0, deck1)
    
    step = 0
    while obs_dict and "winner" not in obs_dict:
        step += 1
        obs: Observation = to_observation_class(obs_dict)
        
        if obs.select is None:
            # End of game or setup
            break
            
        options = obs.select.option
        max_cnt = obs.select.maxCount
        min_cnt = obs.select.minCount
        
        # Pick random valid options
        choice = random.sample(list(range(len(options))), min(max_cnt, len(options)))
        
        player_idx = obs.current.yourIndex if obs.current else "?"
        turn = obs.current.turn if obs.current else "?"
        
        print(f"Step {step:03d} | Player {player_idx} | Turn {turn} | Options: {len(options)} | Selected: {choice}")
        
        try:
            obs_dict = battle_select(choice)
        except Exception as e:
            print(f"Game finished or error: {e}")
            break
            
    print(f"Match finished in {step} steps!")
    winner = obs_dict.get("winner") if isinstance(obs_dict, dict) else "Completed"
    print("Winner:", winner)
    
    viz = visualize_data()
    print(f"Official C++ Engine Visualization Data Size: {len(viz)} bytes.")
    battle_finish()

if __name__ == "__main__":
    run_match()
