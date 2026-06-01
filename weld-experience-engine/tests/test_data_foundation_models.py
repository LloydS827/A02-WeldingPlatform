from weldcore.knowledge.foundation import (
    DataFoundation,
    DatasetCard,
    DatasetModality,
    DownloadPolicy,
    PublicAccess,
    ShipbuildingRelevanceLevel,
    SourceCard,
    TaskEvidenceEntry,
    TaskReadiness,
)


def test_source_card_requires_use_boundary_not_just_notes():
    source = SourceCard(
        source_id="vendor-kranendonk-panel-welding-gantry",
        source_type="vendor_case",
        title="KRANENDONK Panel Welding Gantry",
        url="https://kranendonk.com/applications/panel-welding-gantry/",
        publisher="KRANENDONK",
        public_access=PublicAccess.PUBLIC,
        shipbuilding_relevance_level=ShipbuildingRelevanceLevel.STRONG,
        shipbuilding_relevance="Panel line and stiffened panel welding automation.",
        covered_fields=["shipbuilding_context", "stiffened_panel", "torch_angle"],
        missing_fields=["process_signal"],
        usable_for=["scenario_selection", "parameter_range"],
        source_refs=["data-foundation-section-6.1"],
        assumptions=["Use as public scenario and field-coverage evidence."],
        use_boundary="Use for task and field constraints; not process validation.",
        notes="Public vendor page.",
    )

    assert source.is_complete()
    data = source.to_dict()
    assert data["public_access"] == "public"
    assert data["shipbuilding_relevance_level"] == "strong"


def test_source_card_rejects_notes_as_boundary_substitute():
    source = SourceCard(
        source_id="bad-source",
        source_type="process_guide",
        title="Bad",
        url="https://example.com",
        publisher="example",
        public_access=PublicAccess.PUBLIC,
        shipbuilding_relevance_level=ShipbuildingRelevanceLevel.GENERIC,
        shipbuilding_relevance="generic",
        covered_fields=["quality_label"],
        missing_fields=["shipbuilding_context"],
        usable_for=["quality_label"],
        source_refs=["unit-test"],
        assumptions=["example"],
        use_boundary="",
        notes="Only use for labels.",
    )

    assert not source.is_complete()


def test_dataset_card_serializes_download_policy_and_modalities():
    dataset = DatasetCard(
        dataset_id="dataset-gdxray-weld-xray",
        source_id="dataset-gdxray-weld-xray",
        modalities=[DatasetModality.XRAY_IMAGE, DatasetModality.METADATA],
        size_note="Manifest only; do not mirror full dataset in git.",
        download_policy=DownloadPolicy.MANIFEST_ONLY,
        schema_summary="Weld X-ray images with defect categories.",
        quality_label_type="defect vocabulary",
        shipbuilding_fit="benchmark_only",
        use_boundary="Use for defect vocabulary and benchmark orientation only.",
    )

    data = dataset.to_dict()

    assert data["download_policy"] == "manifest_only"
    assert data["modalities"] == ["xray_image", "metadata"]


def test_data_foundation_rejects_forbidden_source_content():
    source = SourceCard(
        source_id="bad-pool-source",
        source_type="paper",
        title="Bad pool source",
        url="https://example.com",
        publisher="example",
        public_access=PublicAccess.PUBLIC,
        shipbuilding_relevance_level=ShipbuildingRelevanceLevel.GENERIC,
        shipbuilding_relevance="generic",
        covered_fields=["weld_pool_width"],
        missing_fields=["shipbuilding_context"],
        usable_for=["schema_reference"],
        source_refs=["unit-test"],
        assumptions=["example"],
        use_boundary="Out of scope for current stage.",
        notes="example",
    )
    foundation = DataFoundation(sources=[source], datasets=[], task_evidence=[])

    result = foundation.validate()

    assert not result.passed
    assert any("out of scope" in issue for issue in result.issues)


def test_task_evidence_entry_ready_for_plan_accepts_synthetic_v2_plan():
    entry = TaskEvidenceEntry(
        family_id="stiffened-panel-fillet",
        required_sources=["vendor_case", "project_internal"],
        supporting_source_ids=[
            "vendor-kranendonk-panel-welding-gantry",
            "project-260522-shipbuilding-welding-brain-plan",
        ],
        supporting_dataset_ids=[],
        required_fields=["shipbuilding_context", "torch_angle"],
        covered_required_fields=["shipbuilding_context", "torch_angle"],
        assumption_fields=["leg_size_mm"],
        readiness=TaskReadiness.READY_FOR_SYNTHETIC_V2_PLAN,
        next_action="Use for SyntheticSkillDataset v2 planning.",
    )

    assert entry.ready_for_plan()
