"""
Minimal CLI entrypoint for the scaffold.
"""

from __future__ import annotations

import argparse

from .runner import (
    run_myle_bind_open_documents_and_observe,
    run_myle_bind_and_agent_task,
    run_browser_observation,
    run_myle_bind_and_observe,
    run_myle_observation,
    run_myle_patient_bind,
    run_task,
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
    observe_parser.add_argument(
        "--url",
        default="https://example.com",
        help="Harmless target URL for screenshot observation",
    )

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
            outcome = run_myle_bind_and_agent_task(args.task_name, args.patient_query, args.prompt)
        else:
            outcome = run_myle_observation(args.task_name, args.prompt)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 1

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
    elif args.command == "bind-and-agent-task":
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
