from __future__ import annotations
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from typing import Any

from .trajectory import Trajectory
from .weave import WeaveTemplate


class SourceType(str, Enum):
    SIMULATION = "simulation"
    REAL_ROBOT = "real_robot"
    EXPERT_KNOWLEDGE = "expert_knowledge"
    HYBRID = "hybrid"


def _to_dict(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Trajectory):
        return {"samples": [_to_dict(sample) for sample in value.samples]}
    if is_dataclass(value):
        return {key: _to_dict(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [_to_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_dict(item) for key, item in value.items()}
    return value


@dataclass
class WeldCondition:
    weld_type: str
    joint_type: str
    plate_thickness_mm: float
    groove_width_mm: float
    length_mm: float
    position: str = "flat"
    material: str = "unknown"


@dataclass
class ProcessSignal:
    t: float
    current: float | None = None
    voltage: float | None = None
    wire_feed: float | None = None
    travel_speed: float | None = None


@dataclass
class WeldEvent:
    t: float
    kind: str
    notes: str = ""


@dataclass
class QualityObservation:
    score: float | None = None
    status: str = "unknown"
    notes: str = ""


@dataclass
class SkillSample:
    sample_id: str
    weld_condition: WeldCondition
    trajectory: Trajectory
    process_signals: list[ProcessSignal]
    events: list[WeldEvent] = field(default_factory=list)
    quality_observation: QualityObservation | None = None
    rerun_recording: str | None = None


@dataclass
class SkillDataset:
    dataset_id: str
    source_type: SourceType
    task: str
    samples: list[SkillSample]
    schema_version: str = "0.1"
    license_and_rights: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _to_dict(self)


@dataclass
class MotionSkill:
    travel_speed: float
    weave: WeaveTemplate


@dataclass
class PostureSkill:
    work_angle_deg: float = 0.0
    travel_angle_deg: float = 0.0
    stickout_mm: float = 0.0


@dataclass
class ProcessSkill:
    current: float | None = None
    voltage: float | None = None
    wire_feed: float | None = None


@dataclass
class TransferRuleSpec:
    max_length_scale: float = 2.0
    max_width_delta_mm: float = 2.0


@dataclass
class HumanReview:
    status: str = "pending"
    reviewer: str | None = None
    notes: str = ""


@dataclass
class SkillEvaluation:
    trajectory_rms_mm: float | None = None
    decision: str = "review"
    notes: str = ""


@dataclass
class WeldSkillPackage:
    package_id: str
    source_sample_ids: list[str]
    applicable_conditions: dict[str, Any]
    motion_skill: MotionSkill
    posture_skill: PostureSkill
    process_skill: ProcessSkill
    transfer_rule: TransferRuleSpec = field(default_factory=TransferRuleSpec)
    human_review: HumanReview = field(default_factory=HumanReview)
    evaluation: SkillEvaluation | None = None

    def to_dict(self) -> dict[str, Any]:
        return _to_dict(self)
