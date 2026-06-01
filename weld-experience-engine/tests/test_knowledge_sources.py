from weldcore.knowledge.seeds import load_seed_knowledge_base
from weldcore.knowledge.sources import (
    PublicWeldKnowledgeBase,
    PublicWeldSource,
    SourceType,
    UsableFor,
)


def test_public_source_requires_traceability_fields():
    source = PublicWeldSource(
        source_id="vendor-hyundai-welding-cobot-shipbuilding-2024",
        source_type=SourceType.VENDOR_CASE,
        title="Hyundai Welding Cobot Solution (Shipbuilding) Leaflet 2024",
        url="https://www.hyundaiwelding.com/data/file/download/brochures/Hyundai_Welding_Cobot%20Solution%20%28Shipbuilding%29_Leaflet_2024.pdf",
        publisher="Hyundai Welding",
        shipbuilding_relevance="shipbuilding cobot welding scenario reference",
        covered_fields=["shipbuilding_context", "robot_welding_application"],
        missing_fields=["trajectory", "process_signal", "quality_result"],
        usable_for=[UsableFor.SCENARIO_SELECTION],
        source_refs=["design-spec-section-7.1"],
        assumptions=["Use as scenario evidence only, not process validation."],
        notes="No direct real-machine dataset imported.",
    )

    assert source.is_complete()
    data = source.to_dict()
    assert data["source_type"] == "vendor_case"
    assert data["usable_for"] == ["scenario_selection"]
    assert "molten" not in " ".join(data["covered_fields"]).lower()


def test_knowledge_base_rejects_incomplete_source():
    source = PublicWeldSource(
        source_id="incomplete",
        source_type=SourceType.DATASET,
        title="Incomplete",
        url="https://example.com",
        publisher="unknown",
        shipbuilding_relevance="",
        covered_fields=[],
        missing_fields=[],
        usable_for=[],
        source_refs=[],
        assumptions=[],
        notes="",
    )
    kb = PublicWeldKnowledgeBase([source])

    issues = kb.validation_issues()

    assert issues
    assert "incomplete" in issues[0]


def test_seed_knowledge_base_has_first_gate_coverage():
    kb = load_seed_knowledge_base()

    assert len(kb.sources) >= 8
    assert kb.validation_issues() == []

    usable_for = {item.value for source in kb.sources for item in source.usable_for}
    assert "scenario_selection" in usable_for
    assert "parameter_range" in usable_for
    assert "quality_label" in usable_for


def test_seed_knowledge_base_has_no_molten_pool_source_content():
    kb = load_seed_knowledge_base()
    source_json_text = str(kb.to_dict()).lower()

    assert "molten_pool" not in source_json_text
    assert "weld_pool" not in source_json_text
    assert "熔池" not in source_json_text
