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
    "blocked_by_missing_robot_identity",
    "blocked_by_missing_frame_context",
    "blocked_by_missing_tcp_calibration",
    "blocked_by_missing_feasibility_result",
    "blocked_by_incomplete_feasibility_result",
    "blocked_by_failed_reachability",
    "blocked_by_failed_collision_check",
    "blocked_by_failed_joint_limit_check",
    "ready_for_expert_review",
    "ready_for_robot_execution",
]
RobotContextSource = Literal[
    "mock",
    "manual_precheck",
    "lightweight_rule",
    "moveit_future",
    "gazebo_future",
    "real_robot_future",
]
RobotFeasibilityStrategy = Literal["manual_precheck", "lightweight_rule"]
RobotFeasibilityAdapterHint = Literal[
    "manual_precheck",
    "lightweight_rule",
    "moveit_future",
    "gazebo_future",
    "real_robot_future",
]
RobotFeasibilityCheck = Literal[
    "reachability",
    "collision",
    "joint_limits",
    "path_continuity",
    "orientation_feasibility",
]
RobotFeasibilityStatus = Literal["passed", "failed", "incomplete"]
RobotFeasibilityCheckStatus = Literal[
    "passed",
    "failed",
    "missing",
    "not_checked",
    "assumed",
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
class RobotContextSpec:
    context_id: str
    robot_model: str | None
    robot_family: str | None
    base_frame: str | None
    tcp_frame: str | None
    tcp_calibration_status: str | None
    workpiece_frame: str | None
    tool_payload: dict[str, Any]
    joint_limits_source: str | None
    workspace_hint: dict[str, Any]
    context_source: RobotContextSource
    evidence_notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class RobotFeasibilityProbe:
    probe_id: str
    draft_id: str
    context_id: str
    strategy: RobotFeasibilityStrategy
    requested_checks: tuple[RobotFeasibilityCheck, ...]
    adapter_hint: RobotFeasibilityAdapterHint
    evidence_notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class RobotFeasibilityResult:
    result_id: str
    probe_id: str
    draft_id: str
    context_id: str
    status: RobotFeasibilityStatus
    reachability_status: RobotFeasibilityCheckStatus
    collision_status: RobotFeasibilityCheckStatus
    joint_limit_status: RobotFeasibilityCheckStatus
    path_continuity_status: RobotFeasibilityCheckStatus
    orientation_feasibility_status: RobotFeasibilityCheckStatus
    blocking_reasons: tuple[str, ...]
    warning_reasons: tuple[str, ...]
    evidence_source: str
    adapter_hint: RobotFeasibilityAdapterHint
    evidence_boundary: tuple[str, ...]
    metrics: dict[str, Any]

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
        return _model_dict(self)
