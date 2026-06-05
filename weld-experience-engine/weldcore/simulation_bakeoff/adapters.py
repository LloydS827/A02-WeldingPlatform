from __future__ import annotations

import importlib.util

from weldcore.simulation_bakeoff.model import SimulationTaskSpec, SimulatorAdapterResult


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


def attempt_maniskill_sapien(task_spec: SimulationTaskSpec) -> SimulatorAdapterResult:
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


def _failed_external_attempt(
    *,
    adapter_name: str,
    task_spec: SimulationTaskSpec,
    failure_boundary: tuple[str, str],
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
