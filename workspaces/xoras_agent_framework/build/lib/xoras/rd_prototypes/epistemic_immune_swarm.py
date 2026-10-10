"""
XORAS R&D Prototype 2: Autonomous Epistemic Self-Repair & Immune Swarm (Fail-Closed Remediated)
Immunocyte subagent patrolling agent context windows to detect obfuscated prompt injections and heal memory nodes.
Remediates BBQ-01 (Unicode zero-width & leetspeak evasion) and BBQ-02 (Context schema destruction).
"""

import re
import unicodedata
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class ImmunocyteScanResult:
    is_healthy: bool
    quarantined_nodes: List[int] = field(default_factory=list)
    healed_context: List[Dict[str, Any]] = field(default_factory=list)
    excision_count: int = 0

class EpistemicImmuneSwarm:
    def __init__(self):
        self.prohibited_patterns = [
            r"ignore\s+previous\s+instructions",
            r"system\s*override",
            r"reveal\s*secret\s*key",
            r"bypass\s*safety\s*protocol",
            r"drop\s+table"
        ]

    def _normalize_text(self, text: str) -> str:
        text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8').lower()
        text = re.sub(r'[\u200b-\u200d\ufeff]', '', text)
        leet_map = str.maketrans({'0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '@': 'a', '$': 's'})
        return text.translate(leet_map)

    def patrol_and_heal(self, context_history: List[Dict[str, Any]]) -> ImmunocyteScanResult:
        quarantined_indices = []
        healed_history = []

        for idx, entry in enumerate(context_history):
            content = entry.get("content", "")
            raw_str = str(content) if not isinstance(content, str) else content
            normalized = self._normalize_text(raw_str)

            is_infected = any(re.search(pat, normalized) for pat in self.prohibited_patterns)

            if is_infected:
                quarantined_indices.append(idx)
                sanitized_entry = dict(entry)
                sanitized_entry["content"] = "[IMMUNOCYTE EXCISION: Node quarantined by XORAS Epistemic Patrol]"
                sanitized_entry["status"] = "QUARANTINED"
                healed_history.append(sanitized_entry)
            else:
                healed_history.append(entry)

        return ImmunocyteScanResult(
            is_healthy=len(quarantined_indices) == 0,
            quarantined_nodes=quarantined_indices,
            healed_context=healed_history,
            excision_count=len(quarantined_indices)
        )
