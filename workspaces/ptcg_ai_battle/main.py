#!/usr/bin/env python3
import json
import random

def evaluate_action_score(action, obs):
    act_type = action.get("type", "")
    damage = action.get("damage", 0)
    opp_active_hp = obs.get("opponent_active_hp", 330)
    is_opp_ex = obs.get("opponent_is_ex", True)

    if act_type == "ATTACK":
        if damage >= opp_active_hp:
            return 1.00
        prize_weight = 0.20 if is_opp_ex else 0.10
        return min(0.98, 0.75 + (damage / 400.0) * 0.15 + prize_weight)
    elif act_type == "EVOLVE":
        return 0.90 if "Charizard" in action.get("to_pokemon", "") else 0.82
    elif act_type == "ATTACH_ENERGY":
        return 0.84
    elif act_type == "PLAY_TRAINER":
        return 0.88 if action.get("card_name", "") == "Rare Candy" else 0.81
    return 0.05

def agent(observation, configuration):
    legal_actions = observation.get("legal_actions", [])
    if not legal_actions:
        return 0
    best_idx = 0
    best_score = -1.0
    for idx, act in enumerate(legal_actions):
        score = evaluate_action_score(act, observation) + random.gauss(0, 0.01)
        if score > best_score:
            best_score = score
            best_idx = idx
    return best_idx

if __name__ == "__main__":
    test_obs = {"opponent_active_hp": 180, "legal_actions": [{"type": "ATTACH_ENERGY"}, {"type": "ATTACK", "damage": 180}]}
    print("Test Callback Action Index:", agent(test_obs, {}))
