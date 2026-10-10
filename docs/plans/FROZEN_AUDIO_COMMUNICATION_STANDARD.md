# XORAS System Standard: Frozen Audio Communication Protocol (Log Entry #081)

**Status:** IMMUTABLE SYSTEM LAW  
**Enforcement:** Mandatory across all Lead Council dispatches  

---

## 1. Specification & Parameters

1. **Hardware Core Optimization**:
   - `opts.intra_op_num_threads = 10` (Apple Silicon M4 Performance Cores)
   - `opts.inter_op_num_threads = 4`
   - `opts.execution_mode = ORT_SEQUENTIAL`
   - `opts.graph_optimization_level = ORT_ENABLE_ALL`
2. **Neural Waveform Silence Trimming**:
   - `nonzero_indices = np.where(np.abs(audio) > 5e-4)[0]`
   - Dual-boundary trimming: `audio = audio[nonzero_indices[0]:nonzero_indices[-1] + 1]`
   - Strips leading and trailing dead air at sample boundaries.
3. **Synthesis Cadence**:
   - `pause = np.zeros(0, dtype=np.float32)` (0ms inter-sentence padding)
   - `speed_arr = np.array([1.10], dtype=np.float32)` (1.10x speech rate)
4. **Canonical Dispatch Architecture**:
   - Executed strictly via `ops/scripts/agent_speak.sh`.
   - Enforced by `/tmp/coreaudio_single_speaker.lock` atomic OS `flock` queuing.
   - Zero wrapper scripts or process alterations permitted.
