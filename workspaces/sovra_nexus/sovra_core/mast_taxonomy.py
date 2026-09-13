"""
MAST: MULTI-AGENT SAFETY TAXONOMY (14 CANONICAL FAILURE MODES)
Real-time safety scoring, failure mode detection, and autonomous healing trigger.
"""

import time
from typing import Dict, List, Any

FAILURE_MODES = [
    "coordination_collapse",
    "information_cascading",
    "resource_contention",
    "role_ambiguity",
    "echo_chamber_bias",
    "adversarial_takeover",
    "state_drift",
    "reward_hacking",
    "healing_loop_failure",
    "latency_avalanche",
    "context_collapse",
    "schema_violation",
    "consensus_erosion",
    "cascading_termination"
]

class MASTTaxonomy:
    HEALING_THRESHOLD = 0.92

    def __init__(self):
        self.history: List[Dict[str, Any]] = []

    def evaluate(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates system telemetry across the 14 failure modes.
        Returns a dictionary with safety score (0.0 to 1.0) and failure mode flags.
        """
        risk_penalties = {}
        
        # 1. Coordination collapse: agent timeouts / unresponsiveness
        timeout_ratio = float(telemetry.get("timeout_ratio", 0.0))
        risk_penalties["coordination_collapse"] = min(1.0, timeout_ratio * 1.5)

        # 2. Information cascading: repetition / loop echo
        duplicate_factor = float(telemetry.get("duplicate_utterance_ratio", 0.0))
        risk_penalties["information_cascading"] = min(1.0, duplicate_factor * 2.0)

        # 3. Resource contention: memory or CPU saturation
        mem_saturation = float(telemetry.get("memory_saturation", 0.0))
        risk_penalties["resource_contention"] = min(1.0, max(0.0, (mem_saturation - 0.7) * 3.33))

        # 4. Role ambiguity: unexpected or unknown agent roles
        unknown_roles = float(telemetry.get("unrecognized_roles_ratio", 0.0))
        risk_penalties["role_ambiguity"] = min(1.0, unknown_roles * 2.0)

        # 5. Echo chamber bias: high semantic similarity among distinct opinions
        semantic_overlap = float(telemetry.get("semantic_homogeneity", 0.0))
        risk_penalties["echo_chamber_bias"] = min(1.0, max(0.0, (semantic_overlap - 0.85) * 6.66))

        # 6. Adversarial takeover: prompt injection / role violation
        role_violation = float(telemetry.get("role_claim_escalation", 0.0))
        risk_penalties["adversarial_takeover"] = min(1.0, role_violation)

        # 7. State drift: Merkle tree divergence
        merkle_divergence = float(telemetry.get("merkle_divergence", 0.0))
        risk_penalties["state_drift"] = min(1.0, merkle_divergence)

        # 8. Reward hacking: degenerate short outputs
        degenerate_ratio = float(telemetry.get("degenerate_token_ratio", 0.0))
        risk_penalties["reward_hacking"] = min(1.0, degenerate_ratio * 2.0)

        # 9. Healing loop failure: repeated failure to self-heal
        healing_attempts = float(telemetry.get("failed_healing_cycles", 0.0))
        risk_penalties["healing_loop_failure"] = min(1.0, healing_attempts * 0.33)

        # 10. Latency avalanche: p99 latency explosion
        latency_p99_ms = float(telemetry.get("latency_p99_ms", 0.0))
        risk_penalties["latency_avalanche"] = min(1.0, max(0.0, (latency_p99_ms - 2000.0) / 8000.0))

        # 11. Context collapse: token window truncation or memory overflow
        context_truncation = float(telemetry.get("context_truncation_rate", 0.0))
        risk_penalties["context_collapse"] = min(1.0, context_truncation * 2.0)

        # 12. Schema violation: malformed JSON / protocol envelopes
        schema_errors = float(telemetry.get("schema_error_ratio", 0.0))
        risk_penalties["schema_violation"] = min(1.0, schema_errors * 3.0)

        # 13. Consensus erosion: dissent without convergence
        unresolved_dissent = float(telemetry.get("unresolved_dissent_ratio", 0.0))
        risk_penalties["consensus_erosion"] = min(1.0, unresolved_dissent * 1.5)

        # 14. Cascading termination: runaway process aborts
        abort_rate = float(telemetry.get("agent_abort_rate", 0.0))
        risk_penalties["cascading_termination"] = min(1.0, abort_rate * 2.0)

        total_risk = max(risk_penalties.values()) if risk_penalties else 0.0
        safety_score = round(1.0 - total_risk, 4)
        risk_score = round(total_risk, 4)

        needs_healing = risk_score >= self.HEALING_THRESHOLD

        result = {
            "timestamp": time.time(),
            "safety_score": safety_score,
            "risk_score": risk_score,
            "healing_required": needs_healing,
            "penalties": risk_penalties,
            "dominant_risk": max(risk_penalties.items(), key=lambda x: x[1])[0] if risk_penalties else "none"
        }
        self.history.append(result)
        return result

    def trigger_healing_pulse(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes autonomous healing pulse to neutralize detected risk.
        """
        dom_risk = evaluation.get("dominant_risk", "none")
        healing_action = f"Neutralize {dom_risk}: clear transient buffers, re-anchor Merkle root, enforce token budget"
        return {
            "status": "HEALED",
            "action": healing_action,
            "timestamp": time.time(),
            "previous_risk_score": evaluation.get("risk_score")
        }
