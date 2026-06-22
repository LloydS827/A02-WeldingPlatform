from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
from typing import Any, Literal


SkillAssetSourceType = Literal[
    "simulation_only",
    "human_demo",
    "real_robot_log",
    "h300_workcell_run",
    "expert_annotation",
]
SkillAssetReviewStatus = Literal["not_reviewed", "expert_review_candidate", "reviewed"]
SkillTransferContractStatus = Literal["requires_contextual_precheck", "blocked"]
SkillTransferAssessmentStatus = Literal[
    "ready_for_contextual_precheck",
    "ready_for_lightweight_feasibility_precheck",
    "ready_for_expert_review",
    "blocked_by_missing_skill_motion",
    "blocked_by_robot_body_asset_issue",
    "blocked_by_missing_robot_context",
    "blocked_by_missing_scene_context",
    "blocked_by_incomplete_feasibility_result",
    "blocked_by_failed_feasibility_check",
]
RobotBodyAssetValidationStatus = Literal[
    "usable_as_robot_body_context",
    "blocked_by_asset_issue",
]
SceneContextAssetValidationStatus = Literal[
    "usable_as_scene_context",
    "blocked_by_scene_context_issue",
]
SkillAssetEvidenceWritebackStatus = Literal[
    "evidence_candidates_identified",
    "blocked_by_missing_evidence_source",
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
class SceneContextAsset:
    scene_id: str
    scene_type: str
    workpiece_frame: str
    seam_path: list[dict[str, Any]]
    fixture_obstacles: tuple[dict[str, Any], ...]
    safety_boundary: dict[str, Any]
    target_region: dict[str, Any]
    source_refs: dict[str, str]
    validation_status: SceneContextAssetValidationStatus
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
    warning_gaps: tuple[str, ...]
    evidence_boundary: tuple[str, ...]
    next_step_recommendation: str
    evidence_notes: tuple[str, ...]
    version: str = "v0.1"

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class SkillAssetEvidenceWritebackSummary:
    summary_id: str
    skill_asset_id: str
    modeled_task_count: int
    simulation_sample_count: int
    completed_sample_count: int
    failed_sample_count: int
    candidate_evidence_refs: tuple[str, ...]
    writeback_status: SkillAssetEvidenceWritebackStatus
    evidence_boundary: tuple[str, ...]
    next_step_recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class EvidenceSourceCatalogEntry:
    source_type: SkillAssetSourceType
    role: str
    status: str
    expected_fields: tuple[str, ...]
    evidence_boundary: tuple[str, ...]
    next_step_recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class A01B06SkillAssetMapping:
    mapping_id: str
    source_system: str
    target_skill_asset_id: str
    evidence_source_type: SkillAssetSourceType
    workcell_fields: tuple[str, ...]
    package_fields: tuple[str, ...]
    skill_asset_field_mapping: dict[str, str]
    context_mapping: dict[str, str]
    quality_feedback_mapping: dict[str, str]
    artifact_refs: dict[str, str]
    evidence_boundary: tuple[str, ...]
    next_step_recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class ExpertReviewRecord:
    review_id: str
    skill_asset_id: str
    robot_context_id: str
    scene_context_id: str
    feasibility_result_id: str
    robot_context_snapshot: dict[str, Any]
    scene_context_snapshot: dict[str, Any]
    feasibility_status_snapshot: dict[str, Any]
    source_evidence_summary: dict[str, Any]
    review_status: str
    review_conclusion: str | None
    blocking_reasons: tuple[str, ...]
    required_real_context: tuple[dict[str, Any], ...]
    next_actions: tuple[str, ...]
    review_boundary: tuple[str, ...]
    reviewer_role: str
    version: str = "v0.1"

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class A02ToA01ProductValidationHandoff:
    handoff_id: str
    skill_asset_id: str
    target_product: str
    candidate_outputs: tuple[str, ...]
    trajectory_candidate_ref: str
    posture_parameter_suggestions: dict[str, Any]
    failure_boundaries: tuple[str, ...]
    required_confirmations: tuple[str, ...]
    not_ready_reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    handoff_boundary: tuple[str, ...]
    next_step_recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class IPDisclosureSupportMatrix:
    support_id: str
    skill_asset_id: str
    items: tuple[dict[str, Any], ...]
    evidence_boundary: tuple[str, ...]
    next_step_recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)
