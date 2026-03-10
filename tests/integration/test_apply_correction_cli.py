import pytest


def test_cli_parser_includes_n1_commands() -> None:
    pytest.importorskip("playwright")

    from clinical_computer_use.main import build_parser

    parser = build_parser()
    subparsers_actions = [a for a in parser._actions if getattr(a, "choices", None)]
    assert subparsers_actions, "No subparsers found."
    choices = set(subparsers_actions[0].choices.keys())
    assert "apply-correction" in choices
    assert "summarize-run" in choices
    assert "continue-agent-task" in choices
    assert "handoff-run" in choices
    assert "cleanup-artifacts" in choices
    assert "stop-run" in choices
    assert "archive-run" in choices
