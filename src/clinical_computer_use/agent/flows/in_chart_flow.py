"""In-chart agent flow implementation."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

from clinical_computer_use.agent.contracts import compile_task_contract
from clinical_computer_use.agent.prompts.action import build_contract_aware_action_prompt
from clinical_computer_use.agent.reasoning.intent import check_decision_against_contract
from clinical_computer_use.agent.reasoning.verifier import verify_completion_claim
from clinical_computer_use.approvals import require_user_approval
from clinical_computer_use.config import OPENAI_MODEL, OPENAI_SAFETY_IDENTIFIER
from clinical_computer_use.domain.myle.policy_guidance import build_myle_policy_config
from clinical_computer_use.kernel.browser.playwright_harness import PlaywrightHarness
from clinical_computer_use.openai_client import build_openai_client
from clinical_computer_use.runtime.artifacts import (
    append_event,
    ensure_artifact_policy_for_session,
    register_artifact,
    write_json_trace,
)
from clinical_computer_use.runtime.autonomy import budget_exceeded_reason, record_action, reset_autonomy_leg
from clinical_computer_use.runtime.checkpoint_policy import append_checkpoint_with_policy
from clinical_computer_use.runtime.checkpoints import (
    make_candidate_found_checkpoint,
    make_completion_checkpoint,
    make_risk_boundary_checkpoint,
    make_start_checkpoint,
    make_surface_exhausted_checkpoint,
)
from clinical_computer_use.runtime.clarification import (
    make_clarification_checkpoint,
    needs_contract_clarification,
)
from clinical_computer_use.runtime.handoff import build_handoff_packet
from clinical_computer_use.runtime.ledgers import (
    SurfaceType,
    add_claim,
    add_evidence_record,
    add_uncertainty,
    build_empty_ledgers,
    mark_artifact_opened,
    mark_artifact_verified,
    next_step,
    note_search_episode,
    unresolved_higher_priority_candidates,
    upsert_artifact_from_candidate,
)
from clinical_computer_use.runtime.policy_context import build_policy_context
from clinical_computer_use.runtime.run_brief import build_run_brief
from clinical_computer_use.runtime.surfaces import restorable_surface_for_resume
from clinical_computer_use.runtime.understanding import (
    build_operational_understanding_block,
    render_operational_understanding_text,
)
from clinical_computer_use.runtime.run_state import (
    RunState,
    SessionContext,
    build_initial_run_state,
    load_run_state,
    mark_bound_patient_context,
    save_run_state,
    session_from_run_state,
    summarize_run_state,
)
from clinical_computer_use.runtime.versioning import build_run_version_bundle
from clinical_computer_use.safety.runtime_gate import gate_action
from clinical_computer_use.schemas.browser_action import BrowserActionDecision
from clinical_computer_use.schemas.contract_types import RiskTier, RunLifecycleState
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


def _action_risk_tier(decision: BrowserActionDecision) -> RiskTier:
    if decision.action_type == "type":
        return RiskTier.TIER1
    if decision.action_type == "finish":
        return RiskTier.TIER1
    return RiskTier.TIER0


def _risk_requires_review(action_tier: RiskTier, threshold: RiskTier) -> bool:
    order = {
        RiskTier.TIER0: 0,
        RiskTier.TIER1: 1,
        RiskTier.TIER2: 2,
        RiskTier.TIER3: 3,
    }
    return order[action_tier] >= order[threshold]


def _gate_clarification_or_raise(*, session: SessionContext, state: RunState) -> None:
    if not needs_contract_clarification(state):
        return
    checkpoint = make_clarification_checkpoint(state)
    append_checkpoint_with_policy(state.checkpoints, checkpoint)
    state.lifecycle_state = RunLifecycleState.PAUSED
    state.lifecycle_reason = "clarification_required"
    save_run_state(session, state)
    write_json_trace(session, "checkpoint_clarification_required.json", checkpoint.to_dict())
    handoff = build_handoff_packet(state)
    write_json_trace(session, "handoff_packet.json", handoff.to_dict())
    raise RuntimeError(
        "Task contract requires clarification before pursuit. "
        "Apply correction via run-state flow, then continue."
    )


def _initialize_agent_run_state(
    *,
    session: SessionContext,
    draft_only: bool,
    patient_query: str,
    user_prompt: str,
    task_name: str,
) -> RunState:
    contract_result = compile_task_contract(user_prompt=user_prompt, patient_target=patient_query)
    start_checkpoint = make_start_checkpoint(
        task_understanding=f"Bind then run in-chart agent task '{task_name}'",
        next_actions=["bind_patient", "iterate_constrained_actions", "finish_or_handoff"],
    )
    state = build_initial_run_state(
        session=session,
        draft_only=draft_only,
        contract=contract_result.contract,
        ledgers=build_empty_ledgers(),
        start_checkpoint=start_checkpoint,
        version_bundle=build_run_version_bundle(
            role_config={
                "primary_role": "executor",
                "roles": ["contract_compiler", "executor", "verifier"],
            }
        ),
    )
    state.checkpoints[0].operational_understanding = build_operational_understanding_block(
        state,
        next_safest_actions=["bind_patient", "iterate_constrained_actions", "finish_or_handoff"],
    )
    save_run_state(session, state)
    write_json_trace(session, "checkpoint_start.json", start_checkpoint.to_dict())

    append_event(
        session,
        "task_contract_compiled",
        {
            "objective_type": contract_result.contract.objective_type.value,
            "preferred_surfaces": [s.value for s in contract_result.contract.preferred_surfaces],
            "required_artifact_classes": [a.value for a in contract_result.contract.required_artifact_classes],
            "acceptable_artifact_classes": [a.value for a in contract_result.contract.acceptable_artifact_classes],
            "disallowed_artifact_classes": [a.value for a in contract_result.contract.disallowed_artifact_classes],
            "uncertainties": contract_result.contract.uncertainties,
            "diagnostics": contract_result.contract.diagnostics.model_dump(),
            "notes": contract_result.notes,
        },
    )
    return state


def _execute_agent_loop(
    *,
    session: SessionContext,
    task_name: str,
    patient_query: str,
    user_prompt: str,
    run_state: RunState,
    max_steps: int,
    resume_required_surface: SurfaceType | None = None,
    resume_context_locked: bool = False,
) -> tuple[Path, str, RunState]:
    task = get_task(task_name)
    policy = build_myle_policy_config(draft_only=task.draft_only)
    policy_context = build_policy_context(run_state.runtime_directives)

    harness = PlaywrightHarness()
    final_report = "Agent did not finish within the step limit."
    screenshot_path = session.screenshot_dir / "agent_final.png"

    try:
        harness.connect()
        harness.bind_patient_from_calendar(patient_query)
        run_state.lifecycle_state = RunLifecycleState.ACTIVE
        run_state.lifecycle_reason = "execution_in_progress"
        reset_autonomy_leg(run_state.autonomy_state)
        mark_bound_patient_context(
            run_state,
            bound_patient_label=patient_query,
            bound_patient_identifier=patient_query,
            verification_source="calendar_bind",
            verification_confidence=0.7,
        )

        client = build_openai_client()
        finished = False
        first_resume_step = True

        for _ in range(max_steps):
            step = next_step(run_state.ledgers)
            surface_state = harness.inspect_surface()
            active_url = surface_state.active_url
            surface = surface_state.surface_type
            run_state.latest_surface_state = surface_state
            understanding_block = build_operational_understanding_block(
                run_state,
                next_safest_actions=["continue_search", "checkpoint_to_user"],
            )

            def _emit_checkpoint(checkpoint) -> None:
                appended = append_checkpoint_with_policy(run_state.checkpoints, checkpoint)
                if appended:
                    if checkpoint.stage in {"risk_boundary", "handoff"}:
                        run_state.lifecycle_state = RunLifecycleState.PAUSED
                        run_state.lifecycle_reason = f"checkpoint:{checkpoint.reason}"
                    reset_autonomy_leg(run_state.autonomy_state)

            candidates = harness.snapshot_actionable_elements()
            step_screenshot = harness.capture_screenshot(session.screenshot_dir / f"agent_step_{step}.png")
            register_artifact(
                session,
                artifact_type="screenshot",
                artifact_path=step_screenshot,
                metadata={"surface": surface.value, "flow": "in_chart_step", "step": step},
            )
            note_search_episode(
                run_state.ledgers,
                step=step,
                surface=surface,
                query=run_state.task_contract.source_prompt,
                date_floor=run_state.task_contract.date_floor,
                date_ceiling=run_state.task_contract.date_ceiling,
                result_count=len(candidates),
                exhausted=len(candidates) == 0,
            )
            add_evidence_record(
                run_state.ledgers,
                step=step,
                source_surface=surface,
                kind="screenshot",
                content=str(step_screenshot),
                artifact_key=None,
            )

            append_event(
                session,
                "agent_step_snapshot",
                {
                    "step": step,
                    "active_url": active_url,
                    "surface": surface.value,
                    "candidate_count": len(candidates),
                    "screenshot_path": str(step_screenshot),
                },
            )

            if (
                first_resume_step
                and resume_context_locked
                and resume_required_surface is not None
                and surface != resume_required_surface
            ):
                append_event(
                    session,
                    "resume_restore_attempted",
                    {
                        "required_surface": resume_required_surface.value,
                        "observed_surface": surface.value,
                        "step": step,
                    },
                )
                restored = harness.restore_surface_for_resume(resume_required_surface)
                if restored:
                    restored_surface = harness.inspect_surface().surface_type
                    if restored_surface == resume_required_surface:
                        append_event(
                            session,
                            "resume_restore_succeeded",
                            {
                                "required_surface": resume_required_surface.value,
                                "restored_surface": restored_surface.value,
                                "step": step,
                            },
                        )
                        continue
                append_event(
                    session,
                    "resume_restore_failed",
                    {
                        "required_surface": resume_required_surface.value,
                        "observed_surface": surface.value,
                        "step": step,
                    },
                )
                checkpoint = make_surface_exhausted_checkpoint(
                    task_understanding=f"Resume policy requires continuation on {resume_required_surface.value}",
                    operational_understanding=understanding_block,
                    step_index=step,
                    where_looked=[episode.surface.value for episode in run_state.ledgers.search_episodes],
                    why_done_or_not=(
                        f"Current surface '{surface.value}' does not match required resume surface "
                        f"'{resume_required_surface.value}'."
                    ),
                    next_actions=["restore_previous_surface", "continue_after_restore"],
                )
                _emit_checkpoint(checkpoint)
                save_run_state(session, run_state)
                append_event(
                    session,
                    "resume_context_mismatch",
                    {
                        "required_surface": resume_required_surface.value,
                        "observed_surface": surface.value,
                        "step": step,
                    },
                )
                raise RuntimeError(
                    "Resume context mismatch: continuation must begin from last persisted surface."
                )

            if not candidates:
                checkpoint = make_surface_exhausted_checkpoint(
                    task_understanding=f"No actionable candidates at step {step}",
                    operational_understanding=understanding_block,
                    step_index=step,
                    where_looked=[episode.surface.value for episode in run_state.ledgers.search_episodes],
                    why_done_or_not="Current surface appears exhausted under visible candidate constraints.",
                    next_actions=["scroll_down", "retry_snapshot", "consider_surface_switch"],
                )
                _emit_checkpoint(checkpoint)
                save_run_state(session, run_state)
                append_event(session, "checkpoint_surface_exhausted", checkpoint.to_dict())
                harness.scroll_page("down")
                first_resume_step = False
                continue

            run_brief = build_run_brief(run_state)
            response = client.responses.parse(
                model=OPENAI_MODEL,
                instructions=build_contract_aware_action_prompt(
                    contract=run_state.task_contract,
                    run_state_summary=summarize_run_state(run_state),
                    step_index=step,
                    candidates=candidates,
                ),
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": run_brief,
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

            intent = check_decision_against_contract(
                decision,
                contract=run_state.task_contract,
                ledgers=run_state.ledgers,
                candidates=candidates,
            )
            if not intent.allowed:
                add_uncertainty(run_state.ledgers, intent.reason)
                checkpoint = make_risk_boundary_checkpoint(
                    task_understanding=f"Intent gate blocked action at step {step}",
                    operational_understanding=understanding_block,
                    step_index=step,
                    where_looked=[episode.surface.value for episode in run_state.ledgers.search_episodes],
                    why_done_or_not=f"Action blocked by contract-aware intent gate: {intent.reason}",
                    next_actions=["choose_alternative_action", "continue_search"],
                )
                _emit_checkpoint(checkpoint)
                save_run_state(session, run_state)
                append_event(
                    session,
                    "intent_gate_blocked",
                    {
                        "step": step,
                        "reason": intent.reason,
                        "candidate_key": intent.candidate_key,
                        "inferred_artifact_class": (
                            intent.inferred_artifact_class.value if intent.inferred_artifact_class else None
                        ),
                    },
                )
                first_resume_step = False
                continue

            action_tier = _action_risk_tier(decision)
            if _risk_requires_review(action_tier, policy_context.require_review_at_or_above):
                checkpoint = make_risk_boundary_checkpoint(
                    task_understanding=f"Policy-context review boundary at step {step}",
                    operational_understanding=understanding_block,
                    step_index=step,
                    where_looked=[episode.surface.value for episode in run_state.ledgers.search_episodes],
                    why_done_or_not=(
                        f"Action tier '{action_tier.value}' reached runtime review threshold "
                        f"'{policy_context.require_review_at_or_above.value}'."
                    ),
                    next_actions=["request_user_approval", "choose_lower_risk_action"],
                )
                _emit_checkpoint(checkpoint)
                save_run_state(session, run_state)
                if not require_user_approval(
                    decision.action_type,
                    context_block=render_operational_understanding_text(understanding_block),
                ):
                    add_uncertainty(run_state.ledgers, "user_denied_policy_context_review_request")
                    first_resume_step = False
                    continue

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
                checkpoint = make_risk_boundary_checkpoint(
                    task_understanding=f"Runtime gate boundary at step {step}",
                    operational_understanding=understanding_block,
                    step_index=step,
                    where_looked=[episode.surface.value for episode in run_state.ledgers.search_episodes],
                    why_done_or_not=f"Action '{decision.action_type}' is approval-bound or blocked: {gate.reason}",
                    next_actions=["request_user_approval", "select_lower_risk_action"],
                )
                _emit_checkpoint(checkpoint)
                save_run_state(session, run_state)

                if gate.requires_approval and require_user_approval(
                    decision.action_type,
                    context_block=render_operational_understanding_text(understanding_block),
                ):
                    append_event(
                        session,
                        "runtime_gate_override_approved",
                        {"step": step, "action": decision.action_type},
                    )
                else:
                    add_uncertainty(run_state.ledgers, f"runtime_gate_blocked:{decision.action_type}")
                    append_event(
                        session,
                        "runtime_gate_blocked",
                        {"step": step, "action": decision.action_type, "reason": gate.reason},
                    )
                    first_resume_step = False
                    continue

            candidate_map = {item["agent_id"]: item for item in candidates if "agent_id" in item}

            if decision.action_type == "finish":
                final_report = decision.final_report or "Agent attempted finish without report."
                add_claim(run_state.ledgers, final_report)
                add_evidence_record(
                    run_state.ledgers,
                    step=step,
                    source_surface=surface,
                    kind="completion_claim",
                    content=final_report,
                    artifact_key=run_state.ledgers.last_candidate_key,
                )

                verification = verify_completion_claim(
                    contract=run_state.task_contract,
                    ledgers=run_state.ledgers,
                    final_report=final_report,
                )
                append_event(
                    session,
                    "completion_verifier_decision",
                    {
                        "step": step,
                        "complete": verification.complete,
                        "reason": verification.reason,
                        "missing_criteria": verification.missing_criteria,
                        "supporting_artifacts": verification.supporting_artifacts,
                        "unresolved_candidates": verification.unresolved_candidates,
                    },
                )

                if verification.complete:
                    for key in verification.supporting_artifacts:
                        mark_artifact_verified(run_state.ledgers, key, step)
                    screenshot_path = step_screenshot
                    completion_checkpoint = make_completion_checkpoint(
                        task_understanding=f"Verifier-approved completion for '{task.name}'",
                        operational_understanding=understanding_block,
                        step_index=step,
                        where_looked=[episode.surface.value for episode in run_state.ledgers.search_episodes],
                        found=verification.supporting_artifacts,
                        why_done_or_not="Verifier approved completion claim after falsification checks.",
                        next_actions=["human_review_report"],
                    )
                    _emit_checkpoint(completion_checkpoint)
                    save_run_state(session, run_state)
                    write_json_trace(session, "checkpoint_completion.json", completion_checkpoint.to_dict())
                    finished = True
                    break

                add_uncertainty(run_state.ledgers, verification.reason)
                for item in verification.missing_criteria:
                    add_uncertainty(run_state.ledgers, f"missing_completion_criterion:{item}")
                checkpoint = make_risk_boundary_checkpoint(
                    task_understanding=f"Completion claim rejected at step {step}",
                    operational_understanding=understanding_block,
                    step_index=step,
                    where_looked=[episode.surface.value for episode in run_state.ledgers.search_episodes],
                    why_done_or_not=(
                        f"Verifier rejected finish; missing criteria: {', '.join(verification.missing_criteria) or 'unknown'}"
                    ),
                    next_actions=["continue_search", "checkpoint_to_user"],
                )
                _emit_checkpoint(checkpoint)
                save_run_state(session, run_state)
                first_resume_step = False
                continue

            if decision.action_type == "click":
                if not decision.target_id or decision.target_id not in candidate_map:
                    raise RuntimeError(f"Model chose invalid click target '{decision.target_id}'.")
                candidate = candidate_map[decision.target_id]
                artifact = upsert_artifact_from_candidate(
                    run_state.ledgers,
                    candidate=candidate,
                    source_surface=surface,
                    step=step,
                )
                mark_artifact_opened(run_state.ledgers, key=artifact.candidate_key, step=step)
                add_evidence_record(
                    run_state.ledgers,
                    step=step,
                    source_surface=surface,
                    kind="candidate_opened",
                    content=artifact.label,
                    artifact_key=artifact.candidate_key,
                )
                checkpoint = make_candidate_found_checkpoint(
                    task_understanding=f"Opened candidate on {surface.value}",
                    operational_understanding=understanding_block,
                    step_index=step,
                    where_looked=[episode.surface.value for episode in run_state.ledgers.search_episodes],
                    found=[artifact.label],
                    next_actions=["inspect_candidate", "verify_artifact_class", "continue_or_reject"],
                )
                _emit_checkpoint(checkpoint)
                harness.click_agent_target(decision.target_id)
            elif decision.action_type == "type":
                if not decision.target_id or decision.target_id not in candidate_map:
                    raise RuntimeError(f"Model chose invalid type target '{decision.target_id}'.")
                if not decision.text:
                    raise RuntimeError("Model chose type action without text.")
                candidate = candidate_map[decision.target_id]
                artifact = upsert_artifact_from_candidate(
                    run_state.ledgers,
                    candidate=candidate,
                    source_surface=surface,
                    step=step,
                )
                add_evidence_record(
                    run_state.ledgers,
                    step=step,
                    source_surface=surface,
                    kind="typed_input",
                    content=decision.text,
                    artifact_key=artifact.candidate_key,
                )
                harness.type_agent_target(decision.target_id, decision.text)
            elif decision.action_type == "scroll":
                if decision.scroll_direction not in ("up", "down"):
                    raise RuntimeError(f"Model chose invalid scroll direction '{decision.scroll_direction}'.")
                harness.scroll_page(decision.scroll_direction)
            else:
                raise RuntimeError(f"Unsupported action type '{decision.action_type}'.")

            progress_made = decision.action_type in {"click", "type", "finish"}
            record_action(
                run_state.autonomy_state,
                tier=action_tier,
                surface=surface.value,
                progress_made=progress_made,
            )
            budget_reason = budget_exceeded_reason(run_state.autonomy_state)
            if budget_reason:
                checkpoint = make_risk_boundary_checkpoint(
                    task_understanding=f"Autonomy budget boundary at step {step}",
                    operational_understanding=build_operational_understanding_block(
                        run_state,
                        next_safest_actions=["checkpoint_to_user", "continue_after_review"],
                    ),
                    step_index=step,
                    where_looked=[episode.surface.value for episode in run_state.ledgers.search_episodes],
                    why_done_or_not=f"Autonomy budget boundary reached: {budget_reason}",
                    next_actions=["checkpoint_to_user", "continue_after_review"],
                )
                _emit_checkpoint(checkpoint)

            save_run_state(session, run_state)
            first_resume_step = False

        if not finished:
            unresolved = unresolved_higher_priority_candidates(
                run_state.ledgers,
                run_state.task_contract.preferred_surfaces,
            )
            handoff_checkpoint = make_surface_exhausted_checkpoint(
                task_understanding=f"In-chart loop ended without verifier-approved completion for '{task.name}'",
                operational_understanding=build_operational_understanding_block(
                    run_state,
                    next_safest_actions=["human_checkpoint_review", "continue_run", "apply_correction"],
                ),
                where_looked=[episode.surface.value for episode in run_state.ledgers.search_episodes],
                why_done_or_not=(
                    "Step budget exhausted before completion criteria were met. "
                    f"Unresolved candidates: {len(unresolved)}"
                ),
                next_actions=["human_checkpoint_review", "continue_run", "apply_correction"],
            )
            _emit_checkpoint(handoff_checkpoint)
            save_run_state(session, run_state)
            handoff = build_handoff_packet(run_state)
            write_json_trace(session, "handoff_packet.json", handoff.to_dict())

        screenshot_path = harness.capture_screenshot(session.screenshot_dir / "agent_final.png")
        register_artifact(
            session,
            artifact_type="screenshot",
            artifact_path=screenshot_path,
            metadata={"flow": "in_chart_final"},
        )
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

    return screenshot_path, final_report, run_state


def run_myle_bind_and_agent_task(
    task_name: str,
    patient_query: str,
    user_prompt: str,
    max_steps: int = 8,
) -> InChartAgentOutcome:
    """Cold-start bind then run constrained in-chart executor with verifier gating."""
    task = get_task(task_name)
    session = SessionContext(task_name=task.name, user_prompt=f"{patient_query} | {user_prompt}")
    ensure_artifact_policy_for_session(session)
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

    run_state = _initialize_agent_run_state(
        session=session,
        draft_only=task.draft_only,
        patient_query=patient_query,
        user_prompt=user_prompt,
        task_name=task.name,
    )
    _gate_clarification_or_raise(session=session, state=run_state)

    screenshot_path, final_report, run_state = _execute_agent_loop(
        session=session,
        task_name=task.name,
        patient_query=patient_query,
        user_prompt=user_prompt,
        run_state=run_state,
        max_steps=max_steps,
    )
    save_run_state(session, run_state)

    write_json_trace(
        session,
        "agent_summary.json",
        {
            "patient_query": patient_query,
            "final_report": final_report,
            "final_screenshot": str(screenshot_path),
        },
    )
    return InChartAgentOutcome(session=session, screenshot_path=screenshot_path, final_report=final_report)


def continue_myle_agent_task(session_id: str, max_steps: int = 8) -> InChartAgentOutcome:
    """Resume an existing in-chart run from persisted state."""
    run_state = load_run_state(session_id)
    session = session_from_run_state(run_state)
    if run_state.lifecycle_state in {RunLifecycleState.ARCHIVED, RunLifecycleState.PURGED}:
        raise RuntimeError(f"Cannot continue run in lifecycle_state '{run_state.lifecycle_state.value}'.")
    ensure_artifact_policy_for_session(session)
    _gate_clarification_or_raise(session=session, state=run_state)

    patient_query = run_state.task_contract.patient_target
    if not patient_query:
        raise RuntimeError("Cannot continue run without patient_target in task contract.")

    last_episode = run_state.ledgers.search_episodes[-1] if run_state.ledgers.search_episodes else None
    required_surface = (
        restorable_surface_for_resume(last_episode.surface)
        if last_episode is not None
        else None
    )

    append_event(
        session,
        "bind_and_agent_task_resumed",
        {
            "task_name": run_state.task_name,
            "patient_query": patient_query,
            "resume_from_step": run_state.ledgers.step_counter + 1,
            "max_steps": max_steps,
            "required_resume_surface": required_surface.value if required_surface is not None else None,
        },
    )

    screenshot_path, final_report, run_state = _execute_agent_loop(
        session=session,
        task_name=run_state.task_name,
        patient_query=patient_query,
        user_prompt=run_state.user_prompt,
        run_state=run_state,
        max_steps=max_steps,
        resume_required_surface=required_surface,
        resume_context_locked=required_surface is not None,
    )
    save_run_state(session, run_state)

    write_json_trace(
        session,
        "agent_summary_resume.json",
        {
            "patient_query": patient_query,
            "final_report": final_report,
            "final_screenshot": str(screenshot_path),
        },
    )

    return InChartAgentOutcome(session=session, screenshot_path=screenshot_path, final_report=final_report)
