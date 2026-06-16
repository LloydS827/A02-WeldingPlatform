# Contextual Transfer Precheck Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `ManipulationSkillAsset + RobotBodyAsset` 从第一层 `ready_for_contextual_precheck` 推进到可复跑的 `RobotContextSpec + SceneContextAsset + lightweight RobotFeasibilityResult` 预检闭环，并把 modeled tasks / 1000 next-batch 重新纳入 skill asset evidence 口径。

**Architecture:** canonical skill asset 相关对象继续放在 `weldcore.skill_asset`；复用现有 `weldcore.robot_process.RobotContextSpec` 和 `RobotFeasibilityResult`，只补一个 `RobotBodyAsset -> RobotContextSpec` 绑定构建器。`SkillTransferAssessment` 保持旧版两输入兼容，同时新增显式 contextual assessment 路径；`asset_report` 输出七个 JSON artifact，但所有结果仍带 `not_ready_for_robot_execution` 边界。

**Tech Stack:** Python dataclasses、现有 `SimulationPathPoint` / `SimulationTaskSpec`、`RobotContextSpec` / `RobotFeasibilityResult`、标准库 JSON、pytest、Markdown/HTML 文档。

---

## File Structure

- Modify: `weld-experience-engine/weldcore/skill_asset/model.py`
  - Add `SceneContextAsset`, `SceneContextAssetValidationStatus`, `SkillAssetEvidenceWritebackSummary`, extended `SkillTransferAssessmentStatus`.
- Create: `weld-experience-engine/weldcore/skill_asset/context.py`
  - Build default `SceneContextAsset` from a `ManipulationSkillAsset` and optional source refs.
  - Build `RobotFeasibilityResult` from `ManipulationSkillAsset + RobotContextSpec + SceneContextAsset`.
  - Build `SkillAssetEvidenceWritebackSummary`.
- Modify: `weld-experience-engine/weldcore/robot_process/feasibility.py`
  - Add `build_robot_context_from_body_asset`.
- Modify: `weld-experience-engine/weldcore/robot_process/__init__.py`
  - Export `build_robot_context_from_body_asset`.
- Modify: `weld-experience-engine/weldcore/skill_asset/assessment.py`
  - Extend `build_skill_transfer_assessment` signature with optional `robot_context`, `scene_context`, `feasibility_result`, `contextual_precheck_requested`.
  - Preserve old two-input result.
- Modify: `weld-experience-engine/weldcore/skill_asset/asset_report.py`
  - Write seven artifacts: skill asset, robot body asset, robot context spec, scene context asset, transfer assessment, robot feasibility result, evidence writeback summary.
- Modify: `weld-experience-engine/weldcore/skill_asset/__init__.py`
  - Export new dataclasses and builders.
- Test: `weld-experience-engine/tests/test_contextual_transfer_precheck.py`
  - New focused tests for scene context, robot context binding, contextual feasibility, assessment state priority, evidence writeback summary.
- Modify: `weld-experience-engine/tests/test_skill_asset_report.py`
  - Update report artifact count and minimal field assertions.
- Modify: `README.md`, `details.md`, `weld-experience-engine/README.md`
  - Update current stage, report outputs, and next-stage plan.
- Modify: `README.html`, `details.html`
  - Keep reader-facing HTML copies synchronized with Markdown.

## Task 1: Scene Context and Evidence Writeback Models

**Files:**
- Modify: `weld-experience-engine/weldcore/skill_asset/model.py`
- Modify: `weld-experience-engine/weldcore/skill_asset/__init__.py`
- Create: `weld-experience-engine/tests/test_contextual_transfer_precheck.py`

- [ ] **Step 1: Write failing model serialization tests**

Add `tests/test_contextual_transfer_precheck.py`:

```python
from weldcore.skill_asset import (
    SceneContextAsset,
    SkillAssetEvidenceWritebackSummary,
)


def test_scene_context_asset_serializes_precheck_contract():
    scene = SceneContextAsset(
        scene_id="scene-skill-asset-task-1",
        scene_type="welding_transfer_precheck",
        workpiece_frame="workpiece",
        seam_path=[{"t": 0.0, "x": 0.0, "y": 0.0, "z": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0}],
        fixture_obstacles=(),
        safety_boundary={"max_radius_m": 1.4, "min_clearance_m": 0.05},
        target_region={"frame": "workpiece"},
        source_refs={"task_id": "task-1"},
        validation_status="usable_as_scene_context",
        validation_issues=(),
        evidence_boundary=("scene_context_asset_precheck_only", "not_real_fixture_validated"),
        version="v0.1",
    )

    data = scene.to_dict()

    assert data["workpiece_frame"] == "workpiece"
    assert data["validation_status"] == "usable_as_scene_context"
    assert "not_real_fixture_validated" in data["evidence_boundary"]


def test_evidence_writeback_summary_serializes_candidate_counts():
    summary = SkillAssetEvidenceWritebackSummary(
        summary_id="writeback-skill-asset-task-1",
        skill_asset_id="skill-asset-task-1",
        modeled_task_count=8,
        simulation_sample_count=1000,
        completed_sample_count=1000,
        failed_sample_count=0,
        candidate_evidence_refs=("modeled_task_specs:8", "next_batch_samples:1000"),
        writeback_status="evidence_candidates_identified",
        evidence_boundary=("simulation_evidence_candidate_only", "not_real_robot_validated"),
        next_step_recommendation="Use candidate evidence for expert review selection.",
    )

    data = summary.to_dict()

    assert data["modeled_task_count"] == 8
    assert data["completed_sample_count"] == 1000
    assert "simulation_evidence_candidate_only" in data["evidence_boundary"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_contextual_transfer_precheck.py -q
```

Expected: FAIL with import errors for new classes.

- [ ] **Step 3: Implement dataclasses and status literals**

In `skill_asset/model.py`:

```python
SceneContextAssetValidationStatus = Literal[
    "usable_as_scene_context",
    "blocked_by_scene_context_issue",
]
SkillAssetEvidenceWritebackStatus = Literal[
    "evidence_candidates_identified",
    "blocked_by_missing_evidence_source",
]
SkillTransferAssessmentStatus = Literal[
    "ready_for_contextual_precheck",
    "ready_for_lightweight_feasibility_precheck",
    "ready_for_expert_review",
    "blocked_by_missing_skill_motion",
    "blocked_by_robot_body_asset_issue",
    "blocked_by_missing_robot_context",
    "blocked_by_missing_scene_context",
    "blocked_by_incomplete_feasibility_result",
    "blocked_by_failed_feasibility_check",
]
```

Add frozen dataclasses `SceneContextAsset` and `SkillAssetEvidenceWritebackSummary`, each with `to_dict()` using `_model_dict`.

Export them from `skill_asset/__init__.py`.

- [ ] **Step 4: Run model tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_contextual_transfer_precheck.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add weld-experience-engine/weldcore/skill_asset/model.py \
  weld-experience-engine/weldcore/skill_asset/__init__.py \
  weld-experience-engine/tests/test_contextual_transfer_precheck.py
git commit -m "feat: add contextual skill asset models"
```

## Task 2: Context Builders, Lightweight Feasibility, and Evidence Writeback

**Files:**
- Create: `weld-experience-engine/weldcore/skill_asset/context.py`
- Modify: `weld-experience-engine/weldcore/skill_asset/__init__.py`
- Modify: `weld-experience-engine/weldcore/robot_process/feasibility.py`
- Modify: `weld-experience-engine/weldcore/robot_process/__init__.py`
- Test: `weld-experience-engine/tests/test_contextual_transfer_precheck.py`

- [ ] **Step 1: Write failing builder tests**

Append tests:

```python
from dataclasses import replace
from pathlib import Path

from weldcore.robot_process import build_robot_context_from_body_asset
from weldcore.skill_asset import (
    build_contextual_feasibility_result,
    build_default_evidence_writeback_summary,
    build_default_scene_context_asset,
    build_manipulation_skill_asset_from_simulation_bundle,
    build_robot_body_asset_from_urdf,
)
from weldcore.simulation_bakeoff import (
    build_simulation_evidence_bundle,
    default_simulation_task_specs,
    run_simlite_reference,
)

ROOT = Path(__file__).resolve().parents[2]
URDF = ROOT / "docs" / "real-urdf" / "robot.urdf"


def _default_skill_asset():
    task_spec = default_simulation_task_specs()[0]
    bundle = build_simulation_evidence_bundle(task_spec, run_simlite_reference(task_spec))
    return build_manipulation_skill_asset_from_simulation_bundle(bundle)


def test_default_scene_context_asset_uses_skill_motion_and_boundaries():
    skill = _default_skill_asset()

    scene = build_default_scene_context_asset(skill)

    assert scene.validation_status == "usable_as_scene_context"
    assert scene.workpiece_frame == "workpiece"
    assert len(scene.seam_path) == skill.motion["trajectory_point_count"]
    assert "scene_context_asset_precheck_only" in scene.evidence_boundary
    assert "not_real_fixture_validated" in scene.evidence_boundary


def test_scene_context_asset_blocks_missing_workpiece_frame_or_seam_path():
    skill = _default_skill_asset()

    missing_frame = build_default_scene_context_asset(skill, workpiece_frame=None)
    assert missing_frame.validation_status == "blocked_by_scene_context_issue"
    assert "missing_workpiece_frame" in missing_frame.validation_issues

    missing_path = build_default_scene_context_asset(
        replace(skill, motion={**skill.motion, "tcp_trajectory": []})
    )
    assert missing_path.validation_status == "blocked_by_scene_context_issue"
    assert "missing_seam_path" in missing_path.validation_issues


def test_robot_context_from_real_body_asset_keeps_tcp_boundary():
    robot = build_robot_body_asset_from_urdf(URDF)

    context = build_robot_context_from_body_asset(robot)

    assert context.robot_model == robot.robot_model
    assert context.robot_family == robot.robot_family
    assert context.joint_limits_source == robot.source_urdf
    assert context.tcp_frame == "torch_tcp_nominal"
    assert context.tcp_calibration_status == "nominal_from_asset_not_calibrated"
    assert "not_tcp_calibrated" in context.evidence_notes
    assert "not_ready_for_robot_execution" in context.evidence_notes


def test_contextual_feasibility_passes_default_context_as_lightweight_precheck():
    skill = _default_skill_asset()
    robot = build_robot_body_asset_from_urdf(URDF)
    robot_context = build_robot_context_from_body_asset(robot)
    scene = build_default_scene_context_asset(skill)

    result = build_contextual_feasibility_result(skill, robot_context, scene)

    assert result.status == "passed"
    assert result.reachability_status == "passed"
    assert result.collision_status == "assumed"
    assert result.joint_limit_status == "passed"
    assert result.path_continuity_status == "passed"
    assert result.orientation_feasibility_status == "passed"
    assert "collision_geometry_not_validated" in result.warning_reasons
    assert "not_full_ik_solver" in result.evidence_boundary
    assert "not_ready_for_robot_execution" in result.evidence_boundary


def test_contextual_feasibility_fails_when_workspace_hint_is_too_small():
    skill = _default_skill_asset()
    robot = build_robot_body_asset_from_urdf(URDF)
    robot_context = replace(
        build_robot_context_from_body_asset(robot),
        workspace_hint={"max_radius_m": 0.001},
    )
    scene = build_default_scene_context_asset(skill)

    result = build_contextual_feasibility_result(skill, robot_context, scene)

    assert result.status == "failed"
    assert result.reachability_status == "failed"
    assert "tcp_trajectory_outside_workspace_hint" in result.blocking_reasons


def test_contextual_feasibility_consumes_blocked_scene_context():
    skill = _default_skill_asset()
    robot = build_robot_body_asset_from_urdf(URDF)
    robot_context = build_robot_context_from_body_asset(robot)
    scene = build_default_scene_context_asset(skill, workpiece_frame=None)

    result = build_contextual_feasibility_result(skill, robot_context, scene)

    assert result.status == "incomplete"
    assert result.collision_status != "passed"
    assert result.path_continuity_status != "passed"
    assert "missing_workpiece_frame" in result.blocking_reasons


def test_contextual_feasibility_marks_missing_orientation_incomplete():
    skill = _default_skill_asset()
    skill = replace(skill, motion={**skill.motion, "tool_orientation": []})
    robot = build_robot_body_asset_from_urdf(URDF)
    robot_context = build_robot_context_from_body_asset(robot)
    scene = build_default_scene_context_asset(skill)

    result = build_contextual_feasibility_result(skill, robot_context, scene)

    assert result.status == "incomplete"
    assert result.orientation_feasibility_status == "missing"
    assert "missing_tool_orientation" in result.blocking_reasons


def test_contextual_feasibility_marks_missing_joint_limit_source_incomplete():
    skill = _default_skill_asset()
    robot = build_robot_body_asset_from_urdf(URDF)
    robot_context = replace(build_robot_context_from_body_asset(robot), joint_limits_source=None)
    scene = build_default_scene_context_asset(skill)

    result = build_contextual_feasibility_result(skill, robot_context, scene)

    assert result.status == "incomplete"
    assert result.joint_limit_status == "missing"
    assert "missing_joint_limits_source" in result.blocking_reasons


def test_contextual_feasibility_marks_single_point_path_continuity_missing():
    skill = _default_skill_asset()
    one_point_motion = {
        **skill.motion,
        "tcp_trajectory": skill.motion["tcp_trajectory"][:1],
        "tool_orientation": skill.motion["tool_orientation"][:1],
        "trajectory_point_count": 1,
        "orientation_point_count": 1,
    }
    skill = replace(skill, motion=one_point_motion)
    robot = build_robot_body_asset_from_urdf(URDF)
    robot_context = build_robot_context_from_body_asset(robot)
    scene = build_default_scene_context_asset(skill)

    result = build_contextual_feasibility_result(skill, robot_context, scene)

    assert result.status == "incomplete"
    assert result.path_continuity_status == "missing"
    assert "missing_path_continuity" in result.blocking_reasons


def test_default_evidence_writeback_summary_links_modeled_tasks_and_next_batch():
    skill = _default_skill_asset()

    summary = build_default_evidence_writeback_summary(skill)

    assert summary.skill_asset_id == skill.asset_id
    assert summary.modeled_task_count == 8
    assert summary.simulation_sample_count == 1000
    assert summary.completed_sample_count == 1000
    assert summary.failed_sample_count == 0
    assert summary.writeback_status == "evidence_candidates_identified"
    assert "modeled_task_specs:8" in summary.candidate_evidence_refs
    assert "next_batch_samples:1000" in summary.candidate_evidence_refs
    assert "not_real_welding_quality_validation" in summary.evidence_boundary
    assert "not_ready_for_robot_execution" in summary.evidence_boundary
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_contextual_transfer_precheck.py -q
```

Expected: FAIL with missing builders.

- [ ] **Step 3: Implement `build_robot_context_from_body_asset`**

In `robot_process/feasibility.py`, import `RobotBodyAsset` under `TYPE_CHECKING` or normal import if no cycle occurs. Add:

```python
def build_robot_context_from_body_asset(
    robot_body_asset: RobotBodyAsset,
    *,
    context_id: str | None = None,
    base_frame: str | None = None,
    tcp_frame: str = "torch_tcp_nominal",
    workpiece_frame: str = "workpiece",
) -> RobotContextSpec:
    ...
```

Rules:
- `context_id = f"context-{robot_body_asset.robot_id}"` if absent.
- `base_frame = base_frame or first link name or "robot_base"`.
- `tcp_calibration_status = "nominal_from_asset_not_calibrated"`.
- `joint_limits_source = robot_body_asset.source_urdf` when joint limits exist; otherwise `None`.
- `workspace_hint = {"max_radius_m": 1.4, "z_min_m": -0.2, "z_max_m": 1.5}`.
- `evidence_notes` includes `uploaded_urdf_asset`, `not_tcp_calibrated`, `not_vendor_validated`, `not_ready_for_robot_execution`, plus robot asset issues if present.

Export from `robot_process/__init__.py`.

- [ ] **Step 4: Implement scene context and feasibility builders**

Create `skill_asset/context.py`:

```python
def build_default_scene_context_asset(
    skill_asset: ManipulationSkillAsset,
    *,
    workpiece_frame: str | None = "workpiece",
) -> SceneContextAsset:
    ...

def build_contextual_feasibility_result(
    skill_asset: ManipulationSkillAsset,
    robot_context: RobotContextSpec | None,
    scene_context: SceneContextAsset | None,
) -> RobotFeasibilityResult:
    ...

def build_default_evidence_writeback_summary(
    skill_asset: ManipulationSkillAsset,
    *,
    modeled_task_count: int = 8,
    simulation_sample_count: int = 1000,
    completed_sample_count: int = 1000,
    failed_sample_count: int = 0,
) -> SkillAssetEvidenceWritebackSummary:
    ...
```

Implementation rules:
- Scene seam path defaults to `skill_asset.motion["tcp_trajectory"]`.
- Missing workpiece frame or empty seam path produces `blocked_by_scene_context_issue`.
- Default evidence boundary includes `scene_context_asset_precheck_only`, `not_real_fixture_validated`, `not_collision_validated`, `not_ready_for_robot_execution`.
- Feasibility result uses `draft_id=skill_asset.asset_id`, `context_id=robot_context.context_id if present else "missing-context"`.
- Missing robot context: status `incomplete`, reachability `missing`, collision `not_checked`, joint limit `missing`, path continuity `missing`, orientation `missing`, blocking `missing_robot_context`.
- Missing scene context: status `incomplete`, collision `missing`, path continuity `missing`, blocking `missing_scene_context`.
- Blocked scene context: status `incomplete`, collision `missing`, path continuity `missing`, and all `scene_context.validation_issues` appear in `blocking_reasons`.
- Missing `tcp_trajectory`: reachability `missing`, blocking `missing_tcp_trajectory`.
- Missing `tool_orientation`: orientation feasibility `missing`, blocking `missing_tool_orientation`.
- Missing `robot_context.joint_limits_source`: joint limit `missing`, blocking `missing_joint_limits_source`.
- Path continuity requires at least two TCP points and at least two scene seam points; otherwise path continuity `missing`, blocking `missing_path_continuity`.
- Workspace radius check uses sqrt(x² + y² + z²) over TCP trajectory when `max_radius_m` exists.
- Collision is `assumed` only when scene context is usable; warning `collision_geometry_not_validated`.
- Evidence boundary includes `lightweight_feasibility_precheck_only`, `not_full_ik_solver`, `not_collision_validated`, `not_moveit_validated`, `not_gazebo_validated`, `not_real_robot_validated`, `not_ready_for_robot_execution`.
- Evidence writeback status is `evidence_candidates_identified` when modeled count and sample count are positive.
- Evidence writeback candidate refs include `modeled_task_specs:{count}` and `next_batch_samples:{count}`.
- Evidence writeback boundary includes `simulation_evidence_candidate_only`, `modeled_task_specs_not_expert_reviewed`, `not_real_welding_quality_validation`, `not_ready_for_robot_execution`.
- Evidence writeback recommendation must say candidates are for expert review and future asset evidence selection, not execution proof.

Export from `skill_asset/__init__.py`.

- [ ] **Step 5: Run focused tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_contextual_transfer_precheck.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add weld-experience-engine/weldcore/skill_asset/context.py \
  weld-experience-engine/weldcore/skill_asset/__init__.py \
  weld-experience-engine/weldcore/robot_process/feasibility.py \
  weld-experience-engine/weldcore/robot_process/__init__.py \
  weld-experience-engine/tests/test_contextual_transfer_precheck.py
git commit -m "feat: add contextual lightweight feasibility precheck"
```

## Task 3: Contextual Transfer Assessment and Report Artifacts

**Files:**
- Modify: `weld-experience-engine/weldcore/skill_asset/assessment.py`
- Modify: `weld-experience-engine/weldcore/skill_asset/asset_report.py`
- Test: `weld-experience-engine/tests/test_contextual_transfer_precheck.py`
- Test: `weld-experience-engine/tests/test_skill_asset_report.py`

- [ ] **Step 1: Write failing assessment status tests**

Append tests:

```python
from weldcore.skill_asset import build_skill_transfer_assessment


def test_legacy_transfer_assessment_keeps_contextual_precheck_status():
    skill = _default_skill_asset()
    robot = build_robot_body_asset_from_urdf(URDF)

    assessment = build_skill_transfer_assessment(skill, robot)

    assert assessment.status == "ready_for_contextual_precheck"
    assert "requires_robot_context_spec" in assessment.warning_gaps
    assert "requires_scene_context_asset" in assessment.warning_gaps


def test_contextual_assessment_missing_both_contexts_prioritizes_robot_context():
    skill = _default_skill_asset()
    robot = build_robot_body_asset_from_urdf(URDF)

    assessment = build_skill_transfer_assessment(
        skill,
        robot,
        contextual_precheck_requested=True,
    )

    assert assessment.status == "blocked_by_missing_robot_context"
    assert "missing_robot_context" in assessment.blocking_gaps
    assert "missing_scene_context" in assessment.blocking_gaps


def test_contextual_assessment_missing_scene_context_blocks_scene_context():
    skill = _default_skill_asset()
    robot = build_robot_body_asset_from_urdf(URDF)
    robot_context = build_robot_context_from_body_asset(robot)

    assessment = build_skill_transfer_assessment(
        skill,
        robot,
        robot_context=robot_context,
    )

    assert assessment.status == "blocked_by_missing_scene_context"
    assert "missing_scene_context" in assessment.blocking_gaps


def test_contextual_assessment_ready_for_lightweight_precheck_without_result():
    skill = _default_skill_asset()
    robot = build_robot_body_asset_from_urdf(URDF)
    robot_context = build_robot_context_from_body_asset(robot)
    scene = build_default_scene_context_asset(skill)

    assessment = build_skill_transfer_assessment(
        skill,
        robot,
        robot_context=robot_context,
        scene_context=scene,
    )

    assert assessment.status == "ready_for_lightweight_feasibility_precheck"


def test_contextual_assessment_reaches_expert_review_with_passed_lightweight_result():
    skill = _default_skill_asset()
    robot = build_robot_body_asset_from_urdf(URDF)
    robot_context = build_robot_context_from_body_asset(robot)
    scene = build_default_scene_context_asset(skill)
    result = build_contextual_feasibility_result(skill, robot_context, scene)

    assessment = build_skill_transfer_assessment(
        skill,
        robot,
        robot_context=robot_context,
        scene_context=scene,
        feasibility_result=result,
    )

    assert assessment.status == "ready_for_expert_review"
    assert "lightweight_feasibility_precheck_passed" in assessment.passed_checks
    assert "not_ready_for_robot_execution" in assessment.evidence_boundary


def test_contextual_assessment_blocks_failed_feasibility_result():
    skill = _default_skill_asset()
    robot = build_robot_body_asset_from_urdf(URDF)
    robot_context = replace(
        build_robot_context_from_body_asset(robot),
        workspace_hint={"max_radius_m": 0.001},
    )
    scene = build_default_scene_context_asset(skill)
    result = build_contextual_feasibility_result(skill, robot_context, scene)

    assessment = build_skill_transfer_assessment(
        skill,
        robot,
        robot_context=robot_context,
        scene_context=scene,
        feasibility_result=result,
    )

    assert assessment.status == "blocked_by_failed_feasibility_check"
    assert "tcp_trajectory_outside_workspace_hint" in assessment.blocking_gaps


def test_contextual_assessment_blocks_incomplete_scene_feasibility_result():
    skill = _default_skill_asset()
    robot = build_robot_body_asset_from_urdf(URDF)
    robot_context = build_robot_context_from_body_asset(robot)
    scene = build_default_scene_context_asset(skill, workpiece_frame=None)
    result = build_contextual_feasibility_result(skill, robot_context, scene)

    assessment = build_skill_transfer_assessment(
        skill,
        robot,
        robot_context=robot_context,
        scene_context=scene,
        feasibility_result=result,
    )

    assert assessment.status == "blocked_by_incomplete_feasibility_result"
    assert "missing_workpiece_frame" in assessment.blocking_gaps
```

This covers both explicit `contextual_precheck_requested=True` and implicit contextual triggering by passing a contextual object.

- [ ] **Step 2: Update report tests to expect seven artifacts**

In `tests/test_skill_asset_report.py`, update assertions:

```python
assert payload["transfer_assessment"]["status"] == "ready_for_expert_review"
assert payload["robot_feasibility_result"]["status"] == "passed"
assert payload["robot_feasibility_result"]["collision_status"] == "assumed"
assert "not_ready_for_robot_execution" in payload["transfer_assessment"]["evidence_boundary"]
assert "not_full_ik_solver" in payload["robot_feasibility_result"]["evidence_boundary"]
assert payload["robot_context_spec"]["tcp_calibration_status"] == "nominal_from_asset_not_calibrated"
assert "not_tcp_calibrated" in payload["robot_context_spec"]["evidence_notes"]
assert payload["scene_context_asset"]["workpiece_frame"] == "workpiece"
assert payload["scene_context_asset"]["validation_status"] == "usable_as_scene_context"
assert "scene_context_asset_precheck_only" in payload["scene_context_asset"]["evidence_boundary"]
assert payload["evidence_writeback_summary"]["modeled_task_count"] == 8
assert payload["evidence_writeback_summary"]["simulation_sample_count"] == 1000
for filename in (
    "skill_asset_report.json",
    "robot_body_asset_report.json",
    "robot_context_spec.json",
    "scene_context_asset_report.json",
    "skill_transfer_assessment.json",
    "robot_feasibility_result.json",
    "skill_asset_evidence_writeback_summary.json",
):
    assert (tmp_path / filename).exists()
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_contextual_transfer_precheck.py tests/test_skill_asset_report.py -q
```

Expected: FAIL because assessment and report are not yet extended.

- [ ] **Step 4: Extend assessment logic**

Update `build_skill_transfer_assessment` signature:

```python
def build_skill_transfer_assessment(
    skill_asset: ManipulationSkillAsset,
    robot_body_asset: RobotBodyAsset,
    *,
    robot_context: RobotContextSpec | None = None,
    scene_context: SceneContextAsset | None = None,
    feasibility_result: RobotFeasibilityResult | None = None,
    contextual_precheck_requested: bool = False,
) -> SkillTransferAssessment:
```

Status priority:
1. Missing skill motion -> `blocked_by_missing_skill_motion`.
2. Robot body issue -> `blocked_by_robot_body_asset_issue`.
3. If no contextual object and `contextual_precheck_requested` is false -> old `ready_for_contextual_precheck`.
4. Missing robot context -> `blocked_by_missing_robot_context`; include `missing_scene_context` too if absent.
5. Missing scene context -> `blocked_by_missing_scene_context`.
6. Missing feasibility result -> `ready_for_lightweight_feasibility_precheck`.
7. Failed check or `feasibility_result.status == "failed"` -> `blocked_by_failed_feasibility_check`.
8. Incomplete result or blocking reasons -> `blocked_by_incomplete_feasibility_result`.
9. Passed result without blocking reasons -> `ready_for_expert_review`.

Append contextual evidence boundaries from robot context notes, scene context boundary, and feasibility result boundary. Never remove `not_ready_for_robot_execution`.

- [ ] **Step 5: Extend `asset_report`**

Build:
- `robot_context = build_robot_context_from_body_asset(robot_body_asset)`
- `scene_context = build_default_scene_context_asset(skill_asset)`
- `feasibility_result = build_contextual_feasibility_result(skill_asset, robot_context, scene_context)`
- `evidence_writeback_summary = build_default_evidence_writeback_summary(skill_asset)`
- contextual `assessment` with all three objects.

Write:
- `skill_asset_report.json`
- `robot_body_asset_report.json`
- `robot_context_spec.json`
- `scene_context_asset_report.json`
- `skill_transfer_assessment.json`
- `robot_feasibility_result.json`
- `skill_asset_evidence_writeback_summary.json`

- [ ] **Step 6: Run focused tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_contextual_transfer_precheck.py tests/test_skill_asset_report.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add weld-experience-engine/weldcore/skill_asset/assessment.py \
  weld-experience-engine/weldcore/skill_asset/asset_report.py \
  weld-experience-engine/tests/test_contextual_transfer_precheck.py \
  weld-experience-engine/tests/test_skill_asset_report.py
git commit -m "feat: extend skill transfer assessment with context precheck"
```

## Task 4: Documentation and Default Verification

**Files:**
- Modify: `README.md`
- Modify: `details.md`
- Modify: `weld-experience-engine/README.md`
- Modify: `README.html`
- Modify: `details.html`

- [ ] **Step 1: Update Markdown docs**

In `README.md`:
- Update core chain to include `RobotContextSpec`, `SceneContextAsset`, `RobotFeasibilityResult`.
- Update completed capabilities with contextual lightweight transfer precheck and seven report artifacts.
- Update next-stage direction away from larger sample expansion and toward expert review object, TCP/workpiece calibration records, and heavier robot adapter反证.
- Preserve all boundaries: no real robot execution, no real welding quality validation, no WPS/PQR.

In `details.md`:
- Update date to 2026-06-16.
- Add a new 2026-06-16 recent update section with implemented objects, report artifacts, evidence writeback summary, and a verification result to be filled from the fresh test run in Step 3.
- Move “尚未完成/下一步建议” to the new stage.
- Update default verification count after running full tests.

In `weld-experience-engine/README.md`:
- Update core model diagram.
- Document extended `asset_report` outputs.
- Clarify lightweight precheck boundaries.

- [ ] **Step 2: Refresh HTML reading copies**

Update `README.html` and `details.html` to reflect the Markdown changes. Keep them reader-facing and consistent; do not add unrelated style or layout changes.

- [ ] **Step 3: Run full verification**

Run:

```bash
cd weld-experience-engine
uv run pytest -q
uv run python -m weldcore.skill_asset.asset_report --outdir /tmp/weld-skill-asset-report-check
```

Expected:
- pytest reports all tests passing.
- report command writes seven artifacts.
- JSON output contains `transfer_assessment.status == "ready_for_expert_review"` and `robot_feasibility_result.status == "passed"`.

- [ ] **Step 4: Update docs with verified test count**

After Step 3 finishes, update `details.md` and `details.html` with the exact pytest result.

- [ ] **Step 5: Commit**

```bash
git add README.md details.md weld-experience-engine/README.md README.html details.html
git commit -m "docs: document contextual transfer precheck stage"
```

## Final Verification

- [ ] Run:

```bash
cd weld-experience-engine
uv run pytest -q
uv run python -m weldcore.skill_asset.asset_report --outdir /tmp/weld-skill-asset-report-final
```

- [ ] Confirm:
  - Full pytest passes.
  - Seven report artifacts exist.
  - `skill_transfer_assessment.json` status is `ready_for_expert_review`.
  - `robot_feasibility_result.json` status is `passed`.
  - Evidence boundaries include `not_ready_for_robot_execution`, `not_full_ik_solver`, `not_collision_validated`, `not_real_robot_validated`.

- [ ] Request final code review.

- [ ] Push branch, create PR, merge remote PR, then clean up local branch/worktree after the remote merge succeeds.
