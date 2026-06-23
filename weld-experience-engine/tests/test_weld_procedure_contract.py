from pathlib import Path

import pytest

from weldcore.skill_asset.procedure_contract import (
    DEFAULT_PROCEDURE_WORKBOOK_PATH,
    build_weld_procedure_knowledge_contract,
)


def _field_by_name(contract, display_name):
    return next(
        field for field in contract["fields"] if field["display_name"] == display_name
    )


def test_build_weld_procedure_contract_summarizes_excel_contract():
    contract = build_weld_procedure_knowledge_contract()

    assert contract["source_workbook_ref"].endswith(
        "docs/焊接工艺数据库主要参数表.xlsx"
    )
    assert contract["contract_version"] == "k01.v0.1"
    assert contract["field_count"] == 47
    assert contract["category_count"] == 8
    assert contract["requirement_summary"] == {
        "required": 21,
        "conditional_required": 12,
        "supplemental": 14,
    }


def test_build_weld_procedure_contract_preserves_expected_categories():
    contract = build_weld_procedure_knowledge_contract()

    assert contract["categories"] == [
        "母材信息",
        "焊材信息",
        "接头形式",
        "焊接方法",
        "焊接参数",
        "气体参数",
        "质量要求",
        "工艺规程关联",
    ]
    assert all(field["category"] for field in contract["fields"])


def test_build_weld_procedure_contract_maps_representative_fields():
    contract = build_weld_procedure_knowledge_contract()

    base_thickness = _field_by_name(contract, "母材厚度(mm)")
    assert base_thickness["unit"] == "mm"
    assert base_thickness["data_type"] == "number"
    assert base_thickness["requirement_level"] == "required"

    heat_input = _field_by_name(contract, "热输入(kJ/mm)")
    assert heat_input["field_id"] == "heat_input_kj_per_mm"
    assert heat_input["acquisition_mode"] == "system_computed"
    assert "wps_pqr_release" in heat_input["blocks"]

    wps_number = _field_by_name(contract, "WPS编号")
    assert wps_number["acquisition_mode"] == "human_required"
    assert "expert_review" in wps_number["blocks"]

    travel_speed = _field_by_name(contract, "焊接速度(mm/min)")
    assert travel_speed["acquisition_mode"] == "asset_or_simulation_inferred"
    assert "isaac_replay_config" in travel_speed["nv01_usage"]


def test_build_weld_procedure_contract_raises_for_missing_workbook(tmp_path):
    missing_workbook = tmp_path / "missing.xlsx"

    with pytest.raises(FileNotFoundError):
        build_weld_procedure_knowledge_contract(missing_workbook)


def test_default_procedure_workbook_path_points_to_repo_docs_workbook():
    assert DEFAULT_PROCEDURE_WORKBOOK_PATH == (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "焊接工艺数据库主要参数表.xlsx"
    )
    assert DEFAULT_PROCEDURE_WORKBOOK_PATH.exists()
