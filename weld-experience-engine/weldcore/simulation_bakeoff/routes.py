from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

from weldcore.simulation_bakeoff.adapters import (
    attempt_gazebo_moveit,
    attempt_maniskill_sapien,
    run_simlite_reference,
)
from weldcore.simulation_bakeoff.model import SimulationTaskSpec, SimulatorAdapterResult


SimulationAdapterRole = Literal["baseline", "default_candidate", "planning_candidate"]
SimulationAdapterStatus = Literal["available", "optional_dependency", "not_integrated"]
SimulationAdapterRunner = Callable[[SimulationTaskSpec], SimulatorAdapterResult]


@dataclass(frozen=True)
class SimulationAdapterRoute:
    route_id: str
    display_name: str
    role: SimulationAdapterRole
    status: SimulationAdapterStatus
    runner: SimulationAdapterRunner
    default_for_batch: bool
    dependency_boundary: tuple[str, ...]
    evidence_boundary: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "route_id": self.route_id,
            "display_name": self.display_name,
            "role": self.role,
            "status": self.status,
            "default_for_batch": self.default_for_batch,
            "dependency_boundary": list(self.dependency_boundary),
            "evidence_boundary": list(self.evidence_boundary),
        }


def default_simulation_adapter_routes() -> tuple[SimulationAdapterRoute, ...]:
    return (
        SimulationAdapterRoute(
            route_id="simlite_reference",
            display_name="R0 / simlite reference",
            role="baseline",
            status="available",
            runner=run_simlite_reference,
            default_for_batch=False,
            dependency_boundary=(),
            evidence_boundary=("r0_baseline", "not_final_simulator_selection"),
        ),
        SimulationAdapterRoute(
            route_id="maniskill_sapien",
            display_name="ManiSkill/SAPIEN",
            role="default_candidate",
            status="optional_dependency",
            runner=attempt_maniskill_sapien,
            default_for_batch=True,
            dependency_boundary=("mani_skill_or_sapien_optional",),
            evidence_boundary=(
                "stage_default_candidate",
                "not_final_simulator_selection",
                "not_locked_for_robot_execution",
            ),
        ),
        SimulationAdapterRoute(
            route_id="gazebo_moveit",
            display_name="Gazebo/MoveIt",
            role="planning_candidate",
            status="not_integrated",
            runner=attempt_gazebo_moveit,
            default_for_batch=False,
            dependency_boundary=("rclpy_moveit_or_moveit_configs_utils_optional",),
            evidence_boundary=(
                "planning_candidate_only",
                "not_final_simulator_selection",
            ),
        ),
    )


def get_default_batch_route() -> SimulationAdapterRoute:
    defaults = tuple(
        route for route in default_simulation_adapter_routes() if route.default_for_batch
    )
    if len(defaults) != 1:
        raise ValueError("Expected exactly one default simulation adapter route")
    return defaults[0]


def run_adapter_route(
    route_id: str,
    task_spec: SimulationTaskSpec,
    routes: tuple[SimulationAdapterRoute, ...] | None = None,
) -> SimulatorAdapterResult:
    route = _route_by_id(route_id, routes)
    try:
        return route.runner(task_spec)
    except Exception:
        return _failed_route_result(
            route_id=route_id,
            task_spec=task_spec,
            failure_boundary=("simulation_run_failed",),
        )


def run_comparison_routes(
    task_spec: SimulationTaskSpec,
    routes: tuple[SimulationAdapterRoute, ...] | None = None,
) -> tuple[SimulatorAdapterResult, ...]:
    selected_routes = default_simulation_adapter_routes() if routes is None else routes
    return tuple(
        run_adapter_route(route.route_id, task_spec, routes=selected_routes)
        for route in selected_routes
    )


def _route_by_id(
    route_id: str,
    routes: tuple[SimulationAdapterRoute, ...] | None,
) -> SimulationAdapterRoute:
    selected_routes = default_simulation_adapter_routes() if routes is None else routes
    for route in selected_routes:
        if route.route_id == route_id:
            return route
    raise ValueError(f"Unknown simulation adapter route: {route_id}")


def _failed_route_result(
    route_id: str,
    task_spec: SimulationTaskSpec,
    failure_boundary: tuple[str, ...],
) -> SimulatorAdapterResult:
    return SimulatorAdapterResult(
        adapter_name=route_id,
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
