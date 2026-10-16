/**
 * MTPO: Monotonic Trajectory Pre-Order Server Singleton
 * ====================================================
 * High-performance Node.js wrapper around C11 lock-free HexCellRing engine
 * (native/mtpo_tool -> native/libmtpo_engine.dylib -> POSIX SHM /mtpo_hexcell_ring).
 *
 * Provides atomic CAS 3-Phase Saga coordination directly to Remix loaders & actions.
 */

import { execFileSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  marsSupervisor,
  CANDIDATE_TAINT,
  DECISION_TAINT,
  type MarsVerificationReceipt,
} from "./mars.server";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const APP_ROOT = path.resolve(__dirname, "..");
const MTPO_TOOL_PATH = path.join(APP_ROOT, "native", "mtpo_tool");

export interface SlotState {
  slot: number;
  active: string;
  shadow: string;
}

export interface RingState {
  status: string;
  slots: SlotState[];
  total_committed: number;
  total_compensated: number;
}

export interface SagaExecutionResult {
  status: "COMMITTED" | "COMPENSATED_ROLLBACK" | "ERROR";
  success: boolean;
  slot_idx: number;
  tx_id: number;
  active_val: string;
  shadow_val: string;
  total_committed: number;
  total_compensated: number;
  error?: string;
}

export interface PipelineExecutionReceipt {
  success: boolean;
  action: string;
  slotIdx: number;
  txId: number;
  mars: MarsVerificationReceipt;
  mtpo?: SagaExecutionResult;
  timestamp: string;
}

let txSequence = 1000;

class MtpoEngineSingleton {
  constructor() {
    this.ensureInitialized();
  }

  private ensureInitialized() {
    try {
      execFileSync(MTPO_TOOL_PATH, ["init"], { encoding: "utf-8" });
    } catch (err) {
      console.error("[MTPO] Failed to initialize ring:", err);
    }
  }

  public getRingState(): RingState {
    try {
      const output = execFileSync(MTPO_TOOL_PATH, ["read"], { encoding: "utf-8" });
      return JSON.parse(output) as RingState;
    } catch (err) {
      console.error("[MTPO] Failed to read ring state:", err);
      return {
        status: "ERROR",
        slots: Array.from({ length: 6 }, (_, i) => ({
          slot: i,
          active: "0x0000000000000000",
          shadow: "0x0000000000000000",
        })),
        total_committed: 0,
        total_compensated: 0,
      };
    }
  }

  public executeSaga(
    slotIdx: number,
    txId: number,
    newValHex: string,
    injectFault = false,
  ): SagaExecutionResult {
    try {
      const faultArg = injectFault ? "1" : "0";
      const output = execFileSync(
        MTPO_TOOL_PATH,
        ["execute", slotIdx.toString(), txId.toString(), newValHex, faultArg],
        { encoding: "utf-8" },
      );
      return JSON.parse(output) as SagaExecutionResult;
    } catch (err: any) {
      if (err.stdout) {
        try {
          return JSON.parse(err.stdout) as SagaExecutionResult;
        } catch {
          // ignore
        }
      }
      return {
        status: "ERROR",
        success: false,
        slot_idx: slotIdx,
        tx_id: txId,
        active_val: "0x0000000000000000",
        shadow_val: "0x0000000000000000",
        total_committed: 0,
        total_compensated: 0,
        error: String(err),
      };
    }
  }

  /**
   * Complete Pipeline Execution:
   * 1. Evaluates candidate payload against the 14-Gate MARS Gauntlet & Trinity Quorum
   * 2. If approved, promotes candidate taint (0xDEAD0000) to decision taint (0xBEAF0000)
   * 3. Executes atomic 3-Phase SAGA on native C11 HexCell memory ring slot
   * 4. Fails closed with zero memory mutation if any gate fails
   */
  public processVerifiedAction(
    actionName: string,
    payloadData: Record<string, unknown>,
    slotIdx = 0,
    injectFault = false,
  ): PipelineExecutionReceipt {
    const txId = ++txSequence;
    const nonce = `nonce_${Date.now()}_${Math.random().toString(36).substring(2, 10)}`;
    const lineageRef = `lineage_${Date.now()}_dag_node_${txId.toString(16).padStart(8, "0")}`;

    // Step 1: 14-Gate Sovereign BBQ Gauntlet Verification
    const marsReceipt = marsSupervisor.runGauntlet({
      id: `TX-${txId}`,
      nonce,
      taint: CANDIDATE_TAINT,
      payload: { action: actionName, ...payloadData },
      lineage_ref: lineageRef,
    });

    if (marsReceipt.status !== "APPROVED") {
      return {
        success: false,
        action: actionName,
        slotIdx,
        txId,
        mars: marsReceipt,
        timestamp: new Date().toISOString(),
      };
    }

    // Step 2: Encode 64-bit decision value: High 32 bits = 0xBEAF0000, Low 32 bits = txId
    const high32 = BigInt(DECISION_TAINT) << 32n;
    const low32 = BigInt(txId & 0xffffffff);
    const combinedValBigInt = high32 | low32;
    const newValHex = `0x${combinedValBigInt.toString(16)}`;

    // Step 3: MTPO 3-Phase SAGA Atomic Commit on Lock-Free Memory Lattice
    const mtpoResult = this.executeSaga(slotIdx, txId, newValHex, injectFault);

    return {
      success: mtpoResult.success,
      action: actionName,
      slotIdx,
      txId,
      mars: marsReceipt,
      mtpo: mtpoResult,
      timestamp: new Date().toISOString(),
    };
  }
}

export const mtpoEngine = new MtpoEngineSingleton();
