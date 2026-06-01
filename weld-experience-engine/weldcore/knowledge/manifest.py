from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .foundation import (
    DataFoundation,
    DatasetCard,
    DatasetModality,
    DownloadPolicy,
    FieldCoverageRow,
    PublicAccess,
    ShipbuildingRelevanceLevel,
    SourceCard,
    TaskEvidenceEntry,
    TaskReadiness,
)


DEFAULT_FOUNDATION_ROOT = Path(__file__).resolve().parents[3] / "docs" / "data-foundation"


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _split_ids(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def _source_from_dict(data: dict[str, Any]) -> SourceCard:
    return SourceCard(
        source_id=data["source_id"],
        source_type=data["source_type"],
        title=data["title"],
        url=data["url"],
        publisher=data["publisher"],
        public_access=PublicAccess(data["public_access"]),
        shipbuilding_relevance_level=ShipbuildingRelevanceLevel(
            data["shipbuilding_relevance_level"]
        ),
        shipbuilding_relevance=data["shipbuilding_relevance"],
        covered_fields=list(data["covered_fields"]),
        missing_fields=list(data["missing_fields"]),
        usable_for=list(data["usable_for"]),
        source_refs=list(data["source_refs"]),
        assumptions=list(data["assumptions"]),
        use_boundary=data["use_boundary"],
        notes=data["notes"],
    )


def _dataset_from_dict(data: dict[str, Any]) -> DatasetCard:
    return DatasetCard(
        dataset_id=data["dataset_id"],
        source_id=data["source_id"],
        modalities=[DatasetModality(value) for value in data["modalities"]],
        size_note=data["size_note"],
        download_policy=DownloadPolicy(data["download_policy"]),
        schema_summary=data["schema_summary"],
        quality_label_type=data["quality_label_type"],
        shipbuilding_fit=data["shipbuilding_fit"],
        use_boundary=data["use_boundary"],
    )


def _task_evidence_from_dict(data: dict[str, Any]) -> TaskEvidenceEntry:
    return TaskEvidenceEntry(
        family_id=data["family_id"],
        required_sources=list(data["required_sources"]),
        supporting_source_ids=list(data["supporting_source_ids"]),
        supporting_dataset_ids=list(data["supporting_dataset_ids"]),
        required_fields=list(data["required_fields"]),
        covered_required_fields=list(data["covered_required_fields"]),
        assumption_fields=list(data["assumption_fields"]),
        readiness=TaskReadiness(data["readiness"]),
        next_action=data["next_action"],
    )


def _load_field_coverage(path: Path) -> list[FieldCoverageRow]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [
            FieldCoverageRow(
                field_name=row["field_name"],
                source_ids=_split_ids(row["source_ids"]),
                dataset_ids=_split_ids(row["dataset_ids"]),
                coverage_role=row["coverage_role"],
                notes=row["notes"],
            )
            for row in csv.DictReader(handle)
        ]


def load_data_foundation(root: str | Path | None = None) -> DataFoundation:
    foundation_root = Path(root) if root is not None else DEFAULT_FOUNDATION_ROOT
    manifests_root = foundation_root / "manifests"

    sources = [_source_from_dict(item) for item in _load_json(manifests_root / "sources.json")]
    datasets = [_dataset_from_dict(item) for item in _load_json(manifests_root / "datasets.json")]
    task_evidence = [
        _task_evidence_from_dict(item)
        for item in _load_json(manifests_root / "task_evidence_map.json")
    ]
    field_coverage = _load_field_coverage(manifests_root / "field_coverage.csv")

    return DataFoundation(
        sources=sources,
        datasets=datasets,
        task_evidence=task_evidence,
        field_coverage=field_coverage,
    )
