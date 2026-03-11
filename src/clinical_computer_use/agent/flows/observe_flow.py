"""Observation and bind flow implementations."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

from clinical_computer_use.agent.contracts import compile_task_contract
from clinical_computer_use.agent.prompts.observation import (
    build_contract_aware_observation_prompt,
    build_contract_aware_patient_bind_prompt,
)
from clinical_computer_use.config import EMR_BASE_URL, OPENAI_MODEL, OPENAI_SAFETY_IDENTIFIER
from clinical_computer_use.kernel.browser.playwright_harness import PlaywrightHarness
from clinical_computer_use.openai_client import build_openai_client
from clinical_computer_use.runtime.artifacts import (
    append_event,
    ensure_artifact_policy_for_session,
    register_artifact,
    write_json_trace,
)
from clinical_computer_use.runtime.checkpoint_policy import append_checkpoint_with_policy
from clinical_computer_use.runtime.checkpoints import make_completion_checkpoint, make_start_checkpoint
from clinical_computer_use.runtime.clarification import make_clarification_checkpoint, needs_contract_clarification
from clinical_computer_use.runtime.handoff import build_handoff_packet
from clinical_computer_use.runtime.ledgers import (
    SurfaceType,
    add_evidence_record,
    build_empty_ledgers,
    next_step,
    note_search_episode,
)
from clinical_computer_use.runtime.run_brief import build_run_brief
from clinical_computer_use.runtime.understanding import build_operational_understanding_block
from clinical_computer_use.runtime.run_state import (
    RunState,
    SessionContext,
    build_initial_run_state,
    mark_bound_patient_context,
    save_run_state,
    summarize_run_state,
)
from clinical_computer_use.runtime.versioning import build_run_version_bundle
from clinical_computer_use.schemas.agent_plan import ObservedScreenPlan
from clinical_computer_use.schemas.contract_types import RunLifecycleState
from clinical_computer_use.tasks.registry import get_task


@dataclass
class BrowserObservationOutcome:
    session: SessionContext
    screenshot_path: Path
    observation: ObservedScreenPlan


@dataclass
class PatientBindOutcome:
    session: SessionContext
    screenshot_path: Path
    observation: ObservedScreenPlan


@dataclass
class BindAndObserveOutcome:
    session: SessionContext
    screenshot_path: Path
    observation: ObservedScreenPlan


@dataclass
class BindOpenDocumentsObserveOutcome:
    session: SessionContext
    screenshot_path: Path
    observation: ObservedScreenPlan


def _image_path_to_data_url(path: Path) -> str:
    mime = "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _initialize_run_state(
    *,
    session: SessionContext,
    draft_only: bool,
    user_prompt: str,
    patient_target: str | None,
    task_understanding: str,
    next_actions: list[str],
) -> RunState:
    contract_result = compile_task_contract(user_prompt=user_prompt, patient_target=patient_target)
    start_checkpoint = make_start_checkpoint(task_understanding=task_understanding, next_actions=next_actions)
    state = build_initial_run_state(
        session=session,
        draft_only=draft_only,
        contract=contract_result.contract,
        ledgers=build_empty_ledgers(),
        start_checkpoint=start_checkpoint,
        version_bundle=build_run_version_bundle(
            role_config={
                "primary_role": "observer",
                "roles": ["contract_compiler", "observer"],
            }
        ),
    )
    state.checkpoints[0].operational_understanding = build_operational_understanding_block(
        state,
        next_safest_actions=next_actions,
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


def _gate_clarification_or_raise(*, session: SessionContext, state: RunState) -> None:
    if not needs_contract_clarification(state):
        return
    checkpoint = make_clarification_checkpoint(state=state, stage="handoff", reason="handoff")
    append_checkpoint_with_policy(state.checkpoints, checkpoint)
    state.lifecycle_state = RunLifecycleState.PAUSED
    state.lifecycle_reason = "clarification_required"
    save_run_state(session, state)
    write_json_trace(session, "checkpoint_clarification_required.json", checkpoint.to_dict())
    write_json_trace(session, "handoff_packet.json", build_handoff_packet(state).to_dict())
    raise RuntimeError("Contract clarification required before pursuit can continue.")


def _record_observation(
    *,
    state: RunState,
    screenshot_path: Path,
    observation: ObservedScreenPlan,
    surface: SurfaceType,
) -> None:
    step = next_step(state.ledgers)
    note_search_episode(
        state.ledgers,
        step=step,
        surface=surface,
        query=state.user_prompt,
        date_floor=state.task_contract.date_floor,
        date_ceiling=state.task_contract.date_ceiling,
        result_count=len(observation.proposed_next_actions),
    )
    add_evidence_record(
        state.ledgers,
        step=step,
        source_surface=surface,
        kind="screen_summary",
        content=observation.screen_summary,
        artifact_key=None,
    )
    add_evidence_record(
        state.ledgers,
        step=step,
        source_surface=surface,
        kind="screenshot",
        content=str(screenshot_path),
        artifact_key=None,
    )


def run_browser_observation(task_name: str, user_prompt: str, target_url: str) -> BrowserObservationOutcome:
    task = get_task(task_name)
    session = SessionContext(task_name=task.name, user_prompt=user_prompt)
    ensure_artifact_policy_for_session(session)
    append_event(
        session,
        "browser_observation_started",
        {"task_name": task.name, "target_url": target_url, "draft_only": task.draft_only},
    )
    state = _initialize_run_state(
        session=session,
        draft_only=task.draft_only,
        user_prompt=user_prompt,
        patient_target=None,
        task_understanding=f"Observe screen for task '{task.name}'",
        next_actions=["capture_screenshot", "produce_structured_observation"],
    )
    _gate_clarification_or_raise(session=session, state=state)

    harness = PlaywrightHarness()
    try:
        harness.connect()
        if target_url == EMR_BASE_URL:
            harness.ensure_myle_ready()
        else:
            harness.open_url(target_url)
        screenshot_path = harness.capture_screenshot(session.screenshot_dir / "screen.png")
        surface_state = harness.inspect_surface()
        active_url = surface_state.active_url
        surface = surface_state.surface_type
        state.latest_surface_state = surface_state
        append_event(
            session,
            "browser_screenshot_captured",
            {
                "target_url": target_url,
                "active_url": active_url,
                "surface": surface.value,
                "screenshot_path": str(screenshot_path),
            },
        )
        register_artifact(
            session,
            artifact_type="screenshot",
            artifact_path=screenshot_path,
            metadata={"surface": surface.value, "flow": "observe"},
        )
    finally:
        harness.close()

    run_brief = build_run_brief(state)
    client = build_openai_client()
    response = client.responses.parse(
        model=OPENAI_MODEL,
        instructions=build_contract_aware_observation_prompt(
            contract=state.task_contract,
            run_state_summary=summarize_run_state(state),
            user_prompt=user_prompt,
        ),
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": run_brief},
                    {"type": "input_image", "image_url": _image_path_to_data_url(screenshot_path)},
                ],
            }
        ],
        text_format=ObservedScreenPlan,
        safety_identifier=f"{OPENAI_SAFETY_IDENTIFIER}:{task.name}:observe",
    )

    observation = getattr(response, "output_parsed", None)
    if observation is None:
        raise RuntimeError("Model response did not contain parsed observed screen output.")

    _record_observation(state=state, screenshot_path=screenshot_path, observation=observation, surface=surface)
    completion_checkpoint = make_completion_checkpoint(
        task_understanding=f"Observation complete for task '{task.name}'",
        operational_understanding=build_operational_understanding_block(
            state,
            next_safest_actions=["human_review_observation"],
        ),
        where_looked=[episode.surface.value for episode in state.ledgers.search_episodes],
        found=[observation.screen_summary],
        why_done_or_not="Screen summary produced in read-only mode.",
        next_actions=["human_review_observation"],
    )
    append_checkpoint_with_policy(state.checkpoints, completion_checkpoint)
    save_run_state(session, state)
    write_json_trace(session, "checkpoint_completion.json", completion_checkpoint.to_dict())
    write_json_trace(session, "observation.json", observation.model_dump())
    append_event(
        session,
        "browser_observation_completed",
        {
            "screenshot_path": str(screenshot_path),
            "proposed_next_actions": [item.action for item in observation.proposed_next_actions],
        },
    )
    return BrowserObservationOutcome(session=session, screenshot_path=screenshot_path, observation=observation)


def run_myle_observation(task_name: str, user_prompt: str) -> BrowserObservationOutcome:
    return run_browser_observation(task_name=task_name, user_prompt=user_prompt, target_url=EMR_BASE_URL)


def run_myle_patient_bind(task_name: str, patient_query: str) -> PatientBindOutcome:
    task = get_task(task_name)
    session = SessionContext(task_name=task.name, user_prompt=patient_query)
    ensure_artifact_policy_for_session(session)
    append_event(
        session,
        "patient_bind_started",
        {"task_name": task.name, "patient_query": patient_query, "draft_only": task.draft_only},
    )
    state = _initialize_run_state(
        session=session,
        draft_only=task.draft_only,
        user_prompt=patient_query,
        patient_target=patient_query,
        task_understanding=f"Bind patient for task '{task.name}'",
        next_actions=["calendar_search", "patient_selection", "screen_assessment"],
    )
    _gate_clarification_or_raise(session=session, state=state)

    harness = PlaywrightHarness()
    try:
        harness.connect()
        harness.bind_patient_from_calendar(patient_query)
        screenshot_path = harness.capture_screenshot(session.screenshot_dir / "patient_bind.png")
        surface_state = harness.inspect_surface()
        active_url = surface_state.active_url
        surface = surface_state.surface_type
        state.latest_surface_state = surface_state
        mark_bound_patient_context(
            state,
            bound_patient_label=patient_query,
            bound_patient_identifier=patient_query,
            verification_source="calendar_bind",
            verification_confidence=0.7,
        )
        append_event(
            session,
            "patient_bind_screenshot_captured",
            {
                "patient_query": patient_query,
                "active_url": active_url,
                "surface": surface.value,
                "screenshot_path": str(screenshot_path),
            },
        )
        register_artifact(
            session,
            artifact_type="screenshot",
            artifact_path=screenshot_path,
            metadata={"surface": surface.value, "flow": "bind_patient"},
        )
    finally:
        harness.close()

    run_brief = build_run_brief(state)
    client = build_openai_client()
    response = client.responses.parse(
        model=OPENAI_MODEL,
        instructions=build_contract_aware_patient_bind_prompt(
            patient_query=patient_query,
            contract=state.task_contract,
            run_state_summary=summarize_run_state(state),
        ),
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": run_brief},
                    {"type": "input_image", "image_url": _image_path_to_data_url(screenshot_path)},
                ],
            }
        ],
        text_format=ObservedScreenPlan,
        safety_identifier=f"{OPENAI_SAFETY_IDENTIFIER}:{task.name}:bind_patient",
    )

    observation = getattr(response, "output_parsed", None)
    if observation is None:
        raise RuntimeError("Model response did not contain parsed patient-bind output.")

    _record_observation(state=state, screenshot_path=screenshot_path, observation=observation, surface=surface)
    completion_checkpoint = make_completion_checkpoint(
        task_understanding=f"Patient bind assessment complete for task '{task.name}'",
        operational_understanding=build_operational_understanding_block(
            state,
            next_safest_actions=["continue_with_in_chart_task_or_review"],
        ),
        where_looked=[episode.surface.value for episode in state.ledgers.search_episodes],
        found=[observation.screen_summary],
        why_done_or_not="Bind completed and assessed from screenshot evidence.",
        next_actions=["continue_with_in_chart_task_or_review"],
    )
    append_checkpoint_with_policy(state.checkpoints, completion_checkpoint)
    save_run_state(session, state)
    write_json_trace(session, "checkpoint_completion.json", completion_checkpoint.to_dict())
    write_json_trace(session, "patient_bind_observation.json", observation.model_dump())
    append_event(
        session,
        "patient_bind_completed",
        {
            "patient_query": patient_query,
            "screenshot_path": str(screenshot_path),
            "proposed_next_actions": [item.action for item in observation.proposed_next_actions],
        },
    )
    return PatientBindOutcome(session=session, screenshot_path=screenshot_path, observation=observation)


def run_myle_bind_and_observe(task_name: str, patient_query: str, user_prompt: str) -> BindAndObserveOutcome:
    task = get_task(task_name)
    session = SessionContext(task_name=task.name, user_prompt=f"{patient_query} | {user_prompt}")
    ensure_artifact_policy_for_session(session)
    append_event(
        session,
        "bind_and_observe_started",
        {
            "task_name": task.name,
            "patient_query": patient_query,
            "user_prompt": user_prompt,
            "draft_only": task.draft_only,
        },
    )
    state = _initialize_run_state(
        session=session,
        draft_only=task.draft_only,
        user_prompt=user_prompt,
        patient_target=patient_query,
        task_understanding=f"Bind then observe for task '{task.name}'",
        next_actions=["bind_patient", "capture_bound_screen", "produce_structured_observation"],
    )
    _gate_clarification_or_raise(session=session, state=state)

    harness = PlaywrightHarness()
    try:
        harness.connect()
        harness.bind_patient_from_calendar(patient_query)
        screenshot_path = harness.capture_screenshot(session.screenshot_dir / "bind_and_observe.png")
        surface_state = harness.inspect_surface()
        active_url = surface_state.active_url
        surface = surface_state.surface_type
        state.latest_surface_state = surface_state
        mark_bound_patient_context(
            state,
            bound_patient_label=patient_query,
            bound_patient_identifier=patient_query,
            verification_source="calendar_bind",
            verification_confidence=0.7,
        )
        append_event(
            session,
            "bind_and_observe_screenshot_captured",
            {
                "patient_query": patient_query,
                "active_url": active_url,
                "surface": surface.value,
                "screenshot_path": str(screenshot_path),
            },
        )
        register_artifact(
            session,
            artifact_type="screenshot",
            artifact_path=screenshot_path,
            metadata={"surface": surface.value, "flow": "bind_and_observe"},
        )
    finally:
        harness.close()

    run_brief = build_run_brief(state)
    client = build_openai_client()
    response = client.responses.parse(
        model=OPENAI_MODEL,
        instructions=build_contract_aware_observation_prompt(
            contract=state.task_contract,
            run_state_summary=summarize_run_state(state),
            user_prompt=user_prompt,
        ),
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": run_brief},
                    {"type": "input_image", "image_url": _image_path_to_data_url(screenshot_path)},
                ],
            }
        ],
        text_format=ObservedScreenPlan,
        safety_identifier=f"{OPENAI_SAFETY_IDENTIFIER}:{task.name}:bind_and_observe",
    )

    observation = getattr(response, "output_parsed", None)
    if observation is None:
        raise RuntimeError("Model response did not contain parsed bind-and-observe output.")

    _record_observation(state=state, screenshot_path=screenshot_path, observation=observation, surface=surface)
    completion_checkpoint = make_completion_checkpoint(
        task_understanding=f"Bind and observe complete for task '{task.name}'",
        operational_understanding=build_operational_understanding_block(
            state,
            next_safest_actions=["human_review_observation"],
        ),
        where_looked=[episode.surface.value for episode in state.ledgers.search_episodes],
        found=[observation.screen_summary],
        why_done_or_not="Bound-chart observation produced.",
        next_actions=["human_review_observation"],
    )
    append_checkpoint_with_policy(state.checkpoints, completion_checkpoint)
    save_run_state(session, state)
    write_json_trace(session, "checkpoint_completion.json", completion_checkpoint.to_dict())
    write_json_trace(session, "bind_and_observe_observation.json", observation.model_dump())
    append_event(
        session,
        "bind_and_observe_completed",
        {
            "patient_query": patient_query,
            "screenshot_path": str(screenshot_path),
            "proposed_next_actions": [item.action for item in observation.proposed_next_actions],
        },
    )
    return BindAndObserveOutcome(session=session, screenshot_path=screenshot_path, observation=observation)


def run_myle_bind_open_documents_and_observe(
    task_name: str,
    patient_query: str,
    user_prompt: str,
) -> BindOpenDocumentsObserveOutcome:
    task = get_task(task_name)
    session = SessionContext(task_name=task.name, user_prompt=f"{patient_query} | {user_prompt}")
    ensure_artifact_policy_for_session(session)
    append_event(
        session,
        "bind_open_documents_and_observe_started",
        {
            "task_name": task.name,
            "patient_query": patient_query,
            "user_prompt": user_prompt,
            "draft_only": task.draft_only,
        },
    )
    state = _initialize_run_state(
        session=session,
        draft_only=task.draft_only,
        user_prompt=user_prompt,
        patient_target=patient_query,
        task_understanding=f"Bind, open Documents, then observe for task '{task.name}'",
        next_actions=["bind_patient", "open_documents", "capture_and_observe"],
    )
    _gate_clarification_or_raise(session=session, state=state)

    harness = PlaywrightHarness()
    try:
        harness.connect()
        harness.bind_patient_from_calendar(patient_query)
        harness.open_current_patient_documents()
        screenshot_path = harness.capture_screenshot(session.screenshot_dir / "bind_open_documents_and_observe.png")
        surface_state = harness.inspect_surface()
        active_url = surface_state.active_url
        surface = surface_state.surface_type
        state.latest_surface_state = surface_state
        mark_bound_patient_context(
            state,
            bound_patient_label=patient_query,
            bound_patient_identifier=patient_query,
            verification_source="calendar_bind",
            verification_confidence=0.7,
        )
        append_event(
            session,
            "bind_open_documents_and_observe_screenshot_captured",
            {
                "patient_query": patient_query,
                "active_url": active_url,
                "surface": surface.value,
                "screenshot_path": str(screenshot_path),
            },
        )
        register_artifact(
            session,
            artifact_type="screenshot",
            artifact_path=screenshot_path,
            metadata={"surface": surface.value, "flow": "bind_open_documents_and_observe"},
        )
    finally:
        harness.close()

    run_brief = build_run_brief(state)
    client = build_openai_client()
    response = client.responses.parse(
        model=OPENAI_MODEL,
        instructions=build_contract_aware_observation_prompt(
            contract=state.task_contract,
            run_state_summary=summarize_run_state(state),
            user_prompt=user_prompt,
        ),
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": run_brief},
                    {"type": "input_image", "image_url": _image_path_to_data_url(screenshot_path)},
                ],
            }
        ],
        text_format=ObservedScreenPlan,
        safety_identifier=f"{OPENAI_SAFETY_IDENTIFIER}:{task.name}:bind_docs_obs",
    )

    observation = getattr(response, "output_parsed", None)
    if observation is None:
        raise RuntimeError("Model response did not contain parsed bind-open-documents output.")

    _record_observation(state=state, screenshot_path=screenshot_path, observation=observation, surface=surface)
    completion_checkpoint = make_completion_checkpoint(
        task_understanding=f"Bind/open Documents/observe complete for task '{task.name}'",
        operational_understanding=build_operational_understanding_block(
            state,
            next_safest_actions=["human_review_observation"],
        ),
        where_looked=[episode.surface.value for episode in state.ledgers.search_episodes],
        found=[observation.screen_summary],
        why_done_or_not="Documents-surface observation produced.",
        next_actions=["human_review_observation"],
    )
    append_checkpoint_with_policy(state.checkpoints, completion_checkpoint)
    save_run_state(session, state)

    write_json_trace(session, "checkpoint_completion.json", completion_checkpoint.to_dict())
    write_json_trace(session, "bind_open_documents_and_observe_observation.json", observation.model_dump())
    append_event(
        session,
        "bind_open_documents_and_observe_completed",
        {
            "patient_query": patient_query,
            "screenshot_path": str(screenshot_path),
            "proposed_next_actions": [item.action for item in observation.proposed_next_actions],
        },
    )
    return BindOpenDocumentsObserveOutcome(session=session, screenshot_path=screenshot_path, observation=observation)
