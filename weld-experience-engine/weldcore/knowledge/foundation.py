from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


FORBIDDEN_POOL_TERMS = ("molten", "molten_pool", "molten pool", "weld_pool", "weld pool", "熔池")


class PublicAccess(str, Enum):
    PUBLIC = "public"
    PROJECT_INTERNAL = "project_internal"
    REQUIRES_SCREENING = "requires_screening"


class ShipbuildingRelevanceLevel(str, Enum):
    STRONG = "strong"
    ADJACENT = "adjacent"
    GENERIC = "generic"


class DownloadPolicy(str, Enum):
    MANIFEST_ONLY = "manifest_only"
    SAMPLE_CACHE_LATER = "sample_cache_later"
    EXTERNAL_CACHE_ONLY = "external_cache_only"


class DatasetModality(str, Enum):
    XRAY_IMAGE = "xray_image"
    SURFACE_IMAGE = "surface_image"
    CURRENT_VOLTAGE_TIMESERIES = "current_voltage_timeseries"
    ROBOT_POSE = "robot_pose"
    SCAN_3D = "scan_3d"
    VIDEO = "video"
    METADATA = "metadata"


class TaskReadiness(str, Enum):
    READY_FOR_SYNTHETIC_V2_PLAN = "ready_for_synthetic_v2_plan"
    NEEDS_MORE_SOURCES = "needs_more_sources"
    DEFER = "defer"


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


def _duplicate_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


@dataclass(frozen=True)
class SourceCard:
    source_id: str
    source_type: str
    title: str
    url: str
    publisher: str
    public_access: PublicAccess
    shipbuilding_relevance_level: ShipbuildingRelevanceLevel
    shipbuilding_relevance: str
    covered_fields: list[str]
    missing_fields: list[str]
    usable_for: list[str]
    source_refs: list[str]
    assumptions: list[str]
    use_boundary: str
    notes: str

    def is_complete(self) -> bool:
        return all(
            [
                self.source_id,
                self.source_type,
                self.title,
                self.url,
                self.publisher,
                self.public_access,
                self.shipbuilding_relevance_level,
                self.shipbuilding_relevance,
                self.covered_fields,
                self.missing_fields,
                self.usable_for,
                self.source_refs,
                self.assumptions,
                self.use_boundary,
                self.notes,
            ]
        )

    def to_dict(self) -> dict[str, Any]:
        return {key: _jsonable(value) for key, value in asdict(self).items()}


@dataclass(frozen=True)
class DatasetCard:
    dataset_id: str
    source_id: str
    modalities: list[DatasetModality]
    size_note: str
    download_policy: DownloadPolicy
    schema_summary: str
    quality_label_type: str
    shipbuilding_fit: str
    use_boundary: str

    def is_complete(self) -> bool:
        return all(
            [
                self.dataset_id,
                self.source_id,
                self.modalities,
                self.size_note,
                self.download_policy,
                self.schema_summary,
                self.quality_label_type,
                self.shipbuilding_fit,
                self.use_boundary,
            ]
        )

    def to_dict(self) -> dict[str, Any]:
        return {key: _jsonable(value) for key, value in asdict(self).items()}


@dataclass(frozen=True)
class FieldCoverageRow:
    field_name: str
    source_ids: list[str]
    dataset_ids: list[str]
    coverage_role: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TaskEvidenceEntry:
    family_id: str
    required_sources: list[str]
    supporting_source_ids: list[str]
    supporting_dataset_ids: list[str]
    required_fields: list[str]
    covered_required_fields: list[str]
    assumption_fields: list[str]
    readiness: TaskReadiness
    next_action: str

    def ready_for_plan(self) -> bool:
        return self.readiness == TaskReadiness.READY_FOR_SYNTHETIC_V2_PLAN

    def to_dict(self) -> dict[str, Any]:
        return {key: _jsonable(value) for key, value in asdict(self).items()}


@dataclass(frozen=True)
class DataFoundationGateResult:
    passed: bool
    issues: list[str]


@dataclass
class DataFoundation:
    sources: list[SourceCard]
    datasets: list[DatasetCard]
    task_evidence: list[TaskEvidenceEntry]
    field_coverage: list[FieldCoverageRow] | None = None

    def validate(self) -> DataFoundationGateResult:
        issues: list[str] = []
        for source_id in _duplicate_values([source.source_id for source in self.sources]):
            issues.append(f"{source_id}: duplicate source_id")
        for dataset_id in _duplicate_values([dataset.dataset_id for dataset in self.datasets]):
            issues.append(f"{dataset_id}: duplicate dataset_id")
        for family_id in _duplicate_values([entry.family_id for entry in self.task_evidence]):
            issues.append(f"{family_id}: duplicate family_id")
        for source in self.sources:
            if not source.is_complete():
                issues.append(f"{source.source_id}: incomplete source card")
            text = str(source.to_dict()).lower()
            if any(term in text for term in FORBIDDEN_POOL_TERMS):
                issues.append(f"{source.source_id}: molten-pool dependency is out of scope")
        for dataset in self.datasets:
            if not dataset.is_complete():
                issues.append(f"{dataset.dataset_id}: incomplete dataset card")
        return DataFoundationGateResult(not issues, issues)
