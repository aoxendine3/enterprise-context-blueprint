# Empirical Experiment Runner for Clara
import sys, os, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from clara_engine import run_experiment

if __name__ == "__main__":
    receipt = run_experiment()
    # Save receipt to private brain
    brain_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "brain"))
    os.makedirs(brain_dir, exist_ok=True)
    receipt_path = os.path.join(brain_dir, "latest_experiment_receipt.json")
    with open(receipt_path, "w") as f:
        json.dump(receipt, f, indent=2)
    print(json.dumps(receipt, indent=2))
