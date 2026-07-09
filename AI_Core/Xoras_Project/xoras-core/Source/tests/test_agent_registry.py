"""Tests for ELITE_BOW agent registry."""

import unittest

from xoras_agent_registry import AgentRegistry, get_agent_registry


class TestAgentRegistry(unittest.TestCase):
    def test_list_agents(self):
        registry = get_agent_registry()
        agents = registry.list_agents()
        self.assertGreaterEqual(len(agents), 10)
        ids = {a["id"] for a in agents}
        self.assertIn("xoras", ids)
        self.assertIn("maxx", ids)
        self.assertIn("clara", ids)

    def test_route_maxx(self):
        registry = get_agent_registry()
        sel = registry.route(agent_id="maxx")
        self.assertEqual(sel.agent_id, "maxx")
        self.assertEqual(sel.label, "Maxx")
        self.assertIn("Maxx", sel.system_prompt)
        self.assertGreater(len(sel.system_prompt), 200)

    def test_route_unknown_falls_back(self):
        registry = AgentRegistry()
        sel = registry.route(agent_id="nonexistent_agent")
        self.assertEqual(sel.agent_id, registry.default_agent)

    def test_departments(self):
        registry = get_agent_registry()
        depts = registry.list_departments()
        self.assertGreaterEqual(len(depts), 2)
        exec_dept = next(d for d in depts if d["id"] == "executive")
        self.assertTrue(any(a["id"] == "xoras" for a in exec_dept["agents"]))


if __name__ == "__main__":
    unittest.main()
