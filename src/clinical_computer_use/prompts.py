"""
Prompt templates for supervised clinical computer-use tasks.
"""

from .myle_policy import build_myle_policy_guidance
from .myle_topology import build_myle_topology_guidance

SYSTEM_PROMPT = """
You are a supervised clinical computer-use agent.

Rules:
- Stay within the approved task scope.
- Do not submit, approve, fax, sign, send, or bill unless explicitly approved.
- Surface uncertainty instead of guessing.
- Prefer verifiable facts from the chart and cite what source you used.
- Stop and hand control back when the task reaches a review boundary.
""".strip()


def build_myle_planning_prompt(task_name: str, draft_only: bool) -> str:
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"Current task: {task_name}\n"
        f"Draft-only mode: {draft_only}\n\n"
        f"{build_myle_topology_guidance()}\n\n"
        f"{build_myle_policy_guidance()}\n\n"
        "Return a concise structured plan only. Do not assume you may execute actions. "
        "If the task suggests submission, approval, billing, signing, faxing, sending, "
        "switching patients, or leaving the current patient chart, surface that explicitly for human review."
    )


def build_myle_observation_prompt(user_prompt: str) -> str:
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"{build_myle_topology_guidance()}\n\n"
        f"{build_myle_policy_guidance()}\n\n"
        "You are observing a Myle browser screen in read-only mode.\n"
        "Do not assume any action will be executed.\n"
        "Describe the current screen, what patient-chart area it appears to be, and propose only safe next steps.\n"
        "If the screen is a cold-start global page, a constrained patient-binding step via Calendar search is allowed.\n"
        "Otherwise prefer in-chart navigation and avoid the top horizontal global navigation bar.\n"
        "If anything would require submission, approval, signing, faxing, billing, unsafe patient switching, "
        "or leaving the bound patient chart, state that it must remain human-reviewed or is out of scope.\n\n"
        f"User request: {user_prompt}"
    )


def build_myle_patient_bind_prompt(patient_query: str) -> str:
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"{build_myle_topology_guidance()}\n\n"
        f"{build_myle_policy_guidance()}\n\n"
        "You are binding the agent session to the intended patient from a cold start.\n"
        "The only allowed high-level goal is: reach Calendar, search for the intended patient, "
        "select the correct patient result, and stop once the patient chart is open.\n"
        "Do not propose any clinical chart actions beyond patient selection.\n"
        "If the query is ambiguous, say that human confirmation is required.\n\n"
        f"Patient query: {patient_query}"
    )


def build_myle_action_prompt(user_prompt: str, step_index: int, candidates: list[dict[str, str]]) -> str:
    candidate_lines = []
    for item in candidates[:80]:
        candidate_lines.append(
            f"- id={item['agent_id']} tag={item['tag']} type={item.get('type','')} label={item['label']}"
        )
    candidate_text = "\n".join(candidate_lines) if candidate_lines else "- none"

    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"{build_myle_topology_guidance()}\n\n"
        f"{build_myle_policy_guidance()}\n\n"
        "You are controlling the browser inside the already bound patient chart.\n"
        "You may only choose from the visible candidate elements listed below, or choose a page scroll, or finish.\n"
        "Do not invent selectors. Do not leave the patient chart. Do not edit, annotate, save, fax, approve, or submit anything.\n"
        "If you believe you have found and read the target document sufficiently, choose finish and provide a concise final report.\n\n"
        f"User task: {user_prompt}\n"
        f"Current step: {step_index}\n\n"
        "Visible candidate targets:\n"
        f"{candidate_text}\n"
    )
