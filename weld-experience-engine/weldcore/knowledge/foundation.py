from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


FORBIDDEN_POOL_TERMS = ("molten_pool", "molten pool", "weld_pool", "weld pool", "熔池")


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


def _has_forbidden_term(value: Any) -> bool:
    text = str(value).lower()
    return any(term in text for term in FORBIDDEN_POOL_TERMS)


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
        source_by_id = {source.source_id: source for source in self.sources}
        dataset_by_id = {dataset.dataset_id: dataset for dataset in self.datasets}

        for source_id in _duplicate_values([source.source_id for source in self.sources]):
            issues.append(f"{source_id}: duplicate source_id")
        for dataset_id in _duplicate_values([dataset.dataset_id for dataset in self.datasets]):
            issues.append(f"{dataset_id}: duplicate dataset_id")
        for family_id in _duplicate_values([entry.family_id for entry in self.task_evidence]):
            issues.append(f"{family_id}: duplicate family_id")
        if self.field_coverage is not None:
            for field_name in _duplicate_values([row.field_name for row in self.field_coverage]):
                issues.append(f"{field_name}: duplicate field_name")

        public_source_count = sum(
            source.public_access == PublicAccess.PUBLIC for source in self.sources
        )
        strong_source_count = sum(
            source.shipbuilding_relevance_level == ShipbuildingRelevanceLevel.STRONG
            for source in self.sources
        )
        if len(self.sources) < 20:
            issues.append("data foundation requires at least 20 sources")
        if public_source_count < 15:
            issues.append("data foundation requires at least 15 public sources")
        if strong_source_count < 8:
            issues.append("data foundation requires at least 8 strong shipbuilding sources")

        for source in self.sources:
            if not source.is_complete():
                issues.append(f"{source.source_id}: incomplete source card")
            if not isinstance(source.public_access, PublicAccess):
                issues.append(f"{source.source_id}: invalid public_access")
            if not isinstance(source.shipbuilding_relevance_level, ShipbuildingRelevanceLevel):
                issues.append(f"{source.source_id}: invalid shipbuilding_relevance_level")
            if _has_forbidden_term(source.to_dict()):
                issues.append(f"{source.source_id}: forbidden pool-route dependency is out of scope")

        for dataset in self.datasets:
            if not dataset.is_complete():
                issues.append(f"{dataset.dataset_id}: incomplete dataset card")
            if dataset.source_id not in source_by_id:
                issues.append(f"{dataset.dataset_id}: unknown source_id {dataset.source_id}")
            if not isinstance(dataset.download_policy, DownloadPolicy):
                issues.append(f"{dataset.dataset_id}: unsupported download_policy")
            if any(not isinstance(modality, DatasetModality) for modality in dataset.modalities):
                issues.append(f"{dataset.dataset_id}: unsupported modality")
            if _has_forbidden_term(dataset.to_dict()):
                issues.append(f"{dataset.dataset_id}: forbidden pool-route dependency is out of scope")

        supported_policies = {
            DownloadPolicy.MANIFEST_ONLY,
            DownloadPolicy.SAMPLE_CACHE_LATER,
            DownloadPolicy.EXTERNAL_CACHE_ONLY,
        }
        for dataset in self.datasets:
            if dataset.download_policy not in supported_policies:
                issues.append(f"{dataset.dataset_id}: unsupported download_policy")

        public_dataset_count = sum(
            dataset.source_id in source_by_id
            and source_by_id[dataset.source_id].public_access == PublicAccess.PUBLIC
            for dataset in self.datasets
        )
        if public_dataset_count < 6:
            issues.append("data foundation requires at least 6 public datasets")

        ready_entries = [entry for entry in self.task_evidence if entry.ready_for_plan()]
        if len(ready_entries) < 3:
            issues.append("data foundation requires at least 3 ready task entries")

        for entry in self.task_evidence:
            if not isinstance(entry.readiness, TaskReadiness):
                issues.append(f"{entry.family_id}: invalid readiness")
            for source_id in entry.supporting_source_ids:
                if source_id not in source_by_id:
                    issues.append(f"{entry.family_id}: unknown supporting_source_id {source_id}")
            for dataset_id in entry.supporting_dataset_ids:
                if dataset_id not in dataset_by_id:
                    issues.append(f"{entry.family_id}: unknown supporting_dataset_id {dataset_id}")
            if _has_forbidden_term(entry.to_dict()):
                issues.append(f"{entry.family_id}: forbidden pool-route dependency is out of scope")
            if entry.ready_for_plan():
                has_strong_source = any(
                    source_id in source_by_id
                    and source_by_id[source_id].shipbuilding_relevance_level
                    == ShipbuildingRelevanceLevel.STRONG
                    for source_id in entry.supporting_source_ids
                )
                if not has_strong_source:
                    issues.append(f"{entry.family_id}: ready task needs a strong source")
                supported_fields = set(entry.covered_required_fields) | set(entry.assumption_fields)
                missing_fields = sorted(set(entry.required_fields) - supported_fields)
                if missing_fields:
                    issues.append(
                        f"{entry.family_id}: ready task missing required fields {missing_fields}"
                    )

        for row in self.field_coverage or []:
            if not row.field_name or not row.coverage_role or not row.notes:
                issues.append(f"{row.field_name}: incomplete field coverage row")
            for source_id in row.source_ids:
                if source_id not in source_by_id:
                    issues.append(f"{row.field_name}: unknown source_id {source_id}")
            for dataset_id in row.dataset_ids:
                if dataset_id not in dataset_by_id:
                    issues.append(f"{row.field_name}: unknown dataset_id {dataset_id}")
            if _has_forbidden_term(row.to_dict()):
                issues.append(f"{row.field_name}: forbidden pool-route dependency is out of scope")

        return DataFoundationGateResult(not issues, issues)
