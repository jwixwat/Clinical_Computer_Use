"""
Minimal CLI entrypoint for the scaffold.
"""

from __future__ import annotations

import argparse
import json

from .runner import (
    apply_run_correction,
    archive_run,
    build_run_handoff,
    cleanup_artifacts,
    continue_myle_agent_task,
    run_myle_bind_open_documents_and_observe,
    run_myle_bind_and_agent_task,
    run_browser_observation,
    run_myle_bind_and_observe,
    run_myle_observation,
    run_myle_patient_bind,
    run_task,
    stop_run,
    summarize_run,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="clinical_computer_use scaffold CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan", help="Run text-only supervised planning")
    plan_parser.add_argument("task_name", help="Registered task name")
    plan_parser.add_argument("prompt", help="User prompt for the run")

    observe_parser = subparsers.add_parser("observe", help="Run read-only browser observation")
    observe_parser.add_argument("task_name", help="Registered task name")
    observe_parser.add_argument("prompt", help="User prompt for the run")
    observe_parser.add_argument("--url", default="https://example.com", help="Harmless target URL for screenshot observation")

    observe_myle_parser = subparsers.add_parser("observe-myle", help="Observe the current Myle context")
    observe_myle_parser.add_argument("task_name", help="Registered task name")
    observe_myle_parser.add_argument("prompt", help="User prompt for the run")

    bind_patient_parser = subparsers.add_parser("bind-patient", help="Cold-start bind the dedicated Myle browser to a patient")
    bind_patient_parser.add_argument("task_name", help="Registered task name")
    bind_patient_parser.add_argument("patient_query", help="Patient name or identifier to search from Calendar")

    bind_observe_parser = subparsers.add_parser(
        "bind-and-observe",
        help="Cold-start bind to a patient, then observe the resulting chart in the same run",
    )
    bind_observe_parser.add_argument("task_name", help="Registered task name")
    bind_observe_parser.add_argument("patient_query", help="Patient name or identifier to search from Calendar")
    bind_observe_parser.add_argument("prompt", help="Read-only observation prompt to run after patient bind")

    bind_documents_observe_parser = subparsers.add_parser(
        "bind-open-documents-and-observe",
        help="Cold-start bind to a patient, open Documents, then observe in the same run",
    )
    bind_documents_observe_parser.add_argument("task_name", help="Registered task name")
    bind_documents_observe_parser.add_argument("patient_query", help="Patient name or identifier to search from Calendar")
    bind_documents_observe_parser.add_argument("prompt", help="Read-only observation prompt to run after opening Documents")

    bind_agent_parser = subparsers.add_parser(
        "bind-and-agent-task",
        help="Cold-start bind to a patient, then let the model choose constrained in-chart actions",
    )
    bind_agent_parser.add_argument("task_name", help="Registered task name")
    bind_agent_parser.add_argument("patient_query", help="Patient name or identifier to search from Calendar")
    bind_agent_parser.add_argument("prompt", help="In-chart task instruction")
    bind_agent_parser.add_argument("--max-steps", type=int, default=8, help="Maximum new steps for this run leg")

    continue_agent_parser = subparsers.add_parser(
        "continue-agent-task",
        help="Continue a previously started in-chart run from persisted run_state",
    )
    continue_agent_parser.add_argument("session_id", help="Session id to continue")
    continue_agent_parser.add_argument("--max-steps", type=int, default=8, help="Maximum additional steps for this continuation leg")

    correction_parser = subparsers.add_parser("apply-correction", help="Apply free-text correction to existing run state")
    correction_parser.add_argument("session_id", help="Session id to update")
    correction_parser.add_argument("correction_text", help="Correction text from user")

    summarize_parser = subparsers.add_parser("summarize-run", help="Summarize persisted run state")
    summarize_parser.add_argument("session_id", help="Session id to summarize")

    handoff_parser = subparsers.add_parser("handoff-run", help="Generate structured human handoff packet")
    handoff_parser.add_argument("session_id", help="Session id to summarize as handoff")

    cleanup_parser = subparsers.add_parser("cleanup-artifacts", help="Cleanup tracked PHI-bearing artifacts by age")
    cleanup_parser.add_argument("--older-than-days", type=int, default=14, help="Delete tracked artifacts older than N days")
    cleanup_parser.add_argument("--dry-run", action="store_true", help="Report cleanup candidates without deleting files")

    stop_parser = subparsers.add_parser("stop-run", help="Mark a run as stopped (resumable until archived)")
    stop_parser.add_argument("session_id", help="Session id to stop")
    stop_parser.add_argument("--reason", default="manual_stop", help="Lifecycle reason")

    archive_parser = subparsers.add_parser("archive-run", help="Mark a run as archived (non-resumable)")
    archive_parser.add_argument("session_id", help="Session id to archive")
    archive_parser.add_argument("--reason", default="manual_archive", help="Lifecycle reason")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "plan":
            outcome = run_task(args.task_name, args.prompt)
        elif args.command == "observe":
            outcome = run_browser_observation(args.task_name, args.prompt, args.url)
        elif args.command == "bind-patient":
            outcome = run_myle_patient_bind(args.task_name, args.patient_query)
        elif args.command == "bind-and-observe":
            outcome = run_myle_bind_and_observe(args.task_name, args.patient_query, args.prompt)
        elif args.command == "bind-open-documents-and-observe":
            outcome = run_myle_bind_open_documents_and_observe(args.task_name, args.patient_query, args.prompt)
        elif args.command == "bind-and-agent-task":
            outcome = run_myle_bind_and_agent_task(args.task_name, args.patient_query, args.prompt, max_steps=args.max_steps)
        elif args.command == "continue-agent-task":
            outcome = continue_myle_agent_task(args.session_id, max_steps=args.max_steps)
        elif args.command == "apply-correction":
            outcome = apply_run_correction(args.session_id, args.correction_text)
        elif args.command == "summarize-run":
            outcome = summarize_run(args.session_id)
        elif args.command == "handoff-run":
            outcome = build_run_handoff(args.session_id)
        elif args.command == "cleanup-artifacts":
            outcome = cleanup_artifacts(older_than_days=args.older_than_days, dry_run=args.dry_run)
        elif args.command == "stop-run":
            outcome = stop_run(args.session_id, reason=args.reason)
        elif args.command == "archive-run":
            outcome = archive_run(args.session_id, reason=args.reason)
        else:
            outcome = run_myle_observation(args.task_name, args.prompt)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 1

    if args.command == "apply-correction":
        print(f"Applied correction to session '{outcome.state.session_id}'.")
        print(f"Contract history entries: {len(outcome.state.contract_history)}")
        print(f"Latest objective: {outcome.state.task_contract.objective_type.value}")
        return 0

    if args.command == "summarize-run":
        print(json.dumps(outcome.summary, indent=2))
        return 0

    if args.command == "handoff-run":
        print(json.dumps(outcome.handoff.to_dict(), indent=2))
        return 0

    if args.command == "cleanup-artifacts":
        print(json.dumps(outcome.summary, indent=2))
        return 0

    if args.command in {"stop-run", "archive-run"}:
        print(f"Run '{outcome.state.session_id}' lifecycle_state={outcome.state.lifecycle_state.value}")
        print(f"Lifecycle reason: {outcome.state.lifecycle_reason}")
        return 0

    print(f"Started session {outcome.session.session_id} for task '{outcome.session.task_name}'.")
    print(f"Trace directory: {outcome.session.trace_dir}")

    if args.command == "plan":
        print(f"Summary: {outcome.plan.task_summary}")
        if outcome.plan.uncertainties:
            print("Uncertainties:")
            for item in outcome.plan.uncertainties:
                print(f"- {item}")
        if outcome.blocked_actions:
            print("Blocked actions proposed by the model:")
            for item in outcome.blocked_actions:
                print(f"- {item}")
    elif args.command in {"bind-and-agent-task", "continue-agent-task"}:
        print(f"Screenshot: {outcome.screenshot_path}")
        print(f"Final report: {outcome.final_report}")
    else:
        print(f"Screenshot: {outcome.screenshot_path}")
        print(f"Screen summary: {outcome.observation.screen_summary}")
        if outcome.observation.uncertainty_flags:
            print("Uncertainty flags:")
            for item in outcome.observation.uncertainty_flags:
                print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
