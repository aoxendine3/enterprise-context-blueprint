"""Unit tests for demo_app.greeting module.

Covers T-UNIT-01 through T-UNIT-09 plus template interpolation and style variants.
Zero external dependencies.
"""

from __future__ import annotations

import os
import sys
import unittest

# Ensure demo_app is importable
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from demo_app.greeting import VALID_STYLES, generate_greeting


class TestGreeting(unittest.TestCase):
    """Test suite for greeting generation logic."""

    def test_default_greeting(self) -> None:
        """T-UNIT-01: Default greeting returns 'Hello, World!'."""
        result = generate_greeting()
        self.assertEqual(result, "Hello, World!")

    def test_custom_name(self) -> None:
        """T-UNIT-02: Custom name returns 'Hello, <name>!'."""
        result = generate_greeting(name="Anthony")
        self.assertEqual(result, "Hello, Anthony!")

    def test_style_formal(self) -> None:
        """T-UNIT-03: Formal style includes formal salutation and recipient."""
        result = generate_greeting(name="Dr. Smith", style="formal")
        self.assertIn("Dr. Smith", result)
        self.assertIn("Greetings", result)
        self.assertEqual(result, "Greetings, Dr. Smith. Welcome to the SSOT Agentic Brain.")

    def test_style_sovereign(self) -> None:
        """T-UNIT-04: Sovereign style returns sovereign greeting."""
        result = generate_greeting(name="Operator", style="sovereign")
        self.assertIn("Operator", result)
        self.assertIn("Sovereign", result)
        self.assertEqual(result, "Greetings, Operator. Xoras Sovereign Core is online and operational.")

    def test_style_casual(self) -> None:
        """Casual style returns casual salutation."""
        result = generate_greeting(name="Anthony", style="casual")
        self.assertEqual(result, "Hey Anthony, what's happening?")

    def test_style_enthusiastic(self) -> None:
        """Enthusiastic style returns uppercase greeting."""
        result = generate_greeting(name="Anthony", style="enthusiastic")
        self.assertEqual(result, "HELLO ANTHONY! WELCOME ABOARD!")

    def test_empty_name_fallback(self) -> None:
        """T-UNIT-05: Empty name falls back to 'World'."""
        result = generate_greeting(name="")
        self.assertEqual(result, "Hello, World!")

    def test_whitespace_name(self) -> None:
        """T-UNIT-06: Whitespace-only name falls back to 'World'."""
        result = generate_greeting(name="   ")
        self.assertEqual(result, "Hello, World!")

    def test_special_characters(self) -> None:
        """T-UNIT-07: Names with special characters preserve formatting."""
        result = generate_greeting(name="Alice & Bob #1")
        self.assertEqual(result, "Hello, Alice & Bob #1!")

    def test_unicode_name(self) -> None:
        """T-UNIT-08: Unicode names are handled cleanly without corruption."""
        result = generate_greeting(name="世界")
        self.assertEqual(result, "Hello, 世界!")

    def test_invalid_style(self) -> None:
        """T-UNIT-09: Invalid style raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            generate_greeting(name="User", style="nonexistent")
        self.assertIn("Invalid style", str(ctx.exception))

    def test_template_interpolation(self) -> None:
        """Custom template interpolates {name} safely."""
        result = generate_greeting(name="Anthony", template="Welcome aboard, {name}!")
        self.assertEqual(result, "Welcome aboard, Anthony!")

    def test_template_with_date_and_time(self) -> None:
        """Custom template with {date} and {time} populates timestamp tokens."""
        result = generate_greeting(name="Anthony", template="{name} logged in at {date}")
        self.assertIn("Anthony logged in at 202", result)

    def test_template_safe_missing_placeholder(self) -> None:
        """Templates with unrecognized braces do not raise KeyError."""
        result = generate_greeting(name="Anthony", template="Hello {name}, key is {unknown_key}!")
        self.assertEqual(result, "Hello Anthony, key is {unknown_key}!")


if __name__ == "__main__":
    unittest.main()
