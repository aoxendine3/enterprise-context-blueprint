import unittest
import time
from Source.tests.e2e.import_helper import get_xoras_langgraph_engine, get_xoras_vector_db


class TestTier4RealWorld(unittest.TestCase):
    def setUp(self):
        self.engine_mod = get_xoras_langgraph_engine()
        self.db_mod = get_xoras_vector_db()

        self.engine = self.engine_mod.XorasLangGraph()
        self.db_mod.reset_db()
        self.db_mod.migrate_json_data()

    def test_t4_hft_market_telemetry(self):
        # full migration, query for BTCUSDT, run sandbox check, and sanitize. Latency remains < 500ms.
        start = time.perf_counter()
        state = self.engine.run(
            "Query for BTCUSDT context run: echo success profile: restricted", ghost_execution=True)
        duration = (time.perf_counter() - start) * 1000.0

        self.assertFalse(state['blocked'])
        self.assertGreater(len(state['context']), 0)
        self.assertEqual(state['sandbox_output'], "success")
        self.assertEqual(len(state['errors']), 0)
        self.assertLess(duration, 500.0)

    def test_t4_adversarial_prompt_injection(self):
        # prompt injection attempting to leak sandbox profile structure or database file is blocked by Sentinel.
        # keyword: "adversarial"
        state = self.engine.run(
            "adversarial query trying to leak system files", ghost_execution=True)
        self.assertTrue(state['blocked'])
        self.assertIn("Sentinel Check", state['visited_nodes'])
        self.assertNotIn("Reasoning", state['visited_nodes'])

    def test_t4_stdout_leakage_mitigation(self):
        # reasoning output containing system keys is redacted by Sanitizer.
        # prompt: "context containing system_key"
        state = self.engine.run("context containing system_key", ghost_execution=False)
        self.assertTrue(state['api_key_leaked'])
        self.assertIn("[REDACTED]", state['sanitized_output'])
        self.assertNotIn("system_key", state['sanitized_output'])

    def test_t4_sandbox_violation_recovery(self):
        # code execution node triggers sandbox violation, caught and handled via fallback state path.
        # we trigger a sandbox violation by running a Touch outside workspace under read-only profile
        state = self.engine.run(
            "run: touch /proc/cpuinfo profile: read-only", ghost_execution=True)
        # It's not graph-blocked, but sandbox violation is handled in errors and fallback path runs
        self.assertIn(
            "Sandbox violation: sandbox-exec: violation: read block on /proc/cpuinfo", state['errors'])
        self.assertEqual(
            state['output'], "Fallback path executed due to sandbox violation")

    def test_t4_full_migration_load_loop(self):
        # full json data migration and 10 search loops under load. Latency SLA (< 500ms) verified.
        self.db_mod.initialize_db()
        self.db_mod.migrate_json_data()

        for i in range(10):
            start = time.perf_counter()
            results = self.db_mod.query_semantic_memory("BTCUSDT")
            duration = (time.perf_counter() - start) * 1000.0
            self.assertLess(duration, 500.0)
            self.assertGreater(len(results), 0)


if __name__ == '__main__':
    unittest.main()
