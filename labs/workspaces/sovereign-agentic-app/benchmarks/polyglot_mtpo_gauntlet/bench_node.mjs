import { Worker, isMainThread, parentPort, workerData } from "node:worker_threads";
import { fileURLToPath } from "node:url";

const HEXCELL_SLOTS = 6;
const TOTAL_OPS = 1000000;
const NUM_THREADS = 8;
const OPS_PER_THREAD = TOTAL_OPS / NUM_THREADS;

// Layout in BigInt64Array:
// [0..5]: active slots
// [6..11]: shadow slots
// [12]: total_committed
// [13]: total_compensated
// [14]: total_retries

if (isMainThread) {
  const sab = new SharedArrayBuffer(16 * 8); // 16 BigInt64 elements
  const ring = new BigInt64Array(sab);

  const t0 = performance.now();
  let completed = 0;
  const workers = [];

  for (let tid = 0; tid < NUM_THREADS; tid++) {
    const w = new Worker(fileURLToPath(import.meta.url), {
      workerData: { tid, sab },
    });
    w.on("message", () => {
      completed++;
      if (completed === NUM_THREADS) {
        const elapsedMs = performance.now() - t0;
        const elapsedSec = elapsedMs / 1000.0;
        const opsSec = TOTAL_OPS / elapsedSec;
        const avgLatencyNs = (elapsedSec / TOTAL_OPS) * 1e9;
        const mem = process.memoryUsage();
        const rssMB = mem.rss / (1024 * 1024);

        const out = {
          language: "Node.js (Atomics + SharedArrayBuffer)",
          standard: "V8 Engine / ECMAScript Shared Memory",
          total_ops: TOTAL_OPS,
          threads: NUM_THREADS,
          elapsed_ms: Number(elapsedMs.toFixed(2)),
          throughput_ops_sec: Math.round(opsSec),
          avg_latency_ns: Number(avgLatencyNs.toFixed(2)),
          total_committed: Number(Atomics.load(ring, 12)),
          contention_retries: Number(Atomics.load(ring, 14)),
          peak_rss_mb: Number(rssMB.toFixed(2)),
        };

        console.log(JSON.stringify(out, null, 2));
      }
    });
    workers.push(w);
  }
} else {
  const { tid, sab } = workerData;
  const ring = new BigInt64Array(sab);
  const startTx = BigInt(tid * OPS_PER_THREAD + 1);
  let localRetries = 0n;

  for (let i = 0; i < OPS_PER_THREAD; i++) {
    const txId = startTx + BigInt(i);
    const slot = Number(txId % BigInt(HEXCELL_SLOTS));
    const newVal = 0xbeaf000000000000n | txId;

    while (true) {
      const initial = Atomics.load(ring, slot);
      Atomics.store(ring, 6 + slot, newVal);

      const oldVal = Atomics.compareExchange(ring, slot, initial, newVal);
      if (oldVal === initial) {
        Atomics.add(ring, 12, 1n);
        break;
      } else {
        Atomics.store(ring, 6 + slot, initial);
        Atomics.add(ring, 13, 1n);
        localRetries++;
      }
    }
  }

  Atomics.add(ring, 14, localRetries);
  parentPort?.postMessage("DONE");
}
