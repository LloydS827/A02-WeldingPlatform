from weldcore.knowledge.scenario import (
    EvidenceRole,
    ParameterRange,
    ScenarioGateResult,
    SimulationScenarioSpec,
    scenario_from_task_family,
)
from weldcore.knowledge.seeds import load_seed_task_families
from weldcore.knowledge.shipbuilding import TaskDisposition


def test_scenario_from_task_family_preserves_sources_context_and_roles():
    family = next(
        item for item in load_seed_task_families() if item.family_id == "stiffened-panel-fillet"
    )

    scenario = scenario_from_task_family(family)

    assert scenario.scenario_id == "scenario-stiffened-panel-fillet"
    assert scenario.shipbuilding_context == family.shipbuilding_context
    assert scenario.source_refs == family.source_ids
    assert scenario.task_disposition == TaskDisposition.CANDIDATE
    assert EvidenceRole.PUBLIC_CONSTRAINT in scenario.evidence_roles
    assert EvidenceRole.REQUIRES_REAL_VALIDATION_LATER in scenario.evidence_roles


def test_scenario_gate_rejects_deferred_when_candidate_required():
    family = next(
        item for item in load_seed_task_families() if item.family_id == "curved-complex-seams"
    )
    scenario = scenario_from_task_family(family)

    result = ScenarioGateResult.from_scenario(scenario, require_candidate=True)

    assert scenario.source_refs == family.source_ids
    assert not result.passed
    assert any("candidate" in issue for issue in result.issues)


def test_parameter_range_serializes_units_and_source_role():
    value = ParameterRange(
        name="travel_speed",
        unit="mm/s",
        min_value=3.0,
        max_value=8.0,
        evidence_role=EvidenceRole.PUBLIC_CONSTRAINT,
        source_refs=["vendor-kranendonk-panel-welding-gantry"],
    )

    assert value.to_dict()["evidence_role"] == "public_constraint"


def test_scenario_gate_rejects_weld_pool_dependency_written_with_spaces():
    scenario = SimulationScenarioSpec(
        scenario_id="scenario-pool-dependent",
        shipbuilding_task="Pool dependent",
        shipbuilding_context="panel line",
        difficulty="easy",
        task_disposition=TaskDisposition.CANDIDATE,
        weld_condition={"family_id": "pool-dependent"},
        parameter_ranges=[],
        motion_templates=["straight"],
        quality_placeholders=["weld pool feedback label"],
        source_refs=[
            "vendor-hyundai-welding-cobot-shipbuilding-2024",
            "project-260522-shipbuilding-welding-brain-plan",
        ],
        assumptions=[],
    )

    result = ScenarioGateResult.from_scenario(scenario, require_candidate=True)

    assert not result.passed
    assert any("out of scope" in issue for issue in result.issues)


def test_scenario_gate_rejects_pool_dependency_in_condition_and_ranges():
    scenario = SimulationScenarioSpec(
        scenario_id="scenario-pool-condition",
        shipbuilding_task="Pool condition",
        shipbuilding_context="panel line",
        difficulty="easy",
        task_disposition=TaskDisposition.CANDIDATE,
        weld_condition={"sensor": "weld_pool_camera"},
        parameter_ranges=[
            ParameterRange(
                name="熔池宽度",
                unit="mm",
                min_value=1.0,
                max_value=3.0,
                evidence_role=EvidenceRole.ASSUMPTION,
                source_refs=["project-260522-shipbuilding-welding-brain-plan"],
            )
        ],
        motion_templates=["straight"],
        quality_placeholders=["geometry_risk_label"],
        source_refs=[
            "vendor-hyundai-welding-cobot-shipbuilding-2024",
            "project-260522-shipbuilding-welding-brain-plan",
        ],
        assumptions=[],
    )

    result = ScenarioGateResult.from_scenario(scenario, require_candidate=True)

    assert not result.passed
    assert any("out of scope" in issue for issue in result.issues)
