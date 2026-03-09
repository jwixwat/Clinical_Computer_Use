import pytest


def test_cli_parser_includes_expected_commands() -> None:
    pytest.importorskip("playwright")

    from clinical_computer_use.main import build_parser

    parser = build_parser()
    subparsers_actions = [a for a in parser._actions if getattr(a, "choices", None)]
    assert subparsers_actions, "No subparsers found."
    choices = set(subparsers_actions[0].choices.keys())
    assert {
        "plan",
        "observe",
        "observe-myle",
        "bind-patient",
        "bind-and-observe",
        "bind-open-documents-and-observe",
        "bind-and-agent-task",
    }.issubset(choices)

