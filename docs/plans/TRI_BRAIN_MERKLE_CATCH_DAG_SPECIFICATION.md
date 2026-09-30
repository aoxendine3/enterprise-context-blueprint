# XORAS ARCHITECTURAL SPECIFICATION: TRI-BRAIN VECTOR-MERKLE CATCH DAG SUBSTRATE
**Specification ID**: `SPEC-2026-MERKLE-CATCH-001`  
**Version**: `1.0.0-SOVEREIGN`  
**Effective Date**: `2026-09-29`  
**Authoritative Location**: `docs/plans/TRI_BRAIN_MERKLE_CATCH_DAG_SPECIFICATION.md`  

---

## 1. Executive Summary & Purpose

This specification defines the replacement of legacy flat markdown/JSON catch logs with the **Tri-Brain Vector-Merkle Catch DAG Substrate**. 

Instead of traditional static catch entries, every observation, decision, and spoken dispatch is committed as a node in an append-only, tamper-proof, semantically indexable Directed Acyclic Graph (DAG) spanning all 3 Brain Containers.

```mermaid
flowchart TD
    A["Root Merkle Catch Rolodex (memory/catch_log/CATCH_LOG.md)"] --> B["Brain Container 1: Short-Term Thread (memory/tri_brain/container_1/)"]
    A --> C["Brain Container 2: Long-Term Memory Fabric (memory/tri_brain/container_2/)"]
    A --> D["Brain Container 3: 18,432-D Vector Engine (memory/tri_brain/container_3/)"]
    
    subgraph Merkle Catch DAG Node
        E["Cryptographic Root: SHA-256 / BLAKE3"]
        F["Semantic Norm: 18,432-D Poincaré Vector"]
        G["Lifecycle Beat: INTENT | STATUS | RESULT | TRANSITION"]
        H["Agent Identity & Timestamp"]
    end
    
    B --> Merkle Catch DAG Node
    C --> Merkle Catch DAG Node
    D --> Merkle Catch DAG Node
```

---

## 2. Target Installation Directory Map

The Vector-Merkle Catch DAG engine installs across the following canonical locations:

| Brain Container | Primary Target Directory | Operational Role | Merkle DAG Component |
| --- | --- | --- | --- |
| **Master Overseer** | `memory/catch_log/CATCH_LOG.md` | Master Merkle Catch Rolodex & Global Root | Global SHA-256 Attestation Root ($R_{\text{global}}$) |
| **Brain Container 1** | `memory/tri_brain/container_1/` | Short-Term Execution & Speech Beats | Real-time 4-Beat Spoken Audio Receipts |
| **Brain Container 2** | `memory/tri_brain/container_2/` | Long-Term Knowledge Fabric | Poincaré Hyperbolic Semantic Folding |
| **Brain Container 3** | `memory/tri_brain/container_3/` | 18,432-D SIMD Vector Engine | Bare-Metal Vector Index & Node Leaves |

---

## 3. Node Structure: Cryptographic Root + Semantic Embedding

Traditional Merkle DAGs only commit to raw byte hashes. The **Xoras Merkle Catch DAG** pairs cryptographic integrity with semantic location:

```json
{
  "node_id": "sha256:8910426ab4793532c384b445279f60df02280b5305597c08894b16d4115ef47a",
  "parent_node_id": "sha256:0d2ac42319a3e1237e4d18e91a15fdd58172665e9fd7a03d855018ceefae7160",
  "timestamp": "2026-09-29T08:09:00Z",
  "brain_container": 1,
  "agent_id": "eden",
  "beat_type": "INTENT",
  "raw_payload": "Doctor Eden Veritas online. Human perspective active.",
  "cryptographic_hash": "8910426ab4793532c384b445279f60df02280b5305597c08894b16d4115ef47a",
  "vector_embedding_18432d": {
    "dim": 18432,
    "poincare_norm": 0.048219,
    "hyperbolic_curvature": -1.0
  }
}
```

---

## 4. Operational Principles

1. **Zero-Loss Append-Only Protocol**: Catch entries are never overwritten or deleted; new nodes are linked to parent hashes in the DAG.
2. **Synchronous Pure-Bash Audio Lock**: Every spoken beat is emitted synchronously via native `say` before the DAG node is committed.
3. **Quorum Certification**: A Merkle Catch block is certified only when signed by a minimum 3-Agent Deliberation Quorum (Lead, Critic, Human Perspective).
