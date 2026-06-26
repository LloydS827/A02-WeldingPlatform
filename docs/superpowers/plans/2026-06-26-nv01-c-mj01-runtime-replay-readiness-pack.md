# NV01-C + MJ01 Runtime Replay Readiness Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 NV01-C + MJ01 readiness pack，从 NV01-B artifact 生成 Isaac runtime validation input manifest、MuJoCo lightweight replay feasibility report 和共享 runtime/replay blocking report。

**Architecture:** 新增轻量 builder 消费 NV01-B 输出，不引入 Isaac Sim、MuJoCo、OpenUSD SDK、GPU、`pxr` 或 `mujoco` 依赖。新增 report CLI 默认自举 `_source_nv01b/`，显式 source 缺失时失败；输出 JSON/Markdown artifact 和 per-task 输入清单。

**Tech Stack:** Python 3.10+, standard-library JSON/Path/argparse, existing `weldcore.skill_asset.nv01_b_experiment_base_report`, pytest, Markdown docs and static HTML reading copies.

---

## Scope Check

In scope:

- 新增 builder：`weldcore.skill_asset.nv01_c_mj01_readiness`
- 新增 report CLI：`weldcore.skill_asset.nv01_c_mj01_readiness_report`
- 新增 tests：builder tests and report tests
- 输出：
  - `nv01_c_mj01_summary.md`
  - `nv01_c_mj01_summary.json`
  - `isaac_runtime_validation_input_manifest.json`
  - `mujoco_lightweight_replay_feasibility_report.json`
  - `runtime_replay_blocking_report.json`
  - `readiness_reproducibility_manifest.json`
  - per-task `isaac_runtime_task_validation_input.json`
  - per-task `mujoco_task_replay_feasibility.json`
  - per-task `runtime_replay_task_blocking_report.json`
- 更新 `README.md`, `README.html`, `details.md`, `details.html`, `weld-experience-engine/README.md`
- 验证与 PR 合并清理

Out of scope:

- Isaac Sim runtime execution.
- MuJoCo runtime execution.
- OpenUSD SDK / `pxr` validation.
- MJCF conversion implementation.
- Contact/collision/dynamics validation.
- Replicator dataset.
- Isaac Lab or MuJoCo policy training.
- Robot execution.
- Formal WPS/PQR.

## File Map

- Create: `weld-experience-engine/weldcore/skill_asset/nv01_c_mj01_readiness.py`
  - Load required NV01-B artifacts.
  - Build top-level and task-level Isaac/MuJoCo readiness payloads.
  - Aggregate shared blocking report.
- Create: `weld-experience-engine/weldcore/skill_asset/nv01_c_mj01_readiness_report.py`
  - CLI/report entry point.
  - Generate `_source_nv01b/` by default.
  - Accept `--source-nv01b-dir`.
  - Write JSON and Markdown outputs.
- Create: `weld-experience-engine/tests/test_nv01_c_mj01_readiness.py`
  - Builder tests.
- Create: `weld-experience-engine/tests/test_nv01_c_mj01_readiness_report.py`
  - CLI/report tests.
- Modify: `README.md`
  - Add current capability and boundary text for readiness pack.
- Modify: `README.html`
  - Sync root HTML reading copy.
- Modify: `details.md`
  - Add stage entry and update current deliverables / not completed / next step.
- Modify: `details.html`
  - Sync details HTML reading copy.
- Modify: `weld-experience-engine/README.md`
  - Add command and output list for new report.

Do not modify `pyproject.toml`; no dependency is required.

---

### Task 1: Core Readiness Builder

**Files:**
- Create: `weld-experience-engine/tests/test_nv01_c_mj01_readiness.py`
- Create: `weld-experience-engine/weldcore/skill_asset/nv01_c_mj01_readiness.py`

- [ ] **Step 1: Write failing builder tests**

Create `weld-experience-engine/tests/test_nv01_c_mj01_readiness.py`:

```python
import pytest

from weldcore.skill_asset.nv01_b_experiment_base_report import (
    run_nv01_b_experiment_base_report,
)
from weldcore.skill_asset.nv01_c_mj01_readiness import (
    CANONICAL_NV01C_MJ01_STATUS,
    MissingNV01BArtifactError,
    build_nv01_c_mj01_readiness_payloads,
    load_nv01b_artifacts,
)


def _source_nv01b(tmp_path):
    source_dir = tmp_path / "nv01b"
    run_nv01_b_experiment_base_report(outdir=source_dir)
    return source_dir


def test_load_nv01b_artifacts_requires_complete_source(tmp_path):
    source_dir = _source_nv01b(tmp_path)
    artifacts = load_nv01b_artifacts(source_dir)

    assert artifacts["summary"]["report_id"] == (
        "nv01-b-openusd-isaac-reproducible-experiment-base"
    )
    assert artifacts["stage_text"].startswith("#usda 1.0")
    assert artifacts["task_ids"]

    (source_dir / "isaac_replay_fixture.json").unlink()
    with pytest.raises(MissingNV01BArtifactError, match="isaac_replay_fixture.json"):
        load_nv01b_artifacts(source_dir)


def test_build_readiness_payloads_create_isaac_mujoco_and_blocking_reports(tmp_path):
    artifacts = load_nv01b_artifacts(_source_nv01b(tmp_path))

    payloads = build_nv01_c_mj01_readiness_payloads(artifacts)

    assert set(payloads) == {
        "isaac_runtime_validation_input_manifest",
        "mujoco_lightweight_replay_feasibility_report",
        "runtime_replay_blocking_report",
        "readiness_reproducibility_manifest",
        "task_payloads",
    }

    isaac = payloads["isaac_runtime_validation_input_manifest"]
    assert isaac["manifest_id"] == "nv01-c-isaac-runtime-validation-input-manifest"
    assert isaac["runtime_target"] == "Isaac Sim"
    assert isaac["runtime_status"] == "blocked_by_missing_isaac_runtime"
    assert isaac["static_input_status"] == "ready_for_isaac_runtime_validation_input_review"
    assert isaac["source_stage_ref"] == "openusd_stage.usda"
    assert isaac["source_replay_fixture_ref"] == "isaac_replay_fixture.json"
    assert "/World/WeldTasks" in isaac["required_prim_paths"]
    assert isaac["frame_bindings"]
    assert isaac["trajectory_bindings"]
    assert isaac["procedure_parameter_bindings"]
    assert isaac["sensor_placeholders"]
    assert isaac["task_inputs"]
    assert "isaac_sim_runtime" in isaac["blocked_by"]
    assert "not_isaac_sim_runtime_validation" in isaac["readiness_boundary"]
    assert "not_formal_WPS_PQR" in isaac["readiness_boundary"]
    assert "not_ready_for_robot_execution" in isaac["readiness_boundary"]

    mujoco = payloads["mujoco_lightweight_replay_feasibility_report"]
    assert mujoco["report_id"] == "mj01-mujoco-lightweight-replay-feasibility"
    assert mujoco["runtime_target"] == "MuJoCo"
    assert mujoco["runtime_status"] == "blocked_by_missing_mujoco_runtime"
    assert mujoco["model_input_status"] == "ready_for_mj01_lightweight_replay_input_review"
    assert mujoco["mjcf_conversion_status"] == "not_converted_to_mjcf"
    assert mujoco["model_source"] == "nv01_b_robot_body_asset_ref"
    assert mujoco["urdf_ref"]
    assert mujoco["frame_binding_inputs"]
    assert mujoco["trajectory_replay_inputs"]
    assert mujoco["contact_and_dynamics_assumptions"]
    assert mujoco["task_reports"]
    assert "mujoco_runtime" in mujoco["blocked_by"]
    assert "not_mujoco_dynamics_validation" in mujoco["readiness_boundary"]
    assert "not_formal_WPS_PQR" in mujoco["readiness_boundary"]
    assert "not_ready_for_robot_execution" in mujoco["readiness_boundary"]

    blocking = payloads["runtime_replay_blocking_report"]
    assert blocking["overall_status"] == "blocked_for_runtime_replay_validation"
    assert blocking["scope_status"]["isaac_runtime_validation"] == "blocked_by_missing_isaac_runtime"
    assert blocking["scope_status"]["mujoco_lightweight_replay"] == "blocked_by_missing_mujoco_runtime"
    for scope in (
        "sensor_simulation",
        "replicator_dataset",
        "policy_training",
        "expert_review",
        "a01_product_validation",
        "robot_execution",
    ):
        assert scope in blocking["scope_status"]
    assert blocking["blocking_items"]
    assert "isaac_sim_runtime" in blocking["missing_runtime_inputs"]
    assert "mujoco_runtime" in blocking["missing_runtime_inputs"]
    assert "tcp_calibration" in blocking["missing_calibrations"]
    assert blocking["missing_process_inputs"]
    assert blocking["next_required_inputs"]
    assert "not_isaac_sim_runtime_validation" in blocking["readiness_boundary"]
    assert "not_mujoco_dynamics_validation" in blocking["readiness_boundary"]
    assert "not_formal_WPS_PQR" in blocking["readiness_boundary"]
    assert "not_ready_for_robot_execution" in blocking["readiness_boundary"]

    task_payloads = payloads["task_payloads"]
    assert task_payloads
    for task_id, task in task_payloads.items():
        assert task["isaac_runtime_task_validation_input"]["task_id"] == task_id
        assert task["mujoco_task_replay_feasibility"]["task_id"] == task_id
        assert task["runtime_replay_task_blocking_report"]["task_id"] == task_id
        for key in (
            "source_task_dir_ref",
            "stage_task_prim_ref",
            "trajectory_ref",
            "tcp_frame_ref",
            "tool_frame_ref",
            "workpiece_frame_ref",
            "procedure_parameter_refs",
            "blocked_by",
            "readiness_boundary",
        ):
            assert key in task["isaac_runtime_task_validation_input"]
            assert key in task["mujoco_task_replay_feasibility"]
        blocking_task = task["runtime_replay_task_blocking_report"]
        assert blocking_task["source_task_dir_ref"]
        assert blocking_task["stage_task_prim_ref"]
        assert blocking_task["blocked_by"]
        assert "not_formal_WPS_PQR" in blocking_task["readiness_boundary"]


def test_canonical_status_vocabulary():
    expected = {
        "ready_for_isaac_runtime_validation_input_review",
        "ready_for_mj01_lightweight_replay_input_review",
        "blocked_by_missing_isaac_runtime",
        "blocked_by_missing_mujoco_runtime",
        "blocked_for_runtime_replay_validation",
        "not_isaac_sim_runtime_validation",
        "not_mujoco_dynamics_validation",
        "not_policy_training_result",
        "not_formal_WPS_PQR",
        "not_ready_for_robot_execution",
    }
    assert expected <= CANONICAL_NV01C_MJ01_STATUS
    assert "ready_for_robot_execution" not in CANONICAL_NV01C_MJ01_STATUS
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_nv01_c_mj01_readiness.py -q
```

Expected: FAIL because module does not exist.

- [ ] **Step 3: Implement builder**

Create `weld-experience-engine/weldcore/skill_asset/nv01_c_mj01_readiness.py`.

Implementation requirements:

- Define:

```python
CANONICAL_NV01C_MJ01_STATUS = {
    "ready_for_isaac_runtime_validation_input_review",
    "ready_for_mj01_lightweight_replay_input_review",
    "blocked_by_missing_isaac_runtime",
    "blocked_by_missing_mujoco_runtime",
    "blocked_for_runtime_replay_validation",
    "not_isaac_sim_runtime_validation",
    "not_mujoco_dynamics_validation",
    "not_policy_training_result",
    "not_formal_WPS_PQR",
    "not_ready_for_robot_execution",
}
```

- Define `MissingNV01BArtifactError(RuntimeError)`.
- Define `load_nv01b_artifacts(source_nv01b_dir)`.
- Required top-level files:
  - `nv01_b_summary.json`
  - `openusd_stage.usda`
  - `openusd_stage_validation_report.json`
  - `isaac_replay_fixture.json`
  - `procedure_sim_parameter_audit.json`
  - `sensor_annotation_manifest.json`
  - `simulation_blocking_report.json`
  - `experiment_reproducibility_manifest.json`
- Load per-task files from `summary["tasks"]`:
  - `isaac_replay_task_fixture.json`
  - `procedure_sim_parameter_audit.json`
  - `sensor_annotation_manifest.json`
  - `simulation_blocking_report.json`
- Define `build_nv01_c_mj01_readiness_payloads(artifacts)`.
- Extract task frame and trajectory refs from existing task fixtures when available; otherwise use stable fallback strings:
  - `trajectory_ref = "skill_asset.motion.tcp_trajectory"`
  - `tcp_frame_ref = "tool_tcp_frame"`
  - `tool_frame_ref = "tool_frame"`
  - `workpiece_frame_ref = "workpiece_frame"`
- Use stable relative refs only; do not serialize absolute tmp paths.

- [ ] **Step 4: Run builder tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_nv01_c_mj01_readiness.py -q
```

Expected: PASS.

---

### Task 2: Report CLI and Artifact Writer

**Files:**
- Create: `weld-experience-engine/tests/test_nv01_c_mj01_readiness_report.py`
- Create: `weld-experience-engine/weldcore/skill_asset/nv01_c_mj01_readiness_report.py`

- [ ] **Step 1: Write failing report tests**

Create `weld-experience-engine/tests/test_nv01_c_mj01_readiness_report.py`:

```python
import json

import pytest


EXPECTED_TOP_LEVEL = {
    "nv01_c_mj01_summary.md",
    "nv01_c_mj01_summary.json",
    "isaac_runtime_validation_input_manifest.json",
    "mujoco_lightweight_replay_feasibility_report.json",
    "runtime_replay_blocking_report.json",
    "readiness_reproducibility_manifest.json",
}

EXPECTED_TASK = {
    "isaac_runtime_task_validation_input.json",
    "mujoco_task_replay_feasibility.json",
    "runtime_replay_task_blocking_report.json",
}


def _relative_files(root):
    return sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())


def test_readiness_report_writes_default_artifacts(tmp_path):
    from weldcore.skill_asset.nv01_c_mj01_readiness_report import (
        run_nv01_c_mj01_readiness_report,
    )

    outdir = tmp_path / "readiness"
    summary = run_nv01_c_mj01_readiness_report(outdir=outdir)

    assert summary["report_id"] == "nv01-c-mj01-runtime-replay-readiness-pack"
    assert summary["overall_status"] == "blocked_for_runtime_replay_validation"
    assert summary["source_nv01b"]["source_mode"] == "generated_default"
    assert summary["isaac_status"] == "blocked_by_missing_isaac_runtime"
    assert summary["mujoco_status"] == "blocked_by_missing_mujoco_runtime"
    assert "not_isaac_sim_runtime_validation" in summary["readiness_boundary"]
    assert "not_mujoco_dynamics_validation" in summary["readiness_boundary"]
    assert "not_formal_WPS_PQR" in summary["readiness_boundary"]
    assert "not_ready_for_robot_execution" in summary["readiness_boundary"]
    assert sorted(summary["generated_artifacts"]) == _relative_files(outdir)

    for filename in EXPECTED_TOP_LEVEL:
        assert (outdir / filename).exists()

    for task in summary["tasks"]:
        task_dir = outdir / task["task_output_dir"]
        for filename in EXPECTED_TASK:
            assert (task_dir / filename).exists()

    markdown = (outdir / "nv01_c_mj01_summary.md").read_text(encoding="utf-8")
    assert "不是 Isaac Sim runtime 验证" in markdown
    assert "不是 MuJoCo dynamics validation" in markdown
    assert "不是 ready_for_robot_execution" in markdown


def test_readiness_report_explicit_missing_source_fails(tmp_path):
    from weldcore.skill_asset.nv01_c_mj01_readiness import MissingNV01BArtifactError
    from weldcore.skill_asset.nv01_c_mj01_readiness_report import (
        run_nv01_c_mj01_readiness_report,
    )

    with pytest.raises(MissingNV01BArtifactError, match="missing_source_nv01b_dir"):
        run_nv01_c_mj01_readiness_report(
            outdir=tmp_path / "out",
            source_nv01b_dir=tmp_path / "missing",
        )


def test_readiness_report_explicit_source_uses_stable_refs(tmp_path):
    from weldcore.skill_asset.nv01_b_experiment_base_report import (
        run_nv01_b_experiment_base_report,
    )
    from weldcore.skill_asset.nv01_c_mj01_readiness_report import (
        run_nv01_c_mj01_readiness_report,
    )

    source = tmp_path / "source"
    outdir = tmp_path / "out"
    run_nv01_b_experiment_base_report(outdir=source)

    summary = run_nv01_c_mj01_readiness_report(
        outdir=outdir,
        source_nv01b_dir=source,
    )
    manifest = json.loads(
        (outdir / "readiness_reproducibility_manifest.json").read_text(
            encoding="utf-8"
        )
    )

    assert summary["source_nv01b"]["source_mode"] == "external_source_nv01b"
    assert summary["source_nv01b"]["source_nv01b_root_ref"] == "<source-nv01b-dir>"
    assert not any(path.startswith("_source_nv01b/") for path in summary["generated_artifacts"])
    assert manifest["source_nv01b_root_ref"] == "<source-nv01b-dir>"
    assert "--source-nv01b-dir <source-nv01b-dir>" in manifest["command"]

    serialized = json.dumps({"summary": summary, "manifest": manifest}, ensure_ascii=False)
    assert str(source) not in serialized
    assert str(tmp_path) not in serialized


def test_readiness_report_main_prints_json(tmp_path, capsys):
    from weldcore.skill_asset import nv01_c_mj01_readiness_report

    nv01_c_mj01_readiness_report.main(["--outdir", str(tmp_path)])

    output = json.loads(capsys.readouterr().out)
    assert output["overall_status"] == "blocked_for_runtime_replay_validation"
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_nv01_c_mj01_readiness_report.py -q
```

Expected: FAIL because module does not exist.

- [ ] **Step 3: Implement report CLI**

Create `weld-experience-engine/weldcore/skill_asset/nv01_c_mj01_readiness_report.py`.

Implementation requirements:

- Public function:

```python
def run_nv01_c_mj01_readiness_report(
    outdir: str | Path,
    source_nv01b_dir: str | Path | None = None,
) -> dict[str, Any]:
```

- Default source behavior:
  - If `source_nv01b_dir is None`, run `run_nv01_b_experiment_base_report(outdir=output_dir / "_source_nv01b")`.
  - If explicit source missing or incomplete, raise `MissingNV01BArtifactError`.
  - Before pushing, verify the current branch is `codex/nv01-c-mj01-readiness-pack`; create/switch if needed before committing.
- Top-level output filenames exactly:
  - `nv01_c_mj01_summary.md`
  - `nv01_c_mj01_summary.json`
  - `isaac_runtime_validation_input_manifest.json`
  - `mujoco_lightweight_replay_feasibility_report.json`
  - `runtime_replay_blocking_report.json`
  - `readiness_reproducibility_manifest.json`
- Per-task output filenames exactly:
  - `isaac_runtime_task_validation_input.json`
  - `mujoco_task_replay_feasibility.json`
  - `runtime_replay_task_blocking_report.json`
- Summary fields:
  - `report_id = "nv01-c-mj01-runtime-replay-readiness-pack"`
  - `overall_status`
  - `isaac_status`
  - `mujoco_status`
  - `source_nv01b`
  - `task_count`
  - `tasks`
  - `generated_artifacts`
  - `readiness_boundary`
  - `next_step_recommendation`
- Markdown boundaries:
  - `不是 Isaac Sim runtime 验证`
  - `不是 MuJoCo dynamics validation`
  - `不是 policy training 结果`
  - `不是正式 WPS/PQR`
  - `不是 ready_for_robot_execution`

- [ ] **Step 4: Run report tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_nv01_c_mj01_readiness.py tests/test_nv01_c_mj01_readiness_report.py -q
```

Expected: PASS.

---

### Task 3: Documentation and Final Verification

**Files:**
- Modify: `README.md`
- Modify: `README.html`
- Modify: `details.md`
- Modify: `details.html`
- Modify: `weld-experience-engine/README.md`

- [ ] **Step 1: Update README.md**

Add to “当前可运行能力”:

```markdown
- `weldcore.skill_asset.nv01_c_mj01_readiness_report` 默认生成 NV01-C + MJ01 readiness pack：Isaac runtime validation input manifest、MuJoCo lightweight replay feasibility report、runtime/replay blocking report、readiness reproducibility manifest 和 per-task runtime/replay 输入清单。该入口不需要 Isaac Sim、MuJoCo、OpenUSD SDK、GPU、`pxr` 或 `mujoco`；默认状态仍是 `blocked_for_runtime_replay_validation`，不是 Isaac Sim runtime replay、MuJoCo dynamics validation、policy training、正式 WPS/PQR 或真实机器人执行验证。
```

Add a short section after NV01-B command:

```markdown
## NV01-C + MJ01 Readiness Pack

默认入口：

```bash
cd weld-experience-engine
uv run python -m weldcore.skill_asset.nv01_c_mj01_readiness_report \
  --outdir artifacts/demo/nv01-c-mj01-readiness-pack
```

预期输出包括 `isaac_runtime_validation_input_manifest.json`、`mujoco_lightweight_replay_feasibility_report.json`、`runtime_replay_blocking_report.json`、`readiness_reproducibility_manifest.json` 和 per-task runtime/replay 输入清单。该命令默认自举 `_source_nv01b/`，不运行 Isaac Sim 或 MuJoCo。
```

- [ ] **Step 2: Update weld-experience-engine/README.md**

Add a concise command section for:

```bash
uv run python -m weldcore.skill_asset.nv01_c_mj01_readiness_report \
  --outdir artifacts/demo/nv01-c-mj01-readiness-pack
```

Mention generated artifacts and boundaries.

- [ ] **Step 3: Update details.md**

Add a new `2026-06-26` bullet group or extend the existing 2026-06-26 entry to state:

- Implemented `nv01_c_mj01_readiness_report`.
- It consumes NV01-B artifacts and generates Isaac/MuJoCo readiness inputs.
- It is not runtime validation and keeps boundary tokens.
- Next stage is external/runtime runner implementation.

Update “已完成能力”, “尚未完成”, and “下一步建议” if needed to distinguish readiness pack from runtime execution.

- [ ] **Step 4: Sync README.html and details.html**

Use the existing static HTML style; do not introduce Mermaid renderer, JavaScript, or CSS redesign.

- [ ] **Step 5: Run documentation checks**

Run:

```bash
for file in README.md README.html details.md details.html weld-experience-engine/README.md; do
  rg -n "nv01_c_mj01_readiness_report" "$file"
  rg -n "NV01-C \\+ MJ01" "$file"
  rg -n "not_formal_WPS_PQR|正式 WPS/PQR" "$file"
done
rg -n "blocked_by_missing_mujoco_runtime|not_mujoco_dynamics_validation|not_isaac_sim_runtime_validation|not_ready_for_robot_execution" README.md README.html details.md details.html weld-experience-engine/README.md
```

Expected: each target doc contains the new report entry point, `NV01-C + MJ01`, and WPS/PQR boundary; the docs collectively contain the runtime/MuJoCo/Isaac/robot execution boundary tokens.

- [ ] **Step 6: Run full test suite**

Run:

```bash
cd weld-experience-engine
uv run pytest -q
```

Expected: all tests pass.

- [ ] **Step 7: Review diff**

Run:

```bash
git diff --stat
git diff --name-only
```

Expected: only planned files changed.

- [ ] **Step 8: Commit, PR, merge, cleanup**

Run:

```bash
git add README.md README.html details.md details.html weld-experience-engine/README.md \
  weld-experience-engine/weldcore/skill_asset/nv01_c_mj01_readiness.py \
  weld-experience-engine/weldcore/skill_asset/nv01_c_mj01_readiness_report.py \
  weld-experience-engine/tests/test_nv01_c_mj01_readiness.py \
  weld-experience-engine/tests/test_nv01_c_mj01_readiness_report.py \
  docs/superpowers/specs/2026-06-26-nv01-c-mj01-runtime-replay-readiness-pack-design.md \
  docs/superpowers/plans/2026-06-26-nv01-c-mj01-runtime-replay-readiness-pack.md
git commit -m "feat: add nv01-c mj01 readiness pack"
test "$(git branch --show-current)" = "codex/nv01-c-mj01-readiness-pack"
git push -u origin codex/nv01-c-mj01-readiness-pack
gh pr create --title "feat: add NV01-C MJ01 readiness pack" --body "<summary and tests>"
gh pr merge --merge --delete-branch
git switch main
git pull --ff-only
git fetch --prune
git branch -d codex/nv01-c-mj01-readiness-pack
```

Then verify `git status --short --branch` is clean on `main`.
