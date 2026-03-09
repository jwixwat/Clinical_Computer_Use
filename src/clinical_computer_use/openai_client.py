"""
OpenAI client helpers.
"""

from __future__ import annotations

from openai import OpenAI

from .config import OPENAI_API_KEY


def build_openai_client() -> OpenAI:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set. Populate .env before running the model loop.")
    return OpenAI(api_key=OPENAI_API_KEY)
