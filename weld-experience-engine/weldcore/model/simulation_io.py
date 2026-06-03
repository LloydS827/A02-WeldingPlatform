from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


SIMULATION_BUNDLE_SCHEMA_VERSION = "synthetic-v2-bundle-v0.1"
SYNTHETIC_DATASET_SCHEMA_VERSION = "synthetic-v2-dataset-v0.1"


class SimulatorName(str, Enum):
    SIMLITE = "simlite"
    MANISKILL = "maniskill"
    ISAAC_SIM = "isaac_sim"
    ISAAC_LAB = "isaac_lab"
    SAPIEN = "sapien"
    OTHER = "other"


class SimulationRunStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    IMPORTED = "imported"


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


@dataclass(frozen=True)
class SimulationBundleManifest:
    bundle_id: str
    simulation_run_id: str
    input_id: str
    taxonomy_ref: str
    simulator: SimulatorName
    simulator_version: str
    adapter_version: str
    seed: int
    sample_count: int
    generated_at: str
    assumption_summary: list[str]
    requires_real_validation_later: bool
    missing_signal_notes: list[str]
    generation_boundary: list[str]
    source_type: str = "simulation"
    schema_version: str = SIMULATION_BUNDLE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {key: _jsonable(value) for key, value in asdict(self).items()}


@dataclass(frozen=True)
class SimulationRunRecord:
    simulation_run_id: str
    input_ids: list[str]
    simulator: SimulatorName
    simulator_version: str
    adapter_name: str
    adapter_version: str
    seed: int
    started_at: str
    finished_at: str
    status: SimulationRunStatus
    output_bundle_uris: list[str]
    sample_count: int
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    boundary_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {key: _jsonable(value) for key, value in asdict(self).items()}
