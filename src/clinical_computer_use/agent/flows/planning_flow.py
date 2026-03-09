"""Planning flow implementation."""

from __future__ import annotations

from dataclasses import dataclass

from clinical_computer_use.approvals import require_user_approval
from clinical_computer_use.config import OPENAI_MODEL, OPENAI_SAFETY_IDENTIFIER
from clinical_computer_use.domain.myle.policy_guidance import build_myle_policy_config
from clinical_computer_use.openai_client import build_openai_client
from clinical_computer_use.prompts import build_myle_planning_prompt
from clinical_computer_use.runtime.artifacts import append_event, write_json_trace
from clinical_computer_use.runtime.checkpoints import make_start_checkpoint
from clinical_computer_use.runtime.ledgers import build_empty_ledgers
from clinical_computer_use.runtime.run_state import SessionContext
from clinical_computer_use.safety.runtime_gate import gate_action
from clinical_computer_use.schemas.agent_plan import AgentPlan
from clinical_computer_use.tasks.registry import get_task


@dataclass
class RunOutcome:
    session: SessionContext
    plan: AgentPlan
    blocked_actions: list[str]
    approved_actions: list[str]
    denied_actions: list[str]


def run_task(task_name: str, user_prompt: str) -> RunOutcome:
    """
    Run a minimal supervised planning pass with GPT-5.4.

    This does not execute any browser actions. It only produces a structured
    plan, evaluates proposed actions against policy, and records approvals.
    """
    task = get_task(task_name)
    policy = build_myle_policy_config(draft_only=task.draft_only)
    session = SessionContext(task_name=task.name, user_prompt=user_prompt)
    append_event(
        session,
        "session_started",
        {
            "task_name": task.name,
            "description": task.description,
            "user_prompt": user_prompt,
            "draft_only": task.draft_only,
        },
    )
    write_json_trace(session, "ledgers.json", build_empty_ledgers().to_dict())
    write_json_trace(
        session,
        "checkpoint_start.json",
        make_start_checkpoint(
            task_understanding=f"Planning task '{task.name}'",
            next_actions=["produce_structured_plan", "evaluate_policy_for_proposed_actions"],
        ).to_dict(),
    )

    client = build_openai_client()
    response = client.responses.parse(
        model=OPENAI_MODEL,
        instructions=build_myle_planning_prompt(task.name, task.draft_only),
        input=user_prompt,
        text_format=AgentPlan,
        safety_identifier=f"{OPENAI_SAFETY_IDENTIFIER}:{task.name}",
    )

    plan = getattr(response, "output_parsed", None)
    if plan is None:
        raise RuntimeError("Model response did not contain parsed structured output.")

    blocked_actions: list[str] = []
    approved_actions: list[str] = []
    denied_actions: list[str] = []

    for item in plan.proposed_actions:
        decision = gate_action(item.action, policy)
        append_event(
            session,
            "policy_evaluated",
            {
                "action": item.action,
                "allowed": decision.allowed,
                "reason": decision.reason,
                "requires_approval": decision.requires_approval,
            },
        )
        if decision.allowed:
            continue

        blocked_actions.append(item.action)
        if decision.requires_approval:
            approved = require_user_approval(item.action)
            append_event(
                session,
                "approval_decision",
                {
                    "action": item.action,
                    "approved": approved,
                },
            )
            if approved:
                approved_actions.append(item.action)
            else:
                denied_actions.append(item.action)

    write_json_trace(session, "plan.json", plan.model_dump())
    write_json_trace(
        session,
        "summary.json",
        {
            "task_name": task.name,
            "model": OPENAI_MODEL,
            "blocked_actions": blocked_actions,
            "approved_actions": approved_actions,
            "denied_actions": denied_actions,
        },
    )
    append_event(
        session,
        "run_completed",
        {
            "blocked_actions": blocked_actions,
            "approved_actions": approved_actions,
            "denied_actions": denied_actions,
        },
    )
    return RunOutcome(
        session=session,
        plan=plan,
        blocked_actions=blocked_actions,
        approved_actions=approved_actions,
        denied_actions=denied_actions,
    )
