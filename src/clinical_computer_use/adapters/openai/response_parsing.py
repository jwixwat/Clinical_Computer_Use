"""OpenAI response parsing helpers (scaffold)."""

from typing import TypeVar

T = TypeVar("T")


def get_output_parsed(response: object) -> object | None:
    """Compatibility helper for parsed structured output access."""
    return getattr(response, "output_parsed", None)

