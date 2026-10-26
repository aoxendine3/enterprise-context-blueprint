"""
XORAS AGENT FRAMEWORK: DEEP INVARIANT & CONCURRENCY TORTURE GAUNTLET
Tests for dark modules: MerkleDAG, MTPO Saga Ring, and Polyglot IPC Bridge
"""

import pytest
import concurrent.futures
from xoras.merkle_dag import MerkleDAGNode, ContextLineageDAGEngine, canonical_json
from xoras.mtpo import HexCellRing, HEXCELL_SLOTS, SagaState
from xoras.ipc.polyglot_ipc_bridge import PolyglotIPCBridge, IPCExecutionResult

# ==============================================================================
# 1. MERKLE DAG LINEAGE & ANTI-REPLAY TORTURE
# ==============================================================================

def test_merkle_dag_node_creation_and_canonical_hash():
    payload = {"agent": "maxx", "status": "nominal", "step": 1}
    node = MerkleDAGNode("node_001", [], payload)
    assert node.node_id == "node_001"
    assert len(node.payload_hash) == 64
    assert len(node.state_hash) == 64
    assert node.to_dict()["node_id"] == "node_001"

def test_merkle_dag_anti_replay_quarantine():
    engine = ContextLineageDAGEngine()
    payload = {"metric": "latency", "val": 42}
    
    # First commit succeeds
    success, state_hash, err = engine.commit("node_01", [], payload)
    assert success is True
    assert state_hash is not None
    assert err is None
    
    # Replay attack with identical payload must be quarantined
    success2, hash2, err2 = engine.commit("node_02", ["node_01"], payload)
    assert success2 is False
    assert hash2 is None
    assert err2 == "UNLINKED_REPLAY_QUARANTINED"
    assert len(engine.quarantine_ledger) == 1
    assert engine.quarantine_ledger[0]["event"] == "REPLAY_DETECTED"

def test_merkle_dag_missing_parent_rejection():
    engine = ContextLineageDAGEngine()
    payload = {"data": "test"}
    success, h, err = engine.commit("node_child", ["ghost_parent_999"], payload)
    assert success is False
    assert "PARENT_NODE_NOT_FOUND" in err

def test_merkle_dag_dynamic_root_calculation():
    engine = ContextLineageDAGEngine()
    assert engine.get_dynamic_merkle_root() == "0" * 64
    
    engine.commit("root_0", [], {"p": 0})
    root1 = engine.get_dynamic_merkle_root()
    assert len(root1) == 64
    
    engine.commit("child_1", ["root_0"], {"p": 1})
    root2 = engine.get_dynamic_merkle_root()
    assert root1 != root2

# ==============================================================================
# 2. MTPO CONCURRENCY & DETERMINISTIC SAGA TORTURE
# ==============================================================================

def test_mtpo_hexcell_ring_saga_commit_and_compensate():
    ring = HexCellRing()
    
    # Successful commit
    committed = ring.execute_saga(slot_idx=0, tx_id=101, new_val=999, inject_fault=False)
    assert committed is True
    assert ring.read(0) == 999
    assert ring.total_committed == 1
    assert ring.total_compensated == 0
    
    # Injected fault triggers automatic rollback
    failed = ring.execute_saga(slot_idx=0, tx_id=102, new_val=111, inject_fault=True)
    assert failed is False
    assert ring.read(0) == 999  # Preserved original value
    assert ring.total_committed == 1
    assert ring.total_compensated == 1

def test_mtpo_hexcell_ring_bounds_checking():
    ring = HexCellRing()
    with pytest.raises(ValueError):
        ring.read(-1)
    with pytest.raises(ValueError):
        ring.read(HEXCELL_SLOTS)
    with pytest.raises(ValueError):
        ring.execute_saga(HEXCELL_SLOTS, 1, 10)

def test_mtpo_high_concurrency_race_free():
    ring = HexCellRing()
    num_threads = 16
    iterations_per_thread = 500

    def worker(t_id: int):
        for i in range(iterations_per_thread):
            slot = (t_id + i) % HEXCELL_SLOTS
            fault = (i % 7 == 0)
            ring.execute_saga(slot, t_id * 1000 + i, i, inject_fault=fault)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker, t) for t in range(num_threads)]
        for f in concurrent.futures.as_completed(futures):
            f.result()

    total_ops = num_threads * iterations_per_thread
    assert ring.total_committed + ring.total_compensated == total_ops
    assert ring.total_committed > 0
    assert ring.total_compensated > 0

# ==============================================================================
# 3. POLYGLOT IPC BRIDGE TORTURE
# ==============================================================================

def test_polyglot_ipc_bridge_missing_binary_rejection():
    bridge = PolyglotIPCBridge()
    res = bridge.execute_binary_ipc("/nonexistent/binary_target", ["--flag"], runtime_type="wasm")
    assert res.success is False
    assert "not found" in res.stderr
    assert res.exit_code == 1

def test_polyglot_ipc_bridge_supported_runtimes_and_structure():
    bridge = PolyglotIPCBridge()
    assert "wasm" in bridge.SUPPORTED_RUNTIMES
    assert "rust_binary" in bridge.SUPPORTED_RUNTIMES
    assert hasattr(bridge, "execute_binary_ipc")
    assert hasattr(bridge, "ast_engine")
