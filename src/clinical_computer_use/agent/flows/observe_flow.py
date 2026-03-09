"""Observation and bind flow implementations."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

from clinical_computer_use.config import EMR_BASE_URL, OPENAI_MODEL, OPENAI_SAFETY_IDENTIFIER
from clinical_computer_use.kernel.browser.playwright_harness import PlaywrightHarness
from clinical_computer_use.openai_client import build_openai_client
from clinical_computer_use.prompts import build_myle_observation_prompt, build_myle_patient_bind_prompt
from clinical_computer_use.runtime.artifacts import append_event, write_json_trace
from clinical_computer_use.runtime.checkpoints import make_start_checkpoint
from clinical_computer_use.runtime.ledgers import build_empty_ledgers
from clinical_computer_use.runtime.run_state import SessionContext
from clinical_computer_use.schemas.agent_plan import ObservedScreenPlan
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


def run_browser_observation(task_name: str, user_prompt: str, target_url: str) -> BrowserObservationOutcome:
    """
    Open a harmless browser page, capture a screenshot, and have the model
    describe the screen plus propose next actions without executing anything.
    """
    task = get_task(task_name)
    session = SessionContext(task_name=task.name, user_prompt=user_prompt)
    append_event(
        session,
        "browser_observation_started",
        {
            "task_name": task.name,
            "target_url": target_url,
            "draft_only": task.draft_only,
        },
    )
    write_json_trace(session, "ledgers.json", build_empty_ledgers().to_dict())
    write_json_trace(
        session,
        "checkpoint_start.json",
        make_start_checkpoint(
            task_understanding=f"Observe screen for task '{task.name}'",
            next_actions=["capture_screenshot", "produce_structured_observation"],
        ).to_dict(),
    )

    harness = PlaywrightHarness()
    try:
        harness.connect()
        if target_url == EMR_BASE_URL:
            harness.ensure_myle_ready()
        else:
            harness.open_url(target_url)
        screenshot_path = harness.capture_screenshot(session.screenshot_dir / "screen.png")
        append_event(
            session,
            "browser_screenshot_captured",
            {
                "target_url": target_url,
                "active_url": harness.state.active_url,
                "screenshot_path": str(screenshot_path),
            },
        )
    finally:
        harness.close()

    client = build_openai_client()
    response = client.responses.parse(
        model=OPENAI_MODEL,
        instructions=build_myle_observation_prompt(user_prompt),
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": f"Observe this screen for task '{task.name}'."},
                    {
                        "type": "input_image",
                        "image_url": _image_path_to_data_url(screenshot_path),
                    },
                ],
            }
        ],
        text_format=ObservedScreenPlan,
        safety_identifier=f"{OPENAI_SAFETY_IDENTIFIER}:{task.name}:observe",
    )

    observation = getattr(response, "output_parsed", None)
    if observation is None:
        raise RuntimeError("Model response did not contain parsed observed screen output.")

    write_json_trace(session, "observation.json", observation.model_dump())
    append_event(
        session,
        "browser_observation_completed",
        {
            "screenshot_path": str(screenshot_path),
            "proposed_next_actions": [item.action for item in observation.proposed_next_actions],
        },
    )
    return BrowserObservationOutcome(
        session=session,
        screenshot_path=screenshot_path,
        observation=observation,
    )


def run_myle_observation(task_name: str, user_prompt: str) -> BrowserObservationOutcome:
    """
    Observe the currently available Myle context in the dedicated agent profile.
    """
    return run_browser_observation(task_name=task_name, user_prompt=user_prompt, target_url=EMR_BASE_URL)


def run_myle_patient_bind(task_name: str, patient_query: str) -> PatientBindOutcome:
    """
    Cold-start patient binding flow: launch/attach, login if needed, open Calendar,
    search for the intended patient, select the result, then stop and observe.
    """
    task = get_task(task_name)
    session = SessionContext(task_name=task.name, user_prompt=patient_query)
    append_event(
        session,
        "patient_bind_started",
        {
            "task_name": task.name,
            "patient_query": patient_query,
            "draft_only": task.draft_only,
        },
    )
    write_json_trace(session, "ledgers.json", build_empty_ledgers().to_dict())
    write_json_trace(
        session,
        "checkpoint_start.json",
        make_start_checkpoint(
            task_understanding=f"Bind patient for task '{task.name}'",
            next_actions=["calendar_search", "patient_selection", "screen_assessment"],
        ).to_dict(),
    )

    harness = PlaywrightHarness()
    try:
        harness.connect()
        harness.bind_patient_from_calendar(patient_query)
        screenshot_path = harness.capture_screenshot(session.screenshot_dir / "patient_bind.png")
        append_event(
            session,
            "patient_bind_screenshot_captured",
            {
                "patient_query": patient_query,
                "active_url": harness.state.active_url,
                "screenshot_path": str(screenshot_path),
            },
        )
    finally:
        harness.close()

    client = build_openai_client()
    response = client.responses.parse(
        model=OPENAI_MODEL,
        instructions=build_myle_patient_bind_prompt(patient_query),
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": f"Assess whether this screen appears bound to patient query '{patient_query}'."},
                    {
                        "type": "input_image",
                        "image_url": _image_path_to_data_url(screenshot_path),
                    },
                ],
            }
        ],
        text_format=ObservedScreenPlan,
        safety_identifier=f"{OPENAI_SAFETY_IDENTIFIER}:{task.name}:bind_patient",
    )

    observation = getattr(response, "output_parsed", None)
    if observation is None:
        raise RuntimeError("Model response did not contain parsed patient-bind output.")

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
    return PatientBindOutcome(
        session=session,
        screenshot_path=screenshot_path,
        observation=observation,
    )


def run_myle_bind_and_observe(task_name: str, patient_query: str, user_prompt: str) -> BindAndObserveOutcome:
    """
    Single-run cold-start flow: launch/attach, login if needed, bind patient,
    then observe the resulting patient chart from the same live page without
    navigating away.
    """
    task = get_task(task_name)
    session = SessionContext(task_name=task.name, user_prompt=f"{patient_query} | {user_prompt}")
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
    write_json_trace(session, "ledgers.json", build_empty_ledgers().to_dict())
    write_json_trace(
        session,
        "checkpoint_start.json",
        make_start_checkpoint(
            task_understanding=f"Bind then observe for task '{task.name}'",
            next_actions=["bind_patient", "capture_bound_screen", "produce_structured_observation"],
        ).to_dict(),
    )

    harness = PlaywrightHarness()
    try:
        harness.connect()
        harness.bind_patient_from_calendar(patient_query)
        screenshot_path = harness.capture_screenshot(session.screenshot_dir / "bind_and_observe.png")
        append_event(
            session,
            "bind_and_observe_screenshot_captured",
            {
                "patient_query": patient_query,
                "active_url": harness.state.active_url,
                "screenshot_path": str(screenshot_path),
            },
        )
    finally:
        harness.close()

    client = build_openai_client()
    response = client.responses.parse(
        model=OPENAI_MODEL,
        instructions=build_myle_observation_prompt(user_prompt),
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            f"The patient bind step has already been completed for query '{patient_query}'. "
                            "Observe the resulting screen only."
                        ),
                    },
                    {
                        "type": "input_image",
                        "image_url": _image_path_to_data_url(screenshot_path),
                    },
                ],
            }
        ],
        text_format=ObservedScreenPlan,
        safety_identifier=f"{OPENAI_SAFETY_IDENTIFIER}:{task.name}:bind_and_observe",
    )

    observation = getattr(response, "output_parsed", None)
    if observation is None:
        raise RuntimeError("Model response did not contain parsed bind-and-observe output.")

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
    return BindAndObserveOutcome(
        session=session,
        screenshot_path=screenshot_path,
        observation=observation,
    )


def run_myle_bind_open_documents_and_observe(
    task_name: str,
    patient_query: str,
    user_prompt: str,
) -> BindOpenDocumentsObserveOutcome:
    """
    Single-run staged flow: cold start, bind patient, open Documents for the
    bound patient, then stop and observe from that screen.
    """
    task = get_task(task_name)
    session = SessionContext(task_name=task.name, user_prompt=f"{patient_query} | {user_prompt}")
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
    write_json_trace(session, "ledgers.json", build_empty_ledgers().to_dict())
    write_json_trace(
        session,
        "checkpoint_start.json",
        make_start_checkpoint(
            task_understanding=f"Bind, open Documents, then observe for task '{task.name}'",
            next_actions=["bind_patient", "open_documents", "capture_and_observe"],
        ).to_dict(),
    )

    harness = PlaywrightHarness()
    try:
        harness.connect()
        harness.bind_patient_from_calendar(patient_query)
        harness.open_current_patient_documents()
        screenshot_path = harness.capture_screenshot(session.screenshot_dir / "bind_open_documents_and_observe.png")
        append_event(
            session,
            "bind_open_documents_and_observe_screenshot_captured",
            {
                "patient_query": patient_query,
                "active_url": harness.state.active_url,
                "screenshot_path": str(screenshot_path),
            },
        )
    finally:
        harness.close()

    client = build_openai_client()
    response = client.responses.parse(
        model=OPENAI_MODEL,
        instructions=build_myle_observation_prompt(user_prompt),
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            f"The patient bind step has already been completed for query '{patient_query}', "
                            "and the Documents section has already been opened. Observe the resulting screen only."
                        ),
                    },
                    {
                        "type": "input_image",
                        "image_url": _image_path_to_data_url(screenshot_path),
                    },
                ],
            }
        ],
        text_format=ObservedScreenPlan,
        safety_identifier=f"{OPENAI_SAFETY_IDENTIFIER}:{task.name}:bind_docs_obs",
    )

    observation = getattr(response, "output_parsed", None)
    if observation is None:
        raise RuntimeError("Model response did not contain parsed bind-open-documents output.")

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
    return BindOpenDocumentsObserveOutcome(
        session=session,
        screenshot_path=screenshot_path,
        observation=observation,
    )
