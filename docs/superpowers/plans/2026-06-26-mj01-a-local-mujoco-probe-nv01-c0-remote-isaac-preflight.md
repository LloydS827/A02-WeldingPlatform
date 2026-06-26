# MJ01-A Local MuJoCo Probe + NV01-C0 Remote Isaac Preflight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现本地 MuJoCo optional probe 和 Isaac 远端 preflight，从 NV01-C + MJ01 readiness pack 生成可复跑的 MJ01-A/NV01-C0 artifact。

**Architecture:** 新增一个 builder 读取 readiness pack，不写文件；新增 report CLI 默认自举 `_source_readiness/` 并写 JSON/Markdown artifact。MuJoCo 通过 optional extra 管理，默认路径未安装 MuJoCo 时输出 skipped report 且测试通过；Isaac 只生成远端 preflight 契约，不引入本地 Isaac 依赖。

**Tech Stack:** Python 3.10+, standard-library JSON/Path/argparse/importlib, optional `mujoco` Python package, existing `weldcore.skill_asset.nv01_c_mj01_readiness_report`, pytest, Markdown docs and static HTML reading copies.

---

## Scope Check

In scope:

- 新增 optional dependency extra：`mujoco = ["mujoco>=3.2"]`
- 新增 builder：`weldcore.skill_asset.mj01_mujoco_probe`
- 新增 report CLI：`weldcore.skill_asset.mj01_mujoco_probe_report`
- 新增 tests：
  - `tests/test_mj01_mujoco_probe.py`
  - `tests/test_mj01_mujoco_probe_report.py`
- 输出：
  - `mj01_a_summary.md`
  - `mj01_a_summary.json`
  - `mj01_mujoco_runtime_probe_report.json`
  - `mj01_mujoco_model_input_resolution_report.json`
  - `mj01_mujoco_probe_report.json`
  - `nv01_c0_isaac_remote_preflight_report.json`
  - `mj01_a_reproducibility_manifest.json`
  - per-task `mj01_task_trajectory_dry_run_input.json`
  - per-task `nv01_c0_task_isaac_remote_preflight_input.json`
- 更新 `README.md`, `README.html`, `details.md`, `details.html`, `weld-experience-engine/README.md`
- 验证与 PR 合并清理

Out of scope:

- Isaac Sim 本地安装或 runtime 执行。
- 完整 URDF->MJCF 转换器。
- MuJoCo dynamics validation 结论。
- 接触、碰撞、热过程或焊接质量仿真。
- Isaac Lab / MuJoCo policy training。
- Robot execution。
- Formal WPS/PQR。

## File Map

- Modify: `weld-experience-engine/pyproject.toml`
  - Add optional dependency extra `mujoco = ["mujoco>=3.2"]`.
- Create: `weld-experience-engine/weldcore/skill_asset/mj01_mujoco_probe.py`
  - Load readiness pack.
  - Probe optional MuJoCo runtime via importlib.
  - Resolve robot body asset report and source URDF metadata.
  - Build MuJoCo runtime/model/probe payloads.
  - Build Isaac remote preflight payloads.
  - Do not write files.
- Create: `weld-experience-engine/weldcore/skill_asset/mj01_mujoco_probe_report.py`
  - CLI/report entry point.
  - Generate `_source_readiness/` by default.
  - Accept `--source-readiness-dir`.
  - Write JSON and Markdown outputs.
- Create: `weld-experience-engine/tests/test_mj01_mujoco_probe.py`
  - Builder tests.
- Create: `weld-experience-engine/tests/test_mj01_mujoco_probe_report.py`
  - CLI/report tests.
- Modify: `README.md`
  - Add current capability and next stage route.
- Modify: `README.html`
  - Sync root HTML reading copy.
- Modify: `details.md`
  - Add stage entry and update completed/not completed/commands.
- Modify: `details.html`
  - Sync details HTML reading copy.
- Modify: `weld-experience-engine/README.md`
  - Add optional MuJoCo install and report command.

---

### Task 1: Core MJ01-A/NV01-C0 Builder

**Files:**
- Create: `weld-experience-engine/tests/test_mj01_mujoco_probe.py`
- Create: `weld-experience-engine/weldcore/skill_asset/mj01_mujoco_probe.py`

- [ ] **Step 1: Write failing builder tests**

Create `weld-experience-engine/tests/test_mj01_mujoco_probe.py`:

```python
import json

import pytest

from weldcore.skill_asset.mj01_mujoco_probe import (
    CANONICAL_MJ01A_NV01C0_STATUS,
    MissingReadinessArtifactError,
    build_mj01_a_nv01_c0_payloads,
    load_readiness_artifacts,
    probe_mujoco_runtime,
)
from weldcore.skill_asset.nv01_c_mj01_readiness_report import (
    run_nv01_c_mj01_readiness_report,
)


RUNTIME_KEYS = {
    "report_id",
    "runtime_target",
    "runtime_probe_status",
    "mujoco_python_import_status",
    "mujoco_version",
    "install_hint",
    "optional_dependency_extra",
    "blocked_by",
    "readiness_boundary",
}

MODEL_KEYS = {
    "report_id",
    "source_readiness_ref",
    "source_mujoco_feasibility_ref",
    "robot_body_asset_report_ref",
    "source_urdf_status",
    "source_urdf_ref",
    "link_count",
    "joint_count",
    "mesh_reference_count",
    "frame_binding_inputs",
    "trajectory_replay_inputs",
    "blocked_by",
    "readiness_boundary",
}

PROBE_KEYS = {
    "report_id",
    "runtime_probe_status",
    "minimal_mjcf_probe_status",
    "real_urdf_load_status",
    "real_urdf_load_error",
    "model_load_diagnostics",
    "model_load_blocking_items",
    "real_urdf_load_next_step",
    "trajectory_dry_run_status",
    "task_reports",
    "blocked_by",
    "readiness_boundary",
}

ISAAC_PREFLIGHT_KEYS = {
    "report_id",
    "runtime_target",
    "runtime_location",
    "local_runtime_status",
    "remote_runtime_status",
    "source_stage_ref",
    "source_replay_fixture_ref",
    "required_prim_paths",
    "frame_bindings",
    "trajectory_bindings",
    "sensor_placeholders",
    "expected_remote_outputs",
    "expected_isaac_sim_version",
    "required_gpu_driver",
    "remote_launch_method",
    "remote_stage_path_policy",
    "remote_fixture_path_policy",
    "expected_runtime_report_schema",
    "blocked_by",
    "readiness_boundary",
}


def _source_readiness(tmp_path):
    source_dir = tmp_path / "readiness"
    run_nv01_c_mj01_readiness_report(outdir=source_dir)
    return source_dir


def test_load_readiness_artifacts_requires_top_level_and_task_sources(tmp_path):
    source_dir = _source_readiness(tmp_path)
    artifacts = load_readiness_artifacts(source_dir)

    assert artifacts["summary"]["report_id"] == (
        "nv01-c-mj01-runtime-replay-readiness-pack"
    )
    assert artifacts["mujoco_feasibility"]["urdf_ref"].endswith(
        "robot_body_asset_report.json"
    )
    assert artifacts["source_readiness_dir"] == source_dir
    assert artifacts["task_ids"]
    assert artifacts["task_artifacts"]
    assert artifacts["robot_body_asset_report"]

    (source_dir / "mujoco_lightweight_replay_feasibility_report.json").unlink()
    with pytest.raises(
        MissingReadinessArtifactError,
        match="mujoco_lightweight_replay_feasibility_report.json",
    ):
        load_readiness_artifacts(source_dir)


def test_load_readiness_artifacts_requires_task_artifacts(tmp_path):
    source_dir = _source_readiness(tmp_path)
    summary = json.loads(
        (source_dir / "nv01_c_mj01_summary.json").read_text(encoding="utf-8")
    )
    task_dir = source_dir / summary["tasks"][0]["task_output_dir"]
    (task_dir / "mujoco_task_replay_feasibility.json").unlink()

    with pytest.raises(
        MissingReadinessArtifactError,
        match="mujoco_task_replay_feasibility.json",
    ):
        load_readiness_artifacts(source_dir)


def test_probe_mujoco_runtime_missing_path(monkeypatch):
    def fake_import_module(name):
        raise ModuleNotFoundError(name)

    monkeypatch.setattr("importlib.import_module", fake_import_module)

    probe = probe_mujoco_runtime()

    assert RUNTIME_KEYS <= set(probe)
    assert probe["report_id"] == "mj01-a-mujoco-runtime-probe"
    assert probe["runtime_target"] == "MuJoCo"
    assert probe["runtime_probe_status"] == "skipped_by_missing_mujoco_runtime"
    assert probe["mujoco_python_import_status"] == "missing"
    assert probe["mujoco_version"] is None
    assert probe["optional_dependency_extra"] == "mujoco"
    assert "uv sync --extra dev --extra viz --extra mujoco" in probe["install_hint"]
    assert "mujoco_runtime" in probe["blocked_by"]
    assert "not_mujoco_dynamics_validation" in probe["readiness_boundary"]


def test_probe_mujoco_runtime_import_error_path(monkeypatch):
    def fake_import_module(name):
        raise RuntimeError("broken native library")

    monkeypatch.setattr("importlib.import_module", fake_import_module)

    probe = probe_mujoco_runtime()

    assert RUNTIME_KEYS <= set(probe)
    assert probe["runtime_probe_status"] == "blocked_by_mujoco_import_error"
    assert probe["mujoco_python_import_status"] == "import_error"
    assert "broken native library" in probe["import_error"]
    assert "mujoco_import_error" in probe["blocked_by"]


def test_probe_mujoco_runtime_available_path(monkeypatch):
    class FakeMjModel:
        @staticmethod
        def from_xml_string(xml):
            assert "<mujoco" in xml
            return object()

    class FakeMujoco:
        __version__ = "test-mujoco"
        MjModel = FakeMjModel

    def fake_import_module(name):
        assert name == "mujoco"
        return FakeMujoco

    monkeypatch.setattr("importlib.import_module", fake_import_module)

    probe = probe_mujoco_runtime()

    assert RUNTIME_KEYS <= set(probe)
    assert probe["runtime_probe_status"] == "available"
    assert probe["mujoco_python_import_status"] == "imported"
    assert probe["mujoco_version"] == "test-mujoco"
    assert probe["blocked_by"] == []


def test_build_payloads_without_mujoco_still_emit_preflight_reports(tmp_path, monkeypatch):
    def fake_import_module(name):
        raise ModuleNotFoundError(name)

    monkeypatch.setattr("importlib.import_module", fake_import_module)
    artifacts = load_readiness_artifacts(_source_readiness(tmp_path))

    payloads = build_mj01_a_nv01_c0_payloads(artifacts)

    assert set(payloads) == {
        "mujoco_runtime_probe_report",
        "mujoco_model_input_resolution_report",
        "mujoco_probe_report",
        "isaac_remote_preflight_report",
        "reproducibility_manifest",
        "task_payloads",
    }

    runtime = payloads["mujoco_runtime_probe_report"]
    assert RUNTIME_KEYS <= set(runtime)
    assert runtime["runtime_probe_status"] == "skipped_by_missing_mujoco_runtime"

    model = payloads["mujoco_model_input_resolution_report"]
    assert MODEL_KEYS <= set(model)
    assert model["report_id"] == "mj01-a-mujoco-model-input-resolution"
    assert model["source_readiness_ref"] == "nv01_c_mj01_summary.json"
    assert model["source_mujoco_feasibility_ref"] == (
        "mujoco_lightweight_replay_feasibility_report.json"
    )
    assert model["robot_body_asset_report_ref"].endswith("robot_body_asset_report.json")
    assert model["source_urdf_status"] in {
        "resolved_from_robot_body_asset_report",
        "blocked_by_missing_robot_body_asset_source_urdf",
    }
    assert model["source_urdf_ref"] != artifacts["robot_body_asset_report"].get(
        "source_urdf"
    )
    assert model["link_count"] >= 0
    assert model["joint_count"] >= 0
    assert model["mesh_reference_count"] >= 0
    assert model["frame_binding_inputs"]
    assert model["trajectory_replay_inputs"]
    assert model["blocked_by"] is not None
    assert "not_mujoco_dynamics_validation" in model["readiness_boundary"]

    probe = payloads["mujoco_probe_report"]
    assert PROBE_KEYS <= set(probe)
    assert probe["report_id"] == "mj01-a-mujoco-probe"
    assert probe["minimal_mjcf_probe_status"] == "skipped_by_missing_mujoco_runtime"
    assert probe["real_urdf_load_status"] == "skipped_by_missing_mujoco_runtime"
    assert probe["real_urdf_load_error"] is None
    assert probe["model_load_diagnostics"]
    assert probe["model_load_blocking_items"]
    assert probe["real_urdf_load_next_step"]
    assert probe["trajectory_dry_run_status"] == "dry_run_inputs_prepared"
    assert probe["task_reports"]
    assert "not_mujoco_dynamics_validation" in probe["readiness_boundary"]

    isaac = payloads["isaac_remote_preflight_report"]
    assert ISAAC_PREFLIGHT_KEYS <= set(isaac)
    assert isaac["report_id"] == "nv01-c0-isaac-remote-preflight"
    assert isaac["runtime_target"] == "Isaac Sim"
    assert isaac["runtime_location"] == "remote_or_server_required"
    assert isaac["local_runtime_status"] == "not_installed_locally_by_design"
    assert isaac["remote_runtime_status"] == "blocked_by_missing_remote_isaac_runtime"
    assert isaac["source_stage_ref"] == "openusd_stage.usda"
    assert isaac["source_replay_fixture_ref"] == "isaac_replay_fixture.json"
    assert isaac["required_prim_paths"]
    assert isaac["frame_bindings"]
    assert isaac["trajectory_bindings"]
    assert isaac["sensor_placeholders"]
    assert isaac["expected_remote_outputs"]
    assert isaac["expected_isaac_sim_version"] == "to_be_selected_on_remote_runtime"
    assert isaac["required_gpu_driver"] == "nvidia_driver_required_on_remote_runtime"
    assert isaac["remote_launch_method"] == "headless_or_workstation_server_runner"
    assert isaac["remote_stage_path_policy"]
    assert isaac["remote_fixture_path_policy"]
    assert "stage_import_status" in isaac["expected_runtime_report_schema"]
    assert "not_isaac_sim_runtime_validation" in isaac["readiness_boundary"]

    task_payloads = payloads["task_payloads"]
    assert task_payloads
    for task_id, task in task_payloads.items():
        assert task["mj01_task_trajectory_dry_run_input"]["task_id"] == task_id
        assert task["nv01_c0_task_isaac_remote_preflight_input"]["task_id"] == task_id
        assert "not_formal_WPS_PQR" in task[
            "mj01_task_trajectory_dry_run_input"
        ]["readiness_boundary"]

    serialized = json.dumps(payloads, ensure_ascii=False)
    assert str(tmp_path) not in serialized
    assert str(artifacts["source_readiness_dir"]) not in serialized
    assert artifacts["robot_body_asset_report"].get("source_urdf") not in serialized


def test_build_payloads_with_mocked_mujoco_available_runs_minimal_probe(tmp_path, monkeypatch):
    class FakeMjModel:
        @staticmethod
        def from_xml_string(xml):
            assert "<mujoco" in xml
            return object()

        @staticmethod
        def from_xml_path(path):
            raise ValueError(f"mock compiler rejected {path}")

    class FakeMujoco:
        __version__ = "test-mujoco"
        MjModel = FakeMjModel

    def fake_import_module(name):
        assert name == "mujoco"
        return FakeMujoco

    monkeypatch.setattr("importlib.import_module", fake_import_module)
    artifacts = load_readiness_artifacts(_source_readiness(tmp_path))

    payloads = build_mj01_a_nv01_c0_payloads(artifacts)
    runtime = payloads["mujoco_runtime_probe_report"]
    probe = payloads["mujoco_probe_report"]

    assert runtime["runtime_probe_status"] == "available"
    assert runtime["mujoco_version"] == "test-mujoco"
    assert probe["minimal_mjcf_probe_status"] == "passed_minimal_mjcf_sanity_probe"
    assert probe["real_urdf_load_status"] == "blocked_by_mujoco_model_load_error"
    assert "mock compiler rejected" in probe["real_urdf_load_error"]
    assert probe["model_load_diagnostics"]["error_type"] == "ValueError"
    assert probe["model_load_blocking_items"]
    assert probe["real_urdf_load_next_step"] in {
        "repair_mesh_paths_before_mujoco_load",
        "prepare_minimal_mjcf_adapter",
    }

    serialized = json.dumps(payloads, ensure_ascii=False)
    assert str(tmp_path) not in serialized


def test_canonical_status_vocabulary():
    expected = {
        "skipped_by_missing_mujoco_runtime",
        "available",
        "blocked_by_mujoco_import_error",
        "passed_minimal_mjcf_sanity_probe",
        "blocked_by_mujoco_model_load_error",
        "blocked_by_missing_remote_isaac_runtime",
        "not_installed_locally_by_design",
        "not_mujoco_dynamics_validation",
        "not_isaac_sim_runtime_validation",
        "not_policy_training_result",
        "not_formal_WPS_PQR",
        "not_ready_for_robot_execution",
    }
    assert expected <= CANONICAL_MJ01A_NV01C0_STATUS
    assert "ready_for_robot_execution" not in CANONICAL_MJ01A_NV01C0_STATUS
```


- [ ] **Step 2: Run builder tests to verify failure**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_mj01_mujoco_probe.py -q
```

Expected: FAIL because module does not exist.

- [ ] **Step 3: Implement builder**

Create `weld-experience-engine/weldcore/skill_asset/mj01_mujoco_probe.py`.

Implementation requirements:

- Define `CANONICAL_MJ01A_NV01C0_STATUS`.
- Define `READINESS_BOUNDARY`:

```python
[
    "not_mujoco_dynamics_validation",
    "not_isaac_sim_runtime_validation",
    "not_policy_training_result",
    "not_formal_WPS_PQR",
    "not_ready_for_robot_execution",
]
```

- Define `MissingReadinessArtifactError(RuntimeError)`.
- Define `load_readiness_artifacts(source_readiness_dir)`.
- Required top-level files:
  - `nv01_c_mj01_summary.json`
  - `mujoco_lightweight_replay_feasibility_report.json`
  - `isaac_runtime_validation_input_manifest.json`
  - `runtime_replay_blocking_report.json`
  - `readiness_reproducibility_manifest.json`
- Required per-task files from `summary["tasks"]`:
  - `mujoco_task_replay_feasibility.json`
  - `isaac_runtime_task_validation_input.json`
- Resolve `robot_body_asset_report_ref` from `mujoco_feasibility["urdf_ref"]`.
  - For generated default readiness, first try `source_readiness_dir / "_source_nv01b" / "_source_nv01a" / "_source_demo_evidence" / urdf_ref`.
  - Then try `source_readiness_dir / urdf_ref`.
  - Do not serialize absolute paths.
- Load `robot_body_asset_report.json` if found; otherwise create blocked metadata.
- Define `probe_mujoco_runtime()`.
  - Use `importlib.import_module("mujoco")`.
  - Missing module -> `skipped_by_missing_mujoco_runtime`.
  - Import error -> `blocked_by_mujoco_import_error`.
  - Success -> `available`, include `mujoco.__version__` when present.
- Define `build_mj01_a_nv01_c0_payloads(artifacts)`.
  - It calls `probe_mujoco_runtime()`.
  - When MuJoCo is missing, skip minimal MJCF and real URDF load.
  - When MuJoCo is available, attempt minimal MJCF sanity model with `mujoco.MjModel.from_xml_string(...)`.
  - Attempt real URDF load only if `source_urdf` is resolvable and MuJoCo is available. Catch all exceptions and report them.
  - Never raise due to MuJoCo model load failure.

Required payload keys:

```python
{
    "mujoco_runtime_probe_report",
    "mujoco_model_input_resolution_report",
    "mujoco_probe_report",
    "isaac_remote_preflight_report",
    "reproducibility_manifest",
    "task_payloads",
}
```

- [ ] **Step 4: Run builder tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_mj01_mujoco_probe.py -q
```

Expected: PASS.

---

### Task 2: Report CLI and Artifact Writer

**Files:**
- Create: `weld-experience-engine/tests/test_mj01_mujoco_probe_report.py`
- Create: `weld-experience-engine/weldcore/skill_asset/mj01_mujoco_probe_report.py`

- [ ] **Step 1: Write failing report tests**

Create `weld-experience-engine/tests/test_mj01_mujoco_probe_report.py`:

```python
import json

import pytest


EXPECTED_TOP_LEVEL = {
    "mj01_a_summary.md",
    "mj01_a_summary.json",
    "mj01_mujoco_runtime_probe_report.json",
    "mj01_mujoco_model_input_resolution_report.json",
    "mj01_mujoco_probe_report.json",
    "nv01_c0_isaac_remote_preflight_report.json",
    "mj01_a_reproducibility_manifest.json",
}

EXPECTED_TASK = {
    "mj01_task_trajectory_dry_run_input.json",
    "nv01_c0_task_isaac_remote_preflight_input.json",
}


def _relative_files(root):
    return sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _all_text(root):
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in root.rglob("*")
        if path.is_file() and path.suffix in {".json", ".md"}
    )


def test_mj01_a_report_writes_default_artifacts(tmp_path, monkeypatch):
    def fake_import_module(name):
        raise ModuleNotFoundError(name)

    monkeypatch.setattr("importlib.import_module", fake_import_module)

    from weldcore.skill_asset.mj01_mujoco_probe_report import (
        run_mj01_mujoco_probe_report,
    )

    outdir = tmp_path / "mj01a"
    summary = run_mj01_mujoco_probe_report(outdir=outdir)

    assert summary["report_id"] == "mj01-a-local-mujoco-probe-nv01-c0-remote-isaac-preflight"
    assert summary["source_readiness"]["source_mode"] == "generated_default"
    assert summary["mujoco_runtime_status"] == "skipped_by_missing_mujoco_runtime"
    assert summary["isaac_remote_status"] == "blocked_by_missing_remote_isaac_runtime"
    assert "not_mujoco_dynamics_validation" in summary["readiness_boundary"]
    assert "not_isaac_sim_runtime_validation" in summary["readiness_boundary"]
    assert "not_formal_WPS_PQR" in summary["readiness_boundary"]
    assert "not_ready_for_robot_execution" in summary["readiness_boundary"]
    assert sorted(summary["generated_artifacts"]) == _relative_files(outdir)

    for filename in EXPECTED_TOP_LEVEL:
        assert (outdir / filename).exists()

    runtime = _json(outdir / "mj01_mujoco_runtime_probe_report.json")
    model = _json(outdir / "mj01_mujoco_model_input_resolution_report.json")
    probe = _json(outdir / "mj01_mujoco_probe_report.json")
    isaac = _json(outdir / "nv01_c0_isaac_remote_preflight_report.json")

    assert runtime["report_id"] == "mj01-a-mujoco-runtime-probe"
    assert runtime["runtime_target"] == "MuJoCo"
    assert runtime["runtime_probe_status"] == "skipped_by_missing_mujoco_runtime"
    assert runtime["readiness_boundary"]
    assert model["report_id"] == "mj01-a-mujoco-model-input-resolution"
    assert model["source_readiness_ref"] == "nv01_c_mj01_summary.json"
    assert model["source_mujoco_feasibility_ref"] == (
        "mujoco_lightweight_replay_feasibility_report.json"
    )
    assert model["blocked_by"] is not None
    assert probe["report_id"] == "mj01-a-mujoco-probe"
    assert probe["real_urdf_load_error"] is None
    assert probe["trajectory_dry_run_status"] == "dry_run_inputs_prepared"
    assert probe["task_reports"]
    assert isaac["report_id"] == "nv01-c0-isaac-remote-preflight"
    assert isaac["source_stage_ref"] == "openusd_stage.usda"
    assert isaac["source_replay_fixture_ref"] == "isaac_replay_fixture.json"
    assert isaac["required_prim_paths"]
    assert isaac["frame_bindings"]
    assert isaac["trajectory_bindings"]
    assert isaac["sensor_placeholders"]
    assert isaac["expected_remote_outputs"]
    assert "stage_import_status" in isaac["expected_runtime_report_schema"]

    for task in summary["tasks"]:
        task_dir = outdir / task["task_output_dir"]
        for filename in EXPECTED_TASK:
            assert (task_dir / filename).exists()
        task_mj01 = _json(task_dir / "mj01_task_trajectory_dry_run_input.json")
        task_isaac = _json(task_dir / "nv01_c0_task_isaac_remote_preflight_input.json")
        assert task_mj01["task_id"] == task["task_id"]
        assert task_mj01["trajectory_ref"]
        assert task_isaac["task_id"] == task["task_id"]
        assert task_isaac["stage_task_prim_ref"]

    markdown = (outdir / "mj01_a_summary.md").read_text(encoding="utf-8")
    assert "不是 MuJoCo dynamics validation" in markdown
    assert "不是 Isaac Sim runtime 验证" in markdown
    assert "不是 policy training 结果" in markdown
    assert "不是正式 WPS/PQR" in markdown
    assert "不是 ready_for_robot_execution" in markdown

    serialized = _all_text(outdir)
    assert str(tmp_path) not in serialized


def test_mj01_a_report_explicit_missing_source_fails(tmp_path):
    from weldcore.skill_asset.mj01_mujoco_probe import MissingReadinessArtifactError
    from weldcore.skill_asset.mj01_mujoco_probe_report import (
        run_mj01_mujoco_probe_report,
    )

    with pytest.raises(MissingReadinessArtifactError, match="missing_source_readiness_dir"):
        run_mj01_mujoco_probe_report(
            outdir=tmp_path / "out",
            source_readiness_dir=tmp_path / "missing",
        )


def test_mj01_a_report_explicit_source_uses_stable_refs(tmp_path, monkeypatch):
    def fake_import_module(name):
        raise ModuleNotFoundError(name)

    monkeypatch.setattr("importlib.import_module", fake_import_module)

    from weldcore.skill_asset.nv01_c_mj01_readiness_report import (
        run_nv01_c_mj01_readiness_report,
    )
    from weldcore.skill_asset.mj01_mujoco_probe_report import (
        run_mj01_mujoco_probe_report,
    )

    source = tmp_path / "source"
    outdir = tmp_path / "out"
    run_nv01_c_mj01_readiness_report(outdir=source)

    summary = run_mj01_mujoco_probe_report(
        outdir=outdir,
        source_readiness_dir=source,
    )
    manifest = _json(outdir / "mj01_a_reproducibility_manifest.json")

    assert summary["source_readiness"]["source_mode"] == "external_source_readiness"
    assert summary["source_readiness"]["source_readiness_root_ref"] == "<source-readiness-dir>"
    assert not any(path.startswith("_source_readiness/") for path in summary["generated_artifacts"])
    assert manifest["source_readiness_root_ref"] == "<source-readiness-dir>"
    assert "--source-readiness-dir <source-readiness-dir>" in manifest["command"]

    serialized = _all_text(outdir)
    assert str(source) not in serialized
    assert str(tmp_path) not in serialized


def test_mj01_a_report_main_prints_json(tmp_path, capsys, monkeypatch):
    def fake_import_module(name):
        raise ModuleNotFoundError(name)

    monkeypatch.setattr("importlib.import_module", fake_import_module)

    from weldcore.skill_asset import mj01_mujoco_probe_report

    mj01_mujoco_probe_report.main(["--outdir", str(tmp_path)])

    output = json.loads(capsys.readouterr().out)
    assert output["mujoco_runtime_status"] == "skipped_by_missing_mujoco_runtime"
```


- [ ] **Step 2: Run report tests to verify failure**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_mj01_mujoco_probe_report.py -q
```

Expected: FAIL because module does not exist.

- [ ] **Step 3: Implement report CLI**

Create `weld-experience-engine/weldcore/skill_asset/mj01_mujoco_probe_report.py`.

Implementation requirements:

- Public function:

```python
def run_mj01_mujoco_probe_report(
    outdir: str | Path,
    source_readiness_dir: str | Path | None = None,
) -> dict[str, Any]:
```

- Default source behavior:
  - If `source_readiness_dir is None`, run `run_nv01_c_mj01_readiness_report(outdir=output_dir / "_source_readiness")`.
  - If explicit source missing or incomplete, raise `MissingReadinessArtifactError`.
- Top-level output filenames exactly:
  - `mj01_a_summary.md`
  - `mj01_a_summary.json`
  - `mj01_mujoco_runtime_probe_report.json`
  - `mj01_mujoco_model_input_resolution_report.json`
  - `mj01_mujoco_probe_report.json`
  - `nv01_c0_isaac_remote_preflight_report.json`
  - `mj01_a_reproducibility_manifest.json`
- Per-task output filenames exactly:
  - `mj01_task_trajectory_dry_run_input.json`
  - `nv01_c0_task_isaac_remote_preflight_input.json`
- Summary fields:
  - `report_id = "mj01-a-local-mujoco-probe-nv01-c0-remote-isaac-preflight"`
  - `overall_status`
  - `mujoco_runtime_status`
  - `mujoco_model_status`
  - `isaac_remote_status`
  - `source_readiness`
  - `task_count`
  - `tasks`
  - `generated_artifacts`
  - `readiness_boundary`
  - `next_step_recommendation`
- Markdown boundaries:
  - `不是 MuJoCo dynamics validation`
  - `不是 Isaac Sim runtime 验证`
  - `不是 policy training 结果`
  - `不是正式 WPS/PQR`
  - `不是 ready_for_robot_execution`

- [ ] **Step 4: Run report tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_mj01_mujoco_probe.py tests/test_mj01_mujoco_probe_report.py -q
```

Expected: PASS.

---

### Task 3: Optional MuJoCo Dependency and Documentation

**Files:**
- Modify: `weld-experience-engine/pyproject.toml`
- Modify: `README.md`
- Modify: `README.html`
- Modify: `details.md`
- Modify: `details.html`
- Modify: `weld-experience-engine/README.md`

- [ ] **Step 1: Add optional dependency extra**

Modify `weld-experience-engine/pyproject.toml`:

```toml
[project.optional-dependencies]
viz = ["rerun-sdk>=0.15"]
dev = ["pytest>=7.4"]
mujoco = ["mujoco>=3.2"]
```

Do not add MuJoCo to default dependencies.

- [ ] **Step 2: Update README.md**

Add to current capabilities:

```markdown
- `weldcore.skill_asset.mj01_mujoco_probe_report` 默认生成 MJ01-A + NV01-C0 probe/preflight pack：本地 MuJoCo runtime probe、MuJoCo model input resolution、MuJoCo probe report、Isaac remote preflight report 和 per-task dry-run/preflight 输入清单。MuJoCo 通过 optional extra 安装；默认路径未安装 MuJoCo 时输出 `skipped_by_missing_mujoco_runtime`，不导致默认测试失败。Isaac Sim 不在本地安装，只生成远端/服务器 preflight。
```

Add command section after NV01-C + MJ01 Readiness Pack:

```markdown
## MJ01-A Local MuJoCo Probe + NV01-C0 Remote Isaac Preflight

默认入口：

```bash
cd weld-experience-engine
uv run python -m weldcore.skill_asset.mj01_mujoco_probe_report \
  --outdir artifacts/demo/mj01-a-local-mujoco-probe
```

本地安装 MuJoCo probe extra：

```bash
uv sync --extra dev --extra viz --extra mujoco
```

该命令默认自举 `_source_readiness/`。未安装 MuJoCo 时仍会生成 report，状态为 `skipped_by_missing_mujoco_runtime`；安装 MuJoCo 后可执行最小 MJCF sanity probe，并尝试真实 URDF load。Isaac Sim 不在本机安装，本阶段只输出 `nv01_c0_isaac_remote_preflight_report.json`。
```

- [ ] **Step 3: Update weld-experience-engine/README.md**

Add concise command and optional install section for:

```bash
uv sync --extra dev --extra viz --extra mujoco
uv run python -m weldcore.skill_asset.mj01_mujoco_probe_report \
  --outdir artifacts/demo/mj01-a-local-mujoco-probe
```

Mention generated artifacts, default missing-MuJoCo behavior, and Isaac remote boundary.

- [ ] **Step 4: Update details.md**

Add a new 2026-06-26 bullet group or extend existing group:

- Implemented `mj01_mujoco_probe_report`.
- MuJoCo is now an optional local probe extra, not a default dependency.
- Isaac remains remote/server-only preflight.
- Next stage should use probe outputs to decide MJ01-B minimal MJCF adapter and NV01-C1 Isaac server runner.

Update “已完成能力”, “尚未完成”, commands, and next step sections as needed.

- [ ] **Step 5: Sync README.html and details.html**

Use the existing static HTML style; do not introduce Mermaid renderer, JavaScript, or CSS redesign.

- [ ] **Step 6: Run documentation checks**

Run:

```bash
for file in README.md README.html details.md details.html weld-experience-engine/README.md; do
  rg -n "mj01_mujoco_probe_report" "$file"
  rg -n "MJ01-A|MuJoCo" "$file"
  rg -n "Isaac|remote|服务器|远端" "$file"
done
rg -n "not_mujoco_dynamics_validation|not_isaac_sim_runtime_validation|not_formal_WPS_PQR|not_ready_for_robot_execution" README.md README.html details.md details.html weld-experience-engine/README.md
```

Expected: each target doc contains the new report entry point and MuJoCo/Isaac boundary.

---

### Task 4: Verification, Review, PR, Merge, Cleanup

**Files:**
- All planned files.

- [ ] **Step 1: Run targeted tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_mj01_mujoco_probe.py tests/test_mj01_mujoco_probe_report.py -q
```

Expected: PASS.

- [ ] **Step 2: Run full tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q
```

Expected: PASS.

- [ ] **Step 3: Run CLI without MuJoCo requirement**

Run:

```bash
cd weld-experience-engine
uv run python -m weldcore.skill_asset.mj01_mujoco_probe_report \
  --outdir /tmp/a02-mj01-a-local-mujoco-probe-check
```

Expected: command exits 0. If MuJoCo is not installed, summary has `mujoco_runtime_status = "skipped_by_missing_mujoco_runtime"`. If MuJoCo is installed, summary has `mujoco_runtime_status = "available"` and minimal MJCF sanity probe is attempted.

- [ ] **Step 4: Optionally verify MuJoCo extra**

Run only if environment allows dependency sync:

```bash
cd weld-experience-engine
uv sync --extra dev --extra viz --extra mujoco
uv run python -m weldcore.skill_asset.mj01_mujoco_probe_report \
  --outdir /tmp/a02-mj01-a-local-mujoco-probe-with-extra-check
```

Expected: `mujoco_runtime_status = "available"` and `minimal_mjcf_probe_status = "passed_minimal_mjcf_sanity_probe"`.

- [ ] **Step 5: Review diff**

Run:

```bash
git diff --stat
git diff --name-only
```

Expected: only planned files changed.

- [ ] **Step 6: Commit**

Run:

```bash
git add README.md README.html details.md details.html weld-experience-engine/README.md \
  weld-experience-engine/pyproject.toml \
  weld-experience-engine/weldcore/skill_asset/mj01_mujoco_probe.py \
  weld-experience-engine/weldcore/skill_asset/mj01_mujoco_probe_report.py \
  weld-experience-engine/tests/test_mj01_mujoco_probe.py \
  weld-experience-engine/tests/test_mj01_mujoco_probe_report.py \
  docs/superpowers/specs/2026-06-26-mj01-a-local-mujoco-probe-nv01-c0-remote-isaac-preflight-design.md \
  docs/superpowers/plans/2026-06-26-mj01-a-local-mujoco-probe-nv01-c0-remote-isaac-preflight.md
git commit -m "feat: add mj01 local mujoco probe"
```

- [ ] **Step 7: PR, remote merge, cleanup**

Run:

```bash
test "$(git branch --show-current)" = "codex/mj01-a-local-mujoco-probe"
git push -u origin codex/mj01-a-local-mujoco-probe
gh pr create --title "feat: add MJ01 local MuJoCo probe" --body "<summary and tests>"
gh pr view --json mergeStateStatus
gh pr merge --merge --delete-branch
git switch main
git pull --ff-only
git fetch --prune
git branch -d codex/mj01-a-local-mujoco-probe || true
git status --short --branch
```

Expected: PR merged, local feature branch removed if present, clean `main...origin/main`.
