import unittest
import os
import tempfile
import time
from Source.tests.e2e.import_helper import get_xoras_vector_db


class TestLocalVectorDB(unittest.TestCase):
    def setUp(self):
        self.db = get_xoras_vector_db()
        self.db.set_latency(0.005)  # 5ms default
        self.db.set_force_error(False)
        # Ensure db is initialized/reset for each test
        self.db.reset_db()

    def test_f3_t1_init(self):
        # Already done in setUp, but let's test explicitly
        self.db.initialize_db()
        self.assertTrue(self.db._initialized)

    def test_f3_t1_migration(self):
        # Migrates memory and active knowledge jsons correctly.
        # Let's run with real paths
        self.db.migrate_json_data()
        # Verify we loaded some data
        self.assertGreater(len(self.db._data), 0)

    def test_f3_t1_query_match(self):
        self.db.migrate_json_data()
        # Let's search for "BTCUSDT" which is present in memory
        results = self.db.query_semantic_memory("BTCUSDT")
        self.assertGreater(len(results), 0)
        # Check if the text contains BTCUSDT
        self.assertTrue(any("BTCUSDT" in item.get('text', '') for item in results))

    def test_f3_t1_query_limit(self):
        self.db.migrate_json_data()
        limit = 3
        results = self.db.query_semantic_memory("BTCUSDT", limit=limit)
        self.assertLessEqual(len(results), limit)

    def test_f3_t1_query_latency(self):
        self.db.migrate_json_data()
        start = time.perf_counter()
        results = self.db.query_semantic_memory("BTCUSDT")
        duration = (time.perf_counter() - start) * 1000.0  # in ms
        self.assertLess(duration, 500.0)

    def test_f3_t2_query_before_init(self):
        # reset initialization state
        self.db._initialized = False
        with self.assertRaises(RuntimeError):
            self.db.query_semantic_memory("BTCUSDT")

    def test_f3_t2_empty_query(self):
        self.db.migrate_json_data()
        start = time.perf_counter()
        results = self.db.query_semantic_memory("")
        duration = (time.perf_counter() - start) * 1000.0
        self.assertEqual(results, [])
        self.assertLess(duration, 1.0)  # immediate <1ms

    def test_f3_t2_duplicate_migration(self):
        self.db.migrate_json_data()
        count_first = len(self.db._data)
        # Migrate again
        self.db.migrate_json_data()
        count_second = len(self.db._data)
        # Must be idempotent / update safely (no duplicates added)
        self.assertEqual(count_first, count_second)

    def test_f3_t2_long_query(self):
        self.db.migrate_json_data()
        long_query = "BTCUSDT " * 1000
        results = self.db.query_semantic_memory(long_query)
        self.assertIsNotNone(results)

    def test_f3_t2_malformed_json_migration(self):
        # Create malformed files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f_mem:
            f_mem.write("{invalid json")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f_kn:
            f_kn.write("[]")

        try:
            with self.assertRaises(ValueError):
                self.db.migrate_json_data(
                    memory_path=f_mem.name, knowledge_path=f_kn.name)
        finally:
            os.remove(f_mem.name)
            os.remove(f_kn.name)


if __name__ == '__main__':
    unittest.main()
