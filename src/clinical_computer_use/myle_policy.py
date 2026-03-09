"""
Myle-specific task scope and search policy.
"""

from __future__ import annotations

from .policies import PolicyConfig


MYLE_BLOCKED_ACTIONS = (
    "submit",
    "approve",
    "complete",
    "send",
    "sign",
    "fax",
    "bill",
    "revoke",
)

MYLE_BLOCKED_KEYWORDS = (
    "submit",
    "approve",
    "complete",
    "approve_and_complete",
    "fax",
    "sign",
    "send",
    "bill",
    "revoke",
    "edit_med_list",
    "enter_vitals",
)


def build_myle_policy_guidance() -> str:
    return """
Myle task policy for this environment:

- Draft-only by default.
- Save is allowed.
- Approve is not allowed.
- Fax is not allowed.
- Sign is not allowed.
- Submit/finalize/send/bill are not allowed.
- A controlled patient-binding step is allowed on cold start.
- During patient binding, the agent may use the top navigation bar only to reach Calendar, search for the intended patient, and open that patient's chart.
- After patient binding, do not switch to another patient during the task.
- After patient binding, stay inside the bound patient chart.
- Use current-patient Documents and Results as the main evidence stores.
- Documents and Results overlap; the agent may search both intelligently.
- Prefer recent relevant evidence first.
- If the user specifies a date floor, respect it first.
- If evidence is insufficient under the date floor, state that explicitly before broadening scope.
- Cite the source artifact used for each drafted answer when possible.
- If evidence is weak or conflicting, leave the item for human review rather than inventing an answer.
- Built-in note forms may be used when the task explicitly requires a form inside the note.
- For annotation workflows, textbox placement and typing are allowed, but final certification actions are not.
""".strip()


def build_myle_policy_config(draft_only: bool = True) -> PolicyConfig:
    return PolicyConfig(
        blocked_actions=MYLE_BLOCKED_ACTIONS,
        approval_required_actions=MYLE_BLOCKED_ACTIONS,
        blocked_keywords=MYLE_BLOCKED_KEYWORDS,
        draft_only=draft_only,
        require_source_citations=True,
    )
