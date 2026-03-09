"""Myle login helpers."""

from clinical_computer_use.kernel.browser.playwright_harness import PlaywrightHarness


def login_if_needed(harness: PlaywrightHarness) -> None:
    """Login in validated Myle context when required."""
    harness.ensure_myle_ready()

