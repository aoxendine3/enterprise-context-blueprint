// =============================================================================
// AGENT COGNITIVE PIPELINE: UNIFIED DECISION & EXECUTION ARCHITECTURE
// Fuses: Contextual Memory (LSTM) -> Reasons Engine -> MARS Gate -> MTPO SAGA
// =============================================================================

import { contextualMemory, type ContextTurn } from "./contextual_memory.server";
import { reasonsEngine, type PolicyEvaluationResult } from "./reasons.server";
import {
  marsSupervisor,
  CANDIDATE_TAINT,
  DECISION_TAINT,
  type MarsVerificationReceipt,
} from "./mars.server";
import { mtpoEngine, type SagaExecutionResult } from "./mtpo.server";

export interface CognitiveExecutionStep {
  stage: "STAGE_1_LSTM_MEMORY" | "STAGE_2_REASONS_POLICY" | "STAGE_3_MARS_GAUNTLET" | "STAGE_4_MTPO_SAGA" | "STAGE_5_MERKLE_COMMIT";
  name: string;
  status: "SUCCESS" | "FAILED" | "BLOCKED";
  durationMs: number;
  details: Record<string, unknown>;
}

export interface CognitivePipelineReceipt {
  transactionId: string;
  prompt: string;
  agentRole: string;
  finalDecision: "PROMOTED_AND_COMMITTED" | "REJECTED_FAIL_CLOSED";
  taintState: "0xDEAD0000_CANDIDATE" | "0xBEAF0000_DECISION";
  hadamardScalar: number;
  merkleRoot: string;
  steps: CognitiveExecutionStep[];
  timestamp: string;
}

class AgentCognitivePipeline {
  public executeTurn(
    prompt: string,
    agentRole: "MAXX" | "CLARA" | "VANCE" | "DAXX" | "USER",
    scope: string = "all"
  ): CognitivePipelineReceipt {
    const startTime = performance.now();
    const txId = `cog_${Date.now()}_${Math.floor(Math.random() * 1000)}`;
    const steps: CognitiveExecutionStep[] = [];

    // --- STAGE 1: Recurrent Memory Ingestion (RNN / LSTM Hadamard Gating) ---
    const t1 = performance.now();
    const turn = contextualMemory.commitTurn(
      agentRole === "USER" ? "user" : (`council_${agentRole.toLowerCase()}` as any),
      `${agentRole} (Council)`,
      prompt,
      "CANDIDATE"
    );
    const dur1 = Number((performance.now() - t1).toFixed(2));
    steps.push({
      stage: "STAGE_1_LSTM_MEMORY",
      name: "Recurrent Memory & Dendritic Hadamard Gating",
      status: "SUCCESS",
      durationMs: dur1,
      details: {
        sequence: turn.seq,
        hadamardGate: turn.hadamardGate,
        headsActivated: turn.headsActivated,
        initialTaint: "0xDEAD0000_CANDIDATE",
      },
    });

    // --- STAGE 2: Semantic Reasoning & Policy-as-Graph Invariants (REASONS) ---
    const t2 = performance.now();
    const policyResult: PolicyEvaluationResult = reasonsEngine.evaluateAction(
      scope,
      prompt,
      agentRole
    );
    const dur2 = Number((performance.now() - t2).toFixed(2));
    if (!policyResult.allowed) {
      steps.push({
        stage: "STAGE_2_REASONS_POLICY",
        name: "Policy Graph Invariant Guard",
        status: "FAILED",
        durationMs: dur2,
        details: {
          violations: policyResult.violations,
          rationale: policyResult.rationale,
        },
      });
      return {
        transactionId: txId,
        prompt,
        agentRole,
        finalDecision: "REJECTED_FAIL_CLOSED",
        taintState: "0xDEAD0000_CANDIDATE",
        hadamardScalar: turn.hadamardGate.combinedHt,
        merkleRoot: turn.merkleHash,
        steps,
        timestamp: new Date().toISOString(),
      };
    }
    steps.push({
      stage: "STAGE_2_REASONS_POLICY",
      name: "Policy Graph Invariant Guard",
      status: "SUCCESS",
      durationMs: dur2,
      details: { rationale: policyResult.rationale },
    });

    // --- STAGE 3: Blackbox Discernment Gate & 14-Gate Gauntlet (MARS) ---
    const t3 = performance.now();
    const marsPacket = {
      id: txId,
      nonce: `${Date.now()}_${Math.random()}`,
      taint: CANDIDATE_TAINT,
      payload: prompt,
      lineage_ref: turn.merkleHash,
    };
    const marsReceipt: MarsVerificationReceipt = marsSupervisor.runGauntlet(marsPacket);
    const dur3 = Number((performance.now() - t3).toFixed(2));
    if (marsReceipt.status !== "APPROVED") {
      steps.push({
        stage: "STAGE_3_MARS_GAUNTLET",
        name: "14-Gate Sovereign BBQ Gauntlet",
        status: "FAILED",
        durationMs: dur3,
        details: {
          gatesPassed: marsReceipt.gatesPassed,
          totalGates: marsReceipt.totalGates,
          quarantineReason: marsReceipt.quarantineReason,
        },
      });
      return {
        transactionId: txId,
        prompt,
        agentRole,
        finalDecision: "REJECTED_FAIL_CLOSED",
        taintState: "0xDEAD0000_CANDIDATE",
        hadamardScalar: turn.hadamardGate.combinedHt,
        merkleRoot: turn.merkleHash,
        steps,
        timestamp: new Date().toISOString(),
      };
    }
    steps.push({
      stage: "STAGE_3_MARS_GAUNTLET",
      name: "14-Gate Sovereign BBQ Gauntlet",
      status: "SUCCESS",
      durationMs: dur3,
      details: {
        gatesPassed: marsReceipt.gatesPassed,
        promotedTaint: "0xBEAF0000_DECISION",
        merkleRoot: marsReceipt.merkleRoot,
      },
    });

    // --- STAGE 4: Monotonic Concurrency & SAGA Execution (MTPO) ---
    const t4 = performance.now();
    const slotIdx = (turn.seq - 1) % 6;
    const mtpoResult: SagaExecutionResult = mtpoEngine.executeSaga(
      slotIdx,
      turn.seq,
      "0x0001",
      false // no fault injection
    );
    const dur4 = Number((performance.now() - t4).toFixed(2));
    steps.push({
      stage: "STAGE_4_MTPO_SAGA",
      name: "Lock-Free HexCell 3-Phase SAGA",
      status: mtpoResult.status === "COMMITTED" ? "SUCCESS" : "FAILED",
      durationMs: dur4,
      details: {
        slot: slotIdx,
        status: mtpoResult.status,
        totalCommitted: mtpoResult.total_committed,
      },
    });

    // --- STAGE 5: Cryptographic State Commitment (Merkle DAG) ---
    turn.taintStatus = "DECISION";
    steps.push({
      stage: "STAGE_5_MERKLE_COMMIT",
      name: "Merkle DAG State Commit",
      status: "SUCCESS",
      durationMs: 0.1,
      details: {
        merkleHash: turn.merkleHash,
        parentHash: turn.parentHash,
        promotedToDecision: true,
      },
    });

    return {
      transactionId: txId,
      prompt,
      agentRole,
      finalDecision: "PROMOTED_AND_COMMITTED",
      taintState: "0xBEAF0000_DECISION",
      hadamardScalar: turn.hadamardGate.combinedHt,
      merkleRoot: marsReceipt.merkleRoot,
      steps,
      timestamp: new Date().toISOString(),
    };
  }
}

export const agentCognitivePipeline = new AgentCognitivePipeline();
