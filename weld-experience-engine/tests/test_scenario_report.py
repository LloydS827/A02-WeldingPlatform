import json

import pytest

from weldcore.knowledge.seeds import load_seed_knowledge_base
from weldcore.knowledge.shipbuilding import (
    ShipbuildingTaskFamily,
    TaskDisposition,
    WeldJointType,
    WeldPosition,
)
from weldcore.report.scenario_report import run_scenario_report


def test_scenario_report_writes_source_and_scenario_evidence(tmp_path):
    evidence = run_scenario_report(tmp_path)

    assert len(evidence["sources"]["sources"]) >= 8
    assert evidence["scenarios"]
    assert all("shipbuilding_context" in item for item in evidence["scenarios"])
    assert all(
        "requires_real_validation_later" in item["evidence_roles"]
        for item in evidence["scenarios"]
    )

    assert (tmp_path / "sources.json").exists()
    assert (tmp_path / "task_families.json").exists()
    assert (tmp_path / "scenarios.json").exists()
    assert (tmp_path / "field_coverage.csv").exists()
    assert (tmp_path / "evidence.md").exists()

    data = json.loads((tmp_path / "scenarios.json").read_text(encoding="utf-8"))
    assert data[0]["shipbuilding_context"]


def test_scenario_report_blocks_when_task_gate_fails(tmp_path):
    kb = load_seed_knowledge_base()
    bad_family = ShipbuildingTaskFamily(
        family_id="bad-family",
        name="Bad",
        shipbuilding_context="panel line",
        typical_weld_objects=["bad"],
        joint_types=[WeldJointType.FILLET],
        positions=[WeldPosition.FLAT],
        modeling_difficulty=1,
        required_fields=["unsupported"],
        assumption_fields=[],
        source_ids=["missing-source"],
        disposition=TaskDisposition.CANDIDATE,
        notes="bad",
    )

    with pytest.raises(ValueError, match="Task family gate failed"):
        run_scenario_report(tmp_path, knowledge_base=kb, task_families=[bad_family])


def test_scenario_report_keeps_chinese_molten_pool_only_as_boundary_text(tmp_path):
    run_scenario_report(tmp_path)

    evidence_text = (tmp_path / "evidence.md").read_text(encoding="utf-8")
    json_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            tmp_path / "sources.json",
            tmp_path / "task_families.json",
            tmp_path / "scenarios.json",
        ]
    )

    assert "真实焊接质量已经验证" not in evidence_text
    assert "不等于真实焊接质量验证" in evidence_text
    assert "熔池" in evidence_text
    assert "不纳入本阶段" in evidence_text
    assert "熔池" not in json_text
    assert "molten_pool" not in json_text.lower()
    assert "weld_pool" not in json_text.lower()
