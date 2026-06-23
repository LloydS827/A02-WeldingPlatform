from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
from typing import Any

from openpyxl import load_workbook


DEFAULT_PROCEDURE_WORKBOOK_PATH = (
    Path(__file__).resolve().parents[3] / "docs" / "焊接工艺数据库主要参数表.xlsx"
)
CONTRACT_VERSION = "k01.v0.1"
MAIN_SHEET_NAME = "工艺数据库参数总表"
REQUIRED_HEADERS = ("参数类别", "参数名称", "参数说明", "数据类型", "是否必填", "备注")

_REQUIREMENT_LEVELS = {
    "必填": "required",
    "条件必填": "conditional_required",
    "可选": "supplemental",
}
_DATA_TYPES = {
    "文本": "text",
    "数值": "number",
    "整数": "integer",
}
_EXPECTED_FIELD_COUNT = 47
_EXPECTED_CATEGORY_COUNT = 8
_EXPECTED_REQUIREMENT_SUMMARY = {
    "required": 21,
    "conditional_required": 12,
    "supplemental": 14,
}
_FIELD_OVERRIDES: dict[str, dict[str, Any]] = {
    "WPS编号": {
        "field_id": "wps_number",
        "acquisition_mode": "human_required",
        "human_role": "welding_procedure_engineer",
        "a02_target_path": "ExpertReviewRecord.required_real_context",
        "nv01_usage": ["procedure_gate", "expert_gate"],
        "blocks": ["expert_review", "wps_pqr_release"],
    },
    "PQR编号": {
        "field_id": "pqr_number",
        "acquisition_mode": "human_required",
        "human_role": "welding_procedure_engineer",
        "a02_target_path": "ExpertReviewRecord.required_real_context",
        "nv01_usage": ["procedure_gate"],
        "blocks": ["wps_pqr_release"],
    },
    "热输入(kJ/mm)": {
        "field_id": "heat_input_kj_per_mm",
        "acquisition_mode": "system_computed",
        "human_role": "welding_procedure_engineer_review",
        "a02_target_path": "ManipulationSkillAsset.constraints.process_parameters.heat_input",
        "nv01_usage": ["training_readiness_report", "domain_randomization_recipe"],
        "blocks": ["wps_pqr_release"],
    },
    "焊接速度(mm/min)": {
        "field_id": "travel_speed_mm_per_min",
        "acquisition_mode": "asset_or_simulation_inferred",
        "human_role": "welding_robotics_engineer_review",
        "a02_target_path": "ManipulationSkillAsset.motion.tcp_trajectory",
        "nv01_usage": ["isaac_replay_config", "domain_randomization_recipe"],
        "blocks": ["expert_review"],
    },
    "坡口角度α(°)": {
        "field_id": "groove_angle_deg",
        "acquisition_mode": "human_confirmed_or_imported",
        "human_role": "welding_procedure_engineer",
        "a02_target_path": "ManipulationSkillAsset.constraints.joint_geometry.groove_angle",
        "nv01_usage": ["OpenUSD process_metadata", "domain_randomization_recipe"],
        "blocks": ["expert_review"],
    },
    "根部间隙R(mm)": {
        "field_id": "root_gap_mm",
        "acquisition_mode": "human_confirmed_or_imported",
        "human_role": "welding_procedure_engineer",
        "a02_target_path": "ManipulationSkillAsset.constraints.joint_geometry.root_gap",
        "nv01_usage": ["OpenUSD process_metadata", "domain_randomization_recipe"],
        "blocks": ["expert_review"],
    },
    "焊接电流(A)": {
        "field_id": "welding_current_a",
        "acquisition_mode": "workcell_logged",
        "human_role": "welding_procedure_engineer_review",
        "a02_target_path": "ManipulationSkillAsset.constraints.process_parameters.current",
        "nv01_usage": ["procedure_parameter_inputs", "domain_randomization_recipe"],
        "blocks": ["expert_review"],
    },
    "焊接电压(V)": {
        "field_id": "welding_voltage_v",
        "acquisition_mode": "workcell_logged",
        "human_role": "welding_procedure_engineer_review",
        "a02_target_path": "ManipulationSkillAsset.constraints.process_parameters.voltage",
        "nv01_usage": ["procedure_parameter_inputs", "domain_randomization_recipe"],
        "blocks": ["expert_review"],
    },
    "无损检测等级": {
        "field_id": "ndt_acceptance_level",
        "acquisition_mode": "human_required",
        "human_role": "quality_engineer",
        "a02_target_path": "ExpertReviewRecord.required_real_context",
        "nv01_usage": ["expert_gate", "training_readiness_report"],
        "blocks": ["expert_review", "wps_pqr_release"],
    },
}


def build_weld_procedure_knowledge_contract(
    workbook_path: str | Path = DEFAULT_PROCEDURE_WORKBOOK_PATH,
) -> dict[str, Any]:
    path = Path(workbook_path)
    if not path.exists():
        raise FileNotFoundError(path)

    workbook = load_workbook(path, data_only=True, read_only=True)
    worksheet = workbook[MAIN_SHEET_NAME]
    rows = list(worksheet.iter_rows(values_only=True))
    headers = tuple(rows[0][: len(REQUIRED_HEADERS)])
    if headers != REQUIRED_HEADERS:
        raise ValueError(f"Unexpected procedure workbook headers: {headers!r}")

    fields: list[dict[str, Any]] = []
    categories: list[str] = []
    current_category = ""
    for index, row in enumerate(rows[1:], start=1):
        category, display_name, description, data_type, requirement, remark = row[:6]
        if category:
            current_category = str(category)
            categories.append(current_category)
        if not display_name:
            continue
        fields.append(
            _build_field(
                index=index,
                category=current_category,
                display_name=str(display_name),
                description=str(description or ""),
                data_type=str(data_type),
                requirement=str(requirement),
                remark=str(remark or ""),
            )
        )

    requirement_counts = Counter(field["requirement_level"] for field in fields)
    requirement_summary = {
        "required": requirement_counts["required"],
        "conditional_required": requirement_counts["conditional_required"],
        "supplemental": requirement_counts["supplemental"],
    }
    _validate_baseline(fields, categories, requirement_summary)
    return {
        "source_workbook_ref": str(path.resolve()),
        "contract_version": CONTRACT_VERSION,
        "field_count": len(fields),
        "category_count": len(categories),
        "requirement_summary": requirement_summary,
        "categories": categories,
        "fields": fields,
        "a02_target_paths": sorted(
            {field["a02_target_path"] for field in fields if field["a02_target_path"]}
        ),
        "nv01_usage_tags": sorted(
            {usage for field in fields for usage in field["nv01_usage"]}
        ),
        "evidence_boundary": "workbook_contract_only",
    }


def _build_field(
    *,
    index: int,
    category: str,
    display_name: str,
    description: str,
    data_type: str,
    requirement: str,
    remark: str,
) -> dict[str, Any]:
    override = _FIELD_OVERRIDES.get(display_name, {})
    requirement_level = _map_requirement(requirement)
    field = {
        "field_id": f"field_{index:03d}",
        "category": category,
        "display_name": display_name,
        "description": description,
        "data_type": _map_data_type(data_type),
        "unit": _parse_unit(display_name),
        "requirement_level": requirement_level,
        "required_when": remark if requirement_level == "conditional_required" else "",
        "acquisition_mode": "human_confirmed_or_imported",
        "human_role": "",
        "a02_target_path": "",
        "nv01_usage": [],
        "blocks": [],
        "evidence_boundary": "excel_contract_field",
    }
    field.update(override)
    return field


def _validate_baseline(
    fields: list[dict[str, Any]],
    categories: list[str],
    requirement_summary: dict[str, int],
) -> None:
    if (
        len(fields) != _EXPECTED_FIELD_COUNT
        or len(categories) != _EXPECTED_CATEGORY_COUNT
        or requirement_summary != _EXPECTED_REQUIREMENT_SUMMARY
    ):
        raise ValueError(
            "Weld procedure workbook baseline drift: "
            f"fields={len(fields)}, categories={len(categories)}, "
            f"requirement_summary={requirement_summary}"
        )


def _map_requirement(requirement: str) -> str:
    return _REQUIREMENT_LEVELS[requirement]


def _map_data_type(data_type: str) -> str:
    return _DATA_TYPES[data_type]


def _parse_unit(display_name: str) -> str:
    match = re.search(r"\(([^()]+)\)$", display_name)
    return match.group(1) if match else ""
