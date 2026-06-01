from weldcore.knowledge import (
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
