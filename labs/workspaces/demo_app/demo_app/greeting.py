"""Greeting module for SSOT Demonstration Application.

Provides configurable greeting generation, tone styles, and safe template interpolation.
Zero external dependencies.
"""

from __future__ import annotations

import datetime
from typing import Optional

VALID_STYLES = {
    "standard",
    "formal",
    "casual",
    "sovereign",
    "enthusiastic",
}

STYLE_TEMPLATES = {
    "standard": "Hello, {name}!",
    "formal": "Greetings, {name}. Welcome to the SSOT Agentic Brain.",
    "casual": "Hey {name}, what's happening?",
    "sovereign": "Greetings, {name}. Xoras Sovereign Core is online and operational.",
    "enthusiastic": "HELLO {name_upper}! WELCOME ABOARD!",
}


class _SafeDict(dict):
    """Dictionary that returns the key in braces if missing instead of raising KeyError."""

    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"


def generate_greeting(
    name: Optional[str] = None,
    style: str = "standard",
    template: Optional[str] = None,
) -> str:
    """Generate a formatted greeting string.

    Args:
        name: Recipient name. Defaults to 'World' if None or whitespace.
        style: Tone style. Must be one of VALID_STYLES.
        template: Optional custom format string supporting placeholders like
            {name}, {date}, {time}.

    Returns:
        Formatted greeting string.

    Raises:
        ValueError: If an unrecognized style is specified.
    """
    # Normalize name: fallback to 'World' if None or empty/whitespace
    if name is None or not isinstance(name, str) or name.strip() == "":
        target_name = "World"
    else:
        target_name = name.strip()

    # Normalize style
    normalized_style = style.lower().strip() if isinstance(style, str) else ""
    if normalized_style not in VALID_STYLES:
        valid_list = ", ".join(sorted(VALID_STYLES))
        raise ValueError(f"Invalid style '{style}'. Valid styles are: {valid_list}")

    # Build context dictionary for formatting
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    context = _SafeDict(
        name=target_name,
        name_upper=target_name.upper(),
        NAME=target_name.upper(),
        style=normalized_style,
        date=now_utc.strftime("%Y-%m-%d"),
        time=now_utc.strftime("%H:%M:%S"),
        timestamp=now_utc.isoformat(),
    )

    # If custom template provided, interpolate with safe dictionary
    if template is not None and isinstance(template, str) and template.strip() != "":
        return template.format_map(context)

    # Standard style formatting
    pattern = STYLE_TEMPLATES[normalized_style]
    return pattern.format_map(context)
