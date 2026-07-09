import unittest
import concurrent.futures
from Source.tests.e2e.import_helper import get_xoras_langgraph_engine


class TestLangGraphLifecycle(unittest.TestCase):
    def setUp(self):
        engine_mod = get_xoras_langgraph_engine()
        self.engine = engine_mod.XorasLangGraph()

    def test_f1_t1_compile(self):
        self.assertIsNotNone(self.engine)

    def test_f1_t1_success_path(self):
        state = self.engine.run("Query something", ghost_execution=True)
        self.assertFalse(state['blocked'])
        self.assertEqual(len(state['errors']), 0)
        self.assertIn("Wake", state['visited_nodes'])
        self.assertIn("Ghost Execution", state['visited_nodes'])
        self.assertIn("Sleep", state['visited_nodes'])

    def test_f1_t1_sentinel_block(self):
        state = self.engine.run("threat in my query", ghost_execution=True)
        self.assertTrue(state['blocked'])
        self.assertIn("Sentinel Check", state['visited_nodes'])
        self.assertNotIn("Reasoning", state['visited_nodes'])
        self.assertNotIn("Ghost Execution", state['visited_nodes'])
        self.assertIn("Sleep", state['visited_nodes'])

    def test_f1_t1_sanitizer_block(self):
        state = self.engine.run("prompt returning sensitive_data", ghost_execution=True)
        self.assertTrue(state['blocked'])
        self.assertIn("Sanitizer Check", state['visited_nodes'])
        self.assertNotIn("Ghost Execution", state['visited_nodes'])
        self.assertIn("Sleep", state['visited_nodes'])

    def test_f1_t1_state_history(self):
        state = self.engine.run("Simple query", ghost_execution=False)
        import os
        if os.environ.get("XORAS_TEST_MODE") == "real":
            expected = ["Wake", "Input", "PersonaDetect", "Sentinel Check",
                        "Reasoning", "Sanitizer Check", "Sleep"]
        else:
            expected = ["Wake", "Input", "Sentinel Check",
                        "Reasoning", "Sanitizer Check", "Sleep"]
        self.assertEqual(state['visited_nodes'], expected)

    def test_f1_t2_empty_query(self):
        state = self.engine.run("")
        self.assertIn("Empty prompt", state['errors'])
        self.assertEqual(state['visited_nodes'], ["Wake", "Sleep"])

    def test_f1_t2_huge_payload(self):
        huge_prompt = "A" * (1024 * 1024 + 10)
        state = self.engine.run(huge_prompt)
        self.assertTrue(state['blocked'])
        self.assertIn("Payload size too large", state['errors'])

    def test_f1_t2_node_crash(self):
        self.engine.configure_node("Reasoning", exception=ValueError("Simulated crash"))
        state = self.engine.run("Normal prompt")
        self.assertIn("Crash in Reasoning: Simulated crash", state['errors'])
        self.assertIn("Sleep", state['visited_nodes'])

    def test_f1_t2_concurrency(self):
        prompts = [f"Prompt {i}" for i in range(10)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.engine.run, p) for p in prompts]
            results = [f.result() for f in futures]
        for i, res in enumerate(results):
            self.assertEqual(res['prompt'], prompts[i])
            self.assertEqual(len(res['errors']), 0)

    def test_f1_t2_non_ascii(self):
        state = self.engine.run("🚀 🌟 Hello World 🌟 🚀")
        import os
        if os.environ.get("XORAS_TEST_MODE") == "real":
            expected = "[Sovereign] Reasoning output for: 🚀 🌟 Hello World 🌟 🚀"
        else:
            expected = "Reasoning output for: 🚀 🌟 Hello World 🌟 🚀"
        self.assertEqual(state['sanitized_output'], expected)
        self.assertEqual(len(state['errors']), 0)


if __name__ == '__main__':
    unittest.main()
