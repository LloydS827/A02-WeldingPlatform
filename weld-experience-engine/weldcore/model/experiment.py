from __future__ import annotations
from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
from typing import Any

from .trajectory import Trajectory


class TransferDecision(str, Enum):
    PASS = "pass"
    REVIEW = "review"
    FAIL = "fail"


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
class TransferMetrics:
    trajectory_rms_mm: float
    posture_error_deg: float
    weave_amplitude_error_mm: float
    weave_frequency_error_hz: float
    process_current_error: float | None = None


@dataclass
class TransferExperiment:
    experiment_id: str
    source_condition: dict[str, Any]
    target_condition: dict[str, Any]
    skill_package_id: str
    recomposed_trajectory: Trajectory
    metrics: TransferMetrics
    decision: TransferDecision
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _to_dict(self)
