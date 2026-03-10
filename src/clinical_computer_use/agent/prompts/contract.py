"""Prompt helpers for task contract compilation."""

from clinical_computer_use.prompts import SYSTEM_PROMPT


def build_contract_compiler_prompt(user_prompt: str) -> str:
    return (
        f"{SYSTEM_PROMPT}\n\n"
        "Compile the user's request into a strict operational task contract. "
        "Prefer explicit constraints, surface missing fields as uncertainties, "
        "and avoid silent assumptions.\n\n"
        f"User request: {user_prompt}"
    )


def build_correction_compiler_prompt(correction_text: str) -> str:
    return (
        f"{SYSTEM_PROMPT}\n\n"
        "Compile the correction into explicit contract deltas. "
        "Do not restate unchanged fields.\n\n"
        f"Correction: {correction_text}"
    )
