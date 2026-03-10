from clinical_computer_use.schemas.contract_types import ArtifactMatchMode, ObjectiveType
from clinical_computer_use.schemas.task_contract import TaskContract


def test_task_contract_defaults() -> None:
    contract = TaskContract()
    assert contract.objective_type == ObjectiveType.FIND
    assert contract.contract_version == "n1.v2"
    assert contract.artifact_match_mode == ArtifactMatchMode.FAMILY
    assert isinstance(contract.preferred_surfaces, list)
    assert contract.task_review_threshold is None
