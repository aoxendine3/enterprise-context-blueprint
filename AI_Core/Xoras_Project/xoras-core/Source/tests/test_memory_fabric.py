"""Tests for unified memory fabric."""

import unittest

from xoras_memory_fabric import MemoryFabric, get_memory_fabric


class TestMemoryFabric(unittest.TestCase):
    def test_status_reports_sources(self):
        fabric = get_memory_fabric()
        st = fabric.status()
        self.assertIn("dream_db", st)
        self.assertTrue(st["dream_db"])
        self.assertGreaterEqual(st["dream_count"], 1)

    def test_scrap_hydration_loads_dreams(self):
        fabric = MemoryFabric()
        result = fabric.hydrate("maxx", "audit the workspace", mode="scrap")
        self.assertEqual(result.agent_id, "maxx")
        self.assertIn("sovereign_dream", result.sources_reached)
        self.assertTrue(result.proof)
        self.assertNotEqual(result.proof[0], "no_trusted_fragments_loaded — do not claim memory is ingested")

    def test_wake_mode_deep(self):
        fabric = MemoryFabric()
        result = fabric.hydrate("xoras", "WAKE ROUTE xoras ingest memory", mode="wake", force_deep=True)
        self.assertEqual(result.mode, "deep")
        self.assertGreater(len(result.fragments), 0)

    def test_detect_agent_mention(self):
        fabric = MemoryFabric()
        self.assertEqual(fabric.detect_agent_mention("WAKE ROUTE clara"), "clara")
        self.assertEqual(fabric.detect_agent_mention("/route maxx hello"), "maxx")

    def test_blocked_antigravity_not_in_sources(self):
        fabric = MemoryFabric()
        result = fabric.hydrate("xoras", "memory", mode="scrap")
        for frag in result.fragments:
            self.assertNotIn("antigravity", frag.source.lower())


if __name__ == "__main__":
    unittest.main()
