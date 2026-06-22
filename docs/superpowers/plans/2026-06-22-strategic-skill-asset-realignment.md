# Strategic Skill Asset Realignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 A02 默认入口、最小接口对象和默认报告对齐为“机器人技能大师能力的焊接技能资产底座”，并把 A01/B06/IP/expert review 承接为可验证 artifact。

**Architecture:** 保持 `ManipulationSkillAsset` 为核心，不引入生产 connector 或跨仓库 runtime 依赖。新增的 A01/B06 mapping、A02->A01 handoff、IP support 和 expert review record 都是 contract/report artifact，默认只表达候选和边界。低层仿真对象继续使用 `simulation`，canonical skill asset evidence 使用新 source type。

**Tech Stack:** Python dataclasses, pytest, existing `weldcore.skill_asset` builders/report CLI, Markdown docs and generated HTML reading copies.

---

## File Map

- Modify `weld-experience-engine/weldcore/skill_asset/model.py`
  - Update `SkillAssetSourceType`.
  - Add dataclasses for evidence source catalog entries, A01/B06 mapping, expert review record, A02->A01 handoff, IP support matrix.
- Modify `weld-experience-engine/weldcore/skill_asset/builders.py`
  - Change canonical skill asset `source_type` from `simulation` to `simulation_only`.
- Create `weld-experience-engine/weldcore/skill_asset/strategic_alignment.py`
  - Build default catalog, A01/B06 mapping, expert review record, A02->A01 handoff and IP support matrix.
- Modify `weld-experience-engine/weldcore/skill_asset/asset_report.py`
  - Add five strategic artifacts and write twelve JSON outputs.
- Modify `weld-experience-engine/weldcore/skill_asset/__init__.py`
  - Export new dataclasses/builders that tests and downstream users need.
- Modify tests:
  - `weld-experience-engine/tests/test_canonical_skill_asset.py`
  - `weld-experience-engine/tests/test_contextual_transfer_precheck.py`
  - `weld-experience-engine/tests/test_skill_asset_report.py`
  - Create `weld-experience-engine/tests/test_strategic_skill_asset_alignment.py`
- Modify docs:
  - `README.md`
  - `details.md`
  - `weld-experience-engine/README.md`
  - `docs/architecture/README.md`
  - `docs/skill-assets/weld-skill-package.md`
  - regenerate `README.html`, `details.html`

---

### Task 1: Canonical Evidence Source Types

**Files:**
- Modify: `weld-experience-engine/weldcore/skill_asset/model.py`
- Modify: `weld-experience-engine/weldcore/skill_asset/builders.py`
- Test: `weld-experience-engine/tests/test_canonical_skill_asset.py`
- Test: `weld-experience-engine/tests/test_contextual_transfer_precheck.py`
- Test: `weld-experience-engine/tests/test_strategic_skill_asset_alignment.py`

- [ ] **Step 1: Write failing source type tests**

Add to `tests/test_strategic_skill_asset_alignment.py`:

```python
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
```

Also update known existing canonical skill asset assertions in `tests/test_canonical_skill_asset.py`:

- Manual `SkillAssetEvidence(source_type=...)` uses `"simulation_only"`.
- Manual `ManipulationSkillAsset(source_type=...)` uses `"simulation_only"`.
- `test_manipulation_skill_asset_serializes_core_contract` expects `data["evidence"]["source_type"] == "simulation_only"`.
- `test_simulation_evidence_bundle_builds_manipulation_skill_asset` expects `asset.source_type == "simulation_only"`.

Do not change low-level `SimulationEvidenceBundle` or simulation ingest tests that still describe the simulator/source manifest itself.

- [ ] **Step 2: Run source type test to verify RED**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_strategic_skill_asset_alignment.py::test_default_simulation_skill_asset_uses_canonical_simulation_only_source -q
```

Expected: FAIL because current `source_type` is `simulation`.

- [ ] **Step 3: Update source type literals and builder**

In `model.py`, change `SkillAssetSourceType` to:

```python
SkillAssetSourceType = Literal[
    "simulation_only",
    "human_demo",
    "real_robot_log",
    "h300_workcell_run",
    "expert_annotation",
]
```

In `builders.py`, set both `SkillAssetEvidence.source_type` and `ManipulationSkillAsset.source_type` to `"simulation_only"`.

- [ ] **Step 4: Run affected tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_strategic_skill_asset_alignment.py tests/test_contextual_transfer_precheck.py tests/test_canonical_skill_asset.py -q
```

Expected: PASS. If tests that assert old `"simulation"` fail, update them to the new canonical skill asset source type while leaving low-level simulation bundle tests untouched.

- [ ] **Step 5: Commit**

```bash
git add weld-experience-engine/weldcore/skill_asset/model.py \
  weld-experience-engine/weldcore/skill_asset/builders.py \
  weld-experience-engine/tests/test_canonical_skill_asset.py \
  weld-experience-engine/tests/test_contextual_transfer_precheck.py \
  weld-experience-engine/tests/test_strategic_skill_asset_alignment.py
git commit -m "feat: align skill asset evidence source types"
```

---

### Task 2: Strategic Alignment Artifact Models and Builders

**Files:**
- Modify: `weld-experience-engine/weldcore/skill_asset/model.py`
- Create: `weld-experience-engine/weldcore/skill_asset/strategic_alignment.py`
- Modify: `weld-experience-engine/weldcore/skill_asset/__init__.py`
- Test: `weld-experience-engine/tests/test_strategic_skill_asset_alignment.py`

- [ ] **Step 1: Write failing tests for catalog, mappings, review record, handoff and IP support**

Add tests:

```python
from pathlib import Path

from weldcore.robot_process import build_robot_context_from_body_asset
from weldcore.skill_asset import (
    build_a01_b06_skill_asset_mapping,
    build_a02_to_a01_product_validation_handoff,
    build_default_evidence_source_catalog,
    build_default_expert_review_record,
    build_default_scene_context_asset,
    build_ip_disclosure_support_matrix,
    build_contextual_feasibility_result,
    build_robot_body_asset_from_urdf,
)

ROOT = Path(__file__).resolve().parents[2]
URDF = ROOT / "docs" / "real-urdf" / "robot.urdf"


def test_evidence_source_catalog_contains_strategic_sources():
    skill = _default_skill_asset()
    catalog = build_default_evidence_source_catalog(skill)
    source_types = {entry.source_type for entry in catalog}

    assert {
        "simulation_only",
        "human_demo",
        "real_robot_log",
        "h300_workcell_run",
        "expert_annotation",
    } <= source_types


def test_a01_b06_mapping_carries_workcell_and_package_field_contract():
    skill = _default_skill_asset()
    mapping = build_a01_b06_skill_asset_mapping(skill)
    data = mapping.to_dict()

    assert data["evidence_source_type"] == "h300_workcell_run"
    assert {
        "task",
        "weld_seam",
        "workpiece",
        "path_points",
        "robot_pose",
        "torch_pose",
        "process_parameters",
        "manual_correction",
        "execution_log",
        "anomaly",
        "quality_result",
    } <= set(data["workcell_fields"])
    assert {
        "physical_ai_package_profile",
        "task_context",
        "coordinate_frames",
        "frames",
        "events",
        "labels",
        "trajectory",
        "human_correction",
        "metrics",
        "quality_labels",
        "rerun_replay_ref",
    } <= set(data["package_fields"])
    assert data["skill_asset_field_mapping"]["path_points"] == "motion.tcp_trajectory"
    assert data["skill_asset_field_mapping"]["manual_correction"] == "evidence.review_input"
    assert data["quality_feedback_mapping"]["quality_result"] == "quality_feedback_evidence"
    assert "not_WPS_PQR" in data["evidence_boundary"]


def test_expert_review_record_requires_real_context_and_snapshots():
    skill = _default_skill_asset()
    robot = build_robot_body_asset_from_urdf(URDF)
    robot_context = build_robot_context_from_body_asset(robot)
    scene = build_default_scene_context_asset(skill)
    feasibility = build_contextual_feasibility_result(skill, robot_context, scene)

    review = build_default_expert_review_record(skill, robot_context, scene, feasibility)
    data = review.to_dict()
    required_fields = {item["field"] for item in data["required_real_context"]}
    required_keys = {"field", "current_status", "required_evidence", "blocking_if_missing"}

    assert data["review_status"] == "pending_expert_review"
    assert {
        "real_tcp_calibration",
        "workpiece_frame_measurement",
        "robot_model_identity",
        "joint_limits_source",
    } <= required_fields
    assert all(required_keys <= set(item) for item in data["required_real_context"])
    assert all(item["blocking_if_missing"] is True for item in data["required_real_context"])
    assert any(
        item["field"] == "real_tcp_calibration"
        and item["current_status"] == "nominal_from_asset_not_calibrated"
        for item in data["required_real_context"]
    )
    assert data["robot_context_snapshot"]["context_id"] == robot_context.context_id
    assert data["robot_context_snapshot"]["tcp_calibration_status"] == "nominal_from_asset_not_calibrated"
    assert "not_ready_for_robot_execution" in data["robot_context_snapshot"]["evidence_notes"]
    assert data["scene_context_snapshot"]["scene_id"] == scene.scene_id
    assert data["scene_context_snapshot"]["validation_status"] == scene.validation_status
    assert "not_collision_validated" in data["scene_context_snapshot"]["evidence_boundary"]
    assert data["feasibility_status_snapshot"]["result_id"] == feasibility.result_id
    assert data["feasibility_status_snapshot"]["status"] == feasibility.status
    assert "not_full_ik_solver" in data["feasibility_status_snapshot"]["evidence_boundary"]
    assert "not_ready_for_robot_execution" in data["review_boundary"]


def test_a02_to_a01_handoff_and_ip_support_keep_execution_boundary():
    skill = _default_skill_asset()
    handoff = build_a02_to_a01_product_validation_handoff(skill)
    support = build_ip_disclosure_support_matrix(skill)

    assert "trajectory_candidate" in handoff.candidate_outputs
    assert "not_direct_robot_program" in handoff.handoff_boundary
    assert {item["patent_item_id"] for item in support.items} == {"P0-02", "P0-03", "P0-04"}
    assert all(item["supporting_objects"] for item in support.items)
    assert all(item["supporting_reports"] for item in support.items)
    assert all(item["missing_real_world_evidence"] for item in support.items)

    by_id = {item["patent_item_id"]: item for item in support.items}
    assert "ManipulationSkillAsset" in by_id["P0-02"]["supporting_objects"]
    assert "ExpertReviewRecord" in by_id["P0-02"]["supporting_objects"]
    assert "motion.tcp_trajectory" in by_id["P0-03"]["supporting_objects"]
    assert "SimulationEvidenceBundle" in by_id["P0-04"]["supporting_objects"]
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_strategic_skill_asset_alignment.py -q
```

Expected: FAIL because builders/dataclasses do not exist.

- [ ] **Step 3: Add dataclasses**

In `model.py`, add focused frozen dataclasses:

```python
@dataclass(frozen=True)
class SkillAssetEvidenceSourceCatalogEntry:
    source_type: SkillAssetSourceType
    role: str
    status: str
    expected_fields: tuple[str, ...]
    evidence_boundary: tuple[str, ...]
    next_step_recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)
```

Add similar dataclasses:

- `A01B06SkillAssetMapping`
- `ExpertReviewRecord`
- `A02ToA01ProductValidationHandoff`
- `IPDisclosureSupportItem`
- `IPDisclosureSupportMatrix`

Keep fields exactly aligned with the spec; use `dict[str, Any]` for mapping/snapshot fields to avoid over-modeling.

- [ ] **Step 4: Add strategic builders**

Create `strategic_alignment.py` with:

- `build_default_evidence_source_catalog(skill_asset)`
- `build_a01_b06_skill_asset_mapping(skill_asset)`
- `build_default_expert_review_record(skill_asset, robot_context, scene_context, feasibility_result)`
- `build_a02_to_a01_product_validation_handoff(skill_asset)`
- `build_ip_disclosure_support_matrix(skill_asset)`

Implementation rules:

- No B06 runtime import.
- No A01 connector.
- All boundaries include `not_ready_for_robot_execution` where execution could be implied.
- Expert review default status is `pending_expert_review`.
- Required real context has four explicit dict entries.

- [ ] **Step 5: Export builders and run tests**

Update `__init__.py` exports, then run:

```bash
cd weld-experience-engine
uv run pytest tests/test_strategic_skill_asset_alignment.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add weld-experience-engine/weldcore/skill_asset/model.py \
  weld-experience-engine/weldcore/skill_asset/strategic_alignment.py \
  weld-experience-engine/weldcore/skill_asset/__init__.py \
  weld-experience-engine/tests/test_strategic_skill_asset_alignment.py
git commit -m "feat: add strategic skill asset alignment artifacts"
```

---

### Task 3: Extend Default Asset Report to Twelve Artifacts

**Files:**
- Modify: `weld-experience-engine/weldcore/skill_asset/asset_report.py`
- Modify: `weld-experience-engine/tests/test_skill_asset_report.py`
- Test: `weld-experience-engine/tests/test_skill_asset_report.py`

- [ ] **Step 1: Write failing report tests**

Update `test_skill_asset_report_writes_seven_artifacts` to `test_skill_asset_report_writes_twelve_artifacts`.

Required assertions:

```python
assert payload["skill_asset"]["source_type"] == "simulation_only"
assert "evidence_source_catalog" in payload
assert "a01_b06_skill_asset_mapping" in payload
assert "expert_review_record" in payload
assert "a02_to_a01_product_validation_handoff" in payload
assert "ip_disclosure_support_matrix" in payload
assert payload["expert_review_record"]["review_status"] == "pending_expert_review"
assert "not_ready_for_robot_execution" in payload["a02_to_a01_product_validation_handoff"]["handoff_boundary"]
assert {item["patent_item_id"] for item in payload["ip_disclosure_support_matrix"]["items"]} == {
    "P0-02",
    "P0-03",
    "P0-04",
}
assert all(item["supporting_objects"] for item in payload["ip_disclosure_support_matrix"]["items"])
assert all(item["supporting_reports"] for item in payload["ip_disclosure_support_matrix"]["items"])
assert all(item["missing_real_world_evidence"] for item in payload["ip_disclosure_support_matrix"]["items"])
```

Expected filenames:

```python
(
    "skill_asset_report.json",
    "robot_body_asset_report.json",
    "robot_context_spec.json",
    "scene_context_asset_report.json",
    "skill_transfer_assessment.json",
    "robot_feasibility_result.json",
    "skill_asset_evidence_writeback_summary.json",
    "skill_asset_evidence_source_catalog.json",
    "a01_b06_skill_asset_mapping.json",
    "expert_review_record.json",
    "a02_to_a01_product_validation_handoff.json",
    "ip_disclosure_support_matrix.json",
)
```

- [ ] **Step 2: Run report tests to verify RED**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_skill_asset_report.py -q
```

Expected: FAIL because new payload keys/files are missing.

- [ ] **Step 3: Extend `run_skill_asset_report`**

Import strategic builders and build the five new artifacts after feasibility/assessment are available.

Payload keys:

- `evidence_source_catalog`
- `a01_b06_skill_asset_mapping`
- `expert_review_record`
- `a02_to_a01_product_validation_handoff`
- `ip_disclosure_support_matrix`

Write JSON files using existing `_write_json`.

- [ ] **Step 4: Run report tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_skill_asset_report.py -q
```

Expected: PASS.

- [ ] **Step 5: Run focused strategic/contextual tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_strategic_skill_asset_alignment.py tests/test_contextual_transfer_precheck.py tests/test_skill_asset_report.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add weld-experience-engine/weldcore/skill_asset/asset_report.py \
  weld-experience-engine/tests/test_skill_asset_report.py
git commit -m "feat: extend asset report for strategic alignment"
```

---

### Task 4: Rewrite Current Documentation Around Robot Skill Master Asset Foundation

**Files:**
- Modify: `README.md`
- Modify: `details.md`
- Modify: `weld-experience-engine/README.md`
- Modify: `docs/architecture/README.md`
- Modify: `docs/skill-assets/weld-skill-package.md`
- Later generated: `README.html`, `details.html`

- [ ] **Step 1: Rewrite root README source**

Replace the first definition with:

```markdown
A02 是公司机器人技能大师能力的焊接技能资产底座项目，目标是把焊接操作中的动作、意图、轨迹、姿态、工艺约束、证据边界、迁移契约和质量反馈沉淀为 `ManipulationSkillAsset`。项目通过仿真、真实机器人日志、人工示教、专家标注和智能焊接工站回采数据，形成可学习、可迁移、可评测、可审计的技能资产，为 A01 智能焊接工站和后续机器人执行验证提供能力底座。
```

Reorder sections to match spec:

1. 项目定位
2. 当前主链路
3. 核心对象
4. A01/B06/A02 接口
5. 当前可运行能力
6. 下一阶段任务
7. 边界
8. 验证命令
9. 历史能力索引

Keep commands accurate and update `asset_report` description to twelve JSON files.

- [ ] **Step 2: Update details.md**

Set update date to `2026-06-22`.

Add `### 2026-06-22` entry:

- strategic realignment to robot skill master welding skill asset foundation.
- evidence sources standardized.
- A01/B06 mapping artifacts added.
- ExpertReviewRecord and A02->A01/IP artifacts added.
- default report now twelve JSON artifacts.
- verification count to be filled after final test run.

Update “下一步建议” to:

1. Replace nominal context with real TCP calibration and workpiece frame measurement records.
2. Use B06 Physical AI Package / A01 H300 samples as real or desensitized evidence.
3. Run expert review record workflow.
4. Feed A02 outputs back to A01 product validation.
5. Prepare P0-02/P0-03/P0-04 evidence packs.

- [ ] **Step 3: Update engine README**

Describe `weldcore.skill_asset` as the runnable engine for the welding skill asset foundation.

Update report sentence to twelve JSON artifacts and preserve boundaries:

- not real robot executable
- not real welding quality validation
- not WPS/PQR
- not final simulator selection

- [ ] **Step 4: Update current architecture and skill asset docs**

In `docs/architecture/README.md`:

- Replace “焊接技能大师平台” with “机器人技能大师能力的焊接技能资产底座”.
- Make `ManipulationSkillAsset` the mainline object.
- Mention `WeldSkillPackage` as historical/compatibility layer.

In `docs/skill-assets/weld-skill-package.md`:

- Reposition `WeldSkillPackage` as legacy compatibility / skill package facade.
- Point current canonical object to `ManipulationSkillAsset`.
- Remove “可执行” claim unless explicitly bounded as not robot execution.

- [ ] **Step 5: Commit Markdown docs before HTML generation**

```bash
git add README.md details.md weld-experience-engine/README.md \
  docs/architecture/README.md docs/skill-assets/weld-skill-package.md
git commit -m "docs: align A02 positioning with robot skill master strategy"
```

---

### Task 5: Refresh HTML, Verify, Review, and Finalize

**Files:**
- Modify: `README.html`
- Modify: `details.html`
- Possibly modify docs if verification finds stale wording.

- [ ] **Step 1: Regenerate HTML reading copies**

Run this exact command from repository root, preserving the current `README.html` style:

```bash
python - <<'PY'
from __future__ import annotations

import html
import re
from pathlib import Path

STYLE_RE = re.compile(r"<style>(.*?)</style>", re.S)
STYLE = STYLE_RE.search(Path("README.html").read_text()).group(1)


def inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', escaped)
    return escaped


def markdown_body(markdown: str) -> str:
    lines = markdown.splitlines()
    out: list[str] = []
    paragraph: list[str] = []
    list_open = False
    ordered_open = False
    code_open = False
    code_lines: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            out.append(f"    <p>{inline(' '.join(paragraph))}</p>")
            paragraph = []

    def close_lists() -> None:
        nonlocal list_open, ordered_open
        if list_open:
            out.append("    </ul>")
            list_open = False
        if ordered_open:
            out.append("    </ol>")
            ordered_open = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_paragraph()
            close_lists()
            if code_open:
                out.append(f"    <pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
                code_lines = []
                code_open = False
            else:
                code_open = True
            continue
        if code_open:
            code_lines.append(line)
            continue
        if not stripped:
            flush_paragraph()
            close_lists()
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            close_lists()
            out.append(f"    <h1>{inline(stripped[2:])}</h1>")
        elif stripped.startswith("## "):
            flush_paragraph()
            close_lists()
            out.append(f"    <h2>{inline(stripped[3:])}</h2>")
        elif stripped.startswith("### "):
            flush_paragraph()
            close_lists()
            out.append(f"    <h3>{inline(stripped[4:])}</h3>")
        elif stripped.startswith("- "):
            flush_paragraph()
            if ordered_open:
                out.append("    </ol>")
                ordered_open = False
            if not list_open:
                out.append("    <ul>")
                list_open = True
            out.append(f"      <li>{inline(stripped[2:])}</li>")
        elif re.match(r"^\d+\. ", stripped):
            flush_paragraph()
            if list_open:
                out.append("    </ul>")
                list_open = False
            if not ordered_open:
                out.append("    <ol>")
                ordered_open = True
            out.append(f"      <li>{inline(re.sub(r'^\d+\. ', '', stripped))}</li>")
        else:
            paragraph.append(stripped)
    flush_paragraph()
    close_lists()
    return "\n".join(out)


def render(source: str, target: str, title: str) -> None:
    body = markdown_body(Path(source).read_text())
    Path(target).write_text(
        f"""<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{html.escape(title)}</title>
  <style>{STYLE}</style>
</head>
<body>
  <main>
    <div class=\"meta\">HTML 阅读版；维护源：<a href=\"{source}\">{source}</a></div>
{body}
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )


render("README.md", "README.html", "A02 机器人技能大师焊接技能资产底座")
render("details.md", "details.html", "A02 项目进展记录")
PY
```

- [ ] **Step 2: Verify strategic wording in docs**

Run:

```bash
rg -n "机器人技能大师能力|焊接技能资产底座|A01|B06|Physical AI Package|P0-02|P0-03|P0-04|ready_for_expert_review|ready_for_robot_execution|真实机器人可执行|真实焊接质量验证|WPS/PQR|最终仿真器选型" \
  README.md details.md weld-experience-engine/README.md docs/architecture/README.md docs/skill-assets/weld-skill-package.md README.html details.html
```

Expected: strategic terms are present in current docs and HTML. Confirm `docs/architecture/README.md` and `docs/skill-assets/weld-skill-package.md` no longer present A02 as a standalone platform.

- [ ] **Step 3: Run full tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q
```

Expected: all tests pass. Update `details.md` and regenerated `details.html` with the exact count if it changes from `390 passed`.

- [ ] **Step 4: Run default report and inspect artifact count/status**

Run:

```bash
cd weld-experience-engine
uv run python -m weldcore.skill_asset.asset_report --outdir /tmp/a02-strategic-asset-report
python - <<'PY'
import json
from pathlib import Path
out = Path('/tmp/a02-strategic-asset-report')
files = sorted(p.name for p in out.glob('*.json'))
payload = json.loads((out / 'expert_review_record.json').read_text())
print('artifact_count', len(files))
print('review_status', payload['review_status'])
print('required_real_context', [item['field'] for item in payload['required_real_context']])
PY
```

Expected:

- `artifact_count 12`
- `review_status pending_expert_review`
- required context includes the four explicit fields.

- [ ] **Step 5: Commit HTML and verification-count updates**

```bash
git add README.md details.md README.html details.html weld-experience-engine/README.md \
  docs/architecture/README.md docs/skill-assets/weld-skill-package.md
git commit -m "docs: refresh strategic alignment reading copies"
```

Skip this commit if Task 4 commit already included final verification count and HTML generation; keep commits meaningful and avoid empty commits.

- [ ] **Step 6: Request final code review**

Use superpowers:requesting-code-review. Provide:

- base: `origin/main`
- head: current branch HEAD
- spec: `docs/superpowers/specs/2026-06-22-strategic-skill-asset-realignment-design.md`
- plan: this file
- verification results

Fix Critical/Important findings before continuing.

- [ ] **Step 7: Final commit/status check**

Run:

```bash
git status --short --branch
git log --oneline --max-count=8
```

Expected: clean worktree on `strategic-skill-asset-realignment`.
