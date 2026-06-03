# SyntheticSkillDataset v2 输入规范 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an executable input-spec layer that turns shipbuilding welding task taxonomy, industry-standard procedure fields, evidence bindings, and simulation input specs into gates and reports for the next `SyntheticSkillDataset v2` generation step.

**Architecture:** Extend the existing manifest-first data foundation instead of replacing it. Add focused knowledge models, JSON manifest loaders, validation gates, and one report command; stop before generating synthetic samples. Keep all real-quality, WPS/PQR, and molten-pool boundaries explicit.

**Tech Stack:** Python 3.10+, dataclasses, enum, json/csv/pathlib, pytest, existing `weldcore.knowledge` and `weldcore.report` conventions, Markdown/HTML docs.

---

## 0. Scope Boundary

Design spec:

- `docs/superpowers/specs/2026-06-02-synthetic-skilldataset-v2-input-spec-design.md`
- HTML reading copy: `docs/superpowers/specs/2026-06-02-synthetic-skilldataset-v2-input-spec-design.html`

This plan implements the **input-spec layer only**.

It does:

- Produce a pre-modeling research and field-inventory gate from industry materials, standards references, public datasets, and the project's simulation-first route.
- Create `TaskTaxonomyEntry`, `WeldProcedureField`, `EvidenceBinding`, `SimulationInputSpec`, and `SyntheticSkillDatasetV2PlanInput`.
- Create machine-readable manifests for task taxonomy, procedure fields, and first-batch simulation inputs.
- Load those manifests into executable Python objects.
- Enforce taxonomy, required-field, evidence-binding, assumption, real-validation, and forbidden-field gates.
- Generate a `synthetic_v2_input_report`.
- Update project docs to say this completes the input specification, not bulk synthetic dataset generation.

It does not:

- Generate `SkillDataset` samples.
- Implement simulator geometry or trajectories.
- Download public datasets.
- Implement WPS/PQR, real robot control, welding machine control, or real quality validation.
- Add molten-pool, weld-pool, or in-process closed-loop fields.

---

## 1. File Structure

### Data Foundation Manifests

- Create: `docs/data-foundation/research/synthetic_v2_input_research.md`
  - Human-readable research synthesis before model design.
- Create: `docs/data-foundation/research/synthetic_v2_field_gap_matrix.csv`
  - Field-by-field mapping from industry knowledge to planned input schema.
- Create: `docs/data-foundation/manifests/task_taxonomy.json`
  - Wide shipbuilding welding task taxonomy.
- Create: `docs/data-foundation/manifests/procedure_fields.json`
  - Industry-standard key procedure field definitions.
- Create: `docs/data-foundation/manifests/synthetic_v2_inputs.json`
  - First-batch simulation input specs and evidence bindings.

### Python Knowledge Layer

- Create: `weld-experience-engine/weldcore/knowledge/synthetic_input.py`
  - Data models and validation gates.
- Create: `weld-experience-engine/weldcore/knowledge/synthetic_manifest.py`
  - Manifest loader for the new input-spec layer.
- Modify: `weld-experience-engine/weldcore/knowledge/__init__.py`
  - Export new models and loader.

### Report

- Create: `weld-experience-engine/weldcore/report/synthetic_v2_input_report.py`
  - Generates JSON/CSV/Markdown evidence artifacts.

### Tests

- Create: `weld-experience-engine/tests/test_synthetic_input_models.py`
- Create: `weld-experience-engine/tests/test_synthetic_input_manifests.py`
- Create: `weld-experience-engine/tests/test_synthetic_v2_input_report.py`

### Documentation

- Modify: `README.md`
- Modify: `details.md`
- Modify: `weld-experience-engine/README.md`
- Create/update report copies under `docs/data-foundation/reports/`.

---

## 2. Success Criteria

Complete means all of these are true:

- The research gate is completed before model implementation:
  - `synthetic_v2_input_research.md` summarizes shipbuilding welding task classification, weld/joint/position/groove/layer-pass concepts, process variables, quality/defect vocabulary, public datasets, and simulation-first constraints.
  - `synthetic_v2_field_gap_matrix.csv` maps each proposed schema field to source category, source ids, simulation role, evidence role, and validation status.
  - The research output explicitly distinguishes industry/standard knowledge, public dataset schema, project-internal assumptions, simulation assumptions, and fields requiring later real validation.
- `task_taxonomy.json` contains at least 7 task families:
  - 3 with `readiness = "ready_for_synthetic_v2_plan"`.
  - at least 1 with `readiness = "needs_more_sources"`.
  - at least 3 with `readiness = "defer"`.
- `procedure_fields.json` covers at least these field groups:
  - task/joint fields.
  - geometry/material fields.
  - process parameter fields.
  - motion/posture fields.
  - quality/inspection fields.
- Each `SimulationInputSpec` references an existing taxonomy entry with `ready_for_synthetic_v2_plan`.
- First-batch inputs exist for:
  - `stiffened-panel-fillet`
  - `panel-butt`
  - `micro-panel-web-bulkhead`
- Every required key field has at least one `EvidenceBinding`.
- Metadata/index fields such as `input_id`, `taxonomy_ref`, and `evidence_bindings` do not require self-binding.
- Every `simulation_assumption` appears in the report.
- Every quality-related input either uses public label vocabulary, simulation score placeholder, or `requires_real_validation_later`.
- Gate rejects any current-stage JSON/CSV field containing `熔池`, `molten_pool`, `molten pool`, `weld_pool`, or `weld pool`.
- Report outputs include:
  - `synthetic_v2_input_report_out/task_taxonomy.json`
  - `synthetic_v2_input_report_out/procedure_fields.json`
  - `synthetic_v2_input_report_out/simulation_inputs.json`
  - `synthetic_v2_input_report_out/evidence_bindings.csv`
  - `synthetic_v2_input_report_out/evidence.md`
- Committed report copies are refreshed under:
  - `docs/data-foundation/reports/synthetic_v2_input_evidence.md`
- README and `details.md` say this completes the input-spec layer, not `SyntheticSkillDataset v2` bulk generation.
- Commands pass:
  - `cd weld-experience-engine && uv run pytest -q`
  - `cd weld-experience-engine && uv run python -m weldcore.report.synthetic_v2_input_report`
  - Existing report commands still pass:
    - `uv run python -m weldcore.report.generate`
    - `uv run python -m weldcore.report.mvp_report`
    - `uv run python -m weldcore.report.scenario_report`
    - `uv run python -m weldcore.report.data_foundation_report`

---

## Task 0: Baseline Safety Check

**Files:**
- Read only.

- [ ] **Step 1: Confirm branch and worktree**

Run:

```bash
git status --short --branch
```

Expected:

```text
## codex/synthetic-v2-input-spec
```

If unrelated user changes exist, do not revert them. Work around them or stop only if they block the task.

- [ ] **Step 2: Confirm uv is available**

Run:

```bash
command -v uv || true
```

Expected: a path such as `/Users/lloyd/.local/bin/uv`.

If `uv` is unavailable, use fallback commands with `python -m pytest` and `python -m weldcore...`, and state that fallback clearly.

- [ ] **Step 3: Run baseline tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q
```

Expected: all tests pass.

- [ ] **Step 4: Commit nothing**

No commit for this task.

---

## Task 1: Research and Field Inventory Gate

**Files:**
- Create: `docs/data-foundation/research/synthetic_v2_input_research.md`
- Create: `docs/data-foundation/research/synthetic_v2_field_gap_matrix.csv`
- Read: `docs/data-foundation/manifests/sources.json`
- Read: `docs/data-foundation/manifests/datasets.json`
- Read: `docs/data-foundation/manifests/field_coverage.csv`
- Read: `docs/data-foundation/manifests/task_evidence_map.json`
- Read: `docs/data-foundation/source-cards/*.md`
- Read: `docs/project/船舶焊接工艺大脑平台整体规划方案.html`

- [ ] **Step 1: Review existing data foundation materials**

Run:

```bash
rg -n "joint_type|weld_position|groove_geometry|layer_pass|current|voltage|travel_speed|quality_label|defect_label|inspection_reference|WPS|PQR|标准|船级|坡口|层道|焊缝|接头" \
  docs/data-foundation docs/project docs/superpowers/specs
```

Expected: locate the existing project and data-foundation evidence for the fields that will become `TaskTaxonomyEntry`, `WeldProcedureField`, `EvidenceBinding`, and `SimulationInputSpec`.

- [ ] **Step 2: Inspect machine-readable manifests**

Run:

```bash
python3 - <<'PY'
import json
from pathlib import Path

root = Path("docs/data-foundation/manifests")
for name in ["sources.json", "datasets.json", "task_evidence_map.json"]:
    data = json.loads((root / name).read_text(encoding="utf-8"))
    print(name, len(data))
print("field_coverage.csv lines", sum(1 for _ in (root / "field_coverage.csv").open(encoding="utf-8")))
PY
```

Expected:

- `sources.json` has at least 20 sources.
- `datasets.json` has at least 6 datasets.
- `task_evidence_map.json` has at least 3 ready task families.
- `field_coverage.csv` has existing coverage rows.

- [ ] **Step 3: Identify research categories**

Create these category headings in `synthetic_v2_input_research.md`:

```markdown
# SyntheticSkillDataset v2 输入规范前置调研

## 结论

## 1. 船舶焊接任务分类

## 2. 焊缝、接头、位置、坡口和层道知识

## 3. 工艺参数和 WPS/PQR 相关字段

## 4. 质量、缺陷和检查词汇

## 5. 公开数据集与 schema 参考

## 6. 仿真优先路线对字段的约束

## 7. 进入数据结构设计的字段原则

## 8. 暂不进入第一版的内容
```

Keep the report focused on fields and generation input. Do not write an encyclopedia-style literature review.

- [ ] **Step 4: Fill research synthesis**

For each section, write concise findings:

- Which existing source ids support the topic.
- Which fields should enter the first input-spec layer.
- Which values are public constraints versus simulation assumptions.
- Which fields require later real validation.
- Which fields are excluded from this stage.

Required boundary statements:

- This research is not WPS/PQR.
- This research does not prove real welding quality.
- Public datasets provide schema, vocabulary, or benchmark references only.
- Molten-pool, weld-pool, and in-process closed-loop fields remain out of scope.

- [ ] **Step 5: Create field gap matrix**

Create `docs/data-foundation/research/synthetic_v2_field_gap_matrix.csv` with this header:

```csv
field_path,field_group,industry_meaning,source_category,source_ids,simulation_role,evidence_role,value_status,first_batch_required,notes
```

Include at least these rows:

- `task_taxonomy.manufacturing_stage`
- `task_taxonomy.weld_object`
- `task_taxonomy.joint_type`
- `task_taxonomy.weld_position`
- `task_taxonomy.groove_geometry`
- `task_taxonomy.layer_pass`
- `procedure_fields.welding_process`
- `procedure_fields.plate_thickness_mm`
- `procedure_fields.current`
- `procedure_fields.voltage`
- `procedure_fields.travel_speed`
- `procedure_fields.trajectory`
- `procedure_fields.torch_angle`
- `procedure_fields.quality_label`
- `procedure_fields.defect_label`
- `procedure_fields.inspection_reference`
- `geometry_spec.groove_geometry`
- `motion_spec.motion_template`
- `process_spec.current`
- `quality_spec.quality_label`

`source_ids` may be semicolon-separated. Use only source ids already present in `docs/data-foundation/manifests/sources.json`.

- [ ] **Step 6: Verify source ids in gap matrix**

Run:

```bash
python3 - <<'PY'
import csv
import json
from pathlib import Path

root = Path("docs/data-foundation")
sources = {
    item["source_id"]
    for item in json.loads((root / "manifests" / "sources.json").read_text(encoding="utf-8"))
}
bad = []
has_public_dataset_schema = False
with (root / "research" / "synthetic_v2_field_gap_matrix.csv").open(encoding="utf-8", newline="") as handle:
    for row in csv.DictReader(handle):
        if row["source_category"] == "public_dataset_schema":
            has_public_dataset_schema = True
        for source_id in [item.strip() for item in row["source_ids"].split(";") if item.strip()]:
            if source_id not in sources:
                bad.append((row["field_path"], source_id))
if bad:
    raise SystemExit(f"unknown source ids: {bad}")
if not has_public_dataset_schema:
    raise SystemExit("field gap matrix must include at least one public_dataset_schema row")
print("all field gap source ids are known")
PY
```

Expected:

```text
all field gap source ids are known
```

- [ ] **Step 7: Verify research boundary text**

Run:

```bash
rg -n "不是 WPS/PQR|不证明真实焊接质量|schema|vocabulary|benchmark|不纳入|out of scope" \
  docs/data-foundation/research/synthetic_v2_input_research.md
```

Expected: matches for the required boundary statements.

- [ ] **Step 8: Commit**

Run:

```bash
git add docs/data-foundation/research/synthetic_v2_input_research.md \
  docs/data-foundation/research/synthetic_v2_field_gap_matrix.csv
git commit -m "docs: add synthetic v2 input research gate"
```

---

## Task 2: Synthetic Input Data Models

**Files:**
- Create: `weld-experience-engine/weldcore/knowledge/synthetic_input.py`
- Modify: `weld-experience-engine/weldcore/knowledge/__init__.py`
- Test: `weld-experience-engine/tests/test_synthetic_input_models.py`
- Read first: `docs/data-foundation/research/synthetic_v2_input_research.md`
- Read first: `docs/data-foundation/research/synthetic_v2_field_gap_matrix.csv`

- [ ] **Step 1: Write failing model tests**

Do not start this task until Task 1 is committed. Use the research report and field gap matrix as the field source of truth for model names, required fields, evidence roles, and validation boundaries.

Create `weld-experience-engine/tests/test_synthetic_input_models.py`:

```python
import pytest

from weldcore.knowledge.synthetic_input import (
    EvidenceBinding,
    SyntheticEvidenceRole,
    SyntheticReadiness,
    SimulationInputSpec,
    SyntheticSkillDatasetV2PlanInput,
    SyntheticInputFoundation,
    TaskTaxonomyEntry,
    SyntheticValueStatus,
    WeldProcedureField,
)


def test_task_taxonomy_entry_serializes_readiness():
    entry = TaskTaxonomyEntry(
        family_id="stiffened-panel-fillet",
        manufacturing_stage="panel_line",
        weld_object="stiffener-to-panel",
        joint_type="fillet",
        weld_position="horizontal",
        groove_geometry="none",
        layer_pass="single_pass",
        access_context="open_panel",
        motion_structure="single_seam",
        readiness=SyntheticReadiness.READY_FOR_SYNTHETIC_V2_PLAN,
        modeling_difficulty="easy",
        notes="First-batch candidate.",
    )

    data = entry.to_dict()

    assert data["readiness"] == "ready_for_synthetic_v2_plan"
    assert data["joint_type"] == "fillet"


def test_plan_input_records_first_batch_and_deferred_families():
    plan_input = SyntheticSkillDatasetV2PlanInput(
        plan_id="synthetic-v2-plan-input-001",
        first_batch_input_ids=[
            "input-stiffened-panel-fillet-001",
            "input-panel-butt-001",
            "input-micro-panel-web-bulkhead-001",
        ],
        deferred_family_ids=[
            "double-bottom-inner-fillet",
            "vertical-overhead-hull-weld",
        ],
        notes=[
            "Input-spec layer only; bulk sample generation is a later plan."
        ],
    )

    data = plan_input.to_dict()

    assert data["first_batch_input_ids"][0] == "input-stiffened-panel-fillet-001"
    assert "double-bottom-inner-fillet" in data["deferred_family_ids"]


def test_simulation_input_requires_key_field_bindings():
    taxonomy = TaskTaxonomyEntry(
        family_id="panel-butt",
        manufacturing_stage="panel_line",
        weld_object="panel butt seam",
        joint_type="butt",
        weld_position="flat",
        groove_geometry="v_groove_placeholder",
        layer_pass="single_pass",
        access_context="open_panel",
        motion_structure="single_seam",
        readiness=SyntheticReadiness.READY_FOR_SYNTHETIC_V2_PLAN,
        modeling_difficulty="easy",
        notes="Ready.",
    )
    fields = [
        WeldProcedureField("joint_type", "task_joint", required=True),
        WeldProcedureField("weld_position", "task_joint", required=True),
        WeldProcedureField("current", "process", required=True),
    ]
    input_spec = SimulationInputSpec(
        input_id="input-panel-butt-001",
        taxonomy_ref="panel-butt",
        procedure_fields={"joint_type": "butt", "weld_position": "flat", "current": "unknown"},
        geometry_spec={"groove_geometry": "v_groove_placeholder"},
        motion_spec={"motion_template": "straight"},
        process_spec={"current": "unknown"},
        quality_spec={"quality_label": "requires_real_validation_later"},
        variant_policy={"length_variation": [100.0, 150.0]},
        evidence_bindings=[
            EvidenceBinding(
                field_path="procedure_fields.joint_type",
                source_id="vendor-kobelco-shipbuilding-welding",
                evidence_role=SyntheticEvidenceRole.PUBLIC_PROCESS_REFERENCE,
                value_status=SyntheticValueStatus.CONSTRAINED,
                notes="Task field constraint.",
            ),
            EvidenceBinding(
                field_path="procedure_fields.weld_position",
                source_id="vendor-kobelco-shipbuilding-welding",
                evidence_role=SyntheticEvidenceRole.PUBLIC_PROCESS_REFERENCE,
                value_status=SyntheticValueStatus.CONSTRAINED,
                notes="Position field constraint.",
            ),
            EvidenceBinding(
                field_path="procedure_fields.current",
                source_id="standard-aws-swps-public-page",
                evidence_role=SyntheticEvidenceRole.PUBLIC_PROCESS_REFERENCE,
                value_status=SyntheticValueStatus.REQUIRES_REAL_VALIDATION_LATER,
                notes="Do not treat as project WPS.",
            ),
            EvidenceBinding(
                field_path="geometry_spec.groove_geometry",
                source_id="project-260522-shipbuilding-welding-brain-plan",
                evidence_role=SyntheticEvidenceRole.PROJECT_INTERNAL,
                value_status=SyntheticValueStatus.ASSUMED,
                notes="Geometry placeholder for synthetic input.",
            ),
            EvidenceBinding(
                field_path="motion_spec.motion_template",
                source_id="case-siemens-hd-hyundai-mipo-autonomous-welding",
                evidence_role=SyntheticEvidenceRole.SHIPBUILDING_CASE,
                value_status=SyntheticValueStatus.CONSTRAINED,
                notes="Motion structure reference only.",
            ),
            EvidenceBinding(
                field_path="process_spec.current",
                source_id="standard-aws-swps-public-page",
                evidence_role=SyntheticEvidenceRole.PUBLIC_PROCESS_REFERENCE,
                value_status=SyntheticValueStatus.REQUIRES_REAL_VALIDATION_LATER,
                notes="Process value requires later WPS validation.",
            ),
            EvidenceBinding(
                field_path="quality_spec.quality_label",
                source_id="guide-twi-weld-defects",
                evidence_role=SyntheticEvidenceRole.PUBLIC_PROCESS_REFERENCE,
                value_status=SyntheticValueStatus.REQUIRES_REAL_VALIDATION_LATER,
                notes="Quality label vocabulary only.",
            ),
        ],
        generation_boundary=[
            "Synthetic input only; not WPS/PQR or real quality validation."
        ],
    )
    foundation = SyntheticInputFoundation(
        task_taxonomy=[taxonomy],
        procedure_fields=fields,
        simulation_inputs=[input_spec],
        valid_source_ids={
            "vendor-kobelco-shipbuilding-welding",
            "standard-aws-swps-public-page",
            "project-260522-shipbuilding-welding-brain-plan",
            "case-siemens-hd-hyundai-mipo-autonomous-welding",
            "guide-twi-weld-defects",
        },
    )

    gate = foundation.validate()

    assert gate.passed
    assert gate.issues == []


def test_gate_rejects_deferred_task_input():
    taxonomy = TaskTaxonomyEntry(
        family_id="curved-spatial-complex-weld",
        manufacturing_stage="curved_hull",
        weld_object="curved seam",
        joint_type="complex",
        weld_position="multi_position",
        groove_geometry="complex",
        layer_pass="unknown",
        access_context="curved_surface",
        motion_structure="curved_seam",
        readiness=SyntheticReadiness.DEFER,
        modeling_difficulty="hard",
        notes="Deferred.",
    )
    input_spec = SimulationInputSpec(
        input_id="bad-input",
        taxonomy_ref="curved-spatial-complex-weld",
        procedure_fields={},
        geometry_spec={},
        motion_spec={},
        process_spec={},
        quality_spec={},
        variant_policy={},
        evidence_bindings=[],
        generation_boundary=[],
    )
    foundation = SyntheticInputFoundation(
        task_taxonomy=[taxonomy],
        procedure_fields=[],
        simulation_inputs=[input_spec],
    )

    gate = foundation.validate()

    assert not gate.passed
    assert any("not ready_for_synthetic_v2_plan" in issue for issue in gate.issues)


def test_gate_rejects_current_stage_pool_route_fields():
    taxonomy = TaskTaxonomyEntry(
        family_id="stiffened-panel-fillet",
        manufacturing_stage="panel_line",
        weld_object="stiffener-to-panel",
        joint_type="fillet",
        weld_position="horizontal",
        groove_geometry="none",
        layer_pass="single_pass",
        access_context="open_panel",
        motion_structure="single_seam",
        readiness=SyntheticReadiness.READY_FOR_SYNTHETIC_V2_PLAN,
        modeling_difficulty="easy",
        notes="Ready.",
    )
    input_spec = SimulationInputSpec(
        input_id="bad-pool-input",
        taxonomy_ref="stiffened-panel-fillet",
        procedure_fields={"joint_type": "fillet"},
        geometry_spec={"molten_pool_image": "not_allowed"},
        motion_spec={},
        process_spec={},
        quality_spec={},
        variant_policy={},
        evidence_bindings=[],
        generation_boundary=[],
    )
    foundation = SyntheticInputFoundation(
        task_taxonomy=[taxonomy],
        procedure_fields=[],
        simulation_inputs=[input_spec],
    )

    gate = foundation.validate()

    assert not gate.passed
    assert any("forbidden pool-route" in issue for issue in gate.issues)


def test_gate_rejects_missing_business_field_binding():
    taxonomy = TaskTaxonomyEntry(
        family_id="panel-butt",
        manufacturing_stage="panel_line",
        weld_object="panel butt seam",
        joint_type="butt",
        weld_position="flat",
        groove_geometry="v_groove_placeholder",
        layer_pass="single_pass",
        access_context="open_panel",
        motion_structure="single_seam",
        readiness=SyntheticReadiness.READY_FOR_SYNTHETIC_V2_PLAN,
        modeling_difficulty="easy",
        notes="Ready.",
    )
    input_spec = SimulationInputSpec(
        input_id="missing-business-binding",
        taxonomy_ref="panel-butt",
        procedure_fields={"joint_type": "butt"},
        geometry_spec={"groove_geometry": "v_groove_placeholder"},
        motion_spec={},
        process_spec={},
        quality_spec={},
        variant_policy={},
        evidence_bindings=[
            EvidenceBinding(
                field_path="procedure_fields.joint_type",
                source_id="vendor-kobelco-shipbuilding-welding",
                evidence_role=SyntheticEvidenceRole.PUBLIC_PROCESS_REFERENCE,
                value_status=SyntheticValueStatus.CONSTRAINED,
                notes="Task evidence.",
            )
        ],
        generation_boundary=["Input-spec only."],
    )
    foundation = SyntheticInputFoundation(
        task_taxonomy=[taxonomy],
        procedure_fields=[WeldProcedureField("joint_type", "task_joint", required=True)],
        simulation_inputs=[input_spec],
        valid_source_ids={"vendor-kobelco-shipbuilding-welding"},
    )

    gate = foundation.validate()

    assert not gate.passed
    assert any("missing evidence binding for geometry_spec" in issue for issue in gate.issues)


def test_gate_rejects_unknown_evidence_source_id():
    taxonomy = TaskTaxonomyEntry(
        family_id="panel-butt",
        manufacturing_stage="panel_line",
        weld_object="panel butt seam",
        joint_type="butt",
        weld_position="flat",
        groove_geometry="v_groove_placeholder",
        layer_pass="single_pass",
        access_context="open_panel",
        motion_structure="single_seam",
        readiness=SyntheticReadiness.READY_FOR_SYNTHETIC_V2_PLAN,
        modeling_difficulty="easy",
        notes="Ready.",
    )
    input_spec = SimulationInputSpec(
        input_id="bad-source",
        taxonomy_ref="panel-butt",
        procedure_fields={"joint_type": "butt"},
        geometry_spec={},
        motion_spec={},
        process_spec={},
        quality_spec={},
        variant_policy={},
        evidence_bindings=[
            EvidenceBinding(
                field_path="procedure_fields.joint_type",
                source_id="not-a-real-source",
                evidence_role=SyntheticEvidenceRole.PUBLIC_PROCESS_REFERENCE,
                value_status=SyntheticValueStatus.CONSTRAINED,
                notes="Bad source.",
            )
        ],
        generation_boundary=["Input-spec only."],
    )
    foundation = SyntheticInputFoundation(
        task_taxonomy=[taxonomy],
        procedure_fields=[WeldProcedureField("joint_type", "task_joint", required=True)],
        simulation_inputs=[input_spec],
        valid_source_ids={"vendor-kobelco-shipbuilding-welding"},
    )

    gate = foundation.validate()

    assert not gate.passed
    assert any("unknown evidence source_id" in issue for issue in gate.issues)


def test_gate_rejects_quality_field_without_boundary():
    taxonomy = TaskTaxonomyEntry(
        family_id="panel-butt",
        manufacturing_stage="panel_line",
        weld_object="panel butt seam",
        joint_type="butt",
        weld_position="flat",
        groove_geometry="v_groove_placeholder",
        layer_pass="single_pass",
        access_context="open_panel",
        motion_structure="single_seam",
        readiness=SyntheticReadiness.READY_FOR_SYNTHETIC_V2_PLAN,
        modeling_difficulty="easy",
        notes="Ready.",
    )
    input_spec = SimulationInputSpec(
        input_id="bad-quality",
        taxonomy_ref="panel-butt",
        procedure_fields={"joint_type": "butt"},
        geometry_spec={},
        motion_spec={},
        process_spec={},
        quality_spec={"defect_label": "porosity"},
        variant_policy={},
        evidence_bindings=[
            EvidenceBinding(
                field_path="procedure_fields.joint_type",
                source_id="vendor-kobelco-shipbuilding-welding",
                evidence_role=SyntheticEvidenceRole.PUBLIC_PROCESS_REFERENCE,
                value_status=SyntheticValueStatus.CONSTRAINED,
                notes="Task evidence.",
            )
        ],
        generation_boundary=["Input-spec only."],
    )
    foundation = SyntheticInputFoundation(
        task_taxonomy=[taxonomy],
        procedure_fields=[WeldProcedureField("joint_type", "task_joint", required=True)],
        simulation_inputs=[input_spec],
        valid_source_ids={"vendor-kobelco-shipbuilding-welding"},
    )

    gate = foundation.validate()

    assert not gate.passed
    assert any("quality fields require" in issue for issue in gate.issues)


def test_gate_rejects_partially_unbound_business_fields():
    taxonomy = TaskTaxonomyEntry(
        family_id="panel-butt",
        manufacturing_stage="panel_line",
        weld_object="panel butt seam",
        joint_type="butt",
        weld_position="flat",
        groove_geometry="v_groove_placeholder",
        layer_pass="single_pass",
        access_context="open_panel",
        motion_structure="single_seam",
        readiness=SyntheticReadiness.READY_FOR_SYNTHETIC_V2_PLAN,
        modeling_difficulty="easy",
        notes="Ready.",
    )
    input_spec = SimulationInputSpec(
        input_id="partial-business-binding",
        taxonomy_ref="panel-butt",
        procedure_fields={"joint_type": "butt"},
        geometry_spec={
            "groove_geometry": "v_groove_placeholder",
            "plate_thickness_mm": "assumed",
        },
        motion_spec={},
        process_spec={},
        quality_spec={},
        variant_policy={},
        evidence_bindings=[
            EvidenceBinding(
                field_path="procedure_fields.joint_type",
                source_id="vendor-kobelco-shipbuilding-welding",
                evidence_role=SyntheticEvidenceRole.PUBLIC_PROCESS_REFERENCE,
                value_status=SyntheticValueStatus.CONSTRAINED,
                notes="Task evidence.",
            ),
            EvidenceBinding(
                field_path="geometry_spec.groove_geometry",
                source_id="project-260522-shipbuilding-welding-brain-plan",
                evidence_role=SyntheticEvidenceRole.PROJECT_INTERNAL,
                value_status=SyntheticValueStatus.ASSUMED,
                notes="Geometry placeholder.",
            ),
        ],
        generation_boundary=["Input-spec only."],
    )
    foundation = SyntheticInputFoundation(
        task_taxonomy=[taxonomy],
        procedure_fields=[WeldProcedureField("joint_type", "task_joint", required=True)],
        simulation_inputs=[input_spec],
        valid_source_ids={
            "vendor-kobelco-shipbuilding-welding",
            "project-260522-shipbuilding-welding-brain-plan",
        },
    )

    gate = foundation.validate()

    assert not gate.passed
    assert any("geometry_spec.plate_thickness_mm" in issue for issue in gate.issues)


def test_gate_rejects_mixed_quality_field_without_own_boundary():
    taxonomy = TaskTaxonomyEntry(
        family_id="panel-butt",
        manufacturing_stage="panel_line",
        weld_object="panel butt seam",
        joint_type="butt",
        weld_position="flat",
        groove_geometry="v_groove_placeholder",
        layer_pass="single_pass",
        access_context="open_panel",
        motion_structure="single_seam",
        readiness=SyntheticReadiness.READY_FOR_SYNTHETIC_V2_PLAN,
        modeling_difficulty="easy",
        notes="Ready.",
    )
    input_spec = SimulationInputSpec(
        input_id="mixed-quality",
        taxonomy_ref="panel-butt",
        procedure_fields={"joint_type": "butt"},
        geometry_spec={},
        motion_spec={},
        process_spec={},
        quality_spec={
            "quality_label": "requires_real_validation_later",
            "defect_label": "porosity",
        },
        variant_policy={},
        evidence_bindings=[
            EvidenceBinding(
                field_path="procedure_fields.joint_type",
                source_id="vendor-kobelco-shipbuilding-welding",
                evidence_role=SyntheticEvidenceRole.PUBLIC_PROCESS_REFERENCE,
                value_status=SyntheticValueStatus.CONSTRAINED,
                notes="Task evidence.",
            ),
            EvidenceBinding(
                field_path="quality_spec.quality_label",
                source_id="guide-twi-weld-defects",
                evidence_role=SyntheticEvidenceRole.PUBLIC_PROCESS_REFERENCE,
                value_status=SyntheticValueStatus.REQUIRES_REAL_VALIDATION_LATER,
                notes="Quality boundary.",
            ),
        ],
        generation_boundary=["Input-spec only."],
    )
    foundation = SyntheticInputFoundation(
        task_taxonomy=[taxonomy],
        procedure_fields=[WeldProcedureField("joint_type", "task_joint", required=True)],
        simulation_inputs=[input_spec],
        valid_source_ids={
            "vendor-kobelco-shipbuilding-welding",
            "guide-twi-weld-defects",
        },
    )

    gate = foundation.validate()

    assert not gate.passed
    assert any("quality_spec.defect_label" in issue for issue in gate.issues)
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_synthetic_input_models.py -v
```

Expected: FAIL with `ModuleNotFoundError` or import errors for `weldcore.knowledge.synthetic_input`.

- [ ] **Step 3: Implement minimal models**

Create `weld-experience-engine/weldcore/knowledge/synthetic_input.py`:

```python
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


FORBIDDEN_POOL_TERMS = ("molten_pool", "molten pool", "weld_pool", "weld pool", "熔池")
METADATA_FIELD_PATHS = {"input_id", "taxonomy_ref", "evidence_bindings"}
BUSINESS_SPEC_KEYS = ("geometry_spec", "motion_spec", "process_spec", "quality_spec")
QUALITY_KEYS = ("quality_label", "defect_label", "inspection_reference")
QUALITY_BOUNDARY_VALUES = (
    "public_label_vocabulary",
    "simulation_score_placeholder",
    "requires_real_validation_later",
)


class SyntheticReadiness(str, Enum):
    READY_FOR_SYNTHETIC_V2_PLAN = "ready_for_synthetic_v2_plan"
    NEEDS_MORE_SOURCES = "needs_more_sources"
    DEFER = "defer"


class SyntheticEvidenceRole(str, Enum):
    SHIPBUILDING_CASE = "shipbuilding_case"
    PUBLIC_PROCESS_REFERENCE = "public_process_reference"
    PUBLIC_DATASET_SCHEMA = "public_dataset_schema"
    PROJECT_INTERNAL = "project_internal"
    SIMULATION_ASSUMPTION = "simulation_assumption"
    SIMULATION_OUTPUT = "simulation_output"
    REQUIRES_REAL_VALIDATION_LATER = "requires_real_validation_later"


class SyntheticValueStatus(str, Enum):
    CONSTRAINED = "constrained"
    ASSUMED = "assumed"
    GENERATED = "generated"
    UNKNOWN = "unknown"
    REQUIRES_REAL_VALIDATION_LATER = "requires_real_validation_later"


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


def _has_forbidden_pool_term(value: Any) -> bool:
    text = str(value).lower()
    return any(term in text for term in FORBIDDEN_POOL_TERMS)


def _has_quality_boundary(value: Any) -> bool:
    text = str(value).lower()
    return any(marker in text for marker in QUALITY_BOUNDARY_VALUES)


def _field_paths(prefix: str, value: dict[str, Any]) -> set[str]:
    return {f"{prefix}.{key}" for key in value}


@dataclass(frozen=True)
class TaskTaxonomyEntry:
    family_id: str
    manufacturing_stage: str
    weld_object: str
    joint_type: str
    weld_position: str
    groove_geometry: str
    layer_pass: str
    access_context: str
    motion_structure: str
    readiness: SyntheticReadiness
    modeling_difficulty: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {key: _jsonable(value) for key, value in asdict(self).items()}


@dataclass(frozen=True)
class WeldProcedureField:
    field_name: str
    field_group: str
    required: bool
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceBinding:
    field_path: str
    source_id: str
    evidence_role: SyntheticEvidenceRole
    value_status: SyntheticValueStatus
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {key: _jsonable(value) for key, value in asdict(self).items()}


@dataclass(frozen=True)
class SimulationInputSpec:
    input_id: str
    taxonomy_ref: str
    procedure_fields: dict[str, Any]
    geometry_spec: dict[str, Any]
    motion_spec: dict[str, Any]
    process_spec: dict[str, Any]
    quality_spec: dict[str, Any]
    variant_policy: dict[str, Any]
    evidence_bindings: list[EvidenceBinding]
    generation_boundary: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {key: _jsonable(value) for key, value in asdict(self).items()}

    def bound_field_paths(self) -> set[str]:
        return {binding.field_path for binding in self.evidence_bindings}


@dataclass(frozen=True)
class SyntheticSkillDatasetV2PlanInput:
    plan_id: str
    first_batch_input_ids: list[str]
    deferred_family_ids: list[str]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SyntheticInputGateResult:
    passed: bool
    issues: list[str]


@dataclass
class SyntheticInputFoundation:
    task_taxonomy: list[TaskTaxonomyEntry]
    procedure_fields: list[WeldProcedureField]
    simulation_inputs: list[SimulationInputSpec]
    valid_source_ids: set[str] | None = None

    def validate(self) -> SyntheticInputGateResult:
        issues: list[str] = []
        taxonomy_by_id = {entry.family_id: entry for entry in self.task_taxonomy}
        required_fields = {field.field_name for field in self.procedure_fields if field.required}

        for input_spec in self.simulation_inputs:
            task = taxonomy_by_id.get(input_spec.taxonomy_ref)
            if task is None:
                issues.append(f"{input_spec.input_id}: unknown taxonomy_ref {input_spec.taxonomy_ref}")
            elif task.readiness != SyntheticReadiness.READY_FOR_SYNTHETIC_V2_PLAN:
                issues.append(f"{input_spec.input_id}: {task.family_id} is not ready_for_synthetic_v2_plan")

            if _has_forbidden_pool_term(input_spec.to_dict()):
                issues.append(f"{input_spec.input_id}: forbidden pool-route field is out of scope")

            bound = input_spec.bound_field_paths()
            for binding in input_spec.evidence_bindings:
                if self.valid_source_ids is not None and binding.source_id not in self.valid_source_ids:
                    issues.append(
                        f"{input_spec.input_id}: unknown evidence source_id {binding.source_id}"
                    )

            for field_name in required_fields:
                if field_name in METADATA_FIELD_PATHS:
                    continue
                if field_name not in input_spec.procedure_fields:
                    issues.append(f"{input_spec.input_id}: missing required procedure field {field_name}")
                    continue
                field_path = f"procedure_fields.{field_name}"
                if field_path not in bound:
                    issues.append(f"{input_spec.input_id}: missing evidence binding for {field_path}")

            for spec_key in BUSINESS_SPEC_KEYS:
                value = getattr(input_spec, spec_key)
                for field_path in _field_paths(spec_key, value):
                    if field_path not in bound:
                        issues.append(f"{input_spec.input_id}: missing evidence binding for {field_path}")

            binding_by_path = {binding.field_path: binding for binding in input_spec.evidence_bindings}
            for key, value in input_spec.quality_spec.items():
                if key not in QUALITY_KEYS:
                    continue
                field_path = f"quality_spec.{key}"
                binding = binding_by_path.get(field_path)
                if not _has_quality_boundary(value) and (
                    binding is None
                    or binding.value_status != SyntheticValueStatus.REQUIRES_REAL_VALIDATION_LATER
                ):
                    issues.append(f"{input_spec.input_id}: quality fields require boundary for {field_path}")

        return SyntheticInputGateResult(not issues, issues)
```

- [ ] **Step 4: Export models**

Modify `weld-experience-engine/weldcore/knowledge/__init__.py` to export the new types.

Minimal acceptable content:

```python
from .synthetic_input import (
    EvidenceBinding,
    SyntheticEvidenceRole,
    SyntheticReadiness,
    SimulationInputSpec,
    SyntheticInputFoundation,
    SyntheticInputGateResult,
    SyntheticSkillDatasetV2PlanInput,
    TaskTaxonomyEntry,
    SyntheticValueStatus,
    WeldProcedureField,
)
```

If the file already exports other symbols, add these imports without removing existing exports.

- [ ] **Step 5: Run tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_synthetic_input_models.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add weld-experience-engine/weldcore/knowledge/synthetic_input.py \
  weld-experience-engine/weldcore/knowledge/__init__.py \
  weld-experience-engine/tests/test_synthetic_input_models.py
git commit -m "feat(knowledge): add synthetic v2 input models"
```

---

## Task 3: Input-Spec Manifests

**Files:**
- Create: `docs/data-foundation/manifests/task_taxonomy.json`
- Create: `docs/data-foundation/manifests/procedure_fields.json`
- Create: `docs/data-foundation/manifests/synthetic_v2_inputs.json`
- Test: `weld-experience-engine/tests/test_synthetic_input_manifests.py`
- Read first: `docs/data-foundation/research/synthetic_v2_input_research.md`
- Read first: `docs/data-foundation/research/synthetic_v2_field_gap_matrix.csv`

- [ ] **Step 1: Write failing manifest loader tests**

Do not create manifests from memory. Derive field groups, source ids, assumption fields, and validation statuses from the Task 1 research outputs.

Append to `weld-experience-engine/tests/test_synthetic_input_manifests.py`:

```python
from weldcore.knowledge.synthetic_manifest import load_synthetic_input_foundation
from weldcore.knowledge.synthetic_input import SyntheticReadiness


def test_manifest_loads_expected_task_counts():
    foundation = load_synthetic_input_foundation()

    readiness_counts = {}
    for entry in foundation.task_taxonomy:
        readiness_counts[entry.readiness] = readiness_counts.get(entry.readiness, 0) + 1

    assert len(foundation.task_taxonomy) >= 7
    assert readiness_counts[SyntheticReadiness.READY_FOR_SYNTHETIC_V2_PLAN] >= 3
    assert readiness_counts[SyntheticReadiness.NEEDS_MORE_SOURCES] >= 1
    assert readiness_counts[SyntheticReadiness.DEFER] >= 3


def test_manifest_first_batch_inputs_pass_gate():
    foundation = load_synthetic_input_foundation()

    gate = foundation.validate()

    assert gate.passed, gate.issues
    assert {item.taxonomy_ref for item in foundation.simulation_inputs} == {
        "stiffened-panel-fillet",
        "panel-butt",
        "micro-panel-web-bulkhead",
    }


def test_manifest_includes_procedure_field_groups():
    foundation = load_synthetic_input_foundation()

    groups = {field.field_group for field in foundation.procedure_fields}

    assert {
        "task_joint",
        "geometry_material",
        "process",
        "motion_posture",
        "quality_inspection",
    }.issubset(groups)
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_synthetic_input_manifests.py -v
```

Expected: FAIL with import error or missing manifest loader.

- [ ] **Step 3: Create task taxonomy manifest**

Create `docs/data-foundation/manifests/task_taxonomy.json` with at least:

```json
[
  {
    "family_id": "stiffened-panel-fillet",
    "manufacturing_stage": "panel_line",
    "weld_object": "stiffener-to-panel",
    "joint_type": "fillet",
    "weld_position": "horizontal",
    "groove_geometry": "none",
    "layer_pass": "single_pass",
    "access_context": "open_panel",
    "motion_structure": "single_seam",
    "readiness": "ready_for_synthetic_v2_plan",
    "modeling_difficulty": "easy",
    "notes": "First-batch panel line fillet input."
  },
  {
    "family_id": "panel-butt",
    "manufacturing_stage": "panel_line",
    "weld_object": "panel butt seam",
    "joint_type": "butt",
    "weld_position": "flat",
    "groove_geometry": "v_groove_placeholder",
    "layer_pass": "single_pass",
    "access_context": "open_panel",
    "motion_structure": "single_seam",
    "readiness": "ready_for_synthetic_v2_plan",
    "modeling_difficulty": "easy",
    "notes": "First-batch simplified shipbuilding panel butt input."
  },
  {
    "family_id": "micro-panel-web-bulkhead",
    "manufacturing_stage": "subassembly",
    "weld_object": "micro-panel web and bulkhead seams",
    "joint_type": "fillet",
    "weld_position": "multi_position",
    "groove_geometry": "none",
    "layer_pass": "single_pass",
    "access_context": "subassembly",
    "motion_structure": "multi_short_seam",
    "readiness": "ready_for_synthetic_v2_plan",
    "modeling_difficulty": "medium",
    "notes": "First-batch multi-short-seam input."
  },
  {
    "family_id": "double-bottom-inner-fillet",
    "manufacturing_stage": "block_assembly",
    "weld_object": "double-bottom inner fillet",
    "joint_type": "fillet",
    "weld_position": "horizontal",
    "groove_geometry": "none",
    "layer_pass": "single_pass",
    "access_context": "confined_compartment",
    "motion_structure": "multi_short_seam",
    "readiness": "needs_more_sources",
    "modeling_difficulty": "medium",
    "notes": "Needs reachability and confined-space evidence before generation."
  },
  {
    "family_id": "vertical-overhead-hull-weld",
    "manufacturing_stage": "erection",
    "weld_object": "vertical or overhead hull seam",
    "joint_type": "butt_or_fillet",
    "weld_position": "vertical_up_or_overhead",
    "groove_geometry": "unknown",
    "layer_pass": "unknown",
    "access_context": "hull_block",
    "motion_structure": "single_or_multi_seam",
    "readiness": "defer",
    "modeling_difficulty": "hard",
    "notes": "Deferred due to position-specific procedure and posture constraints."
  },
  {
    "family_id": "thick-plate-groove-multipass",
    "manufacturing_stage": "block_assembly",
    "weld_object": "thick plate groove weld",
    "joint_type": "groove",
    "weld_position": "multi_position",
    "groove_geometry": "v_x_or_k_groove",
    "layer_pass": "multi_layer_multi_pass",
    "access_context": "open_or_block",
    "motion_structure": "multi_layer_multi_pass",
    "readiness": "defer",
    "modeling_difficulty": "hard",
    "notes": "Deferred; close to WPS/PQR and multipass planning."
  },
  {
    "family_id": "curved-spatial-complex-weld",
    "manufacturing_stage": "curved_hull",
    "weld_object": "curved spatial seam",
    "joint_type": "complex",
    "weld_position": "multi_position",
    "groove_geometry": "complex",
    "layer_pass": "unknown",
    "access_context": "curved_surface",
    "motion_structure": "curved_seam",
    "readiness": "defer",
    "modeling_difficulty": "hard",
    "notes": "Deferred; curved topology is outside first input-spec implementation."
  }
]
```

- [ ] **Step 4: Create procedure field manifest**

Create `docs/data-foundation/manifests/procedure_fields.json` with at least:

```json
[
  {"field_name": "welding_process", "field_group": "task_joint", "required": true, "description": "GMAW/FCAW/SAW/manual/hybrid or explicit unknown."},
  {"field_name": "joint_type", "field_group": "task_joint", "required": true, "description": "butt/fillet/tee/lap/groove/complex."},
  {"field_name": "weld_position", "field_group": "task_joint", "required": true, "description": "flat/horizontal/vertical-up/overhead/multi-position."},
  {"field_name": "weld_object", "field_group": "task_joint", "required": true, "description": "Shipbuilding structure and seam object."},
  {"field_name": "manufacturing_stage", "field_group": "task_joint", "required": true, "description": "Shipbuilding production stage."},
  {"field_name": "plate_thickness_mm", "field_group": "geometry_material", "required": true, "description": "Plate thickness; may be assumed if marked."},
  {"field_name": "groove_geometry", "field_group": "geometry_material", "required": true, "description": "Groove type, root gap, bevel angle, land, or none."},
  {"field_name": "current", "field_group": "process", "required": true, "description": "Current field or explicit unknown."},
  {"field_name": "voltage", "field_group": "process", "required": true, "description": "Voltage field or explicit unknown."},
  {"field_name": "travel_speed", "field_group": "process", "required": true, "description": "Travel speed field for motion and heat-input placeholder."},
  {"field_name": "trajectory", "field_group": "motion_posture", "required": true, "description": "TCP trajectory input or generation instruction."},
  {"field_name": "torch_angle", "field_group": "motion_posture", "required": true, "description": "Work/travel angle or explicit unknown."},
  {"field_name": "quality_label", "field_group": "quality_inspection", "required": true, "description": "Public label vocabulary, simulation placeholder, or real-validation marker."},
  {"field_name": "inspection_reference", "field_group": "quality_inspection", "required": true, "description": "Inspection reference entry, not acceptance result."}
]
```

- [ ] **Step 5: Create first-batch input manifest**

Create `docs/data-foundation/manifests/synthetic_v2_inputs.json`.

Each entry must include `input_id`, `taxonomy_ref`, `procedure_fields`, `geometry_spec`, `motion_spec`, `process_spec`, `quality_spec`, `variant_policy`, `evidence_bindings`, and `generation_boundary`.

Use three entries:

- `input-stiffened-panel-fillet-001`
- `input-panel-butt-001`
- `input-micro-panel-web-bulkhead-001`

Each required `procedure_fields.<field_name>` must have at least one binding. Each non-empty business spec dictionary must also have bindings for its concrete top-level field paths, for example `geometry_spec.groove_geometry`, `motion_spec.motion_template`, `process_spec.current`, and `quality_spec.quality_label`. Do not introduce nested path recursion in this first implementation; if nested objects are needed later, add a separate schema revision. Use existing source ids from `sources.json`; do not invent external sources.

Example binding:

```json
{
  "field_path": "procedure_fields.joint_type",
  "source_id": "vendor-kranendonk-panel-welding-gantry",
  "evidence_role": "shipbuilding_case",
  "value_status": "constrained",
  "notes": "Used as task and field evidence only; not process validation."
}
```

All quality-related values must include one of these boundary markers: `public_label_vocabulary`, `simulation_score_placeholder`, or `requires_real_validation_later`. For first-batch inputs, prefer `requires_real_validation_later` unless the value is only a public label vocabulary reference.

- [ ] **Step 6: Implement manifest loader**

Create `weld-experience-engine/weldcore/knowledge/synthetic_manifest.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .manifest import DEFAULT_FOUNDATION_ROOT
from .manifest import load_data_foundation
from .synthetic_input import (
    EvidenceBinding,
    SyntheticEvidenceRole,
    SyntheticReadiness,
    SimulationInputSpec,
    SyntheticInputFoundation,
    TaskTaxonomyEntry,
    SyntheticValueStatus,
    WeldProcedureField,
)


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _taxonomy_from_dict(data: dict[str, Any]) -> TaskTaxonomyEntry:
    return TaskTaxonomyEntry(
        family_id=data["family_id"],
        manufacturing_stage=data["manufacturing_stage"],
        weld_object=data["weld_object"],
        joint_type=data["joint_type"],
        weld_position=data["weld_position"],
        groove_geometry=data["groove_geometry"],
        layer_pass=data["layer_pass"],
        access_context=data["access_context"],
        motion_structure=data["motion_structure"],
        readiness=SyntheticReadiness(data["readiness"]),
        modeling_difficulty=data["modeling_difficulty"],
        notes=data["notes"],
    )


def _procedure_field_from_dict(data: dict[str, Any]) -> WeldProcedureField:
    return WeldProcedureField(
        field_name=data["field_name"],
        field_group=data["field_group"],
        required=bool(data["required"]),
        description=data.get("description", ""),
    )


def _binding_from_dict(data: dict[str, Any]) -> EvidenceBinding:
    return EvidenceBinding(
        field_path=data["field_path"],
        source_id=data["source_id"],
        evidence_role=SyntheticEvidenceRole(data["evidence_role"]),
        value_status=SyntheticValueStatus(data["value_status"]),
        notes=data["notes"],
    )


def _input_from_dict(data: dict[str, Any]) -> SimulationInputSpec:
    return SimulationInputSpec(
        input_id=data["input_id"],
        taxonomy_ref=data["taxonomy_ref"],
        procedure_fields=dict(data["procedure_fields"]),
        geometry_spec=dict(data["geometry_spec"]),
        motion_spec=dict(data["motion_spec"]),
        process_spec=dict(data["process_spec"]),
        quality_spec=dict(data["quality_spec"]),
        variant_policy=dict(data["variant_policy"]),
        evidence_bindings=[_binding_from_dict(item) for item in data["evidence_bindings"]],
        generation_boundary=list(data["generation_boundary"]),
    )


def load_synthetic_input_foundation(root: str | Path | None = None) -> SyntheticInputFoundation:
    foundation_root = Path(root) if root is not None else DEFAULT_FOUNDATION_ROOT
    manifests_root = foundation_root / "manifests"
    data_foundation = load_data_foundation(foundation_root)
    valid_source_ids = {source.source_id for source in data_foundation.sources}
    return SyntheticInputFoundation(
        task_taxonomy=[
            _taxonomy_from_dict(item)
            for item in _load_json(manifests_root / "task_taxonomy.json")
        ],
        procedure_fields=[
            _procedure_field_from_dict(item)
            for item in _load_json(manifests_root / "procedure_fields.json")
        ],
        simulation_inputs=[
            _input_from_dict(item)
            for item in _load_json(manifests_root / "synthetic_v2_inputs.json")
        ],
        valid_source_ids=valid_source_ids,
    )
```

- [ ] **Step 7: Export loader**

Modify `weld-experience-engine/weldcore/knowledge/__init__.py`:

```python
from .synthetic_manifest import load_synthetic_input_foundation
```

- [ ] **Step 8: Run tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_synthetic_input_manifests.py -v
```

Expected: PASS.

- [ ] **Step 9: Commit**

Run:

```bash
git add docs/data-foundation/manifests/task_taxonomy.json \
  docs/data-foundation/manifests/procedure_fields.json \
  docs/data-foundation/manifests/synthetic_v2_inputs.json \
  weld-experience-engine/weldcore/knowledge/synthetic_manifest.py \
  weld-experience-engine/weldcore/knowledge/__init__.py \
  weld-experience-engine/tests/test_synthetic_input_manifests.py
git commit -m "feat(knowledge): add synthetic v2 input manifests"
```

---

## Task 4: Synthetic Input Report

**Files:**
- Create: `weld-experience-engine/weldcore/report/synthetic_v2_input_report.py`
- Create: `docs/data-foundation/reports/synthetic_v2_input_evidence.md`
- Test: `weld-experience-engine/tests/test_synthetic_v2_input_report.py`

- [ ] **Step 1: Write failing report tests**

Create `weld-experience-engine/tests/test_synthetic_v2_input_report.py`:

```python
import json

from weldcore.report.synthetic_v2_input_report import run_synthetic_v2_input_report


def test_synthetic_v2_input_report_writes_expected_outputs(tmp_path):
    evidence = run_synthetic_v2_input_report(outdir=tmp_path)

    assert (tmp_path / "task_taxonomy.json").exists()
    assert (tmp_path / "procedure_fields.json").exists()
    assert (tmp_path / "simulation_inputs.json").exists()
    assert (tmp_path / "evidence_bindings.csv").exists()
    assert (tmp_path / "evidence.md").exists()
    assert evidence["summary"]["ready_task_count"] >= 3
    assert evidence["summary"]["simulation_input_count"] == 3


def test_synthetic_v2_input_report_markdown_keeps_boundaries(tmp_path):
    run_synthetic_v2_input_report(outdir=tmp_path)

    text = (tmp_path / "evidence.md").read_text(encoding="utf-8")

    assert "不是 WPS/PQR" in text
    assert "不证明真实焊接质量" in text
    assert "SyntheticSkillDataset v2" in text


def test_synthetic_v2_input_report_json_has_no_pool_route_fields(tmp_path):
    run_synthetic_v2_input_report(outdir=tmp_path)

    combined = ""
    for name in ["task_taxonomy.json", "procedure_fields.json", "simulation_inputs.json"]:
        combined += json.dumps(
            json.loads((tmp_path / name).read_text(encoding="utf-8")),
            ensure_ascii=False,
        ).lower()

    forbidden = ["molten_pool", "molten pool", "weld_pool", "weld pool", "熔池"]
    assert not any(term in combined for term in forbidden)
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_synthetic_v2_input_report.py -v
```

Expected: FAIL with missing module.

- [ ] **Step 3: Implement report command**

Create `weld-experience-engine/weldcore/report/synthetic_v2_input_report.py`:

```python
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from ..knowledge.manifest import DEFAULT_FOUNDATION_ROOT
from ..knowledge.synthetic_input import SyntheticReadiness, SyntheticInputFoundation
from ..knowledge.synthetic_manifest import load_synthetic_input_foundation


DEFAULT_DOCS_REPORT_DIR = DEFAULT_FOUNDATION_ROOT / "reports"


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _summary(foundation: SyntheticInputFoundation) -> dict[str, int]:
    return {
        "task_count": len(foundation.task_taxonomy),
        "ready_task_count": sum(
            entry.readiness == SyntheticReadiness.READY_FOR_SYNTHETIC_V2_PLAN
            for entry in foundation.task_taxonomy
        ),
        "procedure_field_count": len(foundation.procedure_fields),
        "simulation_input_count": len(foundation.simulation_inputs),
        "evidence_binding_count": sum(
            len(item.evidence_bindings) for item in foundation.simulation_inputs
        ),
    }


def run_synthetic_v2_input_report(
    outdir: str | Path = "synthetic_v2_input_report_out",
    foundation: SyntheticInputFoundation | None = None,
    docs_report_dir: str | Path | None = None,
) -> dict[str, Any]:
    outpath = Path(outdir)
    outpath.mkdir(parents=True, exist_ok=True)
    data = foundation or load_synthetic_input_foundation()
    gate = data.validate()
    if not gate.passed:
        raise ValueError("Synthetic v2 input gate failed: " + "; ".join(gate.issues))

    summary = _summary(data)
    taxonomy = [entry.to_dict() for entry in data.task_taxonomy]
    fields = [field.to_dict() for field in data.procedure_fields]
    inputs = [item.to_dict() for item in data.simulation_inputs]
    evidence = {
        "summary": summary,
        "task_taxonomy": taxonomy,
        "procedure_fields": fields,
        "simulation_inputs": inputs,
    }

    _write_json(outpath / "task_taxonomy.json", taxonomy)
    _write_json(outpath / "procedure_fields.json", fields)
    _write_json(outpath / "simulation_inputs.json", inputs)
    _write_bindings_csv(outpath / "evidence_bindings.csv", data)
    _write_evidence_markdown(outpath / "evidence.md", data, summary)

    if docs_report_dir is not None:
        docs_path = Path(docs_report_dir)
        docs_path.mkdir(parents=True, exist_ok=True)
        _write_evidence_markdown(
            docs_path / "synthetic_v2_input_evidence.md",
            data,
            summary,
        )

    print("=== SyntheticSkillDataset v2 输入规范摘要 ===")
    print(f"任务分类数: {summary['task_count']}")
    print(f"ready 任务数: {summary['ready_task_count']}")
    print(f"标准字段数: {summary['procedure_field_count']}")
    print(f"首批输入数: {summary['simulation_input_count']}")
    print(f"证据绑定数: {summary['evidence_binding_count']}")
    print(f"报告目录: {outpath}")
    return evidence


def _write_bindings_csv(path: Path, foundation: SyntheticInputFoundation) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["input_id", "taxonomy_ref", "field_path", "source_id", "evidence_role", "value_status", "notes"])
        for input_spec in foundation.simulation_inputs:
            for binding in input_spec.evidence_bindings:
                writer.writerow([
                    input_spec.input_id,
                    input_spec.taxonomy_ref,
                    binding.field_path,
                    binding.source_id,
                    binding.evidence_role.value,
                    binding.value_status.value,
                    binding.notes,
                ])


def _write_evidence_markdown(
    path: Path,
    foundation: SyntheticInputFoundation,
    summary: dict[str, int],
) -> None:
    lines = [
        "# SyntheticSkillDataset v2 输入规范证据报告",
        "",
        "## 结论",
        "",
        "- 本报告是 SyntheticSkillDataset v2 的输入规范证据，不是 WPS/PQR。",
        "- 本报告不证明真实焊接质量，不替代船厂 WPS、工艺评定、检测或船级审查。",
        "- 第一批输入只能用于后续 synthetic 样本生成、结构化、迁移和评测机制验证。",
        "",
        "## 汇总",
        "",
        f"- 任务分类数：{summary['task_count']}",
        f"- ready 任务数：{summary['ready_task_count']}",
        f"- 标准字段数：{summary['procedure_field_count']}",
        f"- 首批输入数：{summary['simulation_input_count']}",
        f"- 证据绑定数：{summary['evidence_binding_count']}",
        "",
        "## 任务分类",
        "",
        "| family_id | readiness | joint_type | weld_position | groove_geometry | layer_pass | motion_structure |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for entry in foundation.task_taxonomy:
        lines.append(
            f"| {entry.family_id} | {entry.readiness.value} | {entry.joint_type} | {entry.weld_position} | {entry.groove_geometry} | {entry.layer_pass} | {entry.motion_structure} |"
        )

    lines.extend([
        "",
        "## 首批输入",
        "",
        "| input_id | taxonomy_ref | assumption fields | real-validation fields |",
        "| --- | --- | --- | --- |",
    ])
    for input_spec in foundation.simulation_inputs:
        assumed = [
            binding.field_path
            for binding in input_spec.evidence_bindings
            if binding.value_status.value == "assumed"
        ]
        real_validation = [
            binding.field_path
            for binding in input_spec.evidence_bindings
            if binding.value_status.value == "requires_real_validation_later"
        ]
        lines.append(
            f"| {input_spec.input_id} | {input_spec.taxonomy_ref} | {', '.join(assumed) or '无'} | {', '.join(real_validation) or '无'} |"
        )

    path.write_text("\\n".join(lines) + "\\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="synthetic_v2_input_report_out")
    parser.add_argument("--no-docs-copy", action="store_true")
    args = parser.parse_args()
    docs_dir = None if args.no_docs_copy else DEFAULT_DOCS_REPORT_DIR
    run_synthetic_v2_input_report(args.outdir, docs_report_dir=docs_dir)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run report tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_synthetic_v2_input_report.py -v
```

Expected: PASS.

- [ ] **Step 5: Generate report artifacts**

Run:

```bash
cd weld-experience-engine
uv run python -m weldcore.report.synthetic_v2_input_report
```

Expected:

```text
=== SyntheticSkillDataset v2 输入规范摘要 ===
任务分类数: 7
ready 任务数: 3
标准字段数: ...
首批输入数: 3
证据绑定数: ...
报告目录: synthetic_v2_input_report_out
```

- [ ] **Step 6: Commit**

Run:

```bash
git add weld-experience-engine/weldcore/report/synthetic_v2_input_report.py \
  weld-experience-engine/tests/test_synthetic_v2_input_report.py \
  docs/data-foundation/reports/synthetic_v2_input_evidence.md
git commit -m "feat(report): add synthetic v2 input evidence report"
```

Do not commit `weld-experience-engine/synthetic_v2_input_report_out/` unless the repo already tracks equivalent runtime outputs.

---

## Task 5: Documentation Updates

**Files:**
- Modify: `README.md`
- Modify: `details.md`
- Modify: `weld-experience-engine/README.md`

- [ ] **Step 1: Update root README**

Modify `README.md`:

- Add the new input-spec layer to “当前结论” and “已完成成果”.
- Add command:

```bash
uv run python -m weldcore.report.synthetic_v2_input_report
```

- State clearly:
  - This completes the `SyntheticSkillDataset v2` input-spec gate.
  - It does not generate bulk `SyntheticSkillDataset v2` samples.
  - It is not real welding quality validation.

- [ ] **Step 2: Update engine README**

Modify `weld-experience-engine/README.md`:

- Add `synthetic_v2_input_report` command after `data_foundation_report`.
- Explain output directory:

```text
synthetic_v2_input_report_out/
```

- Keep Rerun and ManiSkill optional boundary unchanged.

- [ ] **Step 3: Update details.md**

Modify `details.md`:

- Move the project state from “准备建立输入规范” to “已完成输入规范 gate” only after report implementation is complete.
- Keep this boundary:
  - Not bulk synthetic sample generation.
  - Not real welding quality validation.
  - Not WPS/PQR.

- [ ] **Step 4: Run documentation smoke checks**

Run:

```bash
rg -n "synthetic_v2_input_report|SyntheticSkillDataset v2 输入规范|真实焊接质量|WPS/PQR" README.md details.md weld-experience-engine/README.md
```

Expected: all three docs mention the new command or boundary.

- [ ] **Step 5: Commit**

Run:

```bash
git add README.md details.md weld-experience-engine/README.md
git commit -m "docs: document synthetic v2 input gate"
```

---

## Task 6: End-to-End Verification

**Files:**
- Read only unless verification exposes a bug.

- [ ] **Step 1: Run full tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q
```

Expected: all tests pass.

- [ ] **Step 2: Run all report commands**

Run:

```bash
cd weld-experience-engine
uv run python -m weldcore.report.generate
uv run python -m weldcore.report.mvp_report
uv run python -m weldcore.report.scenario_report
uv run python -m weldcore.report.data_foundation_report
uv run python -m weldcore.report.synthetic_v2_input_report
```

Expected: all commands exit 0 and print their summary blocks.

- [ ] **Step 3: Verify forbidden fields in JSON/CSV outputs**

Run:

```bash
rg -n "熔池|molten_pool|molten pool|weld_pool|weld pool" \
  docs/data-foundation/manifests/task_taxonomy.json \
  docs/data-foundation/manifests/procedure_fields.json \
  docs/data-foundation/manifests/synthetic_v2_inputs.json \
  weld-experience-engine/synthetic_v2_input_report_out/*.json \
  weld-experience-engine/synthetic_v2_input_report_out/*.csv
```

Expected: no matches.

Markdown boundary text may mention excluded molten-pool routes; JSON/CSV must not.

- [ ] **Step 4: Check worktree**

Run:

```bash
git status --short --branch
```

Expected: only intended generated docs or no changes. Do not leave untracked `uv.lock` if `uv` created it by accident and the repo does not track it.

- [ ] **Step 5: Final commit if verification changed docs**

If `synthetic_v2_input_report` refreshed committed docs after the previous commit, commit those docs:

```bash
git add docs/data-foundation/reports/synthetic_v2_input_evidence.md README.md details.md weld-experience-engine/README.md
git commit -m "docs: refresh synthetic v2 input evidence"
```

If nothing changed, commit nothing.

---

## Task 7: Completion Handoff

**Files:**
- Read only.

- [ ] **Step 1: Summarize implemented artifacts**

Include:

- New models.
- New manifests.
- New report command.
- Report outputs.
- Updated docs.

- [ ] **Step 2: Summarize verification evidence**

Include exact commands and outcomes:

- `uv run pytest -q`
- five report commands.
- forbidden-field search.

- [ ] **Step 3: State remaining boundary**

Say clearly:

- The input-spec gate is implemented.
- Bulk `SyntheticSkillDataset v2` generation is still the next stage.
- Real welding quality validation, WPS/PQR, and molten-pool route remain out of scope.
