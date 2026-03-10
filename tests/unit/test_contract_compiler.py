from clinical_computer_use.agent.contracts import compile_task_contract
from clinical_computer_use.schemas.contract_types import ArtifactClass, SurfaceType


def test_compile_task_contract_extracts_constraints() -> None:
    result = compile_task_contract(
        user_prompt=(
            "Find the external firearms form, not a chart note, documents first, "
            "after 2025-01-01, and cite sources."
        ),
        patient_target="9093258013",
    )
    contract = result.contract
    assert contract.patient_target == "9093258013"
    assert SurfaceType.DOCUMENTS in contract.preferred_surfaces
    assert contract.date_floor == "2025-01-01"
    assert ArtifactClass.CHART_NOTE in contract.disallowed_artifact_classes
    assert ArtifactClass.EXTERNAL_DOCUMENT in contract.acceptable_artifact_classes
    assert contract.diagnostics.confidence > 0.0
