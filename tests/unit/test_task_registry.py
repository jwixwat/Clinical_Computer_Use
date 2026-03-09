from clinical_computer_use.tasks.registry import get_task


def test_known_task_is_registered() -> None:
    task = get_task("insurance_form_draft")
    assert task.name == "insurance_form_draft"
    assert task.draft_only is True

