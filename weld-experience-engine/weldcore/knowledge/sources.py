from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


_FORBIDDEN_POOL_TERMS = ("molten", "molten_pool", "molten pool", "weld_pool", "weld pool", "熔池")


class SourceType(str, Enum):
    DATASET = "dataset"
    PROCESS_GUIDE = "process_guide"
    VENDOR_CASE = "vendor_case"
    STANDARD = "standard"
    PAPER = "paper"


class UsableFor(str, Enum):
    SCENARIO_SELECTION = "scenario_selection"
    PARAMETER_RANGE = "parameter_range"
    QUALITY_LABEL = "quality_label"
    BENCHMARK = "benchmark"


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


@dataclass(frozen=True)
class PublicWeldSource:
    source_id: str
    source_type: SourceType
    title: str
    url: str
    publisher: str
    shipbuilding_relevance: str
    covered_fields: list[str]
    missing_fields: list[str]
    usable_for: list[UsableFor]
    source_refs: list[str]
    assumptions: list[str]
    notes: str
    license_or_terms_note: str = ""

    def is_complete(self) -> bool:
        return all(
            [
                self.source_id,
                self.source_type,
                self.title,
                self.url,
                self.publisher,
                self.shipbuilding_relevance,
                self.covered_fields,
                self.missing_fields,
                self.usable_for,
                self.source_refs,
                self.assumptions,
                self.notes,
            ]
        )

    def to_dict(self) -> dict[str, Any]:
        return {key: _jsonable(value) for key, value in asdict(self).items()}


@dataclass(frozen=True)
class FieldCoverageSummary:
    source_count: int
    covered_fields: list[str]
    missing_fields: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PublicWeldKnowledgeBase:
    sources: list[PublicWeldSource]

    def validation_issues(self) -> list[str]:
        issues: list[str] = []
        seen: set[str] = set()
        for source in self.sources:
            if source.source_id in seen:
                issues.append(f"{source.source_id}: duplicate source_id")
            seen.add(source.source_id)
            if not source.is_complete():
                issues.append(f"{source.source_id}: incomplete traceability fields")
            text = str(source.to_dict()).lower()
            if any(term in text for term in _FORBIDDEN_POOL_TERMS):
                issues.append(f"{source.source_id}: molten-pool dependency is out of scope")
        return issues

    def by_id(self) -> dict[str, PublicWeldSource]:
        return {source.source_id: source for source in self.sources}

    def field_coverage(self) -> FieldCoverageSummary:
        covered = sorted({field for source in self.sources for field in source.covered_fields})
        missing = sorted({field for source in self.sources for field in source.missing_fields})
        return FieldCoverageSummary(
            source_count=len(self.sources),
            covered_fields=covered,
            missing_fields=missing,
        )

    def to_dict(self) -> dict[str, Any]:
        return {"sources": [source.to_dict() for source in self.sources]}
