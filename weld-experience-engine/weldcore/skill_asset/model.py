from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
from typing import Any, Literal


SkillAssetSourceType = Literal[
    "simulation",
    "real_robot_log",
    "human_demonstration",
    "expert_annotation",
]
SkillAssetReviewStatus = Literal["not_reviewed", "expert_review_candidate", "reviewed"]
SkillTransferContractStatus = Literal["requires_contextual_precheck", "blocked"]
SkillTransferAssessmentStatus = Literal[
    "ready_for_contextual_precheck",
    "blocked_by_missing_skill_motion",
    "blocked_by_robot_body_asset_issue",
]
RobotBodyAssetValidationStatus = Literal[
    "usable_as_robot_body_context",
    "blocked_by_asset_issue",
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
class SkillAssetEvidence:
    source_type: SkillAssetSourceType
    source_id: str
    adapter_name: str
    status: str
    metrics: dict[str, Any]
    artifact_refs: dict[str, str]
    evidence_boundary: tuple[str, ...]
    review_status: SkillAssetReviewStatus

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class SkillTransferContract:
    required_robot_context: tuple[str, ...]
    required_scene_context: tuple[str, ...]
    required_checks: tuple[str, ...]
    transfer_status: SkillTransferContractStatus
    blocking_gaps: tuple[str, ...]
    evidence_notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class ManipulationSkillAsset:
    asset_id: str
    name: str
    domain: str
    skill_type: str
    source_type: SkillAssetSourceType
    source_refs: dict[str, str | None]
    intent: dict[str, Any]
    motion: dict[str, Any]
    constraints: dict[str, Any]
    context_requirements: dict[str, Any]
    evidence: SkillAssetEvidence
    transfer_contract: SkillTransferContract
    quality_boundary: tuple[str, ...]
    version: str

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class RobotJointLimit:
    joint_name: str
    lower: float
    upper: float
    effort: float | None = None
    velocity: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class RobotBodyAsset:
    robot_id: str
    robot_model: str
    robot_family: str
    source_urdf: str
    link_names: tuple[str, ...]
    joint_names: tuple[str, ...]
    joint_limits: tuple[RobotJointLimit, ...]
    mesh_files: tuple[str, ...]
    mesh_references: tuple[str, ...]
    joint_count: int
    revolute_joint_count: int
    visual_mesh_count: int
    collision_mesh_count: int
    validation_status: RobotBodyAssetValidationStatus
    validation_issues: tuple[str, ...]
    evidence_boundary: tuple[str, ...]
    version: str = "v0.1"

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class SkillTransferAssessment:
    assessment_id: str
    skill_asset_id: str
    robot_body_asset_id: str
    status: SkillTransferAssessmentStatus
    passed_checks: tuple[str, ...]
    blocking_gaps: tuple[str, ...]
    evidence_notes: tuple[str, ...]
    version: str = "v0.1"

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)
