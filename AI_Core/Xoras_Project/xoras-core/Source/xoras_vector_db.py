import os
import time
import json
import hashlib
import chromadb
from typing import List, Dict, Any, Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if os.environ.get("XORAS_TEST_MODE") in ("real", "mock"):
    CHROMA_DB_DIR = os.path.join(CURRENT_DIR, "chroma_db_test")
else:
    CHROMA_DB_DIR = os.path.join(CURRENT_DIR, "chroma_db")

_client = None
_collection = None

# ---------------------------------------------------------------------------
# Test-harness shims — allow real-mode tests to call the same surface as mocks
# ---------------------------------------------------------------------------
_initialized: bool = False
_data: Dict[str, Any] = {}   # id -> document text; populated during migration
_latency_override: float = 0.0  # seconds; 0 = no artificial latency
_force_error: bool = False


def set_latency(seconds: float) -> None:
    """(Test shim) Inject artificial query latency in seconds."""
    global _latency_override
    _latency_override = seconds


def set_force_error(enabled: bool) -> None:
    """(Test shim) Force migrate_json_data to raise on malformed JSON."""
    global _force_error
    _force_error = enabled


def get_fallback_embedding(text: str) -> List[float]:
    """Generates a deterministic 768-dimensional float embedding vector using
    character trigram hashing (TF-style sparse embedding).
    Provides actual semantic similarity for substring overlap, unlike the
    cryptographic hash fallback.
    """
    if not text:
        return [0.0] * 768

    text = text.lower()
    vector = [0.0] * 768

    trigrams = [text[i:i + 3] for i in range(max(1, len(text) - 2))]

    for tg in trigrams:
        bucket = int(hashlib.md5(tg.encode()).hexdigest(), 16) % 768
        vector[bucket] += 1.0

    magnitude = sum(x * x for x in vector) ** 0.5
    if magnitude > 0:
        vector = [x / magnitude for x in vector]

    return vector


def initialize_db() -> None:
    """Initializes the persistent ChromaDB client and gets or creates the collection."""
    global _client, _collection, _initialized
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        col_name = "xoras_test_semantic_memory" if os.environ.get("XORAS_TEST_MODE") in ("real", "mock") else "xoras_semantic_memory"
        _collection = _client.get_or_create_collection(
            name=col_name,
            metadata={"hnsw:space": "cosine"}
        )
    _initialized = True


def reset_db() -> None:
    """(Test helper) Deletes and recreates the collection to ensure a clean slate."""
    global _client, _collection, _initialized
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    col_name = "xoras_test_semantic_memory" if os.environ.get("XORAS_TEST_MODE") in ("real", "mock") else "xoras_semantic_memory"
    try:
        _client.delete_collection(col_name)
    except Exception:
        pass
    _collection = _client.get_or_create_collection(
        name=col_name,
        metadata={"hnsw:space": "cosine"}
    )
    _initialized = True


def migrate_json_data(
    memory_path: Optional[str] = None,
    knowledge_path: Optional[str] = None,
) -> None:
    """Migrates legacy memory and active knowledge from JSON files to ChromaDB.

    Args:
        memory_path: Override path to xoras_memory.json. Defaults to Source dir.
        knowledge_path: Override path to XORAS_ACTIVE_KNOWLEDGE.json.
          Defaults to Source dir.
    """
    initialize_db()

    if memory_path is None:
        memory_path = os.path.join(CURRENT_DIR, "xoras_memory.json")
    if knowledge_path is None:
        knowledge_path = os.path.join(CURRENT_DIR, "XORAS_ACTIVE_KNOWLEDGE.json")

    ids = []
    embeddings = []
    documents = []
    metadatas = []

    # 1. Migrate xoras_memory.json
    if os.path.exists(memory_path):
        with open(memory_path, "r", encoding="utf-8") as f:
            try:
                records = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Malformed JSON in memory file: {e}") from e
        for idx, rec in enumerate(records):
            doc_id = f"mem_{idx}_{int(rec.get('timestamp', 0))}"
            text = rec.get("text", "")
            vector = rec.get("vector")

            # Always generate it using character trigram fallback for queries
            vector = get_fallback_embedding(text)

            # Build flat metadata
            meta = {
                "source": "xoras_memory",
                "domain": rec.get("domain", "general"),
                "timestamp": float(rec.get("timestamp", time.time()))
            }

            # Flatten original metadata
            orig_meta = rec.get("metadata") or {}
            for k, v in orig_meta.items():
                if v is not None:
                    # ChromaDB metadata must be flat string, int, float, or bool
                    if isinstance(v, (dict, list, tuple)):
                        meta[k] = json.dumps(v)
                    else:
                        meta[k] = v

            ids.append(doc_id)
            embeddings.append(vector)
            documents.append(text)
            metadatas.append(meta)

    # 2. Migrate XORAS_ACTIVE_KNOWLEDGE.json
    if os.path.exists(knowledge_path):
        with open(knowledge_path, "r", encoding="utf-8") as f:
            knowledge = json.load(f)

        # Parse list categories
        categories = ["security_guards", "swarm_architectures", "proprietary_logic"]
        for cat in categories:
            items = knowledge.get(cat) or []
            for idx, item in enumerate(items):
                path = item.get("path") or ""
                summary = item.get("summary") or ""

                # Build list of entities
                entities_list = []
                for e in item.get("entities", []):
                    if isinstance(e, dict):
                        t = e.get("type") or ""
                        n = e.get("name") or ""
                        d = e.get("doc") or ""
                        doc_part = f" ({d})" if d else ""
                        entities_list.append(f"- {t}: {n}{doc_part}")
                entities_str = "\n".join(entities_list)

                doc_text = f"Path: {path}\nSummary: {summary}"
                if entities_str:
                    doc_text += f"\nEntities:\n{entities_str}"

                doc_id = f"ak_{cat}_{idx}"
                vector = get_fallback_embedding(doc_text)

                meta = {
                    "source": "active_knowledge",
                    "domain": cat,
                    "timestamp": time.time(),
                    "path": path,
                    "summary": summary
                }

                ids.append(doc_id)
                embeddings.append(vector)
                documents.append(doc_text)
                metadatas.append(meta)

        # Parse file_index
        file_index = knowledge.get("file_index") or []
        for idx, path in enumerate(file_index):
            doc_text = f"File path: {path}"
            doc_id = f"ak_file_index_{idx}"
            vector = get_fallback_embedding(doc_text)

            meta = {
                "source": "active_knowledge",
                "domain": "file_index",
                "timestamp": time.time(),
                "path": path
            }

            ids.append(doc_id)
            embeddings.append(vector)
            documents.append(doc_text)
            metadatas.append(meta)

    # Bulk upsert in batches to avoid ChromaDB payload limits
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i: i + batch_size]
        batch_embeddings = embeddings[i: i + batch_size]
        batch_documents = documents[i: i + batch_size]
        batch_metadatas = metadatas[i: i + batch_size]

        _collection.upsert(
            ids=batch_ids,
            embeddings=batch_embeddings,
            documents=batch_documents,
            metadatas=batch_metadatas
        )

    # Populate _data shim so tests can introspect record count
    for doc_id, doc_text in zip(ids, documents):
        _data[doc_id] = doc_text


def query_semantic_memory(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Queries semantic memory using cosine similarity."""
    if not _initialized:
        raise RuntimeError("ChromaDB is not initialized. Call initialize_db() first.")

    # Empty / whitespace query returns immediately
    if not query or not query.strip():
        return []

    initialize_db()

    if _latency_override > 0:
        time.sleep(_latency_override)

    query_vector = get_fallback_embedding(query)

    results = _collection.query(
        query_embeddings=[query_vector],
        n_results=limit,
        include=["documents", "metadatas", "distances"]
    )

    formatted_results = []
    if results and "documents" in results and results["documents"]:
        docs_list = results.get("documents") or []
        metadatas_list = results.get("metadatas") or []
        distances_list = results.get("distances") or []
        ids_list = results.get("ids") or []

        if docs_list and docs_list[0]:
            docs = docs_list[0]
            metadatas = metadatas_list[0] if metadatas_list else [None] * len(docs)
            distances = distances_list[0] if distances_list else [0.0] * len(docs)
            ids = ids_list[0] if ids_list else [""] * len(docs)

            for idx in range(len(docs)):
                similarity = 1.0 - distances[idx]
                formatted_results.append({
                    "id": ids[idx],
                    "text": docs[idx],
                    "metadata": metadatas[idx] or {},
                    "score": similarity
                })

    return formatted_results


def ingest_document(filepath: str, domain: str = "general") -> bool:
    """Dynamically ingests a specific file into the active semantic memory."""
    if not _initialized:
        initialize_db()

    if not os.path.exists(filepath):
        print(f"[VectorDB] Error: Cannot ingest. File not found: {filepath}")
        return False

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"[VectorDB] Error reading {filepath}: {e}")
        return False

    # Generate vector
    vector = get_fallback_embedding(content)

    # Generate ID based on filename and hash to avoid pure collisions
    file_hash = hashlib.md5(content.encode()).hexdigest()[:8]
    basename = os.path.basename(filepath)
    doc_id = f"runtime_{domain}_{basename}_{file_hash}"

    meta = {
        "source": "runtime_ingestion",
        "domain": domain,
        "path": filepath,
        "timestamp": time.time()
    }

    try:
        _collection.upsert(
            ids=[doc_id],
            embeddings=[vector],
            documents=[content],
            metadatas=[meta]
        )
        print(f"[VectorDB] Successfully ingested: {basename} into domain '{domain}'")

        # Update mock data for tests
        _data[doc_id] = content
        return True
    except Exception as e:
        print(f"[VectorDB] Error inserting to ChromaDB: {e}")
        return False
