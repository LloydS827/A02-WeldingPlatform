# NV01-B OpenUSD Isaac Reproducible Experiment Base Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 NV01-B OpenUSD / Isaac Sim 可复现实验底座，从现有 K01 + NV01-A artifact 生成最小 `.usda` stage、Isaac replay fixture、K01 参数到仿真参数审计、传感器标注清单和真实仿真阻塞报告。

**Architecture:** 新增一个轻量 builder 模块消费 `nvidia_digital_twin_report` 的输出，不改动 K01/NV01-A 主逻辑。新增 report CLI 在未传 source 时自举 `_source_nv01a/`，在显式 source 缺失或不完整时失败；默认验证只做静态文本/JSON gate，不引入 Isaac Sim、OpenUSD SDK、GPU 或 `pxr` 依赖。

**Tech Stack:** Python 3.10+, standard-library JSON/Path/argparse, existing `weldcore.skill_asset.nvidia_digital_twin_report`, pytest, Markdown docs and regenerated root HTML reading copies.

---

## Scope Check

本计划只覆盖 NV01-B 可复现实验底座。

In scope:

- 生成 `openusd_stage.usda` 和 per-task `openusd_task_stage_fragment.usda`。
- 静态验证关键 prim、K01 metadata、canonical refs 和 source refs。
- 生成 `isaac_replay_fixture.json` 和 per-task fixture。
- 生成 `procedure_sim_parameter_audit.json`，覆盖 47 个 K01 字段并标注 blocking scopes。
- 生成 `sensor_annotation_manifest.json`。
- 生成 `simulation_blocking_report.json`。
- 生成 `experiment_reproducibility_manifest.json` 和 summary。
- 更新 README/details/weld engine README 和 HTML 阅读副本。

Out of scope:

- Isaac Sim runtime 安装或执行。
- `pxr` / OpenUSD SDK 默认依赖。
- Nucleus、Replicator dataset、Isaac Lab policy training、Cosmos、Isaac ROS/Jetson。
- 真实 robot USD asset conversion、真实 IK/collision validation、真实焊接质量验证、正式 WPS/PQR。

Canonical status vocabulary for all new NV01-B payloads:

```python
CANONICAL_NV01B_STATUS = {
    "ready_for_static_openusd_review",
    "blocked_by_openusd_stage_contract_issue",
    "blocked_by_missing_isaac_runtime",
    "not_isaac_sim_runtime_validation",
    "blocked_for_real_isaac_sim_replay",
    "blocked_by_missing_sensor_calibration",
    "blocked_by_missing_real_process_inputs",
    "not_policy_training_result",
    "not_formal_WPS_PQR",
    "not_ready_for_robot_execution",
}
```

Do not add synonymous runtime tokens.

## File Map

- Create: `weld-experience-engine/weldcore/skill_asset/nv01_b_experiment_base.py`
  - Load required NV01-A artifacts.
  - Build top-level and per-task NV01-B payloads.
  - Author `.usda` text with static customData.
  - Validate stage text by required substrings / refs.
  - Compute blocking scopes from K01 parameter coverage.
- Create: `weld-experience-engine/weldcore/skill_asset/nv01_b_experiment_base_report.py`
  - CLI/report entry point.
  - Default source behavior: omitted `--source-nv01a-dir` generates `_source_nv01a/`.
  - Explicit missing/incomplete `--source-nv01a-dir` fails.
  - Writes JSON, USDA, Markdown summary.
- Create: `weld-experience-engine/tests/test_nv01_b_experiment_base.py`
  - Builder and static validation tests.
- Create: `weld-experience-engine/tests/test_nv01_b_experiment_base_report.py`
  - CLI/report artifact and source behavior tests.
- Modify: `README.md`
  - Add NV01-B current runnable capability after implementation.
  - Update next step to NV01-C runtime import/static replay validation.
- Modify: `details.md`
  - Add 2026-06-23 NV01-B stage update.
  - Move NV01-B out of "尚未完成"; keep runtime/training/real robot boundaries.
- Modify: `weld-experience-engine/README.md`
  - Add `nv01_b_experiment_base_report` command and artifacts.
- Modify: `README.html`, `details.html`
  - Regenerate from Markdown using existing lightweight renderer pattern.

Do not modify `pyproject.toml`; no new dependency is required.

---

### Task 1: NV01-B Core Builder and Static Stage Gate

**Files:**
- Create: `weld-experience-engine/tests/test_nv01_b_experiment_base.py`
- Create: `weld-experience-engine/weldcore/skill_asset/nv01_b_experiment_base.py`

- [ ] **Step 1: Write failing core builder tests**

Create `weld-experience-engine/tests/test_nv01_b_experiment_base.py` with tests equivalent to:

```python
import json

import pytest

from weldcore.skill_asset.nvidia_digital_twin_report import (
    run_nvidia_digital_twin_report,
)
from weldcore.skill_asset.nv01_b_experiment_base import (
    CANONICAL_NV01B_STATUS,
    MissingNV01AArtifactError,
    author_openusd_stage_usda,
    build_nv01_b_experiment_payloads,
    load_nv01a_artifacts,
    validate_openusd_stage_text,
)


def _source_nv01a(tmp_path):
    source_dir = tmp_path / "nv01a"
    run_nvidia_digital_twin_report(outdir=source_dir)
    return source_dir


def test_load_nv01a_artifacts_requires_complete_source(tmp_path):
    source_dir = _source_nv01a(tmp_path)
    artifacts = load_nv01a_artifacts(source_dir)

    assert artifacts["summary"]["report_id"] == (
        "k01-nv01-a-procedure-constrained-manifest-evidence-pack"
    )
    assert artifacts["procedure_contract"]["field_count"] == 47
    assert artifacts["task_ids"]

    (source_dir / "weld_procedure_knowledge_contract.json").unlink()
    with pytest.raises(MissingNV01AArtifactError, match="weld_procedure_knowledge_contract.json"):
        load_nv01a_artifacts(source_dir)


def test_build_nv01_b_payloads_create_stage_fixture_and_blocking_reports(tmp_path):
    artifacts = load_nv01a_artifacts(_source_nv01a(tmp_path))

    payloads = build_nv01_b_experiment_payloads(artifacts)

    assert set(payloads) == {
        "openusd_stage_usda",
        "openusd_stage_validation_report",
        "isaac_replay_fixture",
        "procedure_sim_parameter_audit",
        "sensor_annotation_manifest",
        "simulation_blocking_report",
        "experiment_reproducibility_manifest",
        "task_payloads",
    }
    assert payloads["openusd_stage_validation_report"]["validation_status"] == (
        "ready_for_static_openusd_review"
    )
    assert payloads["isaac_replay_fixture"]["runtime_status"] == (
        "blocked_by_missing_isaac_runtime"
    )
    assert "not_isaac_sim_runtime_validation" in payloads["isaac_replay_fixture"]["readiness_boundary"]
    assert payloads["simulation_blocking_report"]["overall_status"] == (
        "blocked_for_real_isaac_sim_replay"
    )
    assert "welding_current_a" in payloads["simulation_blocking_report"]["missing_fields_by_scope"]["real_isaac_sim_replay"]
    assert "welding_voltage_v" in payloads["simulation_blocking_report"]["missing_fields_by_scope"]["real_isaac_sim_replay"]
    assert "heat_input_kj_per_mm" in payloads["simulation_blocking_report"]["missing_fields_by_scope"]["policy_training"]

    audit = payloads["procedure_sim_parameter_audit"]
    assert audit["field_count"] == 47
    assert audit["mapped_field_count"] == 47
    mapping = audit["mappings"]["travel_speed_mm_per_min"]
    assert mapping["usd_metadata_path"].endswith(".procedure.travel_speed_mm_per_min")
    assert mapping["isaac_replay_parameter"] == "procedure_parameter_inputs.travel_speed_mm_per_min"
    assert "domain_randomization_recipe" in mapping["domain_randomization_usage"]

    stage = payloads["openusd_stage_usda"]
    for required in (
        '#usda 1.0',
        'def Xform "World"',
        'def Xform "Robot"',
        'def Xform "Workpiece"',
        'def Xform "WeldTasks"',
        'def Xform "SeamPath"',
        'def Xform "TcpTrajectoryCandidate"',
        'def Xform "Torch"',
        'def Xform "Sensors"',
        'def Xform "SafetyBoundary"',
        '"a02:procedure_contract_ref"',
        '"a02:procedure_parameter_set_ref"',
        '"a02:skill_asset_ref"',
        '"a02:robot_body_asset_ref"',
        '"a02:scene_context_asset_ref"',
        '"a02:readiness_boundary"',
        '"a02:not_ready_reasons"',
        '"a02:path_units" = "mm"',
        '"a02:trajectory_units" = "mm,s"',
        '"a02:tcp_frame_ref"',
        '"a02:tool_frame_ref"',
        '"a02:workpiece_frame"',
        '"a02:workpiece_geometry_status"',
        '"a02:seam_path_ref"',
        '"a02:point_count"',
        '"a02:frame_ref"',
        '"a02:trajectory_ref"',
        '"a02:sample_count"',
        '"a02:torch_frame_ref"',
        '"a02:torch_geometry_status"',
        '"a02:sensor_manifest_ref"',
        '"a02:sensor_layout_status"',
        '"a02:required_calibration"',
        '"a02:safety_boundary_ref"',
        '"a02:boundary_status"',
        '"a02:collision_validation_status"',
    ):
        assert required in stage

    validation = payloads["openusd_stage_validation_report"]
    assert validation["stage_ref"] == "openusd_stage.usda"
    assert "/World/WeldTasks" in validation["required_prim_paths"]
    assert validation["missing_prim_paths"] == []
    assert validation["metadata_checks"]["a02:procedure_contract_ref"] == "present"
    assert validation["canonical_ref_checks"]["skill_asset_refs"] == "present"
    assert validation["procedure_metadata_checks"]["procedure_parameter_set_refs"] == "present"

    fixture = payloads["isaac_replay_fixture"]
    for key in (
        "fixture_id",
        "stage_ref",
        "runtime_target",
        "runtime_status",
        "robot_asset",
        "frame_bindings",
        "trajectory_bindings",
        "procedure_parameter_bindings",
        "task_fixtures",
        "blocked_by",
        "readiness_boundary",
    ):
        assert key in fixture
    assert fixture["runtime_target"] == "Isaac Sim"
    assert fixture["robot_asset"]
    assert fixture["frame_bindings"]
    assert fixture["trajectory_bindings"]
    assert fixture["procedure_parameter_bindings"]
    assert "blocked_by_missing_isaac_runtime" in fixture["blocked_by"]

    sensor = payloads["sensor_annotation_manifest"]
    for key in (
        "manifest_id",
        "stage_ref",
        "sensor_placeholders",
        "annotation_layers",
        "required_real_calibration",
        "blocked_by",
        "readiness_boundary",
    ):
        assert key in sensor
    assert sensor["sensor_placeholders"] == [
        "overview_camera_placeholder",
        "torch_camera_placeholder",
    ]
    assert sensor["annotation_layers"] == [
        "tcp_pose_trace",
        "weld_seam_annotation",
        "procedure_parameter_overlay",
    ]
    assert "blocked_by_missing_sensor_calibration" in sensor["blocked_by"]

    blocking = payloads["simulation_blocking_report"]
    for key in (
        "report_id",
        "overall_status",
        "scope_status",
        "blocking_items",
        "missing_fields_by_scope",
        "missing_calibrations",
        "missing_runtime_inputs",
        "next_required_inputs",
        "readiness_boundary",
    ):
        assert key in blocking
    assert "real_isaac_sim_replay" in blocking["scope_status"]
    assert "isaac_sim_runtime" in blocking["missing_runtime_inputs"]
    assert "sensor_layout_calibration" in blocking["missing_calibrations"]

    repro = payloads["experiment_reproducibility_manifest"]
    for key in (
        "manifest_id",
        "source_nv01a_root_ref",
        "source_nv01a_summary_ref",
        "generated_artifacts",
        "command",
        "default_dependency_boundary",
        "source_artifact_refs",
        "validation_commands",
    ):
        assert key in repro
    assert "no_isaac_sim_default_dependency" in repro["default_dependency_boundary"]


def test_openusd_stage_validation_reports_missing_required_contract_parts(tmp_path):
    artifacts = load_nv01a_artifacts(_source_nv01a(tmp_path))
    payloads = build_nv01_b_experiment_payloads(artifacts)

    broken_stage = payloads["openusd_stage_usda"].replace('def Xform "SeamPath"', "")
    report = validate_openusd_stage_text(
        broken_stage,
        payloads["openusd_stage_validation_report"]["required_prim_paths"],
        payloads["openusd_stage_validation_report"]["required_metadata_keys"],
    )

    assert report["validation_status"] == "blocked_by_openusd_stage_contract_issue"
    assert any(path.endswith("/SeamPath") for path in report["missing_prim_paths"])


def test_openusd_stage_validation_checks_paths_not_only_names(tmp_path):
    artifacts = load_nv01a_artifacts(_source_nv01a(tmp_path))
    payloads = build_nv01_b_experiment_payloads(artifacts)
    stage = payloads["openusd_stage_usda"]
    task_path = next(
        path for path in payloads["openusd_stage_validation_report"]["required_prim_paths"]
        if path.endswith("/SeamPath")
    )
    task_prim = task_path.split("/")[-2]
    broken_stage = stage.replace(
        f'def Xform "{task_prim}"',
        f'def Xform "{task_prim}_moved"',
        1,
    )

    report = validate_openusd_stage_text(
        broken_stage,
        payloads["openusd_stage_validation_report"]["required_prim_paths"],
        payloads["openusd_stage_validation_report"]["required_metadata_keys"],
    )

    assert task_path in report["missing_prim_paths"]


def test_nv01_b_status_vocabulary_has_no_aliases():
    assert "blocked_by_missing_isaac_runtime" in CANONICAL_NV01B_STATUS
    assert "not_isaac_sim_runtime_validation" in CANONICAL_NV01B_STATUS
    assert "blocked_by_missing_isaac_runtime_validation" not in CANONICAL_NV01B_STATUS
    assert "not_isaac_runtime_validated" not in CANONICAL_NV01B_STATUS
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_nv01_b_experiment_base.py -q
```

Expected: FAIL because `nv01_b_experiment_base` does not exist.

- [ ] **Step 3: Implement `nv01_b_experiment_base.py` minimally**

Implementation requirements:

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CANONICAL_NV01B_STATUS = {
    "ready_for_static_openusd_review",
    "blocked_by_openusd_stage_contract_issue",
    "blocked_by_missing_isaac_runtime",
    "not_isaac_sim_runtime_validation",
    "blocked_for_real_isaac_sim_replay",
    "blocked_by_missing_sensor_calibration",
    "blocked_by_missing_real_process_inputs",
    "not_policy_training_result",
    "not_formal_WPS_PQR",
    "not_ready_for_robot_execution",
}

REQUIRED_NV01A_FILES = {
    "summary": "nv01_summary.json",
    "procedure_contract": "weld_procedure_knowledge_contract.json",
    "top_parameter_set": "weld_procedure_parameter_set.json",
    "top_validation_report": "weld_procedure_validation_report.json",
    "mapping_matrix": "procedure_to_nv01_mapping_matrix.json",
    "package": "weld_skill_digital_twin_package.json",
    "openusd_scene_manifest": "openusd_scene_manifest.json",
    "isaac_sim_replay_config": "isaac_sim_replay_config.json",
    "domain_randomization_recipe": "domain_randomization_recipe.json",
    "training_readiness_report": "training_readiness_report.json",
}


class MissingNV01AArtifactError(RuntimeError):
    pass


def load_nv01a_artifacts(source_nv01a_dir: str | Path) -> dict[str, Any]:
    root = Path(source_nv01a_dir)
    if not root.exists():
        raise MissingNV01AArtifactError(f"missing_source_nv01a_dir:{root}")
    missing = [rel for rel in REQUIRED_NV01A_FILES.values() if not (root / rel).exists()]
    if missing:
        raise MissingNV01AArtifactError("missing_nv01a_artifacts:" + ",".join(sorted(missing)))
    artifacts = {
        name: json.loads((root / rel).read_text(encoding="utf-8"))
        for name, rel in REQUIRED_NV01A_FILES.items()
    }
    tasks = artifacts["summary"]["tasks"]
    artifacts["root"] = root
    artifacts["task_ids"] = [task["task_id"] for task in tasks]
    artifacts["task_dirs"] = {task["task_id"]: task["task_output_dir"] for task in tasks}
    artifacts["task_artifacts"] = {
        task["task_id"]: _load_task_nv01a_artifacts(root / task["task_output_dir"])
        for task in tasks
    }
    return artifacts
```

Add helper behavior:

- `_load_task_nv01a_artifacts(task_dir)` loads:
  - `skill_asset_ref.json`
  - `weld_procedure_parameter_set.json`
  - `weld_procedure_validation_report.json`
  - `openusd_task_manifest.json`
  - `isaac_replay_task_config.json`
  - `sensor_and_annotation_manifest.json`
  - `training_task_readiness.json`
- `build_nv01_b_experiment_payloads(artifacts)` returns all payloads listed in Step 1.
- `author_openusd_stage_usda(artifacts, task_payloads)` returns deterministic ASCII USDA text.
- `validate_openusd_stage_text(stage_text, required_prim_paths, required_metadata_keys)` must validate prim paths, not only final prim names. Implement a simple static path extractor for the authored subset: scan `def Xform "Name"` lines, maintain a brace-depth stack, emit paths such as `/World/WeldTasks/task_x/SeamPath`, then compare required paths exactly. Metadata keys can be checked as quoted customData keys.
- The authored USDA must include every object-level customData key from the spec table: `a02:workpiece_frame`, `a02:workpiece_geometry_status`, `a02:seam_path_ref`, `a02:point_count`, `a02:path_units`, `a02:frame_ref`, `a02:trajectory_ref`, `a02:trajectory_units`, `a02:sample_count`, `a02:tcp_frame_ref`, `a02:torch_frame_ref`, `a02:tool_frame_ref`, `a02:torch_geometry_status`, `a02:sensor_manifest_ref`, `a02:sensor_layout_status`, `a02:required_calibration`, `a02:safety_boundary_ref`, `a02:boundary_status`, and `a02:collision_validation_status`.
- `openusd_stage_validation_report` must include `validation_status`, `stage_ref`, `required_prim_paths`, `missing_prim_paths`, `required_metadata_keys`, `metadata_checks`, `canonical_ref_checks`, `procedure_metadata_checks`, `not_ready_reasons`, and `readiness_boundary`.
- `isaac_replay_fixture` must include `fixture_id`, `stage_ref`, `runtime_target`, `runtime_status`, `robot_asset`, `frame_bindings`, `trajectory_bindings`, `procedure_parameter_bindings`, `task_fixtures`, `blocked_by`, and `readiness_boundary`.
- `procedure_sim_parameter_audit` must include `audit_id`, `contract_version`, `field_count`, `mappings`, `mapped_field_count`, `blocking_field_count_by_scope`, and `source_refs`; every mapping must include `field_id`, `display_name`, `requirement_level`, `acquisition_mode`, `a02_target_path`, `usd_metadata_path`, `isaac_replay_parameter`, `domain_randomization_usage`, `coverage_status`, `value_source`, `blocks`, `blocking_scopes`, and `source_ref`.
- `sensor_annotation_manifest` must include `manifest_id`, `stage_ref`, `sensor_placeholders`, `annotation_layers`, `required_real_calibration`, `blocked_by`, and `readiness_boundary`.
- `simulation_blocking_report` must include `report_id`, `overall_status`, `scope_status`, `blocking_items`, `missing_fields_by_scope`, `missing_calibrations`, `missing_runtime_inputs`, `next_required_inputs`, and `readiness_boundary`.
- `experiment_reproducibility_manifest` must include `manifest_id`, `source_nv01a_root_ref`, `source_nv01a_summary_ref`, `generated_artifacts`, `command`, `default_dependency_boundary`, `source_artifact_refs`, and `validation_commands`.

Minimal USDA shape:

```text
#usda 1.0
(
    customData = {
        string "a02:report_id" = "nv01-b-openusd-isaac-reproducible-experiment-base"
        string "a02:procedure_contract_ref" = "weld_procedure_knowledge_contract.json"
        string[] "a02:readiness_boundary" = ["not_isaac_sim_runtime_validation", "not_ready_for_robot_execution"]
    }
)

def Xform "World"
{
    def Xform "Robot" { ... }
    def Xform "Workpiece" { ... }
    def Xform "WeldTasks"
    {
        def Xform "task_..." {
            def Xform "SeamPath" { ... }
            def Xform "TcpTrajectoryCandidate" { ... }
            def Xform "Torch" { ... }
            def Xform "Sensors" { ... }
            def Xform "SafetyBoundary" { ... }
        }
    }
}
```

Use `customData` entries as strings and string arrays only. Escape quotes by replacing `"` with `\"`. Task prim names should be sanitized with letters, numbers and `_`.

Blocking-scope rules:

- `missing_required` or `missing_conditional` + acquisition mode `human_required` / `human_confirmed_or_imported` -> `expert_review`, and `wps_pqr_release` when field blocks includes it.
- `missing_required` / `missing_conditional` / `blocked_*` + acquisition mode `workcell_logged` -> `real_isaac_sim_replay`, `sensor_simulation`, `expert_review`.
- `blocked_*` + acquisition mode `system_computed` -> `policy_training`, `wps_pqr_release`.
- Sensor calibration is always missing in NV01-B default -> `sensor_simulation`, `replicator_dataset`, `real_isaac_sim_replay`.

- [ ] **Step 4: Run core tests and fix until passing**

Run from the worktree root:

```bash
cd weld-experience-engine
uv run pytest tests/test_nv01_b_experiment_base.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit Task 1**

Run from the worktree root:

```bash
git add weld-experience-engine/weldcore/skill_asset/nv01_b_experiment_base.py \
  weld-experience-engine/tests/test_nv01_b_experiment_base.py
git commit -m "feat: add nv01-b experiment base builder"
```

---

### Task 2: NV01-B Report CLI and Artifact Writer

**Files:**
- Create: `weld-experience-engine/tests/test_nv01_b_experiment_base_report.py`
- Create: `weld-experience-engine/weldcore/skill_asset/nv01_b_experiment_base_report.py`

- [ ] **Step 1: Write failing report tests**

Create `weld-experience-engine/tests/test_nv01_b_experiment_base_report.py`:

```python
import json

import pytest


EXPECTED_TOP_LEVEL = {
    "nv01_b_summary.md",
    "nv01_b_summary.json",
    "openusd_stage.usda",
    "openusd_stage_validation_report.json",
    "isaac_replay_fixture.json",
    "procedure_sim_parameter_audit.json",
    "sensor_annotation_manifest.json",
    "simulation_blocking_report.json",
    "experiment_reproducibility_manifest.json",
}

EXPECTED_TASK = {
    "openusd_task_stage_fragment.usda",
    "isaac_replay_task_fixture.json",
    "procedure_sim_parameter_audit.json",
    "sensor_annotation_manifest.json",
    "simulation_blocking_report.json",
}


def _relative_files(root):
    return sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())


def test_nv01_b_report_writes_default_artifacts(tmp_path):
    from weldcore.skill_asset.nv01_b_experiment_base_report import (
        run_nv01_b_experiment_base_report,
    )

    outdir = tmp_path / "nv01b"
    summary = run_nv01_b_experiment_base_report(outdir=outdir)

    assert summary["report_id"] == "nv01-b-openusd-isaac-reproducible-experiment-base"
    assert summary["overall_status"] == "blocked_for_real_isaac_sim_replay"
    assert summary["openusd_authoring_status"] == "ready_for_static_openusd_review"
    assert summary["source_nv01a"]["source_mode"] == "generated_default"
    assert "not_isaac_sim_runtime_validation" in summary["readiness_boundary"]
    assert "not_formal_WPS_PQR" in summary["readiness_boundary"]
    assert sorted(summary["generated_artifacts"]) == _relative_files(outdir)

    for filename in EXPECTED_TOP_LEVEL:
        assert (outdir / filename).exists()

    for task in summary["tasks"]:
        task_dir = outdir / task["task_output_dir"]
        for filename in EXPECTED_TASK:
            assert (task_dir / filename).exists()

    stage = (outdir / "openusd_stage.usda").read_text(encoding="utf-8")
    assert '#usda 1.0' in stage
    assert 'def Xform "World"' in stage

    markdown = (outdir / "nv01_b_summary.md").read_text(encoding="utf-8")
    assert "不是 Isaac Sim runtime 验证" in markdown
    assert "不是 policy training 结果" in markdown
    assert "不是正式 WPS/PQR" in markdown
    assert "不是 ready_for_robot_execution" in markdown


def test_nv01_b_report_explicit_missing_source_fails(tmp_path):
    from weldcore.skill_asset.nv01_b_experiment_base import MissingNV01AArtifactError
    from weldcore.skill_asset.nv01_b_experiment_base_report import (
        run_nv01_b_experiment_base_report,
    )

    with pytest.raises(MissingNV01AArtifactError, match="missing_source_nv01a_dir"):
        run_nv01_b_experiment_base_report(
            outdir=tmp_path / "out",
            source_nv01a_dir=tmp_path / "missing",
        )


def test_nv01_b_report_explicit_incomplete_source_fails(tmp_path):
    from weldcore.skill_asset.nvidia_digital_twin_report import (
        run_nvidia_digital_twin_report,
    )
    from weldcore.skill_asset.nv01_b_experiment_base import MissingNV01AArtifactError
    from weldcore.skill_asset.nv01_b_experiment_base_report import (
        run_nv01_b_experiment_base_report,
    )

    source = tmp_path / "source"
    run_nvidia_digital_twin_report(outdir=source)
    (source / "isaac_sim_replay_config.json").unlink()

    with pytest.raises(MissingNV01AArtifactError, match="isaac_sim_replay_config.json"):
        run_nv01_b_experiment_base_report(
            outdir=tmp_path / "out",
            source_nv01a_dir=source,
        )


def test_nv01_b_report_excludes_preexisting_user_files(tmp_path):
    from weldcore.skill_asset.nv01_b_experiment_base_report import (
        run_nv01_b_experiment_base_report,
    )

    outdir = tmp_path / "nv01b"
    outdir.mkdir()
    (outdir / "user_note.txt").write_text("keep\n", encoding="utf-8")

    summary = run_nv01_b_experiment_base_report(outdir=outdir)

    assert "user_note.txt" not in summary["generated_artifacts"]
    assert sorted(summary["generated_artifacts"]) == [
        path for path in _relative_files(outdir) if path != "user_note.txt"
    ]


def test_nv01_b_report_main_prints_json(tmp_path, capsys):
    from weldcore.skill_asset import nv01_b_experiment_base_report

    nv01_b_experiment_base_report.main(["--outdir", str(tmp_path)])

    output = json.loads(capsys.readouterr().out)
    assert output["overall_status"] == "blocked_for_real_isaac_sim_replay"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_nv01_b_experiment_base_report.py -q
```

Expected: FAIL because report module does not exist.

- [ ] **Step 3: Implement `nv01_b_experiment_base_report.py`**

Implementation requirements:

- `run_nv01_b_experiment_base_report(outdir, source_nv01a_dir=None) -> dict[str, Any]`
- `main(argv=None) -> dict[str, Any]`
- Top-level payload file names:

```python
TOP_LEVEL_PAYLOAD_FILES = {
    "openusd_stage_validation_report": "openusd_stage_validation_report.json",
    "isaac_replay_fixture": "isaac_replay_fixture.json",
    "procedure_sim_parameter_audit": "procedure_sim_parameter_audit.json",
    "sensor_annotation_manifest": "sensor_annotation_manifest.json",
    "simulation_blocking_report": "simulation_blocking_report.json",
    "experiment_reproducibility_manifest": "experiment_reproducibility_manifest.json",
}
TASK_PAYLOAD_FILES = {
    "openusd_task_stage_fragment": "openusd_task_stage_fragment.usda",
    "isaac_replay_task_fixture": "isaac_replay_task_fixture.json",
    "procedure_sim_parameter_audit": "procedure_sim_parameter_audit.json",
    "sensor_annotation_manifest": "sensor_annotation_manifest.json",
    "simulation_blocking_report": "simulation_blocking_report.json",
}
```

Source behavior:

```python
def _ensure_source_nv01a(output_dir: Path, source_nv01a_dir: str | Path | None):
    if source_nv01a_dir is None:
        source_dir = output_dir / "_source_nv01a"
        run_nvidia_digital_twin_report(outdir=source_dir)
        return source_dir, {"source_mode": "generated_default", "source_nv01a_root_ref": "_source_nv01a"}
    source_dir = Path(source_nv01a_dir)
    # Do not auto-generate for explicit paths; load_nv01a_artifacts will fail clearly.
    return source_dir, {"source_mode": "external_source_nv01a", "source_nv01a_root_ref": str(source_dir.resolve())}
```

`generated_artifacts` policy:

- When the report generates `_source_nv01a/`, include `_source_nv01a/...` files in `generated_artifacts` because this command created them.
- Exclude files that existed before the report command, including user files under the output root or a pre-existing `_source_nv01a/`.
- When using an external `--source-nv01a-dir`, do not include external source files in `generated_artifacts`; include only NV01-B outputs.

Summary fields:

```python
{
    "report_id": "nv01-b-openusd-isaac-reproducible-experiment-base",
    "overall_status": "blocked_for_real_isaac_sim_replay",
    "openusd_authoring_status": "ready_for_static_openusd_review",
    "task_count": len(task_payloads),
    "source_nv01a": source_summary,
    "generated_artifacts": sorted(generated_artifacts),
    "tasks": [{"task_id": task_id, "task_output_dir": task_dir_name}, ...],
    "readiness_boundary": [
        "not_isaac_sim_runtime_validation",
        "not_policy_training_result",
        "not_formal_WPS_PQR",
        "not_ready_for_robot_execution",
    ],
    "next_step_recommendation": "Proceed to NV01-C Isaac Sim runtime import/static replay validation only after required runtime, calibration, and real process inputs are available.",
}
```

Markdown summary must include:

- `不是 Isaac Sim runtime 验证`
- `不是 policy training 结果`
- `不是正式 WPS/PQR`
- `不是 ready_for_robot_execution`
- generated artifacts list
- task list

Reuse local helper patterns from `nvidia_digital_twin_report.py`: `_write_json_artifact`, `_write_text_artifact`, `_record_generated_artifact`, `_task_output_dir_name`.

- [ ] **Step 4: Run report tests and focused integration tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_nv01_b_experiment_base.py tests/test_nv01_b_experiment_base_report.py -q
```

Expected: PASS.

- [ ] **Step 5: Run the new report command manually**

Run:

```bash
cd weld-experience-engine
uv run python -m weldcore.skill_asset.nv01_b_experiment_base_report \
  --outdir artifacts/demo/nv01-b-experiment-base
```

Expected:

- command exits 0
- prints JSON summary
- writes `openusd_stage.usda`
- summary `overall_status=blocked_for_real_isaac_sim_replay`
- summary `openusd_authoring_status=ready_for_static_openusd_review`

- [ ] **Step 6: Ensure generated runtime artifacts are not staged**

Run:

```bash
git status --short
```

Expected: `artifacts/` output is ignored or left untracked; do not commit generated runtime artifacts.

- [ ] **Step 7: Commit Task 2**

Run:

```bash
git add weld-experience-engine/weldcore/skill_asset/nv01_b_experiment_base_report.py \
  weld-experience-engine/tests/test_nv01_b_experiment_base_report.py
git commit -m "feat: add nv01-b experiment base report"
```

---

### Task 3: Documentation and HTML Reading Copies

**Files:**
- Modify: `README.md`
- Modify: `details.md`
- Modify: `weld-experience-engine/README.md`
- Modify: `README.html`
- Modify: `details.html`

- [ ] **Step 1: Update root README**

In `README.md`:

- In "当前可运行能力", add NV01-B report capability:

```markdown
- `weldcore.skill_asset.nv01_b_experiment_base_report` 默认生成 NV01-B 可复现实验底座：最小 `openusd_stage.usda`、静态 USD validation report、Isaac replay fixture、K01 参数到仿真参数审计、sensor/annotation manifest、simulation blocking report 和 reproducibility manifest。
```

- Add a command section after K01 + NV01-A:

```bash
cd weld-experience-engine
uv run python -m weldcore.skill_asset.nv01_b_experiment_base_report \
  --outdir artifacts/demo/nv01-b-experiment-base
```

- State boundaries:
  - not Isaac Sim runtime validation
  - not policy training
  - not formal WPS/PQR
  - not ready for robot execution

- Update "下一阶段任务" so NV01-C is next:
  - Isaac Sim runtime import/static replay validation
  - only after runtime, robot asset, TCP/tool/workpiece calibration, minimal sensor layout and key process inputs are available.

- [ ] **Step 2: Update details stage log**

In `details.md`, add a 2026-06-23 bullet group under recent updates:

```markdown
- 完成 NV01-B OpenUSD / Isaac Sim 可复现实验底座。
- 新增 `weldcore.skill_asset.nv01_b_experiment_base` 和 `weldcore.skill_asset.nv01_b_experiment_base_report`，默认从 K01 + NV01-A artifact 生成最小 `openusd_stage.usda`、静态 validation gate、Isaac replay fixture、K01 参数到仿真参数 audit、sensor/annotation manifest、simulation blocking report 和 reproducibility manifest。
- 默认不依赖 Isaac Sim、OpenUSD SDK、GPU 或 `pxr`；`.usda` 只进入静态审查，不宣称 Isaac Sim runtime replay。
- 当前真实 replay 仍被 `blocked_for_real_isaac_sim_replay` 阻塞，主要缺真实 Isaac runtime validation、TCP/tool/workpiece/sensor 标定、H300 工站日志、电流/电压、WPS/PQR、专家审查和真实质量反馈。
```

Also update:

- "尚未完成": remove wording that says NV01-B `.usda` stage is not written; replace with "NV01-B 已写出静态 `.usda` 原型，但 Isaac Sim runtime 尚未接入。"
- "下一步建议": recommend NV01-C, not another NV01-B.
- "当前可交付物清单": add the new report command.

- [ ] **Step 3: Update engine README**

In `weld-experience-engine/README.md`, add a section after K01 + NV01-A:

```markdown
## NV01-B 可复现实验底座

```bash
uv run python -m weldcore.skill_asset.nv01_b_experiment_base_report \
  --outdir artifacts/demo/nv01-b-experiment-base
```

`nv01_b_experiment_base_report` 默认生成 `_source_nv01a`，再输出最小 `openusd_stage.usda`、静态 USD validation report、Isaac replay fixture、procedure simulation parameter audit、sensor annotation manifest、simulation blocking report 和 reproducibility manifest。它不需要 Isaac Sim 或 OpenUSD SDK；默认状态仍是 `blocked_for_real_isaac_sim_replay`，不是 runtime replay、policy training、正式 WPS/PQR 或真实机器人执行验证。
```

- [ ] **Step 4: Regenerate root HTML reading copies**

Use this local one-off renderer from repo root. Do not commit a temporary script.

```bash
python - <<'PY'
from pathlib import Path
import html
import re

STYLE_RE = re.compile(r"<style>(.*?)</style>", re.S)
STYLE = STYLE_RE.search(Path("README.html").read_text(encoding="utf-8")).group(1)

def inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\\1</code>", escaped)
    escaped = re.sub(r"\\[([^\\]]+)\\]\\(([^)]+)\\)", r'<a href="\\2">\\1</a>', escaped)
    return escaped

def markdown_body(markdown: str) -> str:
    lines = markdown.splitlines()
    out = []
    i = 0
    in_list = False
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            if in_list:
                out.append("</ul>")
                in_list = False
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            out.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
        elif line.startswith("# "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h1>{inline(line[2:])}</h1>")
        elif line.startswith("## "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.startswith("### "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h3>{inline(line[4:])}</h3>")
        elif line.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(line[2:])}</li>")
        elif not line.strip():
            if in_list:
                out.append("</ul>")
                in_list = False
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<p>{inline(line)}</p>")
        i += 1
    if in_list:
        out.append("</ul>")
    return "\\n".join(out)

def render(source: str, target: str, title: str) -> None:
    body = markdown_body(Path(source).read_text(encoding="utf-8"))
    Path(target).write_text(
        f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>{STYLE}</style>
</head>
<body>
<main>
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

- [ ] **Step 5: Documentation grep checks**

Run:

```bash
rg -n "nv01_b_experiment_base_report|NV01-B|openusd_stage.usda|blocked_for_real_isaac_sim_replay|not_isaac_sim_runtime_validation" README.md details.md weld-experience-engine/README.md
rg -n "NV01-B 尚未写出真实 OpenUSD|OpenUSD Authoring Spike" README.md details.md || true
```

Expected:

- First command finds new capability and boundaries.
- Second command should not find outdated claims that NV01-B still has not written any `.usda` stage. It may find historical plan/spec titles only outside README/details.

- [ ] **Step 6: Commit Task 3**

Run:

```bash
git add README.md README.html details.md details.html weld-experience-engine/README.md
git commit -m "docs: document nv01-b experiment base"
```

---

### Task 4: Full Verification, Final Review, and Cleanup

**Files:**
- Modify only if needed from verification findings.

- [ ] **Step 1: Run focused tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_nv01_b_experiment_base.py tests/test_nv01_b_experiment_base_report.py tests/test_nvidia_digital_twin_report.py tests/test_weld_procedure_contract.py -q
```

Expected: PASS.

- [ ] **Step 2: Run full test suite**

Run:

```bash
cd weld-experience-engine
uv run pytest -q
```

Expected: PASS. Record exact pass count for final response and details if docs still need it.

- [ ] **Step 3: Run default report commands**

Run:

```bash
cd weld-experience-engine
uv run python -m weldcore.skill_asset.nvidia_digital_twin_report \
  --outdir artifacts/demo/nvidia-digital-twin-foundation
uv run python -m weldcore.skill_asset.nv01_b_experiment_base_report \
  --outdir artifacts/demo/nv01-b-experiment-base
```

Expected:

- both commands exit 0
- NV01-B command writes `openusd_stage.usda`
- NV01-B summary prints `blocked_for_real_isaac_sim_replay`
- no generated runtime artifacts are staged

- [ ] **Step 4: Check git status**

Run:

```bash
git status --short
```

Expected: only intended source/docs/test changes are tracked or staged. Generated `artifacts/`, `.pytest_cache/`, `__pycache__/`, `.venv/` are not staged.

- [ ] **Step 5: Dispatch final code review subagent**

Use a fresh reviewer with:

- plan path: `docs/superpowers/plans/2026-06-23-nv01-b-openusd-isaac-reproducible-experiment-base.md`
- spec path: `docs/superpowers/specs/2026-06-23-nv01-b-openusd-isaac-reproducible-experiment-base-design.md`
- diff summary from `git log --oneline` and `git diff origin/main...HEAD --stat`
- ask for bugs, scope drift, missing tests, status vocabulary inconsistencies, and generated artifact leakage.

If reviewer finds blocking issues, fix them and repeat focused verification.

- [ ] **Step 6: Commit verification fixes if any**

If no changes: no commit.

If changes were needed:

```bash
git add <changed-files>
git commit -m "fix: finalize nv01-b experiment base"
```

---

## Final Acceptance Checklist

- [ ] Spec approved by spec reviewer.
- [ ] Plan approved by plan reviewer.
- [ ] `nv01_b_experiment_base.py` generates `.usda`, validation, fixture, audit, sensor manifest, blocking report and reproducibility manifest.
- [ ] `nv01_b_experiment_base_report.py` writes top-level and per-task artifacts.
- [ ] Explicit missing `--source-nv01a-dir` fails.
- [ ] Default omitted source generates `_source_nv01a/`.
- [ ] No Isaac Sim / OpenUSD SDK dependency added.
- [ ] README/details/engine README and HTML copies updated.
- [ ] Focused and full tests pass.
- [ ] Generated runtime artifacts are not staged.
