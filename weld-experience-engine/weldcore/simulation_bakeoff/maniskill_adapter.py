from __future__ import annotations

from weldcore.simulation_bakeoff.maniskill_contract import (
    ExperienceDataset,
    RawManiSkillArtifact,
)
from weldcore.simulation_bakeoff.model import SimulationTaskSpec, SimulatorAdapterResult


def adapt_maniskill_artifact(
    task_spec: SimulationTaskSpec,
    artifact: RawManiSkillArtifact,
) -> SimulatorAdapterResult:
    return SimulatorAdapterResult(
        adapter_name="maniskill_sapien",
        task_id=task_spec.task_id,
        status=artifact.status,
        tcp_trajectory=artifact.tcp_trajectory,
        tool_orientation=artifact.tool_orientation,
        planning_result={
            "attempted": True,
            "validated_task_contract": artifact.status == "completed",
            "task_status": artifact.status,
            "task_state": artifact.task_state,
        },
        failure_boundary=artifact.failure_boundary,
        metrics=dict(artifact.metrics),
        artifacts=dict(artifact.artifacts),
        evidence_notes=(
            *artifact.evidence_notes,
            "experience_dataset_not_robot_process_package",
        ),
    )


def build_maniskill_experience_dataset(
    task_spec: SimulationTaskSpec,
    artifact: RawManiSkillArtifact,
) -> ExperienceDataset:
    sample_id = f"sample-maniskill-{task_spec.task_id}"
    return ExperienceDataset(
        dataset_id=f"experience-maniskill-{task_spec.task_id}",
        source_type="simulation",
        task_id=task_spec.task_id,
        samples=(sample_id,) if artifact.status == "completed" else (),
        review_status="not_reviewed",
        validation_status="simulation_only",
        quality_feedback_status="not_available",
        compatibility_exports=("SkillDataset",),
        evidence_boundary=(
            "not_robot_process_package",
            "not_real_welding_quality_validation",
            "not_WPS_PQR",
        ),
    )
