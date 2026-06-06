from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
from typing import Any, Literal

from weldcore.simulation_bakeoff.model import SimulationPathPoint


RobotProcessDraftStatus = Literal["draft", "blocked"]
RobotExecutionReadiness = Literal[
    "draft",
    "needs_review",
    "blocked_by_failed_simulation",
    "blocked_by_missing_dataset",
    "blocked_by_missing_trajectory",
    "blocked_by_missing_orientation",
    "blocked_by_missing_robot_context",
    "ready_for_expert_review",
    "ready_for_robot_execution",
]
ProcessParameterStatusValue = Literal[
    "available_from_simulation",
    "partially_available_from_simulation",
    "missing_required",
    "conditionally_missing",
    "optional_missing",
    "requires_expert_review",
    "requires_real_validation",
    "requires_robot_context",
    "not_applicable",
    "out_of_scope_now",
    "not_WPS_PQR",
]

BASE_ROBOT_PROCESS_EVIDENCE_BOUNDARY = (
    "simulation_only",
    "not_robot_process_package",
    "not_ready_for_robot_execution",
    "not_real_welding_quality_validation",
    "not_WPS_PQR",
    "requires_expert_review_later",
    "requires_real_robot_validation_later",
)


def _jsonable(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


def _model_dict(value: Any) -> dict[str, Any]:
    payload = asdict(value)
    return {key: _jsonable(getattr(value, key)) for key in payload}


@dataclass(frozen=True)
class ProcessParameterStatus:
    group_name: str
    statuses: tuple[ProcessParameterStatusValue, ...]
    available_fields: tuple[str, ...]
    missing_fields: tuple[str, ...]
    required_future_sources: tuple[str, ...]
    evidence_notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class RobotExecutionSpec:
    robot_model: str | None
    tcp_frame: str | None
    workpiece_frame: str | None
    trajectory: tuple[SimulationPathPoint, ...]
    tool_orientation: tuple[SimulationPathPoint, ...]
    travel_speed: float | None
    reachability_status: str
    collision_status: str
    joint_limit_status: str
    execution_notes: tuple[str, ...]
    missing_robot_context: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class RobotProcessPackageDraft:
    draft_id: str
    source_bundle_id: str
    source_task_id: str
    source_type: Literal["simulation"]
    status: RobotProcessDraftStatus
    source_evidence: dict[str, Any]
    process_parameter_status: tuple[ProcessParameterStatus, ...]
    robot_execution_spec: RobotExecutionSpec
    readiness: RobotExecutionReadiness
    evidence_boundary: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = _model_dict(self)
        data["evidence_boundary"] = [
            item for item in data["evidence_boundary"] if item != "not_ready_for_robot_execution"
        ]
        return data
