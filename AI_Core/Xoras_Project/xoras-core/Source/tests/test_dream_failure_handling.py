import unittest
from unittest.mock import patch, MagicMock
import sys
import asyncio
from pathlib import Path

# Adjust path to import from Source
sys.path.append(str(Path(__file__).resolve().parent.parent))
from xoras_dream_orchestrator import DreamOrchestrator, ActivationSynthesisEngine

class TestDreamFailureHandling(unittest.TestCase):
    
    @patch('requests.get')
    def test_preflight_check_fails_on_missing_model(self, mock_get):
        # Mock API returning models list that doesn't contain MODEL_AFFINITY ("qwen3.5:4b")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "some-other-model:latest"}]}
        mock_get.return_value = mock_response
        
        orchestrator = DreamOrchestrator()
        self.assertFalse(orchestrator.verify_model_availability())

    @patch('requests.get')
    def test_preflight_check_succeeds_on_valid_model(self, mock_get):
        # Mock API returning models list that contains MODEL_AFFINITY
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "qwen3.5:4b"}]}
        mock_get.return_value = mock_response
        
        orchestrator = DreamOrchestrator()
        self.assertTrue(orchestrator.verify_model_availability())

    @patch('xoras_dream_orchestrator.ActivationSynthesisEngine.generate_adversarial_hypothesis')
    @patch('xoras_dream_orchestrator.EntropyHarvester.get_entropy_vector')
    @patch('subprocess.run')
    def test_consecutive_failures_halt_loop(self, mock_run, mock_entropy, mock_synthesis):
        mock_entropy.return_value = {"source_hash": "test"}
        # Mock the LLM query to return the fallback dict (which means failure)
        mock_synthesis.return_value = {
            "archetype": "consolidation",
            "narrative": "System entropy fallback dream cycle.",
            "hypothesis": "Test basic execution limits.",
            "exploit_script": "import time\ntime.sleep(0.5)\n"
        }
        
        orchestrator = DreamOrchestrator()
        
        # We run it 2 times using asyncio run_coroutine_threadsafe or running loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(orchestrator.run_cycle())
        self.assertEqual(orchestrator.consecutive_failures, 1)
        
        loop.run_until_complete(orchestrator.run_cycle())
        self.assertEqual(orchestrator.consecutive_failures, 2)
        
        # The 3rd run should raise a RuntimeError and trigger the voice/alert logic
        with self.assertRaises(RuntimeError) as context:
            loop.run_until_complete(orchestrator.run_cycle())
        self.assertIn("cognitive fuzzer decoupled", str(context.exception))
        self.assertEqual(orchestrator.consecutive_failures, 3)
        loop.close()

if __name__ == '__main__':
    unittest.main()
