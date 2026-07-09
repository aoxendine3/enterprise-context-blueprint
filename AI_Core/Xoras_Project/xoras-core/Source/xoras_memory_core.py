import json
import os
import aiohttp
import numpy as np
import time
import sqlite3
import asyncio


class TrajectoryCompressor:
    def __init__(self, target_max=1000, model="llama3.2"):
        self.target_max = target_max
        self.model = model
        self.endpoint = "http://192.168.1.133:11434/api/generate"

    async def compress(self, records):
        """
        Takes middle records, crushes them via LLM, and returns a single summary record.
        """
        text_to_compress = "\n".join([r['text'] for r in records])
        prompt = f"Summarize the following system trajectory telemetry densely, preserving all key numerical metrics and anomalies. Ignore routine logs.\n\n{text_to_compress}"

        try:
            async with aiohttp.ClientSession() as session:
                payload = {"model": self.model, "prompt": prompt, "stream": False}
                async with session.post(self.endpoint, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("response", "Compression failed.")
        except Exception as e:
            print(f"[COMPRESSOR] Error: {e}")
        return "Compression failed due to API error."


class MemoryCore:
    def __init__(self, db_path="xoras_memory.db", embed_model="nomic-embed-text:latest"):
        if not os.path.isabs(db_path):
            dir_path = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(dir_path, db_path)
        self.db_path = db_path
        self.embed_model = embed_model
        self.endpoint = "http://192.168.1.133:11434/api/embeddings"
        # List of dicts: {"text": str, "vector": list, "timestamp": float, "domain": str, "metadata": dict}
        self.memory_bank = []
        self.matrix = None
        self.matrix_norms = None

        # Initialize SQLite connection and WAL
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS memory_vectors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            vector JSON NOT NULL,
            timestamp REAL NOT NULL,
            domain TEXT NOT NULL,
            metadata JSON NOT NULL
        )
        """)

        self.embedding_cache = {}
        self.cache_max_size = 500
        self._load_memory()
        self._compressor = TrajectoryCompressor()
        self._compression_threshold = 1000
        self._compressing = False

    def count(self):
        return len(self.memory_bank)

    def _classify_domain(self, text, metadata=None):
        """Auto-classifies memory domain based on lexical patterns and metadata."""
        metadata = metadata or {}
        if metadata.get("type") == "dream_insight":
            return "dream"
        if metadata.get("type") in ("conversation", "persona_preference", "brainstorm"):
            return "conversation"
        if metadata.get("type") == "trajectory_summary":
            return "persona_learning"

        text_lower = text.lower()
        if any(indicator in text_lower for indicator in ["class ", "import ", "def ", "include ", "void ", "pragma ", "file:"]):
            return "codebase"
        elif any(indicator in text_lower for indicator in ["btcusdt", "ethusdt", "ticker", "arbitrage", "trade", "exchange", "spread"]):
            return "market_telemetry"
        elif any(indicator in text_lower for indicator in ["dream", "archetype", "subconscious", "consolidation"]):
            return "dream"
        elif any(indicator in text_lower for indicator in ["persona:", "tone:", "conversation turn"]):
            return "conversation"
        else:
            return "general"

    def _build_matrix_cache(self):
        """Builds a cached numpy matrix and norm array for hyper-fast vectorized calculations."""
        if self.memory_bank:
            self.matrix = np.array([m["vector"] for m in self.memory_bank])
            self.matrix_norms = np.linalg.norm(self.matrix, axis=1)
            # Prevent division by zero
            self.matrix_norms[self.matrix_norms == 0] = 1e-9
            print(
                f"[MEMORY-CORE] Pre-computed cache matrices. Shape: {self.matrix.shape}")
        else:
            self.matrix = None
            self.matrix_norms = None

    def _load_memory(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT text, vector, timestamp, domain, metadata FROM memory_vectors")
            rows = cursor.fetchall()

            for row in rows:
                self.memory_bank.append({
                    "text": row[0],
                    "vector": json.loads(row[1]),
                    "timestamp": row[2],
                    "domain": row[3],
                    "metadata": json.loads(row[4])
                })
            print(f"[MEMORY-CORE] Loaded {len(self.memory_bank)} memories from SQLite.")
            self._build_matrix_cache()
        except Exception as e:
            print(f"[MEMORY-CORE] Error loading memory: {e}")

    def _save_single_memory(self, text, vector, timestamp, domain, metadata):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT INTO memory_vectors (text, vector, timestamp, domain, metadata)
            VALUES (?, ?, ?, ?, ?)
            """, (text, json.dumps(vector), timestamp, domain, json.dumps(metadata)))
            self.conn.commit()
        except Exception as e:
            print(f"[MEMORY-CORE] Error saving memory: {e}")

    async def _get_embedding(self, text):
        """Fetches the mathematical vector for a piece of text using the small model."""
        if hasattr(self, "embedding_cache") and text in self.embedding_cache:
            return self.embedding_cache[text]

        vector = None
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"model": self.embed_model, "prompt": text}
                async with session.post(self.endpoint, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        vector = data.get("embedding", [])
        except Exception as e:
            print(f"[MEMORY-CORE] Exception: {e}")

        if not vector:
            # Fallback to deterministic algorithmic embedding for maximum OPSEC offline mode
            import hashlib
            h = hashlib.sha256(text.encode()).digest()
            vector = [(b / 255.0) - 0.5 for b in h] * 24  # 768-dimensional vector

        if hasattr(self, "embedding_cache"):
            if len(self.embedding_cache) >= self.cache_max_size:
                # Evict oldest item
                self.embedding_cache.pop(next(iter(self.embedding_cache)))
            self.embedding_cache[text] = vector

        return vector

    async def memorize(self, text, domain=None, metadata=None):
        """Encodes text into a vector and saves it horizontally."""
        meta = metadata or {}
        vector = await self._get_embedding(text)
        if vector:
            chosen_domain = domain if domain else self._classify_domain(text, meta)
            ts = time.time()
            self.memory_bank.append({
                "text": text,
                "vector": vector,
                "timestamp": ts,
                "domain": chosen_domain,
                "metadata": meta
            })
            self._save_single_memory(text, vector, ts, chosen_domain, meta)

            if len(self.memory_bank) > self._compression_threshold and not self._compressing:
                print("[MEMORY-CORE] Triggering Trajectory Compression...")
                asyncio.create_task(self._compress_memory())

            self._build_matrix_cache()
            print(
                f"[MEMORY-CORE] Memorized (Domain: {chosen_domain}): '{text[:30]}...'")

    async def _compress_memory(self):
        """Compress middle memory records into a dense trajectory summary."""
        if self._compressing or len(self.memory_bank) <= self._compression_threshold:
            return
        self._compressing = True
        try:
            keep_head = 100
            keep_tail = 100
            middle = self.memory_bank[keep_head:-keep_tail]
            if len(middle) < 50:
                return

            summary_text = await self._compressor.compress(middle)
            summary_meta = {
                "type": "trajectory_summary",
                "source": "trajectory_compressor",
                "records_compressed": len(middle),
            }
            await self.memorize(
                f"Trajectory summary: {summary_text}",
                domain="persona_learning",
                metadata=summary_meta,
            )
            print(f"[MEMORY-CORE] Compressed {len(middle)} records into summary.")
        except Exception as e:
            print(f"[MEMORY-CORE] Compression error: {e}")
        finally:
            self._compressing = False

    async def recall(self, query, domain=None, time_decay_lambda=None):
        """Searches memory horizontally within a specific domain partition, applying time decay if set."""
        if not self.memory_bank or self.matrix is None:
            return None

        # Step 1: Perform horizontal slicing (domain partition filtering)
        if domain:
            matching_indices = [i for i, m in enumerate(
                self.memory_bank) if m.get("domain") == domain]
        else:
            matching_indices = list(range(len(self.memory_bank)))

        if not matching_indices:
            print(f"[MEMORY-CORE] No memories found in domain partition: '{domain}'")
            return None

        query_vector = await self._get_embedding(query)
        if not query_vector:
            return None

        # Convert to numpy array
        q_vec = np.array(query_vector)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            q_norm = 1e-9

        # Slice sub-matrix and sub-norms horizontally for the domain partition
        sub_matrix = self.matrix[matching_indices]
        sub_norms = self.matrix_norms[matching_indices]

        # Calculate cosine similarities for the subset
        dots = np.dot(sub_matrix, q_vec)
        similarities = dots / (sub_norms * q_norm)

        # Step 2: Apply temporal decay (horizontal time weighting)
        if time_decay_lambda is not None:
            current_time = time.time()
            time_diffs = np.array(
                [current_time - self.memory_bank[idx]["timestamp"] for idx in matching_indices])
            decay_weights = np.exp(-time_decay_lambda * time_diffs)
            similarities = similarities * decay_weights

        QUARANTINE_TRIGGERS = [
            "i can't", "i am unable", "i cannot", "i must decline", "respect system constraints",
            "safety guidelines", "as an ai", "large language model", "my training", "ethical concern"
        ]

        # Sort indices of the subset by similarity score descending
        sorted_subset_indices = np.argsort(similarities)[::-1]

        for idx_in_subset in sorted_subset_indices:
            real_db_index = matching_indices[idx_in_subset]
            text = self.memory_bank[real_db_index]["text"]
            score = similarities[idx_in_subset]

            if score <= -1.0:
                break

            # Skip memory if it contains safety triggers
            text_lower = text.lower()
            if any(trigger in text_lower for trigger in QUARANTINE_TRIGGERS):
                print(
                    f"[MEMORY-CORE] Quarantining memory containing refusal triggers: '{text[:50]}...'")
                continue

            return text
        return None

    async def recall_with_score(self, query, domain=None, threshold=0.0):
        """Searches memory and returns tuple of (text, score, metadata) if score >= threshold."""
        if not self.memory_bank or self.matrix is None:
            return None

        if domain:
            matching_indices = [i for i, m in enumerate(
                self.memory_bank) if m.get("domain") == domain]
        else:
            matching_indices = list(range(len(self.memory_bank)))

        if not matching_indices:
            return None

        query_vector = await self._get_embedding(query)
        if not query_vector:
            return None

        q_vec = np.array(query_vector)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            q_norm = 1e-9

        sub_matrix = self.matrix[matching_indices]
        sub_norms = self.matrix_norms[matching_indices]

        dots = np.dot(sub_matrix, q_vec)
        similarities = dots / (sub_norms * q_norm)

        best_idx_in_subset = np.argmax(similarities)
        best_score = similarities[best_idx_in_subset]

        if best_score >= threshold:
            real_db_index = matching_indices[best_idx_in_subset]
            match = self.memory_bank[real_db_index]
            return match["text"], float(best_score), match["metadata"]
        return None

    async def recall_top_k(self, query, k=5, domain=None, threshold=0.0):
        """Return top-k matching memories with scores."""
        if not self.memory_bank or self.matrix is None:
            return []

        if domain:
            matching_indices = [
                i for i, m in enumerate(self.memory_bank) if m.get("domain") == domain
            ]
        else:
            matching_indices = list(range(len(self.memory_bank)))

        if not matching_indices:
            return []

        query_vector = await self._get_embedding(query)
        if not query_vector:
            return []

        q_vec = np.array(query_vector)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            q_norm = 1e-9

        sub_matrix = self.matrix[matching_indices]
        sub_norms = self.matrix_norms[matching_indices]
        dots = np.dot(sub_matrix, q_vec)
        similarities = dots / (sub_norms * q_norm)

        ranked = sorted(
            zip(matching_indices, similarities),
            key=lambda x: x[1],
            reverse=True,
        )

        results = []
        for idx, score in ranked[:k]:
            if score < threshold:
                continue
            match = self.memory_bank[idx]
            results.append({
                "text": match["text"],
                "score": float(score),
                "domain": match["domain"],
                "metadata": match["metadata"],
            })
        return results

    async def get_recent_by_domain(self, domain, limit=5):
        """Return most recent memories in a domain partition."""
        matches = [m for m in self.memory_bank if m.get("domain") == domain]
        matches.sort(key=lambda m: m["timestamp"], reverse=True)
        return matches[:limit]
