"""Patient-binding helpers."""

from clinical_computer_use.kernel.browser.playwright_harness import PlaywrightHarness


def bind_patient(harness: PlaywrightHarness, patient_query: str) -> None:
    """Bind current session to a patient from Calendar."""
    harness.bind_patient_from_calendar(patient_query)

