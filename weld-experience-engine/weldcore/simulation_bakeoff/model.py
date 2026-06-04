from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
from typing import Any, Literal

from weldcore.model import SimulationRunRecord, SkillDataset


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
class SimulationPathPoint:
    t: float
    x: float
    y: float
    z: float
    rx: float
    ry: float
    rz: float

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class SimulationTaskSpec:
    task_id: str
    unit_id: str
    name: str
    seam_path: tuple[SimulationPathPoint, ...]
    tcp_frame: str
    tool_orientation_constraint: tuple[str, ...]
    motion_constraint: tuple[str, ...]
    robot_constraint: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    evaluation_metrics: tuple[str, ...]
    out_of_scope: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class SimulatorAdapterResult:
    adapter_name: str
    task_id: str
    status: str
    tcp_trajectory: tuple[SimulationPathPoint, ...]
    tool_orientation: tuple[SimulationPathPoint, ...]
    planning_result: dict[str, Any]
    failure_boundary: tuple[str, ...]
    metrics: dict[str, float]
    artifacts: dict[str, str]
    evidence_notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class SimulationEvidenceBundle:
    bundle_id: str
    task_spec: SimulationTaskSpec
    adapter_result: SimulatorAdapterResult
    run_record: SimulationRunRecord
    dataset: SkillDataset | None
    rerun_replay_uri: str | None
    rerun_replay_status: Literal["not_attempted", "logged", "skipped"]
    rerun_notes: tuple[str, ...]
    bakeoff_score: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class BakeoffScorecard:
    dimension_weights: dict[str, float]
    route_dimension_scores: dict[str, dict[str, float]]
    route_scores: dict[str, float]
    attempted_task_ids: tuple[str, ...]
    recommendation: str
    final_simulator_selected: bool
    evidence_notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)
