from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from weldcore.simulation_bakeoff.model import SimulationPathPoint

FailureBoundary = Literal[
    "environment_missing",
    "simulator_api_changed",
    "task_generation_failed",
    "demo_generation_failed",
    "simulation_run_failed",
    "artifact_missing",
    "adapter_conversion_failed",
]


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
class ManiSkillTaskConfig:
    task_id: str
    unit_id: str
    task_name: str
    seam_path: tuple[SimulationPathPoint, ...]
    tcp_frame: str
    orientation_constraint: tuple[str, ...]
    motion_constraint: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    out_of_scope: tuple[str, ...]
    source_task_spec_id: str

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class RuleBasedDemo:
    demo_id: str
    task_id: str
    tcp_trajectory: tuple[SimulationPathPoint, ...]
    tool_orientation: tuple[SimulationPathPoint, ...]
    generation_method: str
    evidence_notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class RawManiSkillArtifact:
    run_id: str
    task_id: str
    status: Literal["completed", "failed"]
    tcp_trajectory: tuple[SimulationPathPoint, ...]
    tool_orientation: tuple[SimulationPathPoint, ...]
    task_state: dict[str, Any]
    metrics: dict[str, float]
    failure_boundary: tuple[FailureBoundary, ...]
    artifacts: dict[str, str]
    evidence_notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class ExperienceDataset:
    dataset_id: str
    source_type: str
    task_id: str
    samples: tuple[str, ...]
    review_status: str
    validation_status: str
    quality_feedback_status: str
    compatibility_exports: tuple[str, ...]
    evidence_boundary: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


def write_json_artifact(path: str | Path, data: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(_jsonable(data), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def read_json_artifact(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))
