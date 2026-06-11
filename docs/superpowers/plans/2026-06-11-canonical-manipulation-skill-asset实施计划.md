# Canonical Manipulation Skill Asset Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立 canonical manipulation skill asset 本体，并把真实 URDF 协作臂资产作为第一类 RobotBodyAsset / transfer context 接入系统。

**Architecture:** 扩展现有 `weldcore.skill_asset` 命名空间，不破坏 `WeldSkillPackage` / `package_from_sample` 公开入口。新增 focused modules：`model.py` 保存 canonical dataclasses，`builders.py` 从 `SimulationEvidenceBundle` 构建 skill asset，`urdf.py` 解析 URDF 为 robot body asset，`assessment.py` 生成 transfer assessment，`asset_report.py` 输出轻量 JSON 报告。

**Tech Stack:** Python dataclasses、标准库 `xml.etree.ElementTree`、现有 `SimulationEvidenceBundle` / `SimulationPathPoint` / JSON artifact helpers、pytest。

---

## File Structure

- Create: `weld-experience-engine/weldcore/skill_asset/model.py`
  - Defines `ManipulationSkillAsset`, `SkillAssetEvidence`, `SkillTransferContract`, `RobotBodyAsset`, `RobotJointLimit`, `SkillTransferAssessment`.
  - Owns serialization helpers and Literal status types.
- Create: `weld-experience-engine/weldcore/skill_asset/builders.py`
  - Converts `SimulationEvidenceBundle` into `ManipulationSkillAsset`.
- Create: `weld-experience-engine/weldcore/skill_asset/urdf.py`
  - Parses URDF + mesh references into `RobotBodyAsset`.
- Create: `weld-experience-engine/weldcore/skill_asset/assessment.py`
  - Builds `SkillTransferAssessment` from `ManipulationSkillAsset + RobotBodyAsset`.
- Create: `weld-experience-engine/weldcore/skill_asset/asset_report.py`
  - CLI/report writer for `skill_asset_report.json`, `robot_body_asset_report.json`, `skill_transfer_assessment.json`.
- Modify: `weld-experience-engine/weldcore/skill_asset/__init__.py`
  - Preserve existing `WeldSkillPackage` and `package_from_sample` exports.
  - Export new canonical skill asset APIs.
- Create: `weld-experience-engine/tests/test_canonical_skill_asset.py`
  - Tests dataclasses, simulation bundle builder, transfer assessment.
- Create: `weld-experience-engine/tests/test_robot_body_asset_urdf.py`
  - Tests real URDF parse result: 7 links, 6 revolute joints, 33 unique mesh files, 66 mesh references.
- Create: `weld-experience-engine/tests/test_skill_asset_report.py`
  - Tests CLI/report artifacts and JSON status.
- Modify: `README.md`, `details.md`, `README.html`, `details.html`, `weld-experience-engine/README.md`
  - Reframe current project line as canonical skill asset first.
  - Document URDF as RobotBodyAsset / transfer context, not skill本体.
  - Add `asset_report` CLI.
- Add: `docs/real-urdf/robot.urdf`, `docs/real-urdf/meshes/*.stl`
  - Commit user-uploaded real robot body asset. Delete and do not commit `.DS_Store`.

## Task 1: Core Skill Asset Models

**Files:**
- Create: `weld-experience-engine/weldcore/skill_asset/model.py`
- Modify: `weld-experience-engine/weldcore/skill_asset/__init__.py`
- Test: `weld-experience-engine/tests/test_canonical_skill_asset.py`

- [ ] **Step 1: Write failing serialization tests**

Add tests:

```python
from weldcore.skill_asset import (
    ManipulationSkillAsset,
    SkillAssetEvidence,
    SkillTransferContract,
)


def test_manipulation_skill_asset_serializes_core_contract():
    evidence = SkillAssetEvidence(
        source_type="simulation",
        source_id="bundle-1",
        adapter_name="simlite_reference",
        status="completed",
        metrics={"path_continuity": 1.0},
        artifact_refs={"bundle": "memory://bundle-1"},
        evidence_boundary=("simulation_only", "not_ready_for_robot_execution"),
        review_status="not_reviewed",
    )
    contract = SkillTransferContract(
        required_robot_context=("robot_body", "tcp_calibration", "workpiece_frame"),
        required_scene_context=("scene_context_asset",),
        required_checks=(
            "reachability",
            "collision",
            "joint_limits",
            "tcp_calibration",
            "workpiece_frame",
            "path_continuity",
            "orientation_feasibility",
            "expert_review",
        ),
        transfer_status="requires_contextual_precheck",
        blocking_gaps=(),
        evidence_notes=("not_real_robot_validated",),
    )
    asset = ManipulationSkillAsset(
        asset_id="skill-asset-1",
        name="Long straight tracking",
        domain="welding",
        skill_type="seam_tracking",
        source_type="simulation",
        source_refs={"bundle_id": "bundle-1"},
        intent={"task": "follow seam"},
        motion={"tcp_trajectory": [], "tool_orientation": []},
        constraints={"path_continuity": True},
        context_requirements={"tcp_frame": "torch_tcp"},
        evidence=evidence,
        transfer_contract=contract,
        quality_boundary=("not_real_welding_quality_validation", "not_WPS_PQR"),
        version="v0.1",
    )

    data = asset.to_dict()

    assert data["asset_id"] == "skill-asset-1"
    assert data["evidence"]["source_type"] == "simulation"
    assert "expert_review" in data["transfer_contract"]["required_checks"]
    assert data["transfer_contract"]["transfer_status"] == "requires_contextual_precheck"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_canonical_skill_asset.py::test_manipulation_skill_asset_serializes_core_contract -q
```

Expected: FAIL with import error for new classes.

- [ ] **Step 3: Implement dataclasses**

Create `model.py` with frozen dataclasses and `_model_dict` / `_jsonable` following existing project patterns. Literal values:

```python
SkillAssetSourceType = Literal[
    "simulation",
    "real_robot_log",
    "human_demonstration",
    "expert_annotation",
]
SkillAssetReviewStatus = Literal["not_reviewed", "expert_review_candidate", "reviewed"]
SkillTransferContractStatus = Literal["requires_contextual_precheck", "blocked"]
SkillTransferAssessmentStatus = Literal[
    "ready_for_contextual_precheck",
    "blocked_by_missing_skill_motion",
    "blocked_by_robot_body_asset_issue",
]
```

Export the new classes from `skill_asset/__init__.py` while keeping:

```python
from .package import WeldSkillPackage, package_from_sample
```

- [ ] **Step 4: Run model test**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_canonical_skill_asset.py::test_manipulation_skill_asset_serializes_core_contract -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
git add weld-experience-engine/weldcore/skill_asset/model.py \
  weld-experience-engine/weldcore/skill_asset/__init__.py \
  weld-experience-engine/tests/test_canonical_skill_asset.py
git commit -m "feat: add canonical manipulation skill asset models"
```

## Task 2: Simulation Evidence to Skill Asset Builder

**Files:**
- Create: `weld-experience-engine/weldcore/skill_asset/builders.py`
- Modify: `weld-experience-engine/weldcore/skill_asset/__init__.py`
- Test: `weld-experience-engine/tests/test_canonical_skill_asset.py`

- [ ] **Step 1: Write failing builder test**

Append:

```python
from weldcore.simulation_bakeoff import (
    build_simulation_evidence_bundle,
    default_simulation_task_specs,
    run_simlite_reference,
)
from weldcore.skill_asset import build_manipulation_skill_asset_from_simulation_bundle


def test_simulation_evidence_bundle_builds_manipulation_skill_asset():
    task_spec = default_simulation_task_specs()[0]
    bundle = build_simulation_evidence_bundle(task_spec, run_simlite_reference(task_spec))

    asset = build_manipulation_skill_asset_from_simulation_bundle(bundle)
    data = asset.to_dict()

    assert asset.domain == "welding"
    assert asset.source_type == "simulation"
    assert asset.source_refs["bundle_id"] == bundle.bundle_id
    assert asset.motion["trajectory_point_count"] == len(bundle.adapter_result.tcp_trajectory)
    assert asset.motion["orientation_point_count"] == len(bundle.adapter_result.tool_orientation)
    assert asset.context_requirements["tcp_frame"] == task_spec.tcp_frame
    assert asset.transfer_contract.transfer_status == "requires_contextual_precheck"
    assert asset.transfer_contract.required_checks == (
        "reachability",
        "collision",
        "joint_limits",
        "tcp_calibration",
        "workpiece_frame",
        "path_continuity",
        "orientation_feasibility",
        "expert_review",
    )
    assert "simulation_only" in asset.evidence.evidence_boundary
    assert "not_ready_for_robot_execution" in asset.quality_boundary
    assert data["evidence"]["review_status"] == "not_reviewed"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_canonical_skill_asset.py::test_simulation_evidence_bundle_builds_manipulation_skill_asset -q
```

Expected: FAIL with missing builder.

- [ ] **Step 3: Implement builder**

Implement:

```python
def build_manipulation_skill_asset_from_simulation_bundle(
    bundle: SimulationEvidenceBundle,
) -> ManipulationSkillAsset:
    ...
```

Rules:
- `asset_id = f"skill-asset-{bundle.task_spec.task_id}"`
- `domain = "welding"`
- `skill_type = bundle.task_spec.unit_id`
- `source_refs` contains `bundle_id`, `task_id`, `dataset_id`, `run_record_id`
- `motion` contains serialized TCP and orientation points, point counts, metrics
- `context_requirements` contains `tcp_frame`, `robot_body_required=True`, `workpiece_frame_required=True`
- `quality_boundary` contains `not_real_welding_quality_validation`, `not_WPS_PQR`, `not_ready_for_robot_execution`

- [ ] **Step 4: Run builder tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_canonical_skill_asset.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
git add weld-experience-engine/weldcore/skill_asset/builders.py \
  weld-experience-engine/weldcore/skill_asset/__init__.py \
  weld-experience-engine/tests/test_canonical_skill_asset.py
git commit -m "feat: build skill assets from simulation evidence"
```

## Task 3: URDF Robot Body Asset Parser

**Files:**
- Create: `weld-experience-engine/weldcore/skill_asset/urdf.py`
- Modify: `weld-experience-engine/weldcore/skill_asset/model.py`
- Modify: `weld-experience-engine/weldcore/skill_asset/__init__.py`
- Test: `weld-experience-engine/tests/test_robot_body_asset_urdf.py`
- Add: `docs/real-urdf/robot.urdf`, `docs/real-urdf/meshes/*.stl`

- [ ] **Step 1: Write failing real URDF test**

```python
from pathlib import Path

from weldcore.skill_asset import build_robot_body_asset_from_urdf


ROOT = Path(__file__).resolve().parents[2]
URDF = ROOT / "docs" / "real-urdf" / "robot.urdf"


def test_real_urdf_builds_robot_body_asset():
    asset = build_robot_body_asset_from_urdf(URDF)

    assert asset.robot_model == "generated_robot"
    assert asset.robot_family == "six_axis_collaborative_welding_arm_candidate"
    assert asset.validation_status == "usable_as_robot_body_context"
    assert asset.joint_count == 6
    assert asset.revolute_joint_count == 6
    assert len(asset.link_names) == 7
    assert len(asset.mesh_files) == 33
    assert asset.visual_mesh_count == 33
    assert asset.collision_mesh_count == 33
    assert len(asset.mesh_references) == 66
    assert asset.validation_issues == ()
    assert "not_real_robot_validated" in asset.evidence_boundary
    assert all(limit.lower == -1.57 and limit.upper == 1.57 for limit in asset.joint_limits)
```

- [ ] **Step 2: Write failing negative URDF tests**

Append:

```python
def _write_urdf(tmp_path, text, *, mesh_name="part.stl"):
    root = tmp_path / "robot.urdf"
    mesh_dir = tmp_path / "meshes"
    mesh_dir.mkdir()
    (mesh_dir / mesh_name).write_text("solid placeholder\nendsolid placeholder\n")
    root.write_text(text, encoding="utf-8")
    return root


def test_urdf_blocks_missing_mesh_reference(tmp_path):
    urdf = tmp_path / "robot.urdf"
    urdf.write_text(
        '<robot name="bad"><link name="base"><visual><geometry>'
        '<mesh filename="meshes/missing.stl"/></geometry></visual></link></robot>',
        encoding="utf-8",
    )

    asset = build_robot_body_asset_from_urdf(urdf)

    assert asset.validation_status == "blocked_by_asset_issue"
    assert "missing_mesh:meshes/missing.stl" in asset.validation_issues


def test_urdf_blocks_revolute_joint_without_limit(tmp_path):
    urdf = _write_urdf(
        tmp_path,
        '<robot name="bad">'
        '<link name="a"/><link name="b"/>'
        '<joint name="j1" type="revolute"><parent link="a"/><child link="b"/></joint>'
        '</robot>',
    )

    asset = build_robot_body_asset_from_urdf(urdf)

    assert asset.validation_status == "blocked_by_asset_issue"
    assert "missing_joint_limit:j1" in asset.validation_issues


def test_urdf_blocks_bad_xml(tmp_path):
    urdf = tmp_path / "robot.urdf"
    urdf.write_text("<robot", encoding="utf-8")

    asset = build_robot_body_asset_from_urdf(urdf)

    assert asset.validation_status == "blocked_by_asset_issue"
    assert any(issue.startswith("xml_parse_error:") for issue in asset.validation_issues)


def test_urdf_blocks_fewer_than_six_revolute_joints(tmp_path):
    urdf = _write_urdf(
        tmp_path,
        '<robot name="few">'
        '<link name="a"/><link name="b"/>'
        '<joint name="j1" type="revolute"><parent link="a"/><child link="b"/>'
        '<limit lower="-1" upper="1" effort="1" velocity="1"/></joint>'
        '</robot>',
    )

    asset = build_robot_body_asset_from_urdf(urdf)

    assert asset.validation_status == "blocked_by_asset_issue"
    assert "fewer_than_six_revolute_joints" in asset.validation_issues
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_robot_body_asset_urdf.py -q
```

Expected: FAIL with missing parser / model fields.

- [ ] **Step 4: Implement `RobotJointLimit` and parser**

Add to `model.py`:

```python
RobotBodyAssetValidationStatus = Literal[
    "usable_as_robot_body_context",
    "blocked_by_asset_issue",
]

@dataclass(frozen=True)
class RobotJointLimit:
    joint_name: str
    lower: float
    upper: float
    effort: float | None
    velocity: float | None
```

Add `RobotBodyAsset.mesh_references`.

Implement `build_robot_body_asset_from_urdf(path: str | Path)`.

Validation:
- XML parse failure -> `blocked_by_asset_issue`
- missing referenced mesh -> validation issue `missing_mesh:<path>`
- revolute joint without `<limit>` -> validation issue `missing_joint_limit:<joint_name>`
- fewer than 6 revolute joints -> `fewer_than_six_revolute_joints`
- usable only when no validation issues.

- [ ] **Step 5: Run URDF tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_robot_body_asset_urdf.py -q
```

Expected: PASS.

- [ ] **Step 6: Delete `.DS_Store` and verify it is absent**

Run:

```bash
cd "$(git rev-parse --show-toplevel)"
test -d docs/real-urdf
rm -f docs/real-urdf/.DS_Store
test -z "$(find docs/real-urdf -name .DS_Store -print -quit)"
```

Expected: command exits 0; no `.DS_Store` remains in `docs/real-urdf`.

- [ ] **Step 7: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
git add docs/real-urdf/robot.urdf docs/real-urdf/meshes \
  weld-experience-engine/weldcore/skill_asset/model.py \
  weld-experience-engine/weldcore/skill_asset/urdf.py \
  weld-experience-engine/weldcore/skill_asset/__init__.py \
  weld-experience-engine/tests/test_robot_body_asset_urdf.py
git commit -m "feat: add real URDF robot body asset"
```

## Task 4: Skill Transfer Assessment

**Files:**
- Create: `weld-experience-engine/weldcore/skill_asset/assessment.py`
- Modify: `weld-experience-engine/weldcore/skill_asset/__init__.py`
- Test: `weld-experience-engine/tests/test_canonical_skill_asset.py`

- [ ] **Step 1: Write failing assessment tests**

Append:

```python
from pathlib import Path

from dataclasses import replace

from weldcore.skill_asset import (
    build_robot_body_asset_from_urdf,
    build_skill_transfer_assessment,
)


ROOT = Path(__file__).resolve().parents[2]
URDF = ROOT / "docs" / "real-urdf" / "robot.urdf"


def _default_skill_asset():
    task_spec = default_simulation_task_specs()[0]
    bundle = build_simulation_evidence_bundle(task_spec, run_simlite_reference(task_spec))
    return build_manipulation_skill_asset_from_simulation_bundle(bundle)


def test_skill_and_robot_body_are_ready_for_contextual_precheck():
    skill = _default_skill_asset()
    robot = build_robot_body_asset_from_urdf(URDF)

    assessment = build_skill_transfer_assessment(skill, robot)

    assert assessment.status == "ready_for_contextual_precheck"
    assert assessment.blocking_gaps == ()
    assert assessment.passed_checks == ("skill_motion_present", "robot_body_asset_usable")
    assert assessment.warning_gaps == (
        "requires_robot_context_spec",
        "requires_tcp_calibration",
        "requires_workpiece_frame",
        "requires_scene_context_asset",
    )
    assert "requires_tcp_calibration" in assessment.warning_gaps
    assert "requires_scene_context_asset" in assessment.warning_gaps
    assert assessment.next_step_recommendation == (
        "Bind RobotContextSpec and SceneContextAsset before any IK, collision, "
        "or real robot validation claim."
    )
    assert "not_ready_for_robot_execution" in assessment.evidence_boundary


def test_transfer_assessment_blocks_missing_skill_motion():
    skill = replace(_default_skill_asset(), motion={})
    robot = build_robot_body_asset_from_urdf(URDF)

    assessment = build_skill_transfer_assessment(skill, robot)

    assert assessment.status == "blocked_by_missing_skill_motion"
    assert "missing_tcp_trajectory" in assessment.blocking_gaps


def test_transfer_assessment_blocks_robot_body_asset_issue():
    skill = _default_skill_asset()
    robot = replace(
        build_robot_body_asset_from_urdf(URDF),
        validation_status="blocked_by_asset_issue",
        validation_issues=("missing_mesh:meshes/missing.stl",),
    )

    assessment = build_skill_transfer_assessment(skill, robot)

    assert assessment.status == "blocked_by_robot_body_asset_issue"
    assert "robot_body_asset_issue" in assessment.blocking_gaps
    assert "missing_mesh:meshes/missing.stl" in assessment.warning_gaps
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_canonical_skill_asset.py -q
```

Expected: FAIL with missing assessment function.

- [ ] **Step 3: Implement assessment**

Implement:

```python
def build_skill_transfer_assessment(
    skill_asset: ManipulationSkillAsset,
    robot_body_asset: RobotBodyAsset,
) -> SkillTransferAssessment:
    ...
```

Rules:
- Missing `motion["tcp_trajectory"]` or zero `trajectory_point_count` -> `blocked_by_missing_skill_motion`.
- `robot_body_asset.validation_status != "usable_as_robot_body_context"` -> `blocked_by_robot_body_asset_issue`.
- Otherwise -> `ready_for_contextual_precheck`.
- Default warning gaps:
  - `requires_robot_context_spec`
  - `requires_tcp_calibration`
  - `requires_workpiece_frame`
  - `requires_scene_context_asset`
- Never output `ready_for_robot_execution`.

- [ ] **Step 4: Run assessment tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_canonical_skill_asset.py tests/test_robot_body_asset_urdf.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
git add weld-experience-engine/weldcore/skill_asset/assessment.py \
  weld-experience-engine/weldcore/skill_asset/__init__.py \
  weld-experience-engine/tests/test_canonical_skill_asset.py
git commit -m "feat: assess skill transfer context readiness"
```

## Task 5: Skill Asset Report CLI

**Files:**
- Create: `weld-experience-engine/weldcore/skill_asset/asset_report.py`
- Modify: `weld-experience-engine/weldcore/skill_asset/__init__.py` if exports needed
- Test: `weld-experience-engine/tests/test_skill_asset_report.py`

- [ ] **Step 1: Write failing CLI/report test**

```python
import json

from weldcore.skill_asset.asset_report import run_skill_asset_report


def test_skill_asset_report_writes_three_artifacts(tmp_path):
    payload = run_skill_asset_report(tmp_path)

    assert payload["skill_asset"]["domain"] == "welding"
    assert payload["robot_body_asset"]["validation_status"] == "usable_as_robot_body_context"
    assert payload["transfer_assessment"]["status"] == "ready_for_contextual_precheck"
    assert (tmp_path / "skill_asset_report.json").exists()
    assert (tmp_path / "robot_body_asset_report.json").exists()
    assert (tmp_path / "skill_transfer_assessment.json").exists()
    restored = json.loads((tmp_path / "skill_transfer_assessment.json").read_text())
    assert restored["status"] == "ready_for_contextual_precheck"


def test_skill_asset_report_main_prints_json(tmp_path, capsys):
    from weldcore.skill_asset import asset_report

    asset_report.main(["--outdir", str(tmp_path)])

    output = json.loads(capsys.readouterr().out)
    assert output["transfer_assessment"]["status"] == "ready_for_contextual_precheck"
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_skill_asset_report.py -q
```

Expected: FAIL with missing module.

- [ ] **Step 3: Implement CLI/report**

`run_skill_asset_report(outdir, urdf_path=None)` should:
- Use first `default_simulation_task_specs()` task and `run_simlite_reference()`.
- Build evidence bundle.
- Build `ManipulationSkillAsset`.
- Parse `Path(__file__).resolve().parents[3] / "docs/real-urdf/robot.urdf"` unless `urdf_path` passed. This is the repository root from `weldcore/skill_asset/asset_report.py`, so the default works when commands run inside `weld-experience-engine/`.
- Build `SkillTransferAssessment`.
- Write three JSON artifacts using existing JSON helper or local `json.dumps`.
- Return combined payload.

`main(argv=None)` should support:

```text
--outdir artifacts/skill-assets/canonical
--urdf-path ../docs/real-urdf/robot.urdf
```

- [ ] **Step 4: Run CLI tests and smoke command**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_skill_asset_report.py -q
uv run python -m weldcore.skill_asset.asset_report --outdir /tmp/weld-skill-asset-report
```

Expected: tests PASS; CLI prints JSON with `ready_for_contextual_precheck`.

- [ ] **Step 5: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
git add weld-experience-engine/weldcore/skill_asset/asset_report.py \
  weld-experience-engine/tests/test_skill_asset_report.py
git commit -m "feat: add canonical skill asset report"
```

## Task 6: Documentation Updates

**Files:**
- Modify: `README.md`
- Modify: `details.md`
- Modify: `README.html`
- Modify: `details.html`
- Modify: `weld-experience-engine/README.md`

- [ ] **Step 1: Update Markdown docs**

Update root `README.md`:
- Current positioning: canonical manipulation skill asset 本体优先。
- Add chain:

```text
ManipulationSkillAsset
<- SimulationEvidenceBundle
<- real robot log later
<- human demonstration later

ManipulationSkillAsset + RobotBodyAsset(URDF)
-> SkillTransferAssessment
-> RobotContextSpec / SceneContextAsset later
```

- Add completed capability:
  - `ManipulationSkillAsset`
  - `RobotBodyAsset`
  - `SkillTransferAssessment`
  - real URDF asset: 7 links / 6 revolute joints / 33 mesh files / 66 mesh references
- Add CLI command:

```bash
uv run python -m weldcore.skill_asset.asset_report \
  --outdir artifacts/skill-assets/canonical
```

Update `details.md`:
- `更新时间：2026-06-11`
- Add 2026-06-11 entry for canonical skill asset 本体。
- Update next stage: introduce `SceneContextAsset` or connect `SkillTransferAssessment` to `RobotFeasibilityResult`.
- Update verification count after full tests.

Update `weld-experience-engine/README.md`:
- Current core model should mention `ManipulationSkillAsset` as canonical asset instance, while preserving `SkillDataset -> WeldSkillPackage`.
- Add `asset_report` command and boundary.

- [ ] **Step 2: Refresh HTML reading copies**

Run this exact repository-root command to refresh `README.html` and `details.html` with the existing HTML shell/style:

```bash
cd "$(git rev-parse --show-toplevel)"
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
        elif re.match(r"^\d+\\. ", stripped):
            flush_paragraph()
            if list_open:
                out.append("    </ul>")
                list_open = False
            if not ordered_open:
                out.append("    <ol>")
                ordered_open = True
            out.append(f"      <li>{inline(re.sub(r'^\\d+\\. ', '', stripped))}</li>")
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


render("README.md", "README.html", "Physical AI 焊接技能资产底座")
render("details.md", "details.html", "焊接技能大师平台项目进展记录")
PY
```

- [ ] **Step 3: Verify docs mention required terms**

Run:

```bash
rg -n "ManipulationSkillAsset|RobotBodyAsset|SkillTransferAssessment|asset_report|real-urdf|33.*mesh|66.*mesh|ready_for_contextual_precheck" README.md details.md weld-experience-engine/README.md README.html details.html
```

Expected: all required terms appear in appropriate docs.

- [ ] **Step 4: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
git add README.md README.html details.md details.html weld-experience-engine/README.md
git commit -m "docs: reframe project around canonical skill assets"
```

## Task 7: Final Verification and Review

**Files:**
- No planned source changes unless review finds issues.

- [ ] **Step 1: Run focused tests**

```bash
cd weld-experience-engine
uv run pytest tests/test_canonical_skill_asset.py tests/test_robot_body_asset_urdf.py tests/test_skill_asset_report.py -q
```

Expected: PASS.

- [ ] **Step 2: Run full tests**

```bash
cd weld-experience-engine
uv run pytest -q
rm -f uv.lock
```

Expected: all tests PASS.

- [ ] **Step 3: Run CLI smoke**

```bash
cd weld-experience-engine
rm -rf /tmp/weld-skill-asset-report
uv run python -m weldcore.skill_asset.asset_report --outdir /tmp/weld-skill-asset-report
rm -f uv.lock
```

Expected output:
- `skill_asset.domain == "welding"`
- `robot_body_asset.validation_status == "usable_as_robot_body_context"`
- `transfer_assessment.status == "ready_for_contextual_precheck"`

- [ ] **Step 4: Git hygiene**

```bash
git diff --check
git status --short
```

Expected:
- no whitespace errors
- no `uv.lock`
- `.DS_Store` not tracked
- `find docs/real-urdf -name .DS_Store -print -quit` prints nothing

- [ ] **Step 5: Request code review subagent**

Ask a review-only subagent to inspect:
- skill asset model boundaries
- URDF parser correctness
- assessment status semantics
- docs route alignment

Fix any blocking issues and rerun focused/full tests.

## Task 8: PR, Merge, Cleanup

**Files:**
- No file edits unless merge/review requires.

- [ ] **Step 1: Push branch**

```bash
git push -u origin codex/canonical-skill-asset
```

- [ ] **Step 2: Create PR**

Title:

```text
Add canonical manipulation skill asset core
```

Body should summarize:
- `ManipulationSkillAsset` as core asset 本体
- URDF -> `RobotBodyAsset`
- transfer assessment status
- docs update
- verification commands and results

- [ ] **Step 3: Merge PR remotely**

Use `gh pr merge` if possible. If local worktree branch constraints block local checkout, confirm PR state and use GitHub API / CLI path that merges remotely without corrupting local state.

- [ ] **Step 4: Clean branches and worktree**

After merge, run these from the main worktree:

```bash
cd "/Users/lloyd/Nutstore Files/Nutstore/CavLAB/P00-Projects/分类0-核心研发/A02-焊接技能大师平台"
git fetch origin
git pull --ff-only
git worktree remove /Users/lloyd/.config/superpowers/worktrees/A02-焊接技能大师平台/codex-canonical-skill-asset
git branch -D codex/canonical-skill-asset
git push origin --delete codex/canonical-skill-asset  # if PR merge did not delete it
```

- [ ] **Step 5: Final main verification**

Run on main:

```bash
cd weld-experience-engine
uv run pytest -q
rm -f uv.lock
uv run python -m weldcore.skill_asset.asset_report --outdir /tmp/weld-skill-asset-report-main
rm -f uv.lock
```

Expected: full tests PASS and CLI status `ready_for_contextual_precheck`.
