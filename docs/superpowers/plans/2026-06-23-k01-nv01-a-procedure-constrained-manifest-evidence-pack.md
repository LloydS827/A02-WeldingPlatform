# K01 NV01-A Procedure-Constrained Manifest Evidence Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 `K01 + NV01-A Procedure-Constrained Manifest Evidence Pack`，从焊接工艺 Excel 和当前 Demo Evidence Pack 生成可复跑、可审查的 procedure contract、digital twin package、OpenUSD/Isaac-oriented manifest/report。

**Architecture:** 新增一个轻量 K01 parser/builder 模块读取 `docs/焊接工艺数据库主要参数表.xlsx`，生成 `WeldProcedureKnowledgeContract`、per-task `WeldProcedureParameterSet` 和 `WeldProcedureValidationReport`。新增一个 NV01 builder/report 模块复用现有 `demo_report` canonical artifacts，把 K01 payload 与 `ManipulationSkillAsset`、`RobotBodyAsset`、`RobotContextSpec`、`SceneContextAsset`、`ExpertReviewRecord` 组合成 OpenUSD manifest、Isaac replay config、domain randomization recipe、training readiness report 和 alignment matrix。第一版只生成合同和 report，不接 Isaac Sim runtime，不写 `.usd/.usda`，不生成正式 WPS/PQR。

**Tech Stack:** Python 3.10+, dataclasses/dict payloads, `openpyxl` for structured `.xlsx` reading, existing `weldcore.skill_asset.demo_report`, standard-library JSON/HTML/Markdown helpers, pytest.

---

## Scope Check

本计划只覆盖 K01 + NV01-A。它应产出可运行软件，而不是只补文档：

- In scope: Excel 字段合同读取、字段分类、缺口报告、procedure-to-NV01 mapping、OpenUSD/Isaac-oriented JSON manifest/report、默认 CLI、测试、README/details 同步。
- Out of scope: Isaac Sim 安装或运行、OpenUSD SDK writer、Isaac Lab 环境、Replicator 数据集生成、Cosmos、Nucleus、Isaac ROS/Jetson、真实机器人控制、正式 WPS/PQR 审批系统、完整工艺数据库 UI。

如果实现中发现需要真实工位数据或正式工艺审批才能继续，必须写入 `blocked_by` / `not_ready_reasons`，不能用默认值伪造通过。

## File Map

- Modify: `weld-experience-engine/pyproject.toml`
  - Add `openpyxl>=3.1` to default dependencies.
  - Do not add or commit `uv.lock` unless the repository policy changes.
- Create: `weld-experience-engine/weldcore/skill_asset/procedure_contract.py`
  - Read `docs/焊接工艺数据库主要参数表.xlsx`.
  - Fill down merged category cells.
  - Build `WeldProcedureKnowledgeContract`, `WeldProcedureParameterSet`, `WeldProcedureValidationReport`, and `ProcedureToNV01MappingMatrix` payload dictionaries.
  - Keep all WPS/PQR and human-confirmation boundaries explicit.
- Create: `weld-experience-engine/weldcore/skill_asset/nvidia_digital_twin.py`
  - Build `WeldSkillDigitalTwinPackage`.
  - Build `openusd_scene_manifest`, `isaac_sim_replay_config`, `domain_randomization_recipe`, `training_readiness_report`, and `nvidia_stack_alignment_matrix`.
  - Read canonical per-task artifacts produced by `demo_report`.
- Create: `weld-experience-engine/weldcore/skill_asset/nvidia_digital_twin_report.py`
  - CLI/library entry point.
  - If `--source-demo-dir` is missing or does not exist, generate default source demo pack with `run_demo_evidence_pack`.
  - Write top-level and per-task artifacts.
  - Render `nv01_summary.md` and `nv01_summary.json`.
- Modify: `weld-experience-engine/weldcore/skill_asset/__init__.py`
  - Export stable builder functions only if useful for tests or downstream callers.
- Create: `weld-experience-engine/tests/test_weld_procedure_contract.py`
  - Focused K01 parser, classification, parameter set, validation, mapping tests.
- Create: `weld-experience-engine/tests/test_nvidia_digital_twin_report.py`
  - End-to-end CLI/library artifact tests for K01 + NV01-A.
- Modify: `README.md`
  - Move K01 + NV01-A from target-only wording into current runnable capability after implementation.
  - Keep clear boundary: not Isaac Sim runtime, not formal WPS/PQR.
- Modify: `details.md`
  - Add a dated stage update for K01 + NV01-A implementation.
  - Update "尚未完成" and "下一步建议" so NV01-B becomes OpenUSD authoring spike.
- Modify: `weld-experience-engine/README.md`
  - Add `nvidia_digital_twin_report` command and expected artifacts.
- Modify: `README.html`, `details.html`
  - Regenerate from Markdown after README/details changes.

## Contract Baseline

The Excel parser must treat this as the current authoritative baseline:

```text
Workbook: docs/焊接工艺数据库主要参数表.xlsx
Sheet: 工艺数据库参数总表
Headers: 参数类别, 参数名称, 参数说明, 数据类型, 是否必填, 备注
Rows including header: 48
Fields excluding header: 47
Categories after fill-down: 8
Requirement summary: 必填=21, 条件必填=12, 可选=14
Data types: 文本=25, 数值=21, 整数=1
```

Important parser detail: `参数类别` uses merged cells. Direct row reads return `None` for most category cells. The implementation must fill the last non-empty category downward before counting categories or assigning fields.

Requirement mapping:

```python
REQUIREMENT_LEVEL_BY_EXCEL_VALUE = {
    "必填": "required",
    "条件必填": "conditional_required",
    "可选": "supplemental",
}
```

Data type mapping:

```python
DATA_TYPE_BY_EXCEL_VALUE = {
    "文本": "text",
    "数值": "number",
    "整数": "integer",
}
```

Acquisition mode enum:

```python
ACQUISITION_MODES = (
    "human_required",
    "human_confirmed_or_imported",
    "system_computed",
    "asset_or_simulation_inferred",
    "workcell_logged",
    "reference_catalog",
)
```

Use field-specific overrides for semantics, and category defaults only as fallback. Minimum required overrides:

```python
FIELD_RULE_OVERRIDES = {
    "WPS编号": {
        "field_id": "wps_number",
        "acquisition_mode": "human_required",
        "human_role": "welding_procedure_engineer",
        "a02_target_path": "ExpertReviewRecord.required_real_context",
        "nv01_usage": ("procedure_gate", "expert_gate"),
        "blocks": ("expert_review", "wps_pqr_release"),
    },
    "PQR编号": {
        "field_id": "pqr_number",
        "acquisition_mode": "human_required",
        "human_role": "welding_procedure_engineer",
        "a02_target_path": "ExpertReviewRecord.required_real_context",
        "nv01_usage": ("procedure_gate",),
        "blocks": ("wps_pqr_release",),
    },
    "热输入(kJ/mm)": {
        "field_id": "heat_input_kj_per_mm",
        "acquisition_mode": "system_computed",
        "human_role": "welding_procedure_engineer_review",
        "a02_target_path": "ManipulationSkillAsset.constraints.process_parameters.heat_input",
        "nv01_usage": ("training_readiness_report", "domain_randomization_recipe"),
        "blocks": ("wps_pqr_release",),
    },
    "焊接速度(mm/min)": {
        "field_id": "travel_speed_mm_per_min",
        "acquisition_mode": "asset_or_simulation_inferred",
        "human_role": "welding_robotics_engineer_review",
        "a02_target_path": "ManipulationSkillAsset.motion.tcp_trajectory",
        "nv01_usage": ("isaac_replay_config", "domain_randomization_recipe"),
        "blocks": ("expert_review",),
    },
    "坡口角度α(°)": {
        "field_id": "groove_angle_deg",
        "acquisition_mode": "human_confirmed_or_imported",
        "human_role": "welding_procedure_engineer",
        "a02_target_path": "ManipulationSkillAsset.constraints.joint_geometry.groove_angle",
        "nv01_usage": ("OpenUSD process_metadata", "domain_randomization_recipe"),
        "blocks": ("expert_review",),
    },
    "根部间隙R(mm)": {
        "field_id": "root_gap_mm",
        "acquisition_mode": "human_confirmed_or_imported",
        "human_role": "welding_procedure_engineer",
        "a02_target_path": "ManipulationSkillAsset.constraints.joint_geometry.root_gap",
        "nv01_usage": ("OpenUSD process_metadata", "domain_randomization_recipe"),
        "blocks": ("expert_review",),
    },
    "焊接电流(A)": {
        "field_id": "welding_current_a",
        "acquisition_mode": "workcell_logged",
        "human_role": "welding_procedure_engineer_review",
        "a02_target_path": "ManipulationSkillAsset.constraints.process_parameters.current",
        "nv01_usage": ("procedure_parameter_inputs", "domain_randomization_recipe"),
        "blocks": ("expert_review",),
    },
    "焊接电压(V)": {
        "field_id": "welding_voltage_v",
        "acquisition_mode": "workcell_logged",
        "human_role": "welding_procedure_engineer_review",
        "a02_target_path": "ManipulationSkillAsset.constraints.process_parameters.voltage",
        "nv01_usage": ("procedure_parameter_inputs", "domain_randomization_recipe"),
        "blocks": ("expert_review",),
    },
    "无损检测等级": {
        "field_id": "ndt_acceptance_level",
        "acquisition_mode": "human_required",
        "human_role": "quality_engineer",
        "a02_target_path": "ExpertReviewRecord.required_real_context",
        "nv01_usage": ("expert_gate", "training_readiness_report"),
        "blocks": ("expert_review", "wps_pqr_release"),
    },
}
```

Do not hard-code the 47 field rows themselves. Read them from the workbook, then apply overrides by display name.

## Expected Top-Level Output

Default command:

```bash
cd weld-experience-engine
uv run python -m weldcore.skill_asset.nvidia_digital_twin_report \
  --source-demo-dir artifacts/demo/skill-asset-evidence \
  --outdir artifacts/demo/nvidia-digital-twin-foundation
```

If `--source-demo-dir` is omitted or does not exist, the command should generate the source demo pack internally under the output directory, for example:

```text
artifacts/demo/nvidia-digital-twin-foundation/_source_demo_evidence/
```

Expected output files:

```text
nv01_summary.md
nv01_summary.json
weld_procedure_knowledge_contract.json
weld_procedure_parameter_set.json
weld_procedure_validation_report.json
procedure_to_nv01_mapping_matrix.json
weld_skill_digital_twin_package.json
openusd_scene_manifest.json
isaac_sim_replay_config.json
domain_randomization_recipe.json
training_readiness_report.json
nvidia_stack_alignment_matrix.json
task-<unit-id>/skill_asset_ref.json
task-<unit-id>/weld_procedure_parameter_set.json
task-<unit-id>/weld_procedure_validation_report.json
task-<unit-id>/openusd_task_manifest.json
task-<unit-id>/isaac_replay_task_config.json
task-<unit-id>/sensor_and_annotation_manifest.json
task-<unit-id>/training_task_readiness.json
```

---

### Task 1: K01 Excel Contract Parser

**Files:**
- Modify: `weld-experience-engine/pyproject.toml`
- Create: `weld-experience-engine/weldcore/skill_asset/procedure_contract.py`
- Create: `weld-experience-engine/tests/test_weld_procedure_contract.py`

- [ ] **Step 1: Write failing tests for Excel contract parsing**

Create `weld-experience-engine/tests/test_weld_procedure_contract.py`:

```python
import pytest

from weldcore.skill_asset.procedure_contract import (
    DEFAULT_PROCEDURE_WORKBOOK_PATH,
    build_weld_procedure_knowledge_contract,
)


def test_weld_procedure_contract_reads_excel_with_filled_categories():
    contract = build_weld_procedure_knowledge_contract()

    assert contract["source_workbook_ref"].endswith("docs/焊接工艺数据库主要参数表.xlsx")
    assert contract["contract_version"] == "k01.v0.1"
    assert contract["field_count"] == 47
    assert contract["category_count"] == 8
    assert contract["requirement_summary"] == {
        "required": 21,
        "conditional_required": 12,
        "supplemental": 14,
    }
    assert [category["name"] for category in contract["categories"]] == [
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


def test_weld_procedure_contract_normalizes_representative_fields():
    contract = build_weld_procedure_knowledge_contract()
    fields = {field["display_name"]: field for field in contract["fields"]}

    thickness = fields["母材厚度(mm)"]
    assert thickness["unit"] == "mm"
    assert thickness["data_type"] == "number"
    assert thickness["requirement_level"] == "required"

    heat_input = fields["热输入(kJ/mm)"]
    assert heat_input["field_id"] == "heat_input_kj_per_mm"
    assert heat_input["acquisition_mode"] == "system_computed"
    assert "wps_pqr_release" in heat_input["blocks"]

    wps = fields["WPS编号"]
    assert wps["acquisition_mode"] == "human_required"
    assert "expert_review" in wps["blocks"]

    travel_speed = fields["焊接速度(mm/min)"]
    assert travel_speed["acquisition_mode"] == "asset_or_simulation_inferred"
    assert "isaac_replay_config" in travel_speed["nv01_usage"]


def test_weld_procedure_contract_missing_workbook_fails(tmp_path):
    missing = tmp_path / "missing.xlsx"

    with pytest.raises(FileNotFoundError):
        build_weld_procedure_knowledge_contract(missing)


def test_default_workbook_path_points_to_repo_docs():
    assert DEFAULT_PROCEDURE_WORKBOOK_PATH.name == "焊接工艺数据库主要参数表.xlsx"
    assert DEFAULT_PROCEDURE_WORKBOOK_PATH.exists()
```

- [ ] **Step 2: Run the new tests and confirm they fail**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_weld_procedure_contract.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'weldcore.skill_asset.procedure_contract'`.

- [ ] **Step 3: Add the Excel dependency**

Modify `weld-experience-engine/pyproject.toml`:

```toml
dependencies = ["numpy>=1.24", "scipy>=1.10", "matplotlib>=3.7", "openpyxl>=3.1"]
```

Do not add `pandas`. Do not add Isaac/OpenUSD dependencies.

- [ ] **Step 4: Implement the minimal contract parser**

Create `weld-experience-engine/weldcore/skill_asset/procedure_contract.py` with these public constants and functions:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

from openpyxl import load_workbook


DEFAULT_PROCEDURE_WORKBOOK_PATH = (
    Path(__file__).resolve().parents[3] / "docs" / "焊接工艺数据库主要参数表.xlsx"
)
CONTRACT_VERSION = "k01.v0.1"
MAIN_SHEET_NAME = "工艺数据库参数总表"
REQUIRED_HEADERS = ("参数类别", "参数名称", "参数说明", "数据类型", "是否必填", "备注")


def build_weld_procedure_knowledge_contract(
    workbook_path: str | Path = DEFAULT_PROCEDURE_WORKBOOK_PATH,
) -> dict[str, Any]:
    path = Path(workbook_path)
    if not path.exists():
        raise FileNotFoundError(path)

    workbook = load_workbook(path, data_only=True, read_only=True)
    if MAIN_SHEET_NAME not in workbook.sheetnames:
        raise ValueError(f"missing_sheet:{MAIN_SHEET_NAME}")

    rows = list(workbook[MAIN_SHEET_NAME].iter_rows(values_only=True))
    headers = tuple(str(value).strip() if value is not None else "" for value in rows[0][:6])
    if headers != REQUIRED_HEADERS:
        raise ValueError(f"unexpected_headers:{headers!r}")

    fields = _build_fields(rows[1:])
    categories = _summarize_categories(fields)
    requirement_summary = _summarize_requirements(fields)

    if len(fields) != 47:
        raise ValueError(f"unexpected_field_count:{len(fields)}")
    if len(categories) != 8:
        raise ValueError(f"unexpected_category_count:{len(categories)}")

    return {
        "source_workbook_ref": str(path),
        "contract_version": CONTRACT_VERSION,
        "field_count": len(fields),
        "category_count": len(categories),
        "requirement_summary": requirement_summary,
        "categories": categories,
        "fields": fields,
        "a02_target_paths": sorted({field["a02_target_path"] for field in fields}),
        "nv01_usage_tags": sorted({tag for field in fields for tag in field["nv01_usage"]}),
        "evidence_boundary": [
            "excel_field_contract_source",
            "not_formal_WPS_PQR",
            "requires_human_confirmation_before_expert_review",
        ],
    }
```

Also implement private helpers:

```python
def _build_fields(rows: list[tuple[Any, ...]]) -> list[dict[str, Any]]:
    fields = []
    current_category = None
    for index, row in enumerate(rows, start=1):
        category, display_name, description, data_type, requirement, note = row[:6]
        if category:
            current_category = str(category).strip()
        if not display_name:
            continue
        fields.append(_build_field(index, current_category, display_name, description, data_type, requirement, note))
    return fields
```

Requirements:

- `_build_fields` must fill down `current_category`.
- `_split_display_name_and_unit("母材厚度(mm)")` returns `("母材厚度", "mm")`.
- `_build_field` must include all keys required by the spec: `field_id`, `category`, `display_name`, `description`, `data_type`, `unit`, `requirement_level`, `required_when`, `acquisition_mode`, `human_role`, `a02_target_path`, `nv01_usage`, `blocks`, `evidence_boundary`.
- Field-specific overrides must win over category defaults.
- Unknown field names should still produce stable fields using a deterministic fallback id such as `field_001`, not a crash.

- [ ] **Step 5: Run parser tests and make them pass**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_weld_procedure_contract.py -q
```

Expected: all tests in `test_weld_procedure_contract.py` PASS.

- [ ] **Step 6: Commit Task 1**

Run:

```bash
git add weld-experience-engine/pyproject.toml \
  weld-experience-engine/weldcore/skill_asset/procedure_contract.py \
  weld-experience-engine/tests/test_weld_procedure_contract.py
git commit -m "feat: add weld procedure contract parser"
```

---

### Task 2: Procedure Parameter Set, Validation, and Mapping

**Files:**
- Modify: `weld-experience-engine/weldcore/skill_asset/procedure_contract.py`
- Modify: `weld-experience-engine/tests/test_weld_procedure_contract.py`

- [ ] **Step 1: Add failing tests for parameter set and validation report**

Append to `weld-experience-engine/tests/test_weld_procedure_contract.py`:

```python
from weldcore.simulation_bakeoff import (
    build_simulation_evidence_bundle,
    default_simulation_task_specs,
    run_simlite_reference,
)
from weldcore.skill_asset.builders import build_manipulation_skill_asset_from_simulation_bundle
from weldcore.skill_asset.procedure_contract import (
    build_procedure_to_nv01_mapping_matrix,
    build_weld_procedure_parameter_set,
    build_weld_procedure_validation_report,
)


def _default_skill_asset():
    task = default_simulation_task_specs()[0]
    bundle = build_simulation_evidence_bundle(task, run_simlite_reference(task))
    return build_manipulation_skill_asset_from_simulation_bundle(bundle)


def test_parameter_set_marks_missing_human_and_workcell_fields():
    contract = build_weld_procedure_knowledge_contract()
    skill_asset = _default_skill_asset()

    parameter_set = build_weld_procedure_parameter_set(skill_asset, contract)

    assert parameter_set["skill_asset_id"] == skill_asset.asset_id
    assert parameter_set["contract_version"] == contract["contract_version"]
    assert parameter_set["parameter_set_id"].startswith("procedure-params-")
    assert "wps_number" in parameter_set["missing_required_fields"]
    assert "welding_current_a" in parameter_set["missing_required_fields"]
    assert "heat_input_kj_per_mm" in parameter_set["computed_fields"]
    assert "travel_speed_mm_per_min" in parameter_set["inferred_fields"]
    assert "not_formal_WPS_PQR" in parameter_set["review_boundary"]


def test_validation_report_separates_contract_review_from_expert_review():
    contract = build_weld_procedure_knowledge_contract()
    parameter_set = build_weld_procedure_parameter_set(_default_skill_asset(), contract)

    report = build_weld_procedure_validation_report(parameter_set, contract)

    assert report["ready_for_procedure_contract_review"] is True
    assert report["ready_for_simulation_replay_package_design"] is True
    assert report["ready_for_expert_review"] is False
    assert report["validation_status"] == "blocked_by_missing_human_required_fields"
    assert "wps_number" in report["human_required_gaps"]
    assert "welding_current_a" in report["workcell_logged_gaps"]
    assert report["wps_pqr_boundary"] == "not_formal_WPS_PQR"


def test_procedure_to_nv01_mapping_matrix_covers_all_fields():
    contract = build_weld_procedure_knowledge_contract()

    matrix = build_procedure_to_nv01_mapping_matrix(contract)

    assert matrix["contract_version"] == contract["contract_version"]
    assert matrix["field_count"] == 47
    assert len(matrix["field_mappings"]) == 47
    speed = matrix["field_mappings"]["travel_speed_mm_per_min"]
    assert "Isaac Sim replay config" in speed["nv01_targets"]
    assert "domain_randomization_recipe" in speed["nv01_targets"]
    wps = matrix["field_mappings"]["wps_number"]
    assert "ExpertReviewRecord.required_real_context" in wps["a02_targets"]
```

- [ ] **Step 2: Run tests and confirm they fail**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_weld_procedure_contract.py -q
```

Expected: FAIL with missing functions.

- [ ] **Step 3: Implement parameter set builder**

In `procedure_contract.py`, add:

```python
def build_weld_procedure_parameter_set(
    skill_asset: Any,
    contract: dict[str, Any],
    artifact_refs: dict[str, str] | None = None,
) -> dict[str, Any]:
    values = {}
    missing_required_fields = []
    missing_conditional_fields = []
    supplemental_gaps = []
    computed_fields = []
    inferred_fields = []
    workcell_logged_gaps = []

    for field in contract["fields"]:
        field_id = field["field_id"]
        status = _parameter_status_for_field(field, skill_asset)
        values[field_id] = status
        if status["coverage_status"] == "missing_required":
            missing_required_fields.append(field_id)
        if status["coverage_status"] == "missing_conditional":
            missing_conditional_fields.append(field_id)
        if status["coverage_status"] == "supplemental_gap":
            supplemental_gaps.append(field_id)
        if field["acquisition_mode"] == "system_computed":
            computed_fields.append(field_id)
        if field["acquisition_mode"] == "asset_or_simulation_inferred":
            inferred_fields.append(field_id)
        if field["acquisition_mode"] == "workcell_logged" and status["value"] is None:
            workcell_logged_gaps.append(field_id)

    return {
        "parameter_set_id": f"procedure-params-{skill_asset.asset_id}",
        "skill_asset_id": skill_asset.asset_id,
        "contract_version": contract["contract_version"],
        "values": values,
        "missing_required_fields": sorted(missing_required_fields),
        "missing_conditional_fields": sorted(missing_conditional_fields),
        "supplemental_gaps": sorted(supplemental_gaps),
        "computed_fields": sorted(computed_fields),
        "inferred_fields": sorted(inferred_fields),
        "workcell_logged_gaps": sorted(workcell_logged_gaps),
        "source_summary": {
            "skill_asset_source_type": skill_asset.source_type,
            "skill_asset_id": skill_asset.asset_id,
            "artifact_refs": artifact_refs or {},
        },
        "review_boundary": [
            "not_formal_WPS_PQR",
            "missing_human_required_fields",
            "simulation_only_values_require_expert_review",
        ],
    }
```

Implementation rules:

- `values` should include all 47 fields.
- Do not pretend current/voltage/WPS/PQR are known.
- `heat_input_kj_per_mm` should be present in `computed_fields` but its value should be blocked unless current, voltage, and travel speed are real values.
- `travel_speed_mm_per_min`, torch angle, weave fields may be `asset_or_simulation_inferred`, but values must carry `evidence_boundary` such as `simulation_inferred_not_wps_validated`.

- [ ] **Step 4: Implement validation report builder**

Add:

```python
def build_weld_procedure_validation_report(
    parameter_set: dict[str, Any],
    contract: dict[str, Any],
) -> dict[str, Any]:
    human_required_gaps = [
        field_id
        for field_id in parameter_set["missing_required_fields"]
        if _field_by_id(contract, field_id)["acquisition_mode"] in {"human_required", "human_confirmed_or_imported"}
    ]
    workcell_logged_gaps = [
        field_id
        for field_id in parameter_set["missing_required_fields"]
        if _field_by_id(contract, field_id)["acquisition_mode"] == "workcell_logged"
    ]
    not_ready_reasons = []
    if human_required_gaps:
        not_ready_reasons.append("blocked_by_missing_human_required_fields")
    if parameter_set["missing_conditional_fields"]:
        not_ready_reasons.append("blocked_by_missing_conditional_procedure_fields")
    if workcell_logged_gaps:
        not_ready_reasons.append("blocked_by_missing_workcell_logged_fields")

    return {
        "validation_status": not_ready_reasons[0] if not_ready_reasons else "ready_for_procedure_contract_review",
        "ready_for_procedure_contract_review": True,
        "ready_for_expert_review": not not_ready_reasons,
        "ready_for_simulation_replay_package_design": True,
        "ready_for_training_design_review": True,
        "not_ready_reasons": not_ready_reasons,
        "field_coverage": _field_coverage(parameter_set, contract),
        "human_required_gaps": sorted(human_required_gaps),
        "computed_fields": parameter_set["computed_fields"],
        "inferred_fields": parameter_set["inferred_fields"],
        "workcell_logged_gaps": sorted(workcell_logged_gaps),
        "wps_pqr_boundary": "not_formal_WPS_PQR",
    }
```

- [ ] **Step 5: Implement mapping matrix**

Add:

```python
def build_procedure_to_nv01_mapping_matrix(contract: dict[str, Any]) -> dict[str, Any]:
    return {
        "matrix_id": f"procedure-to-nv01-{contract['contract_version']}",
        "contract_version": contract["contract_version"],
        "field_count": contract["field_count"],
        "field_mappings": {
            field["field_id"]: {
                "display_name": field["display_name"],
                "requirement_level": field["requirement_level"],
                "acquisition_mode": field["acquisition_mode"],
                "a02_targets": _a02_targets_for_field(field),
                "nv01_targets": _nv01_targets_for_field(field),
                "blocks": field["blocks"],
                "evidence_boundary": field["evidence_boundary"],
            }
            for field in contract["fields"]
        },
    }
```

Ensure `nv01_targets` uses human-readable target strings expected by tests, including `Isaac Sim replay config`, `OpenUSD process_metadata`, `domain_randomization_recipe`, `training_readiness_report`, and `ExpertReviewRecord.required_real_context` where relevant.

- [ ] **Step 6: Run K01 tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_weld_procedure_contract.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit Task 2**

Run:

```bash
git add weld-experience-engine/weldcore/skill_asset/procedure_contract.py \
  weld-experience-engine/tests/test_weld_procedure_contract.py
git commit -m "feat: add weld procedure validation payloads"
```

---

### Task 3: NV01 Digital Twin Payload Builders

**Files:**
- Create: `weld-experience-engine/weldcore/skill_asset/nvidia_digital_twin.py`
- Create: `weld-experience-engine/tests/test_nvidia_digital_twin_report.py`

- [ ] **Step 1: Write failing builder tests for top-level NV01 payloads**

Create `weld-experience-engine/tests/test_nvidia_digital_twin_report.py`:

```python
from weldcore.skill_asset.demo_report import run_demo_evidence_pack
from weldcore.skill_asset.nvidia_digital_twin import build_nvidia_digital_twin_payloads
from weldcore.skill_asset.procedure_contract import build_weld_procedure_knowledge_contract


def test_nvidia_payloads_bind_procedure_contract_to_canonical_demo(tmp_path):
    source_dir = tmp_path / "source"
    demo = run_demo_evidence_pack(source_dir)
    contract = build_weld_procedure_knowledge_contract()

    payloads = build_nvidia_digital_twin_payloads(source_dir, demo, contract)

    package = payloads["weld_skill_digital_twin_package"]
    assert package["overall_status"] == "ready_for_simulation_replay_package_design"
    assert package["task_count"] == 2
    assert package["procedure_contract_ref"] == "weld_procedure_knowledge_contract.json"
    assert "not_ready_for_robot_execution" in package["readiness_boundary"]

    openusd = payloads["openusd_scene_manifest"]
    assert openusd["root_prim"] == "/World"
    assert "procedure_parameter_bindings" in openusd
    assert openusd["missing_usd_authoring_inputs"]

    isaac = payloads["isaac_sim_replay_config"]
    assert "blocked_by_missing_isaac_runtime" in isaac["not_ready_reasons"]
    assert "procedure_parameter_inputs" in isaac

    recipe = payloads["domain_randomization_recipe"]
    names = {item["name"] for item in recipe["randomization_items"]}
    assert "groove_gap_variation" in names
    assert "travel_speed_window" in names
    assert any(item["linked_procedure_fields"] for item in recipe["randomization_items"])

    training = payloads["training_readiness_report"]
    assert training["training_status"] == "not_ready_for_policy_training"
    assert training["procedure_contract_gates"]
    assert "blocked_by_missing_isaac_runtime" in training["blocked_by"]

    alignment = payloads["nvidia_stack_alignment_matrix"]
    assert "WeldProcedureKnowledgeContract" in alignment["a02_object_mappings"]
    assert "RobotBodyAsset" in alignment["a02_object_mappings"]
```

- [ ] **Step 2: Run builder tests and confirm they fail**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_nvidia_digital_twin_report.py::test_nvidia_payloads_bind_procedure_contract_to_canonical_demo -q
```

Expected: FAIL with missing `nvidia_digital_twin` module.

- [ ] **Step 3: Implement source demo loading helpers**

In `weldcore/skill_asset/nvidia_digital_twin.py`, implement:

```python
def load_demo_pack(source_demo_dir: str | Path) -> dict[str, Any]:
    summary_path = Path(source_demo_dir) / "demo_summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(summary_path)
    return json.loads(summary_path.read_text(encoding="utf-8"))


class MissingCanonicalArtifactError(RuntimeError):
    """Raised when demo_summary artifact refs point to missing files."""


def load_task_artifacts(source_demo_dir: str | Path, task: dict[str, Any]) -> dict[str, Any]:
    task_dir = Path(source_demo_dir) / task["task_id"]
    artifacts: dict[str, Any] = {}
    missing: list[str] = []
    for name in task["artifact_refs"]:
        path = task_dir / name
        if not path.exists():
            missing.append(f"{task['task_id']}/{name}")
            continue
        artifacts[name] = json.loads(path.read_text(encoding="utf-8"))
    if missing:
        raise MissingCanonicalArtifactError(
            "missing_canonical_artifacts:" + ",".join(sorted(missing))
        )
    return artifacts
```

This helper must not silently filter missing files. Existing `--source-demo-dir` inputs are user-provided evidence; if an artifact ref points to a missing file, fail clearly so the pack cannot become non-auditable. The only automatic generation path is when `source_demo_dir` is omitted or the directory does not exist.

- [ ] **Step 4: Implement `build_nvidia_digital_twin_payloads`**

Public signature: `build_nvidia_digital_twin_payloads(source_demo_dir: str | Path, demo_summary: dict[str, Any], procedure_contract: dict[str, Any]) -> dict[str, Any]`.

Return dictionary keys:

```python
{
    "weld_procedure_parameter_set": dict,
    "weld_procedure_validation_report": dict,
    "procedure_to_nv01_mapping_matrix": dict,
    "weld_skill_digital_twin_package": dict,
    "openusd_scene_manifest": dict,
    "isaac_sim_replay_config": dict,
    "domain_randomization_recipe": dict,
    "training_readiness_report": dict,
    "nvidia_stack_alignment_matrix": dict,
    "task_payloads": dict[str, dict[str, dict]],
}
```

Builder rules:

- Top-level `weld_procedure_parameter_set` can aggregate the first task or summarize all task refs, but every task must also have its own parameter set under `task_payloads`.
- All outputs must include refs back to canonical demo artifacts.
- `openusd_scene_manifest` must be a manifest plan, not a USD file.
- `isaac_sim_replay_config` must include `blocked_by_missing_isaac_runtime`.
- `training_readiness_report` must include both `ready_for_training_design_review` and `not_ready_for_policy_training` concepts without treating them as contradiction.

- [ ] **Step 5: Implement randomization recipe with K01-linked items**

Minimum recipe items:

```python
[
    {
        "name": "groove_gap_variation",
        "category": "joint_geometry",
        "linked_procedure_fields": ["root_gap_mm", "groove_angle_deg"],
        "requires_human_confirmation": True,
    },
    {
        "name": "travel_speed_window",
        "category": "process_parameter",
        "linked_procedure_fields": ["travel_speed_mm_per_min"],
        "requires_human_confirmation": True,
    },
    {
        "name": "arc_glare_smoke_spatter",
        "category": "sensor_degradation",
        "linked_procedure_fields": [],
        "requires_real_calibration": True,
    },
]
```

If field ids differ because parser fallback ids are used, fix `FIELD_RULE_OVERRIDES` in Task 1/2 so these semantic ids exist. Do not point randomization at unknown fields.

- [ ] **Step 6: Run builder tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_nvidia_digital_twin_report.py::test_nvidia_payloads_bind_procedure_contract_to_canonical_demo -q
```

Expected: PASS.

- [ ] **Step 7: Commit Task 3**

Run:

```bash
git add weld-experience-engine/weldcore/skill_asset/nvidia_digital_twin.py \
  weld-experience-engine/tests/test_nvidia_digital_twin_report.py
git commit -m "feat: build nvidia digital twin payloads"
```

---

### Task 4: NV01 Report CLI and Artifact Writer

**Files:**
- Create: `weld-experience-engine/weldcore/skill_asset/nvidia_digital_twin_report.py`
- Modify: `weld-experience-engine/tests/test_nvidia_digital_twin_report.py`
- Modify: `weld-experience-engine/weldcore/skill_asset/__init__.py`

- [ ] **Step 1: Add failing end-to-end report tests**

Append to `weld-experience-engine/tests/test_nvidia_digital_twin_report.py`:

```python
import json

from weldcore.skill_asset.nvidia_digital_twin_report import run_nvidia_digital_twin_report


EXPECTED_TOP_LEVEL_ARTIFACTS = {
    "nv01_summary.md",
    "nv01_summary.json",
    "weld_procedure_knowledge_contract.json",
    "weld_procedure_parameter_set.json",
    "weld_procedure_validation_report.json",
    "procedure_to_nv01_mapping_matrix.json",
    "weld_skill_digital_twin_package.json",
    "openusd_scene_manifest.json",
    "isaac_sim_replay_config.json",
    "domain_randomization_recipe.json",
    "training_readiness_report.json",
    "nvidia_stack_alignment_matrix.json",
}


def test_nvidia_report_writes_top_level_and_per_task_artifacts(tmp_path):
    outdir = tmp_path / "nv01"

    summary = run_nvidia_digital_twin_report(outdir=outdir)

    assert summary["report_id"] == "k01-nv01-a-procedure-constrained-manifest-evidence-pack"
    assert summary["task_count"] == 2
    assert summary["overall_status"] == "ready_for_simulation_replay_package_design"
    assert "ready_for_procedure_contract_review" in summary["readiness_states"]
    assert "not_ready_for_policy_training" in summary["readiness_states"]
    assert "not_formal_WPS_PQR" in summary["readiness_boundary"]
    assert EXPECTED_TOP_LEVEL_ARTIFACTS.issubset(set(summary["generated_artifacts"]))

    for filename in EXPECTED_TOP_LEVEL_ARTIFACTS:
        assert (outdir / filename).exists()

    for task in summary["tasks"]:
        task_dir = outdir / task["task_output_dir"]
        assert (task_dir / "skill_asset_ref.json").exists()
        assert (task_dir / "weld_procedure_parameter_set.json").exists()
        assert (task_dir / "weld_procedure_validation_report.json").exists()
        assert (task_dir / "openusd_task_manifest.json").exists()
        assert (task_dir / "isaac_replay_task_config.json").exists()
        assert (task_dir / "sensor_and_annotation_manifest.json").exists()
        assert (task_dir / "training_task_readiness.json").exists()

    restored = json.loads((outdir / "nv01_summary.json").read_text(encoding="utf-8"))
    assert restored == summary


def test_nvidia_report_main_prints_json(tmp_path, capsys):
    from weldcore.skill_asset import nvidia_digital_twin_report

    nvidia_digital_twin_report.main(["--outdir", str(tmp_path)])

    output = json.loads(capsys.readouterr().out)
    assert output["overall_status"] == "ready_for_simulation_replay_package_design"
```

- [ ] **Step 2: Run end-to-end tests and confirm they fail**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_nvidia_digital_twin_report.py -q
```

Expected: FAIL with missing report module/function.

- [ ] **Step 3: Implement report writer**

Create `weldcore/skill_asset/nvidia_digital_twin_report.py` with public functions:

- `run_nvidia_digital_twin_report(outdir: str | Path, source_demo_dir: str | Path | None = None, procedure_workbook_path: str | Path | None = None) -> dict[str, Any]`
- `main(argv: list[str] | None = None) -> dict[str, Any]`

Implementation outline:

```python
def run_nvidia_digital_twin_report(outdir, source_demo_dir=None, procedure_workbook_path=None):
    output_dir = Path(outdir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_dir = _ensure_source_demo_pack(output_dir, source_demo_dir)
    demo_summary = load_demo_pack(source_dir)
    contract = build_weld_procedure_knowledge_contract(procedure_workbook_path or DEFAULT_PROCEDURE_WORKBOOK_PATH)
    payloads = build_nvidia_digital_twin_payloads(source_dir, demo_summary, contract)

    _write_json(output_dir / "weld_procedure_knowledge_contract.json", contract)
    _write_json(output_dir / "weld_procedure_parameter_set.json", payloads["weld_procedure_parameter_set"])
    _write_json(output_dir / "weld_procedure_validation_report.json", payloads["weld_procedure_validation_report"])
    _write_json(output_dir / "procedure_to_nv01_mapping_matrix.json", payloads["procedure_to_nv01_mapping_matrix"])
    _write_json(output_dir / "weld_skill_digital_twin_package.json", payloads["weld_skill_digital_twin_package"])
    _write_json(output_dir / "openusd_scene_manifest.json", payloads["openusd_scene_manifest"])
    _write_json(output_dir / "isaac_sim_replay_config.json", payloads["isaac_sim_replay_config"])
    _write_json(output_dir / "domain_randomization_recipe.json", payloads["domain_randomization_recipe"])
    _write_json(output_dir / "training_readiness_report.json", payloads["training_readiness_report"])
    _write_json(output_dir / "nvidia_stack_alignment_matrix.json", payloads["nvidia_stack_alignment_matrix"])
    _write_task_payloads(output_dir, payloads["task_payloads"])
    summary = _build_summary(demo_summary, contract, payloads)
    _write_text(output_dir / "nv01_summary.md", _render_markdown(summary))
    _write_json(output_dir / "nv01_summary.json", summary)
    return summary
```

CLI arguments:

```text
--source-demo-dir optional
--outdir required
--procedure-workbook-path optional
```

If source demo dir is missing, call:

```python
run_demo_evidence_pack(output_dir / "_source_demo_evidence")
```

- [ ] **Step 4: Export module if needed**

If tests import `from weldcore.skill_asset import nvidia_digital_twin_report`, Python can import submodules without `__all__`, but add a lightweight export only if needed:

```python
from .nvidia_digital_twin_report import run_nvidia_digital_twin_report
```

Do not bloat `__init__.py` with every helper.

- [ ] **Step 5: Run end-to-end report tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_nvidia_digital_twin_report.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit Task 4**

Run:

```bash
git add weld-experience-engine/weldcore/skill_asset/nvidia_digital_twin_report.py \
  weld-experience-engine/weldcore/skill_asset/__init__.py \
  weld-experience-engine/tests/test_nvidia_digital_twin_report.py
git commit -m "feat: add nvidia digital twin report cli"
```

---

### Task 5: Artifact Semantics and Boundary Regression Tests

**Files:**
- Modify: `weld-experience-engine/tests/test_nvidia_digital_twin_report.py`
- Modify: `weld-experience-engine/tests/test_skill_asset_demo_report.py` only if current demo refs need stronger assertions
- Modify: implementation files from Tasks 1-4 as needed

- [ ] **Step 1: Add regression tests for boundaries and references**

Append to `test_nvidia_digital_twin_report.py`:

```python
import pytest

from weldcore.skill_asset.demo_report import run_demo_evidence_pack
from weldcore.skill_asset.nvidia_digital_twin import MissingCanonicalArtifactError


def test_nvidia_report_artifacts_keep_boundaries_and_refs(tmp_path):
    outdir = tmp_path / "nv01"
    summary = run_nvidia_digital_twin_report(outdir=outdir)

    package = json.loads((outdir / "weld_skill_digital_twin_package.json").read_text(encoding="utf-8"))
    assert package["source_demo_pack_ref"].endswith("demo_summary.json")
    assert package["procedure_contract_ref"] == "weld_procedure_knowledge_contract.json"
    assert "not_ready_for_robot_execution" in package["readiness_boundary"]
    assert "not_formal_WPS_PQR" in package["readiness_boundary"]

    validation = json.loads((outdir / "weld_procedure_validation_report.json").read_text(encoding="utf-8"))
    assert validation["ready_for_simulation_replay_package_design"] is True
    assert validation["ready_for_expert_review"] is False
    assert "blocked_by_missing_human_required_fields" in validation["not_ready_reasons"]

    isaac = json.loads((outdir / "isaac_sim_replay_config.json").read_text(encoding="utf-8"))
    assert "blocked_by_missing_isaac_runtime" in isaac["not_ready_reasons"]
    assert "ready_for_simulation_replay" not in summary["readiness_states"]

    md = (outdir / "nv01_summary.md").read_text(encoding="utf-8")
    assert "不是正式 WPS/PQR" in md
    assert "不是 ready_for_robot_execution" in md
    assert "Isaac Sim runtime" in md


def test_existing_source_demo_with_missing_canonical_artifact_fails(tmp_path):
    source_dir = tmp_path / "source"
    run_demo_evidence_pack(source_dir)
    summary = json.loads((source_dir / "demo_summary.json").read_text(encoding="utf-8"))
    first_task_id = summary["tasks"][0]["task_id"]
    (source_dir / first_task_id / "skill_asset_report.json").unlink()

    with pytest.raises(MissingCanonicalArtifactError, match="missing_canonical_artifacts"):
        run_nvidia_digital_twin_report(
            source_demo_dir=source_dir,
            outdir=tmp_path / "nv01",
        )
```

- [ ] **Step 2: Run the regression test and confirm failure if implementation is incomplete**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_nvidia_digital_twin_report.py::test_nvidia_report_artifacts_keep_boundaries_and_refs -q
```

Expected: FAIL until payloads and markdown summary include the specified boundaries and missing canonical artifacts fail clearly.

- [ ] **Step 3: Fix payloads and markdown rendering**

Required summary fields:

```python
summary = {
    "report_id": "k01-nv01-a-procedure-constrained-manifest-evidence-pack",
    "task_count": 2,
    "overall_status": "ready_for_simulation_replay_package_design",
    "readiness_states": [
        "ready_for_procedure_contract_review",
        "ready_for_simulation_replay_package_design",
        "ready_for_training_design_review",
        "not_ready_for_policy_training",
    ],
    "readiness_boundary": [
        "not_formal_WPS_PQR",
        "not_ready_for_robot_execution",
        "not_isaac_sim_runtime_validation",
        "not_policy_training_result",
    ],
    "generated_artifacts": _generated_artifacts(output_dir),
    "tasks": _task_summaries(payloads["task_payloads"]),
    "next_step_recommendation": "Proceed to NV01-B OpenUSD Authoring Spike after expert review of K01 gaps.",
}
```

`_task_summaries` must include `task_output_dir`. Use this helper so task ids that already start with `task-` do not become `task-task-*`:

```python
def _task_output_dir_name(task_id: str) -> str:
    return task_id if task_id.startswith("task-") else f"task-{task_id}"
```

Markdown must explain:

- Excel/K01 is a field contract, not a formal WPS/PQR.
- `ready_for_simulation_replay_package_design` is not Isaac Sim replay.
- `ready_for_training_design_review` is not policy training.
- Missing human/workcell fields are expected gaps, not hidden defaults.
- Existing source demo directories are treated as evidence inputs; missing referenced canonical artifacts fail with `missing_canonical_artifacts` instead of being silently skipped.

- [ ] **Step 4: Run all K01/NV01 tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_weld_procedure_contract.py tests/test_nvidia_digital_twin_report.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit Task 5**

Run:

```bash
git add weld-experience-engine/tests/test_nvidia_digital_twin_report.py \
  weld-experience-engine/tests/test_skill_asset_demo_report.py \
  weld-experience-engine/weldcore/skill_asset/procedure_contract.py \
  weld-experience-engine/weldcore/skill_asset/nvidia_digital_twin.py \
  weld-experience-engine/weldcore/skill_asset/nvidia_digital_twin_report.py
git commit -m "test: lock nvidia digital twin readiness boundaries"
```

If `test_skill_asset_demo_report.py` was not modified, omit it from `git add`.

---

### Task 6: Documentation Sync

**Files:**
- Modify: `README.md`
- Modify: `details.md`
- Modify: `weld-experience-engine/README.md`
- Modify: `README.html`
- Modify: `details.html`

- [ ] **Step 1: Update README current capability**

In `README.md`, after implementation:

- Keep project positioning unchanged.
- In "当前可运行能力", add the implemented `nvidia_digital_twin_report` command.
- In "下一阶段任务", move NV01-B / OpenUSD Authoring Spike to the top.
- Keep boundaries explicit:
  - not formal WPS/PQR
  - not Isaac Sim runtime
  - not policy training
  - not robot execution

Expected command block:

```bash
cd weld-experience-engine
uv run python -m weldcore.skill_asset.nvidia_digital_twin_report \
  --outdir artifacts/demo/nvidia-digital-twin-foundation
```

- [ ] **Step 2: Update details stage log**

In `details.md`, add a new 2026-06-23 entry:

```markdown
- 完成 K01 + NV01-A Procedure-Constrained Manifest Evidence Pack。
- 新增 `weldcore.skill_asset.procedure_contract`，从 `docs/焊接工艺数据库主要参数表.xlsx` 生成 47 字段、8 类、21/12/14 requirement summary 的 K01 字段合同。
- 新增 `weldcore.skill_asset.nvidia_digital_twin_report`，默认生成 procedure contract、parameter set、validation report、procedure-to-NV01 mapping、digital twin package、OpenUSD/Isaac-oriented manifest/report。
- 当前仍不接 Isaac Sim runtime、不写 USD stage、不训练 Isaac Lab 策略、不生成正式 WPS/PQR、不宣称真实机器人执行。
```

Also update "尚未完成" so K01 + NV01-A is no longer listed as unimplemented. Leave NV01-B/C and later items as future work.

- [ ] **Step 3: Update engine README**

In `weld-experience-engine/README.md`, add:

```bash
uv run python -m weldcore.skill_asset.nvidia_digital_twin_report \
  --outdir artifacts/demo/nvidia-digital-twin-foundation
```

State that this command is a contract/report generator and does not require Isaac Sim.

- [ ] **Step 4: Regenerate HTML reading copies**

Use the same lightweight conversion approach already used in this repo. If there is no committed script, use a temporary local conversion command, then inspect the resulting diff. Do not commit the temporary script.

- [ ] **Step 5: Run documentation grep checks**

Run:

```bash
rg -n "K01 \\+ NV01-A|nvidia_digital_twin_report|weld_procedure_knowledge_contract|不是正式 WPS/PQR|not_ready_for_policy_training" README.md details.md weld-experience-engine/README.md
rg -n "K01 焊接工艺知识合同尚未实现|NV01 数字孪生包合同尚未实现" details.md || true
```

Expected:

- First command finds the new capability and boundaries.
- Second command should not find outdated "尚未实现" claims for K01 + NV01-A.

- [ ] **Step 6: Commit Task 6**

Run:

```bash
git add README.md README.html details.md details.html weld-experience-engine/README.md
git commit -m "docs: document k01 nv01 evidence pack"
```

---

### Task 7: Full Verification and Cleanup

**Files:**
- No planned code changes unless verification finds a real issue.

- [ ] **Step 1: Run focused tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_weld_procedure_contract.py tests/test_nvidia_digital_twin_report.py -q
```

Expected: all focused tests PASS.

- [ ] **Step 2: Run existing related tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_skill_asset_demo_report.py tests/test_skill_asset_report.py -q
```

Expected: existing demo and asset report tests PASS.

- [ ] **Step 3: Run full test suite**

Run:

```bash
cd weld-experience-engine
uv run pytest -q
```

Expected: full suite PASS. Current baseline before this plan is `398 passed`; final count should increase after new tests.

- [ ] **Step 4: Run the new CLI manually**

Run:

```bash
cd weld-experience-engine
rm -rf artifacts/demo/nvidia-digital-twin-foundation
uv run python -m weldcore.skill_asset.nvidia_digital_twin_report \
  --outdir artifacts/demo/nvidia-digital-twin-foundation
```

Expected:

- Exit code 0.
- JSON printed to stdout.
- `artifacts/demo/nvidia-digital-twin-foundation/nv01_summary.json` exists.
- `weld_procedure_knowledge_contract.json` has `field_count=47`.
- `training_readiness_report.json` has `training_status=not_ready_for_policy_training`.

- [ ] **Step 5: Remove generated runtime artifacts unless intentionally committed**

Run:

```bash
rm -rf weld-experience-engine/artifacts/demo/nvidia-digital-twin-foundation
rm -f weld-experience-engine/uv.lock
git status --short
```

Expected: no generated artifacts or `uv.lock` remain unless the project deliberately decides to version them.

- [ ] **Step 6: Run diff checks**

Run:

```bash
git diff --check
git status --short
```

Expected: no whitespace errors; only intended source/docs/test files modified.

- [ ] **Step 7: Commit any verification fixes**

If verification required fixes, commit them:

```bash
git add weld-experience-engine/weldcore/skill_asset/procedure_contract.py \
  weld-experience-engine/weldcore/skill_asset/nvidia_digital_twin.py \
  weld-experience-engine/weldcore/skill_asset/nvidia_digital_twin_report.py \
  weld-experience-engine/tests/test_weld_procedure_contract.py \
  weld-experience-engine/tests/test_nvidia_digital_twin_report.py \
  README.md README.html details.md details.html weld-experience-engine/README.md
git commit -m "fix: complete k01 nv01 verification"
```

Skip this step if no files changed after Task 6.

---

## Implementation Notes

- Prefer focused functions returning plain dictionaries over large new class hierarchies. Existing report modules already use dict payloads and JSON artifacts.
- Do not modify existing `ManipulationSkillAsset` semantics in this phase. K01 constrains and references it; it does not replace it.
- Do not commit generated `artifacts/` outputs.
- Keep all human-required gaps visible. A missing human field is a report result, not an exception, unless the workbook itself is missing or malformed.
- Missing Isaac Sim is not an error in this phase. It must be recorded as `blocked_by_missing_isaac_runtime`.
- Excel workbook missing or malformed is an error because K01 is the source contract for NV01-A.
- Any value inferred from current simulation must carry evidence boundary such as `simulation_inferred_not_wps_validated`.
- Any system-computed field must carry boundary such as `computed_not_wps_validated`.
- Never write "ready_for_robot_execution", "ready_for_policy_training", or "formal WPS/PQR" as a result of this plan.

## Final Acceptance Checklist

- [ ] `weldcore.skill_asset.procedure_contract` reads the Excel sheet, fills merged categories, and generates a 47-field / 8-category contract.
- [ ] Contract fields include `requirement_level`, `acquisition_mode`, `a02_target_path`, `nv01_usage`, `blocks`, and `evidence_boundary`.
- [ ] Parameter set and validation report distinguish human-required gaps, conditional gaps, computed fields, inferred fields, and workcell-logged gaps.
- [ ] `procedure_to_nv01_mapping_matrix.json` maps every field into A02/NV01 target surfaces.
- [ ] `weldcore.skill_asset.nvidia_digital_twin_report` writes all expected top-level and per-task artifacts.
- [ ] OpenUSD/Isaac/Training artifacts are manifest/report contracts only, not runtime outputs.
- [ ] README/details/engine README and HTML reading copies are synchronized.
- [ ] Focused tests and full `uv run pytest -q` pass.
- [ ] Generated artifacts and `uv.lock` are not accidentally committed.
