from weldcore.skill_asset import build_manipulation_skill_asset_from_simulation_bundle
from weldcore.simulation_bakeoff import (
    build_simulation_evidence_bundle,
    default_simulation_task_specs,
    run_simlite_reference,
)


def _default_skill_asset():
    task_spec = default_simulation_task_specs()[0]
    bundle = build_simulation_evidence_bundle(task_spec, run_simlite_reference(task_spec))
    return build_manipulation_skill_asset_from_simulation_bundle(bundle)


def test_default_simulation_skill_asset_uses_canonical_simulation_only_source():
    skill = _default_skill_asset()

    assert skill.source_type == "simulation_only"
    assert skill.evidence.source_type == "simulation_only"
    assert "simulation_only" in skill.evidence.evidence_boundary
