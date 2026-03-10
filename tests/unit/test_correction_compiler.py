from clinical_computer_use.agent.contracts import apply_correction, compile_task_contract
from clinical_computer_use.schemas.contract_types import ArtifactClass, SurfaceType


def test_apply_correction_updates_contract_and_mutations() -> None:
    base = compile_task_contract(user_prompt="Find forms in chart").contract
    result = apply_correction(base, "Not a note. Documents first. After 2024-10-10")
    assert ArtifactClass.CHART_NOTE in result.contract.disallowed_artifact_classes
    assert result.contract.preferred_surfaces[0] == SurfaceType.DOCUMENTS
    assert result.contract.date_floor == "2024-10-10"
    assert len(result.delta.contract_changes) >= 2
