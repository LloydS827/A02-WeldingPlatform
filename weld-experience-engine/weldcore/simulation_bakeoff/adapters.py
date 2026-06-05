from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from weldcore.simulation_bakeoff.maniskill_adapter import adapt_maniskill_artifact
from weldcore.simulation_bakeoff.maniskill_contract import RawManiSkillArtifact, read_json_artifact
from weldcore.simulation_bakeoff.model import (
    SimulationPathPoint,
    SimulationTaskSpec,
    SimulatorAdapterResult,
)


def run_simlite_reference(task_spec: SimulationTaskSpec) -> SimulatorAdapterResult:
    return SimulatorAdapterResult(
        adapter_name="simlite_reference",
        task_id=task_spec.task_id,
        status="completed",
        tcp_trajectory=task_spec.seam_path,
        tool_orientation=task_spec.seam_path,
        planning_result={
            "attempted": True,
            "validated_task_contract": True,
            "task_status": "completed",
        },
        failure_boundary=(),
        metrics={
            "path_continuity": 1.0,
            "posture_stability": 1.0,
            "digital_asset_ready": 1.0,
        },
        artifacts={},
        evidence_notes=("r0_baseline", "not_final_simulator_selection"),
    )


def attempt_maniskill_sapien(
    task_spec: SimulationTaskSpec,
    raw_artifact_path: str | Path | None = None,
) -> SimulatorAdapterResult:
    if raw_artifact_path is not None:
        artifact_path = Path(raw_artifact_path)
        if not artifact_path.exists():
            return _failed_external_attempt(
                adapter_name="maniskill_sapien",
                task_spec=task_spec,
                failure_boundary=("artifact_missing",),
            )
        try:
            artifact = _raw_maniskill_artifact_from_data(read_json_artifact(artifact_path))
            return adapt_maniskill_artifact(task_spec, artifact)
        except Exception:
            return _failed_external_attempt(
                adapter_name="maniskill_sapien",
                task_spec=task_spec,
                failure_boundary=("adapter_conversion_failed",),
            )

    dependency_found = _any_dependency_found(("mani_skill", "sapien"))
    if not dependency_found:
        return _failed_external_attempt(
            adapter_name="maniskill_sapien",
            task_spec=task_spec,
            failure_boundary=(
                "optional_dependency_missing",
                "mani_skill_or_sapien_not_available",
            ),
        )

    return _failed_external_attempt(
        adapter_name="maniskill_sapien",
        task_spec=task_spec,
        failure_boundary=("external_spike_not_executed", "task_contract_not_validated"),
    )


def attempt_gazebo_moveit(task_spec: SimulationTaskSpec) -> SimulatorAdapterResult:
    dependency_found = _any_dependency_found(("rclpy", "moveit", "moveit_configs_utils"))
    if not dependency_found:
        return _failed_external_attempt(
            adapter_name="gazebo_moveit",
            task_spec=task_spec,
            failure_boundary=(
                "optional_dependency_missing",
                "rclpy_moveit_or_moveit_configs_utils_not_available",
            ),
        )

    return _failed_external_attempt(
        adapter_name="gazebo_moveit",
        task_spec=task_spec,
        failure_boundary=("external_spike_not_executed", "task_contract_not_validated"),
    )


def _any_dependency_found(module_names: tuple[str, ...]) -> bool:
    return any(importlib.util.find_spec(module_name) is not None for module_name in module_names)


def _raw_maniskill_artifact_from_data(data: dict[str, Any]) -> RawManiSkillArtifact:
    return RawManiSkillArtifact(
        run_id=data["run_id"],
        task_id=data["task_id"],
        status=data["status"],
        tcp_trajectory=_path_points_from_data(data["tcp_trajectory"]),
        tool_orientation=_path_points_from_data(data["tool_orientation"]),
        task_state=dict(data["task_state"]),
        metrics=dict(data["metrics"]),
        failure_boundary=tuple(data["failure_boundary"]),
        artifacts=dict(data["artifacts"]),
        evidence_notes=tuple(data["evidence_notes"]),
    )


def _path_points_from_data(points: list[dict[str, Any]]) -> tuple[SimulationPathPoint, ...]:
    return tuple(SimulationPathPoint(**point) for point in points)


def _failed_external_attempt(
    *,
    adapter_name: str,
    task_spec: SimulationTaskSpec,
    failure_boundary: tuple[str, ...],
) -> SimulatorAdapterResult:
    return SimulatorAdapterResult(
        adapter_name=adapter_name,
        task_id=task_spec.task_id,
        status="failed",
        tcp_trajectory=(),
        tool_orientation=(),
        planning_result={
            "attempted": True,
            "validated_task_contract": False,
            "task_status": "failed",
        },
        failure_boundary=failure_boundary,
        metrics={
            "same_task_attempted": 1.0,
            "task_contract_outputs_ready": 0.0,
        },
        artifacts={},
        evidence_notes=("not_final_simulator_selection",),
    )
