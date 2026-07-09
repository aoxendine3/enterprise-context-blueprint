import unittest
import os
from Source.tests.e2e.import_helper import get_xoras_langgraph_engine, get_xoras_vector_db, get_xoras_sandbox


class TestTier3CrossFeature(unittest.TestCase):
    def setUp(self):
        self.engine_mod = get_xoras_langgraph_engine()
        self.db_mod = get_xoras_vector_db()
        self.sandbox_mod = get_xoras_sandbox()

        self.engine = self.engine_mod.XorasLangGraph()
        self.db_mod.reset_db()
        self.db_mod.migrate_json_data()

    def test_t3_langgraph_vector_context(self):
        # LangGraph reasoning queries vector DB, context is injected, sanitized, and completed.
        state = self.engine.run(
            "query vector for BTCUSDT context", ghost_execution=False)
        self.assertFalse(state['blocked'])
        self.assertGreater(len(state['context']), 0)
        self.assertIn("BTCUSDT", state['context'])
        self.assertIn("Reasoning based on context:", state['output'])

    def test_t3_langgraph_sandbox_execution(self):
        # LangGraph ghost execution runs validator script in sandbox, stdout captured in state.
        # We pass prompt: "run: echo hello_from_sb"
        # We use profile: restricted
        state = self.engine.run(
            "run: echo hello_from_sb profile: restricted", ghost_execution=True)
        self.assertFalse(state['blocked'])
        self.assertEqual(state['sandbox_output'], "hello_from_sb")

    def test_t3_sandbox_vector_db_write_block(self):
        # sandbox command attempting to write/delete vector DB files is blocked.
        # e.g., command: touch Source/xoras_memory.json under read-only profile is blocked.
        res = self.sandbox_mod.run_in_sandbox(
            ["touch", "Source/xoras_memory.json"], "read-only")
        self.assertEqual(res['returncode'], 1)
        self.assertIn("denied under read-only profile", res['stderr'])


if __name__ == '__main__':
    unittest.main()
