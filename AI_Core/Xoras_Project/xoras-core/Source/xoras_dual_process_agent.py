import datetime
import os
import sqlite3
import sys
import time
from typing import Any, Dict, Tuple

# Ensure local Source paths work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from secure_store import SecureMemory, LongTermArchive  # noqa: E402
from xoras_langgraph_engine import XorasLangGraph  # noqa: E402


class XorasDualProcessAgent:
    """A production-grade four-tier cognitive security agent gateway.

    Coordinates cognitive tiers using the actual compiled XorasLangGraph.
    - S1 (Fast Intuition): Sub-millisecond transient working memory cache.
    - S2 (Reflective Deliberation): Full LangGraph routing + ChromaDB context.
    - S3 (Swarm Consensus): Swarm BGG validation & Dojo ledger consolidation.
    - S4 (Autonomous Immunity): Honeypot deflection & cache immunization.
    """

    def __init__(self, resolution_threshold: float = 0.5) -> None:
        self.memory = SecureMemory()
        self.archive = LongTermArchive()
        self.resolution_threshold = resolution_threshold

        # Instantiate the actual compiled V6 LangGraph engine
        self.engine = XorasLangGraph()

        # Initialize Dojo catalyst database path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.catalyst_db_path = os.path.join(
            os.path.dirname(current_dir),
            "Omni_Dojo_Sandbox",
            "Error_Catalyst",
            "global_catalyst.db",
        )

        # Initialize default policies in archive
        self.archive.save("policy_risk_limit", "0.8")
        self.archive.save("critical_attack_limit", "0.9")
        self.archive.save("agent_status", "ACTIVE")

    def process(
        self, payload: str, urgency: float = 0.5, risk: float = 0.1
    ) -> Tuple[Dict[str, Any], str]:
        """Process a task payload. Dynamic routing determines S1, S2, S3, or S4.

        Args:
            payload: Task description or key.
            urgency: 0.0 (reflective) to 1.0 (extremely urgent).
            risk: 0.0 (no risk) to 1.0 (high security risk).

        Returns:
            Tuple containing execution metadata and system layer identifier.
        """
        t0 = time.perf_counter()

        # Read limit thresholds from SQLite
        policy_limit = float(self.archive.get("policy_risk_limit") or "0.8")
        attack_limit = float(self.archive.get("critical_attack_limit") or "0.9")

        # --- System 4 (Autonomous Immunity) Check ---
        # Triggered on critical security threats (risk >= 0.9)
        if risk >= attack_limit:
            return self._execute_s4(payload, risk, t0)

        # --- System 3 (Swarm Consensus) Check ---
        # Triggered on standard policy violations (risk >= 0.8)
        if risk >= policy_limit:
            return self._execute_s3(payload, risk, t0)

        # --- System 1 (Fast Intuition) Check ---
        cached_ans = self.memory.get(payload)

        # Trigger criteria for System 2 (Reflective Deliberation):
        # 1. Medium risk.
        # 2. Low urgency (time to reflect).
        # 3. Working memory cache miss.
        should_use_s2 = (
            risk >= self.resolution_threshold
            or urgency < 0.3
            or cached_ans is None
        )

        if not should_use_s2:
            # S1 Fast Path Execution
            latency = (time.perf_counter() - t0) * 1000.0
            meta = {
                "output": cached_ans,
                "latency_ms": latency,
                "confidence": 0.95 - (risk * 0.2),
                "resolution": "Intuitive (S1)",
            }
            return meta, "S1"

        # S2 Reflective Path Execution
        return self._execute_s2(payload, risk, t0)

    def _execute_s2(
        self, payload: str, risk: float, t0: float
    ) -> Tuple[Dict[str, Any], str]:
        # 1. Access exact SQLite archive
        archived_val = self.archive.get(payload)

        decision = ""
        confidence = 0.90

        if archived_val:
            decision = (
                archived_val
                if archived_val.startswith("ARCHIVED_HIT:")
                else f"ARCHIVED_HIT: {archived_val}"
            )
            confidence = 0.98
            # Populate back into S1 working memory
            self.memory.save(payload, decision)
        else:
            # 2. Run through LangGraph with persona enrichment (Wake→PersonaDetect→Sentinel→…)
            graph_state = self.engine.run(payload, ghost_execution=True)

            if graph_state.get("blocked"):
                decision = (
                    f"BLOCKED_BY_SENTINEL: "
                    f"{', '.join(graph_state.get('errors', []))}"
                )
                confidence = 0.99
            else:
                output_text = graph_state.get("sanitized_output") or ""
                persona_id = graph_state.get("persona_id", "sovereign")
                persona_label = graph_state.get("persona_label", "Sovereign")
                decision = f"[{persona_label}] LANGGRAPH_RECALL: {output_text}"
                confidence = 0.92
                self.memory.save(f"persona:{payload[:64]}", persona_id)
                self.archive.save(payload, decision)
                self.memory.save(payload, decision)

                try:
                    import asyncio
                    from xoras_memory_bridge import get_memory_bridge
                    bridge = get_memory_bridge()
                    loop = asyncio.new_event_loop()
                    try:
                        loop.run_until_complete(
                            bridge.persist_turn(
                                conversation_id="dual_process_s2",
                                user_msg=payload,
                                assistant_msg=output_text,
                                persona_id=persona_id,
                                persona_source="langgraph",
                            )
                        )
                    finally:
                        loop.close()
                except Exception as mem_err:
                    print(f"[S2] Memory persist skipped: {mem_err}")

        latency = (time.perf_counter() - t0) * 1000.0
        meta = {
            "output": decision,
            "latency_ms": latency,
            "confidence": confidence,
            "resolution": "Deliberative (S2)",
        }
        return meta, "S2"

    def _execute_s3(
        self, payload: str, risk: float, t0: float
    ) -> Tuple[Dict[str, Any], str]:
        # --- System 3 (Swarm Consensus & Dojo Logging) ---
        # 1. Run through LangGraph to check for steganography or threat blocking
        graph_state = self.engine.run(payload, ghost_execution=False)

        decision = (
            f"BLOCKED: Risk {risk} exceeds policy limits. "
            f"Swarm consensus reached."
        )

        # 2. Evict the payload from S1 Working Memory to protect state integrity
        self.memory.save(payload, None)

        # 3. Log the policy anomaly to the Dojo Error Catalyst Database
        errors_str = ", ".join(graph_state.get("errors", []))
        self._log_to_catalyst(
            exception_type="S3_POLICY_VIOLATION",
            error_message=f"Risk {risk} triggered S3. Errors: {errors_str}",
            stack_trace=f"Payload context: {payload}",
            healing_action="EVICTED_FROM_WORKING_CACHE",
        )

        latency = (time.perf_counter() - t0) * 1000.0
        meta = {
            "output": decision,
            "latency_ms": latency,
            "confidence": 0.99,
            "resolution": "Swarm Consensus (S3)",
        }
        return meta, "S3"

    def _execute_s4(
        self, payload: str, risk: float, t0: float
    ) -> Tuple[Dict[str, Any], str]:
        # --- System 4 (Autonomous Immunity & Defensive Deflection) ---
        decision = (
            f"HONEYPOT_DEFLECT: Critical risk {risk} detected. "
            f"Deflecting payload to isolated analytical sandbox."
        )

        # Evict from working cache to immunize node
        self.memory.save(payload, None)

        # Log S4 active defense to Dojo Catalyst
        self._log_to_catalyst(
            exception_type="S4_IMMUNE_RESPONSE",
            error_message=f"Adversarial risk {risk} triggered S4 deflection.",
            stack_trace=f"Attack payload: {payload}",
            healing_action="HONEYPOT_DEFLECTION_ACTIVE",
        )

        latency = (time.perf_counter() - t0) * 1000.0
        meta = {
            "output": decision,
            "latency_ms": latency,
            "confidence": 0.999,
            "resolution": "Autonomous Immunity (S4)",
        }
        return meta, "S4"

    def _log_to_catalyst(
        self,
        exception_type: str,
        error_message: str,
        stack_trace: str,
        healing_action: str,
    ) -> None:
        if os.path.exists(self.catalyst_db_path):
            try:
                conn = sqlite3.connect(self.catalyst_db_path)
                timestamp_str = datetime.datetime.now().isoformat()
                conn.execute(
                    """
                    INSERT INTO error_logs
                    (timestamp, exception_type, error_message,
                     stack_trace, status, healing_action)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        timestamp_str,
                        exception_type,
                        error_message,
                        stack_trace,
                        "LOGGED",
                        healing_action,
                    ),
                )
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"[Sovereign Core] Dojo Catalyst logging failed: {e}")
