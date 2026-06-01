from weldcore.knowledge.seeds import load_seed_knowledge_base, load_seed_task_families
from weldcore.knowledge.shipbuilding import (
    ShipbuildingTaskFamily,
    TaskDisposition,
    WeldJointType,
    WeldPosition,
    rank_task_families,
    select_first_batch_candidates,
    validate_task_family_support,
)


def test_seed_task_families_are_shipbuilding_specific_and_ranked():
    kb = load_seed_knowledge_base()
    families = load_seed_task_families()

    assert len(families) >= 6
    assert all(f.shipbuilding_context for f in families)

    ranked = rank_task_families(families, kb)

    assert all(validate_task_family_support(f, kb).passed for f in families)
    assert ranked[0].family_id == "stiffened-panel-fillet"
    assert ranked[0].disposition == TaskDisposition.CANDIDATE
    assert ranked[-1].disposition == TaskDisposition.DEFER


def test_first_batch_requires_kb_supported_sources_and_fields():
    kb = load_seed_knowledge_base()
    families = load_seed_task_families()

    selected = select_first_batch_candidates(families, kb, limit=3)

    assert 2 <= len(selected) <= 3
    assert all(validate_task_family_support(f, kb).passed for f in selected)
    assert {f.family_id for f in selected}.issubset(
        {
            "stiffened-panel-fillet",
            "panel-butt",
            "micro-panel-web-bulkhead",
        }
    )


def test_task_support_rejects_unknown_sources_and_unsupported_fields():
    kb = load_seed_knowledge_base()
    family = ShipbuildingTaskFamily(
        family_id="bad-family",
        name="Bad",
        shipbuilding_context="panel line",
        typical_weld_objects=["unknown"],
        joint_types=[WeldJointType.FILLET],
        positions=[WeldPosition.FLAT],
        modeling_difficulty=1,
        required_fields=["not_covered_or_declared"],
        assumption_fields=[],
        source_ids=["missing-source"],
        disposition=TaskDisposition.CANDIDATE,
        notes="bad",
    )

    result = validate_task_family_support(family, kb)

    assert not result.passed
    assert any("unknown source" in issue for issue in result.issues)
    assert any("unsupported required field" in issue for issue in result.issues)


def test_task_support_does_not_treat_source_missing_fields_as_support():
    kb = load_seed_knowledge_base()
    family = ShipbuildingTaskFamily(
        family_id="missing-field-family",
        name="Missing field family",
        shipbuilding_context="generic public dataset screening",
        typical_weld_objects=["screening"],
        joint_types=[WeldJointType.BUTT],
        positions=[WeldPosition.FLAT],
        modeling_difficulty=1,
        required_fields=["trajectory"],
        assumption_fields=[],
        source_ids=["dataset-gdxray-weld-xray", "dataset-zenodo-metal-arc-welding-10017718"],
        disposition=TaskDisposition.CANDIDATE,
        notes="trajectory is listed as missing by a source and must not count as support",
    )

    result = validate_task_family_support(family, kb)

    assert not result.passed
    assert any("unsupported required field: trajectory" in issue for issue in result.issues)


def test_task_support_accepts_required_field_when_declared_as_assumption():
    kb = load_seed_knowledge_base()
    family = ShipbuildingTaskFamily(
        family_id="assumed-field-family",
        name="Assumed field family",
        shipbuilding_context="generic public dataset screening",
        typical_weld_objects=["screening"],
        joint_types=[WeldJointType.BUTT],
        positions=[WeldPosition.FLAT],
        modeling_difficulty=1,
        required_fields=["trajectory"],
        assumption_fields=["trajectory"],
        source_ids=[
            "dataset-gdxray-weld-xray",
            "vendor-hyundai-welding-cobot-shipbuilding-2024",
        ],
        disposition=TaskDisposition.CANDIDATE,
        notes="trajectory is explicit project assumption for this gate",
    )

    result = validate_task_family_support(family, kb)

    assert result.passed


def test_task_support_rejects_weld_pool_dependency_written_with_spaces():
    kb = load_seed_knowledge_base()
    family = ShipbuildingTaskFamily(
        family_id="pool-dependent-family",
        name="Pool dependent family",
        shipbuilding_context="panel line",
        typical_weld_objects=["screening"],
        joint_types=[WeldJointType.FILLET],
        positions=[WeldPosition.FLAT],
        modeling_difficulty=1,
        required_fields=["shipbuilding_context"],
        assumption_fields=[],
        source_ids=[
            "vendor-hyundai-welding-cobot-shipbuilding-2024",
            "project-260522-shipbuilding-welding-brain-plan",
        ],
        disposition=TaskDisposition.CANDIDATE,
        notes="requires weld pool feedback",
    )

    result = validate_task_family_support(family, kb)

    assert not result.passed
    assert any("out of scope" in issue for issue in result.issues)


def test_task_support_rejects_pool_dependency_in_weld_objects():
    kb = load_seed_knowledge_base()
    family = ShipbuildingTaskFamily(
        family_id="pool-object-family",
        name="Pool object family",
        shipbuilding_context="panel line",
        typical_weld_objects=["weld_pool_camera_roi"],
        joint_types=[WeldJointType.FILLET],
        positions=[WeldPosition.FLAT],
        modeling_difficulty=1,
        required_fields=["shipbuilding_context"],
        assumption_fields=[],
        source_ids=[
            "vendor-hyundai-welding-cobot-shipbuilding-2024",
            "project-260522-shipbuilding-welding-brain-plan",
        ],
        disposition=TaskDisposition.CANDIDATE,
        notes="otherwise supported",
    )

    result = validate_task_family_support(family, kb)

    assert not result.passed
    assert any("out of scope" in issue for issue in result.issues)
