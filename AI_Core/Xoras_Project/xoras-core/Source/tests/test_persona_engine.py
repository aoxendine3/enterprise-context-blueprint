"""Unit tests for xoras persona engine."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xoras_persona_engine import PersonaDetector, PersonaEngine, PromptComposer


class TestPersonaEngine(unittest.TestCase):
    def setUp(self):
        self.engine = PersonaEngine()

    def test_default_sovereign(self):
        sel = self.engine.compose_for_chat("Hello, how are you?")
        self.assertEqual(sel.persona_id, "sovereign")

    def test_explicit_tone_command(self):
        prev = os.environ.get("XORAS_PERSONA_LOCK_MODE")
        os.environ["XORAS_PERSONA_LOCK_MODE"] = "free"
        try:
            import xoras_persona_engine as pe

            pe._engine = None
            engine = pe.PersonaEngine()
            sel = engine.compose_for_chat("/tone legal")
            self.assertEqual(sel.persona_id, "legal")
            self.assertEqual(sel.source, "explicit")
        finally:
            if prev is None:
                os.environ.pop("XORAS_PERSONA_LOCK_MODE", None)
            else:
                os.environ["XORAS_PERSONA_LOCK_MODE"] = prev
            import xoras_persona_engine as pe

            pe._engine = None

    def test_domain_detection_legal(self):
        sel = self.engine.compose_for_chat(
            "Review this contract clause for liability exposure"
        )
        self.assertEqual(sel.persona_id, "legal")

    def test_domain_detection_medical(self):
        sel = self.engine.compose_for_chat(
            "What symptoms might indicate a clinical issue?"
        )
        self.assertEqual(sel.persona_id, "medical")

    def test_explicit_override_param(self):
        sel = self.engine.compose_for_chat(
            "Tell me about the project",
            explicit_override="grunge",
            override_source="system",
        )
        self.assertEqual(sel.persona_id, "grunge")

    def test_compose_includes_base_laws(self):
        sel = self.engine.compose_for_chat("Hi")
        self.assertIn("Maxx", sel.system_prompt)
        self.assertIn("sovereign", sel.system_prompt.lower())

    def test_list_personas(self):
        personas = self.engine.list_personas()
        ids = [p["id"] for p in personas]
        self.assertIn("sovereign", ids)
        self.assertIn("empathetic", ids)
        self.assertIn("mentor", ids)

    def test_mentor_detection(self):
        sel = self.engine.compose_for_chat(
            "Walk me through the architecture trade-offs like a mentor would"
        )
        self.assertEqual(sel.persona_id, "mentor")


if __name__ == "__main__":
    unittest.main()
