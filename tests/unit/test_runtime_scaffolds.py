from clinical_computer_use.runtime.checkpoints import make_start_checkpoint
from clinical_computer_use.runtime.ledgers import build_empty_ledgers


def test_start_checkpoint_shape() -> None:
    checkpoint = make_start_checkpoint("test task", ["step_a"])
    payload = checkpoint.to_dict()
    assert payload["task_understanding"] == "test task"
    assert payload["stage"] == "start"
    assert payload["next_actions"] == ["step_a"]


def test_empty_ledgers_shape() -> None:
    ledgers = build_empty_ledgers().to_dict()
    assert "search" in ledgers
    assert "evidence" in ledgers
    assert ledgers["rejected_candidates"] == []

