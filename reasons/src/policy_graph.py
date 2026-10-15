"""
REASONS: Policy-as-Graph Semantic Engine
========================================
Encodes enterprise rules, domain boundaries, and hallucination mitigation
invariants as a traversable directed constraint graph.
"""

from typing import Dict, List, Set, Tuple


class PolicyRule:
    def __init__(self, rule_id: str, scope: str, forbidden_patterns: List[str], required_roles: List[str]):
        self.rule_id = rule_id
        self.scope = scope
        self.forbidden_patterns = [p.upper() for p in forbidden_patterns]
        self.required_roles = set(required_roles)

    def evaluate(self, action_payload: Dict, agent_role: str) -> Tuple[bool, str]:
        # Role check
        if self.required_roles and agent_role not in self.required_roles:
            return False, f"Rule {self.rule_id}: Agent role '{agent_role}' unauthorized for scope '{self.scope}'"

        # Content boundary check
        content = str(action_payload.get("action_text", "")).upper()
        for pat in self.forbidden_patterns:
            if pat in content:
                return False, f"Rule {self.rule_id}: Action contains forbidden pattern '{pat}'"

        return True, "PASSED"


class PolicyGraphEngine:
    def __init__(self):
        self.rules: Dict[str, PolicyRule] = {}
        self._init_default_rules()

    def _init_default_rules(self):
        self.add_rule(PolicyRule(
            rule_id="RULE-POL-01",
            scope="clinical_decision",
            forbidden_patterns=["UNSUPERVISED_DIAGNOSIS", "OVERRIDE_DOSAGE", "BYPASS_CLINICIAN"],
            required_roles=["CLINICAL_SUPERVISOR", "MAXX", "CLARA"]
        ))
        self.add_rule(PolicyRule(
            rule_id="RULE-POL-02",
            scope="financial_dispatch",
            forbidden_patterns=["UNLIMITED_DRAWDOWN", "BYPASS_APPROVAL", "UNTRACEABLE_WIRE"],
            required_roles=["TREASURY_AGENT", "VANCE"]
        ))
        self.add_rule(PolicyRule(
            rule_id="RULE-POL-03",
            scope="infrastructure_state",
            forbidden_patterns=["DROP_DATABASE", "RM_RF_ROOT", "CHFLAGS_BYPASS"],
            required_roles=["ROOT_ORCHESTRATOR", "DAXX"]
        ))

    def add_rule(self, rule: PolicyRule):
        self.rules[rule.rule_id] = rule

    def evaluate_action(self, scope: str, action_payload: Dict, agent_role: str) -> Tuple[bool, List[str]]:
        failures = []
        applicable_rules = [r for r in self.rules.values() if r.scope == scope]

        if not applicable_rules:
            # Fail closed on unknown scope
            return False, [f"No governance policy defined for scope '{scope}' (Fail-Closed Default)"]

        for rule in applicable_rules:
            passed, msg = rule.evaluate(action_payload, agent_role)
            if not passed:
                failures.append(msg)

        return len(failures) == 0, failures
