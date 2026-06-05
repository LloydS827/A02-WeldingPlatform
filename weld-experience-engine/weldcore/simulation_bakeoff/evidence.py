from __future__ import annotations

from math import dist

from weldcore.model import (
    SimulationRunRecord,
    SimulationRunStatus,
    SimulatorName,
    SkillDataset,
    SkillSample,
    SourceType,
    WeldCondition,
)
from weldcore.model.trajectory import Trajectory, TrajectorySample
from weldcore.simulation_bakeoff.model import (
    SimulationEvidenceBundle,
    SimulationPathPoint,
    SimulationTaskSpec,
    SimulatorAdapterResult,
)


GENERATION_BOUNDARY = (
    "not WPS/PQR",
    "not real welding quality validation",
    "not final simulator selection",
)
RERUN_NOTES = ("rerun_optional_not_attempted_by_evidence_builder",)


def build_simulation_evidence_bundle(
    task_spec: SimulationTaskSpec,
    adapter_result: SimulatorAdapterResult,
) -> SimulationEvidenceBundle:
    status = (
        SimulationRunStatus.COMPLETED
        if adapter_result.status == "completed"
        else SimulationRunStatus.FAILED
    )
    dataset = (
        _build_dataset(task_spec, adapter_result)
        if status == SimulationRunStatus.COMPLETED
        else None
    )
    sample_count = len(dataset.samples) if dataset is not None else 0
    run_record = SimulationRunRecord(
        simulation_run_id=f"run-{adapter_result.adapter_name}-{task_spec.task_id}",
        input_id=task_spec.task_id,
        simulator=_simulator_name(adapter_result.adapter_name),
        simulator_version="bakeoff-v0.1",
        adapter_version="bakeoff-v0.1",
        seed=None,
        sample_count=sample_count,
        status=status,
        created_at="2026-06-04T00:00:00Z",
        completed_at="2026-06-04T00:00:00Z",
        output_bundle_uris=[],
        errors=list(adapter_result.failure_boundary),
        boundary_notes=[
            *GENERATION_BOUNDARY,
            *adapter_result.evidence_notes,
            *adapter_result.failure_boundary,
        ],
    )
    return SimulationEvidenceBundle(
        bundle_id=f"evidence-{adapter_result.adapter_name}-{task_spec.task_id}",
        task_spec=task_spec,
        adapter_result=adapter_result,
        run_record=run_record,
        dataset=dataset,
        rerun_replay_uri=None,
        rerun_replay_status="not_attempted",
        rerun_notes=RERUN_NOTES,
        bakeoff_score=dict(adapter_result.metrics),
    )


def _simulator_name(adapter_name: str) -> SimulatorName:
    if adapter_name == "simlite_reference":
        return SimulatorName.SIMLITE
    if adapter_name == "maniskill_sapien":
        return SimulatorName.MANISKILL
    return SimulatorName.OTHER


def _build_dataset(
    task_spec: SimulationTaskSpec,
    adapter_result: SimulatorAdapterResult,
) -> SkillDataset:
    sample = SkillSample(
        sample_id=f"sample-{adapter_result.adapter_name}-{task_spec.task_id}",
        weld_condition=_weld_condition_from_task_spec(task_spec),
        trajectory=_trajectory_from_points(adapter_result.tcp_trajectory),
        process_signals=[],
        metadata={
            "task_spec": task_spec.to_dict(),
            "adapter_result": adapter_result.to_dict(),
            "requires_real_validation_later": True,
            "generation_boundary": GENERATION_BOUNDARY,
        },
    )
    return SkillDataset(
        dataset_id=f"dataset-{adapter_result.adapter_name}-{task_spec.task_id}",
        source_type=SourceType.SIMULATION,
        task=task_spec.unit_id,
        samples=[sample],
        license_and_rights="simulation evidence only; requires real validation later",
    )


def _trajectory_from_points(points: tuple[SimulationPathPoint, ...]) -> Trajectory:
    return Trajectory(
        samples=[
            TrajectorySample(
                t=point.t,
                x=point.x,
                y=point.y,
                z=point.z,
                rx=point.rx,
                ry=point.ry,
                rz=point.rz,
            )
            for point in points
        ]
    )


def _weld_condition_from_task_spec(task_spec: SimulationTaskSpec) -> WeldCondition:
    return WeldCondition(
        weld_type=task_spec.unit_id,
        joint_type="simulation_task",
        plate_thickness_mm=0.0,
        groove_width_mm=0.0,
        length_mm=_path_length(task_spec.seam_path),
        position="horizontal" if "horizontal" in task_spec.unit_id else "unknown",
        material="unknown",
        motion_structure="; ".join(task_spec.motion_constraint),
    )


def _path_length(points: tuple[SimulationPathPoint, ...]) -> float:
    return sum(
        dist((start.x, start.y, start.z), (end.x, end.y, end.z))
        for start, end in zip(points, points[1:])
    )
