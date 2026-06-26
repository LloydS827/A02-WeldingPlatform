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


def test_probe_mujoco_runtime_transitive_module_missing_is_import_error(monkeypatch):
    def fake_import_module(name):
        raise ModuleNotFoundError("native_dep", name="native_dep")

    monkeypatch.setattr("importlib.import_module", fake_import_module)

    probe = probe_mujoco_runtime()

    assert probe["runtime_probe_status"] == "blocked_by_mujoco_import_error"
    assert probe["mujoco_python_import_status"] == "import_error"
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


def test_build_payloads_without_mujoco_still_emit_preflight_reports(
    tmp_path, monkeypatch
):
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
    assert isaac["remote_stage_path_policy"] == (
        "copy_openusd_stage_usda_to_remote_workspace"
    )
    assert isaac["remote_fixture_path_policy"] == (
        "copy_isaac_runtime_validation_input_manifest_and_replay_fixture_to_remote_workspace"
    )
    for field in {
        "stage_import_status",
        "fixture_load_status",
        "required_prim_path_status",
        "frame_binding_status",
        "trajectory_binding_status",
        "sensor_placeholder_status",
        "runtime_errors",
        "blocking_items",
        "readiness_boundary",
    }:
        assert field in isaac["expected_runtime_report_schema"]
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


def test_build_payloads_with_mocked_mujoco_available_runs_minimal_probe(
    tmp_path, monkeypatch
):
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
        "blocked_by_missing_mujoco_runtime",
        "passed_minimal_mjcf_sanity_probe",
        "blocked_by_mujoco_model_load_error",
        "blocked_by_missing_robot_body_asset_source_urdf",
        "blocked_by_missing_remote_isaac_runtime",
        "blocked_for_runtime_probe_or_preflight",
        "dry_run_inputs_prepared",
        "implemented",
        "imported",
        "import_error",
        "loaded_real_urdf_with_mujoco",
        "missing",
        "not_converted_to_mjcf",
        "not_installed_locally_by_design",
        "ready_for_mj01_lightweight_replay_input_review",
        "resolved_from_robot_body_asset_report",
        "not_mujoco_dynamics_validation",
        "not_isaac_sim_runtime_validation",
        "not_policy_training_result",
        "not_formal_WPS_PQR",
        "not_ready_for_robot_execution",
    }
    assert expected == CANONICAL_MJ01A_NV01C0_STATUS
    assert "ready_for_robot_execution" not in CANONICAL_MJ01A_NV01C0_STATUS
