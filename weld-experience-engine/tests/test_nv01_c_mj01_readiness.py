import json

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


REQUIRED_NV01B_FILES = {
    "nv01_b_summary.json",
    "openusd_stage.usda",
    "openusd_stage_validation_report.json",
    "isaac_replay_fixture.json",
    "procedure_sim_parameter_audit.json",
    "sensor_annotation_manifest.json",
    "simulation_blocking_report.json",
    "experiment_reproducibility_manifest.json",
}


def _source_nv01b(tmp_path):
    source_dir = tmp_path / "nv01b"
    run_nv01_b_experiment_base_report(outdir=source_dir)
    return source_dir


def test_load_nv01b_artifacts_requires_complete_source(tmp_path):
    source_dir = _source_nv01b(tmp_path)
    artifacts = load_nv01b_artifacts(source_dir)

    assert set(artifacts["source_artifact_refs"].values()) == REQUIRED_NV01B_FILES
    assert artifacts["summary"]["report_id"] == (
        "nv01-b-openusd-isaac-reproducible-experiment-base"
    )
    assert artifacts["openusd_stage_usda"].startswith("#usda 1.0")
    assert artifacts["task_ids"]
    assert artifacts["task_artifacts"]
    for task_id in artifacts["task_ids"]:
        assert artifacts["task_artifacts"][task_id]["isaac_replay_task_fixture"]

    (source_dir / "isaac_replay_fixture.json").unlink()
    with pytest.raises(
        MissingNV01BArtifactError,
        match="isaac_replay_fixture.json",
    ):
        load_nv01b_artifacts(source_dir)


def test_load_nv01b_artifacts_requires_complete_task_sources(tmp_path):
    source_dir = _source_nv01b(tmp_path)
    summary = json.loads((source_dir / "nv01_b_summary.json").read_text(encoding="utf-8"))
    task_dir = source_dir / summary["tasks"][0]["task_output_dir"]
    (task_dir / "sensor_annotation_manifest.json").unlink()

    with pytest.raises(
        MissingNV01BArtifactError,
        match="sensor_annotation_manifest.json",
    ):
        load_nv01b_artifacts(source_dir)


def test_nv01_c_mj01_status_vocabulary_has_required_boundaries():
    assert {
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
    } <= CANONICAL_NV01C_MJ01_STATUS
    assert "ready_for_robot_execution" not in CANONICAL_NV01C_MJ01_STATUS


def test_build_nv01_c_mj01_payloads_create_runtime_readiness_pack(tmp_path):
    source_dir = _source_nv01b(tmp_path)
    artifacts = load_nv01b_artifacts(source_dir)

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
    assert isaac["static_input_status"] == (
        "ready_for_isaac_runtime_validation_input_review"
    )
    assert isaac["source_stage_ref"] == "openusd_stage.usda"
    assert isaac["source_replay_fixture_ref"] == "isaac_replay_fixture.json"
    assert "/World/WeldTasks" in isaac["required_prim_paths"]
    assert isaac["stage_validation_status"] == "ready_for_static_openusd_review"
    assert isaac["frame_bindings"]
    assert isaac["trajectory_bindings"]
    assert isaac["procedure_parameter_bindings"]
    assert isaac["sensor_placeholders"]
    assert isaac["task_inputs"]
    assert "isaac_sim_runtime" in isaac["blocked_by"]
    assert {
        "not_isaac_sim_runtime_validation",
        "not_formal_WPS_PQR",
        "not_ready_for_robot_execution",
    } <= set(isaac["readiness_boundary"])

    mujoco = payloads["mujoco_lightweight_replay_feasibility_report"]
    assert mujoco["report_id"] == "mj01-mujoco-lightweight-replay-feasibility"
    assert mujoco["runtime_target"] == "MuJoCo"
    assert mujoco["runtime_status"] == "blocked_by_missing_mujoco_runtime"
    assert mujoco["model_input_status"] == (
        "ready_for_mj01_lightweight_replay_input_review"
    )
    assert mujoco["model_source"] == "nv01_b_robot_body_asset_ref"
    assert mujoco["mjcf_conversion_status"] == "not_converted_to_mjcf"
    assert mujoco["urdf_ref"]
    assert mujoco["frame_binding_inputs"]
    assert mujoco["trajectory_replay_inputs"]
    assert mujoco["contact_and_dynamics_assumptions"]
    assert mujoco["task_reports"]
    assert "mujoco_runtime" in mujoco["blocked_by"]
    assert {
        "not_mujoco_dynamics_validation",
        "not_formal_WPS_PQR",
        "not_ready_for_robot_execution",
    } <= set(mujoco["readiness_boundary"])

    blocking = payloads["runtime_replay_blocking_report"]
    assert blocking["overall_status"] == "blocked_for_runtime_replay_validation"
    assert blocking["scope_status"]["isaac_runtime_validation"] == (
        "blocked_by_missing_isaac_runtime"
    )
    assert blocking["scope_status"]["mujoco_lightweight_replay"] == (
        "blocked_by_missing_mujoco_runtime"
    )
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
    assert {
        "not_isaac_sim_runtime_validation",
        "not_mujoco_dynamics_validation",
        "not_formal_WPS_PQR",
        "not_ready_for_robot_execution",
    } <= set(blocking["readiness_boundary"])

    task_id = artifacts["task_ids"][0]
    task_payload = payloads["task_payloads"][task_id]
    assert set(task_payload) == {
        "isaac_runtime_task_validation_input",
        "mujoco_task_replay_feasibility",
        "runtime_replay_task_blocking_report",
    }
    for key in (
        "isaac_runtime_task_validation_input",
        "mujoco_task_replay_feasibility",
    ):
        task_readiness = task_payload[key]
        assert task_readiness["task_id"] == task_id
        assert task_readiness["source_task_dir_ref"]
        assert task_readiness["stage_task_prim_ref"].startswith("/World/WeldTasks/")
        assert task_readiness["trajectory_ref"]
        assert task_readiness["tcp_frame_ref"]
        assert task_readiness["tool_frame_ref"]
        assert task_readiness["workpiece_frame_ref"]
        assert task_readiness["procedure_parameter_refs"]
        assert task_readiness["blocked_by"]
        assert "not_formal_WPS_PQR" in task_readiness["readiness_boundary"]
    task_blocking = task_payload["runtime_replay_task_blocking_report"]
    assert task_blocking["source_task_dir_ref"]
    assert task_blocking["stage_task_prim_ref"]
    assert task_blocking["blocked_by"]
    assert "not_formal_WPS_PQR" in task_blocking["readiness_boundary"]

    serialized = json.dumps(payloads, ensure_ascii=False)
    assert str(tmp_path) not in serialized
    assert str(source_dir) not in serialized
