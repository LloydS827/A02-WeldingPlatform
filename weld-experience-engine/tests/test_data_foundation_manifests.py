from dataclasses import replace

from weldcore.knowledge import (
    FieldCoverageRow,
    DownloadPolicy,
    PublicAccess,
    ShipbuildingRelevanceLevel,
    TaskReadiness,
)
from weldcore.knowledge.manifest import load_data_foundation


def test_data_foundation_manifests_meet_minimum_gate():
    from weldcore.knowledge import load_data_foundation as exported_loader

    assert exported_loader is load_data_foundation

    foundation = load_data_foundation()
    source_by_id = {source.source_id: source for source in foundation.sources}

    assert len(foundation.sources) >= 20
    assert sum(source.public_access == PublicAccess.PUBLIC for source in foundation.sources) >= 15
    assert (
        sum(
            source.shipbuilding_relevance_level == ShipbuildingRelevanceLevel.STRONG
            for source in foundation.sources
        )
        >= 8
    )

    assert len(foundation.datasets) >= 6
    assert (
        sum(
            source_by_id[dataset.source_id].public_access == PublicAccess.PUBLIC
            for dataset in foundation.datasets
        )
        >= 6
    )
    assert {
        dataset.download_policy for dataset in foundation.datasets
    } <= {
        DownloadPolicy.MANIFEST_ONLY,
        DownloadPolicy.SAMPLE_CACHE_LATER,
        DownloadPolicy.EXTERNAL_CACHE_ONLY,
    }

    assert (
        sum(
            entry.readiness == TaskReadiness.READY_FOR_SYNTHETIC_V2_PLAN
            for entry in foundation.task_evidence
        )
        >= 3
    )
    assert foundation.validate().passed


def test_ready_task_covered_field_must_exist_in_coverage_matrix():
    foundation = load_data_foundation()
    entry = foundation.task_evidence[0]
    foundation.task_evidence[0] = replace(
        entry,
        covered_required_fields=entry.covered_required_fields + ["unlisted_ready_field"],
    )

    result = foundation.validate()

    assert not result.passed
    assert any("unlisted_ready_field" in issue for issue in result.issues)


def test_ready_task_covered_field_must_be_supported_by_task_evidence_sources_or_datasets():
    foundation = load_data_foundation()
    entry = foundation.task_evidence[0]
    foundation.task_evidence[0] = replace(
        entry,
        covered_required_fields=entry.covered_required_fields + ["current"],
    )

    result = foundation.validate()

    assert not result.passed
    assert any("current" in issue and entry.family_id in issue for issue in result.issues)


def test_task_required_source_type_must_be_satisfied_by_supporting_sources():
    foundation = load_data_foundation()
    entry = foundation.task_evidence[0]
    foundation.task_evidence[0] = replace(
        entry,
        required_sources=entry.required_sources + ["standard"],
    )

    result = foundation.validate()

    assert not result.passed
    assert any("standard" in issue and entry.family_id in issue for issue in result.issues)


def test_non_ready_task_required_fields_must_be_covered_or_assumed():
    foundation = load_data_foundation()
    entry = next(
        item for item in foundation.task_evidence if item.family_id == "double-bottom-inner-fillet"
    )
    index = foundation.task_evidence.index(entry)
    foundation.task_evidence[index] = replace(
        entry,
        assumption_fields=[
            field for field in entry.assumption_fields if field != "motion_template"
        ],
    )

    result = foundation.validate()

    assert not result.passed
    assert any("motion_template" in issue and entry.family_id in issue for issue in result.issues)


def test_field_coverage_row_with_unknown_id_fails_validation():
    foundation = load_data_foundation()
    foundation.field_coverage = list(foundation.field_coverage or []) + [
        FieldCoverageRow(
            field_name="unknown_source_probe",
            source_ids=["missing-source-id"],
            dataset_ids=["missing-dataset-id"],
            coverage_role="probe",
            notes="测试未知 id 必须被 gate 拦截。",
        )
    ]

    result = foundation.validate()

    assert not result.passed
    assert any("missing-source-id" in issue for issue in result.issues)
    assert any("missing-dataset-id" in issue for issue in result.issues)
