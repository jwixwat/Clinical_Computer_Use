"""Planning flow implementation."""

from __future__ import annotations

from dataclasses import dataclass

from clinical_computer_use.agent.contracts import compile_task_contract
from clinical_computer_use.agent.prompts.planning import build_contract_aware_planning_prompt
from clinical_computer_use.approvals import require_user_approval
from clinical_computer_use.config import OPENAI_MODEL, OPENAI_SAFETY_IDENTIFIER
from clinical_computer_use.domain.myle.policy_guidance import build_myle_policy_config
from clinical_computer_use.openai_client import build_openai_client
from clinical_computer_use.runtime.artifacts import (
    append_event,
    ensure_artifact_policy_for_session,
    write_json_trace,
)
from clinical_computer_use.runtime.checkpoint_policy import append_checkpoint_with_policy
from clinical_computer_use.runtime.checkpoints import make_completion_checkpoint, make_start_checkpoint
from clinical_computer_use.runtime.clarification import make_clarification_checkpoint, needs_contract_clarification
from clinical_computer_use.runtime.handoff import build_handoff_packet
from clinical_computer_use.runtime.ledgers import SurfaceType, build_empty_ledgers, next_step, note_search_episode
from clinical_computer_use.runtime.run_brief import build_run_brief
from clinical_computer_use.runtime.understanding import (
    build_operational_understanding_block,
    render_operational_understanding_text,
)
from clinical_computer_use.runtime.run_state import SessionContext, build_initial_run_state, save_run_state, summarize_run_state
from clinical_computer_use.runtime.versioning import build_run_version_bundle
from clinical_computer_use.safety.runtime_gate import gate_action
from clinical_computer_use.schemas.agent_plan import AgentPlan
from clinical_computer_use.schemas.contract_types import RunLifecycleState
from clinical_computer_use.tasks.registry import get_task


@dataclass
class RunOutcome:
    session: SessionContext
    plan: AgentPlan
    blocked_actions: list[str]
    approved_actions: list[str]
    denied_actions: list[str]


def run_task(task_name: str, user_prompt: str) -> RunOutcome:
    """Run supervised planning without browser execution."""
    task = get_task(task_name)
    policy = build_myle_policy_config(draft_only=task.draft_only)
    session = SessionContext(task_name=task.name, user_prompt=user_prompt)
    ensure_artifact_policy_for_session(session)
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

    contract_result = compile_task_contract(user_prompt=user_prompt)
    start_checkpoint = make_start_checkpoint(
        task_understanding=f"Planning task '{task.name}'",
        next_actions=["compile_task_contract", "produce_structured_plan", "evaluate_policy_for_proposed_actions"],
    )
    run_state = build_initial_run_state(
        session=session,
        draft_only=task.draft_only,
        contract=contract_result.contract,
        ledgers=build_empty_ledgers(),
        start_checkpoint=start_checkpoint,
        version_bundle=build_run_version_bundle(
            role_config={
                "primary_role": "planner",
                "roles": ["contract_compiler", "planner", "policy_evaluator"],
            }
        ),
    )
    understanding_block = build_operational_understanding_block(
        run_state,
        next_safest_actions=["compile_task_contract", "produce_structured_plan"],
    )
    run_state.checkpoints[0].operational_understanding = understanding_block
    step = next_step(run_state.ledgers)
    note_search_episode(run_state.ledgers, step=step, surface=SurfaceType.UNKNOWN, query=user_prompt, result_count=0)
    save_run_state(session, run_state)

    append_event(
        session,
        "task_contract_compiled",
        {
            "objective_type": contract_result.contract.objective_type.value,
            "preferred_surfaces": [s.value for s in contract_result.contract.preferred_surfaces],
            "required_artifact_classes": [a.value for a in contract_result.contract.required_artifact_classes],
            "acceptable_artifact_classes": [a.value for a in contract_result.contract.acceptable_artifact_classes],
            "disallowed_artifact_classes": [a.value for a in contract_result.contract.disallowed_artifact_classes],
            "diagnostics": contract_result.contract.diagnostics.model_dump(),
            "notes": contract_result.notes,
        },
    )

    if needs_contract_clarification(run_state):
        clarification_checkpoint = make_clarification_checkpoint(state=run_state, stage="handoff", reason="handoff")
        append_checkpoint_with_policy(run_state.checkpoints, clarification_checkpoint)
        run_state.lifecycle_state = RunLifecycleState.PAUSED
        run_state.lifecycle_reason = "clarification_required"
        save_run_state(session, run_state)
        write_json_trace(session, "checkpoint_clarification_required.json", clarification_checkpoint.to_dict())
        write_json_trace(session, "handoff_packet.json", build_handoff_packet(run_state).to_dict())
        raise RuntimeError("Contract clarification required before planning can continue.")

    run_brief = build_run_brief(run_state)
    client = build_openai_client()
    response = client.responses.parse(
        model=OPENAI_MODEL,
        instructions=build_contract_aware_planning_prompt(
            task_name=task.name,
            draft_only=task.draft_only,
            contract=run_state.task_contract,
            run_state_summary=summarize_run_state(run_state),
        ),
        input=run_brief,
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
            approved = require_user_approval(
                item.action,
                context_block=render_operational_understanding_text(understanding_block),
            )
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

    completion_checkpoint = make_completion_checkpoint(
        task_understanding=f"Planning complete for task '{task.name}'",
        operational_understanding=build_operational_understanding_block(
            run_state,
            next_safest_actions=["human_review_plan", "continue_with_execution_flow_if_approved"],
        ),
        where_looked=["planning_context"],
        found=[f"proposed_actions:{len(plan.proposed_actions)}"],
        why_done_or_not="Structured plan generated and policy-evaluated.",
        next_actions=["human_review_plan", "continue_with_execution_flow_if_approved"],
    )
    append_checkpoint_with_policy(run_state.checkpoints, completion_checkpoint)
    save_run_state(session, run_state)

    write_json_trace(session, "checkpoint_start.json", start_checkpoint.to_dict())
    write_json_trace(session, "checkpoint_completion.json", completion_checkpoint.to_dict())
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
