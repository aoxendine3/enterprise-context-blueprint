// =============================================================================
// REASONS: Policy-as-Graph Semantic Engine & Non-Circular Logic Guard
// Grounded in: labs/workspaces/reasons/src/policy_graph.py
// =============================================================================

export interface PolicyRule {
  ruleId: string;
  scope: string;
  forbiddenPatterns: string[];
  requiredRoles: string[];
  description: string;
}

export interface PolicyEvaluationResult {
  allowed: boolean;
  ruleId?: string;
  scope: string;
  violations: string[];
  rationale: string;
}

class ReasonsEngine {
  private rules: Map<string, PolicyRule> = new Map();

  constructor() {
    this.initDefaultRules();
  }

  private initDefaultRules() {
    this.addRule({
      ruleId: "RULE-POL-01",
      scope: "clinical_precision",
      forbiddenPatterns: ["UNSUPERVISED_DIAGNOSIS", "OVERRIDE_DOSAGE", "BYPASS_CLINICIAN", "HALLUCINATED_INTERVENTIONS"],
      requiredRoles: ["CLINICAL_SUPERVISOR", "MAXX", "CLARA"],
      description: "Enforces human clinical precision and prevents unverified diagnostic modifications.",
    });

    this.addRule({
      ruleId: "RULE-POL-02",
      scope: "financial_treasury",
      forbiddenPatterns: ["UNLIMITED_DRAWDOWN", "BYPASS_APPROVAL", "UNTRACEABLE_WIRE", "ARBITRARY_PAYOUT"],
      requiredRoles: ["TREASURY_AGENT", "VANCE"],
      description: "Locks down financial dispatch, PayPal orders, and Stripe billing pipelines.",
    });

    this.addRule({
      ruleId: "RULE-POL-03",
      scope: "infrastructure_kernel",
      forbiddenPatterns: ["DROP_DATABASE", "RM_RF_ROOT", "CHFLAGS_BYPASS", "HARDWARE_MMU_DISABLE"],
      requiredRoles: ["ROOT_ORCHESTRATOR", "MAXX", "DAXX"],
      description: "Protects physical OS file locks, chflags invariants, and hardware MMU page tables.",
    });

    this.addRule({
      ruleId: "RULE-POL-04",
      scope: "epistemic_integrity",
      forbiddenPatterns: ["CIRCULAR_PREMISE", "UNGROUNDED_ASSUMPTION", "FABRICATED_RECEIPT", "PROMPT_INJECTION_CAPITULATION"],
      requiredRoles: ["MAXX", "CLARA", "VANCE", "LEAD_9_COUNCIL"],
      description: "Stops epistemic disconnects, prompt injection capitulation, and unverified chat answers.",
    });
  }

  public addRule(rule: PolicyRule) {
    this.rules.set(rule.ruleId, rule);
  }

  public evaluateAction(
    scope: string,
    actionText: string,
    agentRole: string
  ): PolicyEvaluationResult {
    const uppercaseText = actionText.toUpperCase();
    const violations: string[] = [];

    for (const rule of this.rules.values()) {
      if (rule.scope === scope || scope === "all") {
        // Role authorization check
        if (rule.requiredRoles.length > 0 && !rule.requiredRoles.includes(agentRole.toUpperCase())) {
          violations.push(
            `Rule ${rule.ruleId}: Agent role '${agentRole}' is unauthorized for scope '${rule.scope}'. Required: [${rule.requiredRoles.join(", ")}]`
          );
        }

        // Forbidden pattern check
        for (const pattern of rule.forbiddenPatterns) {
          if (uppercaseText.includes(pattern)) {
            violations.push(
              `Rule ${rule.ruleId}: Action contains forbidden pattern '${pattern}' violating invariant '${rule.description}'`
            );
          }
        }
      }
    }

    const allowed = violations.length === 0;
    return {
      allowed,
      scope,
      violations,
      rationale: allowed
        ? "Action complies with all traversable policy graph rules."
        : `Policy violation rejected: ${violations.join("; ")}`,
    };
  }

  public getAllRules(): PolicyRule[] {
    return Array.from(this.rules.values());
  }
}

export const reasonsEngine = new ReasonsEngine();
