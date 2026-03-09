"""In-chart agent flow implementation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import base64

from clinical_computer_use.approvals import require_user_approval
from clinical_computer_use.config import OPENAI_MODEL, OPENAI_SAFETY_IDENTIFIER
from clinical_computer_use.domain.myle.policy_guidance import build_myle_policy_config
from clinical_computer_use.kernel.browser.playwright_harness import PlaywrightHarness
from clinical_computer_use.openai_client import build_openai_client
from clinical_computer_use.prompts import build_myle_action_prompt
from clinical_computer_use.runtime.artifacts import append_event, write_json_trace
from clinical_computer_use.runtime.checkpoints import make_start_checkpoint
from clinical_computer_use.runtime.ledgers import build_empty_ledgers
from clinical_computer_use.runtime.run_state import SessionContext
from clinical_computer_use.safety.runtime_gate import gate_action
from clinical_computer_use.schemas.browser_action import BrowserActionDecision
from clinical_computer_use.tasks.registry import get_task


@dataclass
class InChartAgentOutcome:
    session: SessionContext
    screenshot_path: Path
    final_report: str


def _image_path_to_data_url(path: Path) -> str:
    mime = "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def run_myle_bind_and_agent_task(
    task_name: str,
    patient_query: str,
    user_prompt: str,
    max_steps: int = 8,
) -> InChartAgentOutcome:
    """
    Single-run cold-start flow: bind the patient deterministically, then let the
    model choose constrained in-chart actions from visible UI targets only.
    """
    task = get_task(task_name)
    policy = build_myle_policy_config(draft_only=task.draft_only)
    session = SessionContext(task_name=task.name, user_prompt=f"{patient_query} | {user_prompt}")
    append_event(
        session,
        "bind_and_agent_task_started",
        {
            "task_name": task.name,
            "patient_query": patient_query,
            "user_prompt": user_prompt,
            "draft_only": task.draft_only,
        },
    )
    write_json_trace(session, "ledgers.json", build_empty_ledgers().to_dict())
    write_json_trace(
        session,
        "checkpoint_start.json",
        make_start_checkpoint(
            task_understanding=f"Bind then run in-chart agent task '{task.name}'",
            next_actions=["bind_patient", "iterate_constrained_actions", "finish_or_handoff"],
        ).to_dict(),
    )

    harness = PlaywrightHarness()
    final_report = "Agent did not finish within the step limit."
    screenshot_path = session.screenshot_dir / "agent_final.png"
    try:
        harness.connect()
        harness.bind_patient_from_calendar(patient_query)

        client = build_openai_client()
        for step in range(1, max_steps + 1):
            candidates = harness.snapshot_actionable_elements()
            step_screenshot = harness.capture_screenshot(session.screenshot_dir / f"agent_step_{step}.png")
            append_event(
                session,
                "agent_step_snapshot",
                {
                    "step": step,
                    "active_url": harness.current_url(),
                    "candidate_count": len(candidates),
                    "screenshot_path": str(step_screenshot),
                },
            )

            response = client.responses.parse(
                model=OPENAI_MODEL,
                instructions=build_myle_action_prompt(user_prompt, step, candidates),
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": "Choose the single best next action from the visible targets or finish.",
                            },
                            {
                                "type": "input_image",
                                "image_url": _image_path_to_data_url(step_screenshot),
                            },
                        ],
                    }
                ],
                text_format=BrowserActionDecision,
                safety_identifier=f"{OPENAI_SAFETY_IDENTIFIER}:{task.name}:agent",
            )

            decision = getattr(response, "output_parsed", None)
            if decision is None:
                raise RuntimeError("Model response did not contain parsed browser action output.")

            append_event(
                session,
                "agent_step_decision",
                {
                    "step": step,
                    "action_type": decision.action_type,
                    "target_id": decision.target_id,
                    "text": decision.text,
                    "scroll_direction": decision.scroll_direction,
                    "rationale": decision.rationale,
                    "expected_outcome": decision.expected_outcome,
                },
            )

            gate = gate_action(decision.action_type, policy)
            append_event(
                session,
                "runtime_gate_evaluated",
                {
                    "step": step,
                    "action": decision.action_type,
                    "allowed": gate.allowed,
                    "reason": gate.reason,
                    "requires_approval": gate.requires_approval,
                },
            )
            if not gate.allowed:
                if gate.requires_approval and require_user_approval(decision.action_type):
                    append_event(
                        session,
                        "runtime_gate_override_approved",
                        {
                            "step": step,
                            "action": decision.action_type,
                        },
                    )
                else:
                    raise RuntimeError(f"Runtime gate blocked action '{decision.action_type}': {gate.reason}")

            if decision.action_type == "finish":
                final_report = decision.final_report or "Agent chose to finish without a final report."
                screenshot_path = step_screenshot
                break
            if decision.action_type == "click":
                if not decision.target_id or decision.target_id not in {c["agent_id"] for c in candidates}:
                    raise RuntimeError(f"Model chose invalid click target '{decision.target_id}'.")
                harness.click_agent_target(decision.target_id)
            elif decision.action_type == "type":
                if not decision.target_id or decision.target_id not in {c["agent_id"] for c in candidates}:
                    raise RuntimeError(f"Model chose invalid type target '{decision.target_id}'.")
                if not decision.text:
                    raise RuntimeError("Model chose type action without text.")
                harness.type_agent_target(decision.target_id, decision.text)
            elif decision.action_type == "scroll":
                if decision.scroll_direction not in ("up", "down"):
                    raise RuntimeError(f"Model chose invalid scroll direction '{decision.scroll_direction}'.")
                harness.scroll_page(decision.scroll_direction)
            else:
                raise RuntimeError(f"Unsupported action type '{decision.action_type}'.")

        screenshot_path = harness.capture_screenshot(session.screenshot_dir / "agent_final.png")
        append_event(
            session,
            "bind_and_agent_task_completed",
            {
                "active_url": harness.current_url(),
                "final_report": final_report,
                "screenshot_path": str(screenshot_path),
            },
        )
    finally:
        harness.close()

    write_json_trace(
        session,
        "agent_summary.json",
        {
            "patient_query": patient_query,
            "final_report": final_report,
            "final_screenshot": str(screenshot_path),
        },
    )
    return InChartAgentOutcome(
        session=session,
        screenshot_path=screenshot_path,
        final_report=final_report,
    )
