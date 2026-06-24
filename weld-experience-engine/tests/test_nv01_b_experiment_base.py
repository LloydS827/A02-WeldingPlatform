import re

import pytest

from weldcore.skill_asset.nvidia_digital_twin_report import (
    run_nvidia_digital_twin_report,
)
from weldcore.skill_asset.nv01_b_experiment_base import (
    CANONICAL_NV01B_STATUS,
    MissingNV01AArtifactError,
    build_nv01_b_experiment_payloads,
    load_nv01a_artifacts,
    validate_openusd_stage_text,
)


def _source_nv01a(tmp_path):
    source_dir = tmp_path / "nv01a"
    run_nvidia_digital_twin_report(outdir=source_dir)
    return source_dir


def _stage_status_values(stage):
    status_keys = {
        "a02:workpiece_geometry_status",
        "a02:torch_geometry_status",
        "a02:sensor_layout_status",
        "a02:boundary_status",
        "a02:collision_validation_status",
    }
    values = {}
    for key, value in re.findall(r'string "(a02:[^"]*status)" = "([^"]+)"', stage):
        if key in status_keys:
            values.setdefault(key, set()).add(value)
    return values


def test_load_nv01a_artifacts_requires_complete_source(tmp_path):
    source_dir = _source_nv01a(tmp_path)
    artifacts = load_nv01a_artifacts(source_dir)

    assert artifacts["summary"]["report_id"] == (
        "k01-nv01-a-procedure-constrained-manifest-evidence-pack"
    )
    assert artifacts["procedure_contract"]["field_count"] == 47
    assert artifacts["task_ids"]

    (source_dir / "weld_procedure_knowledge_contract.json").unlink()
    with pytest.raises(
        MissingNV01AArtifactError,
        match="weld_procedure_knowledge_contract.json",
    ):
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
    assert (
        "not_isaac_sim_runtime_validation"
        in payloads["isaac_replay_fixture"]["readiness_boundary"]
    )
    assert payloads["simulation_blocking_report"]["overall_status"] == (
        "blocked_for_real_isaac_sim_replay"
    )
    assert (
        "welding_current_a"
        in payloads["simulation_blocking_report"]["missing_fields_by_scope"][
            "real_isaac_sim_replay"
        ]
    )
    assert (
        "welding_voltage_v"
        in payloads["simulation_blocking_report"]["missing_fields_by_scope"][
            "real_isaac_sim_replay"
        ]
    )
    assert (
        "heat_input_kj_per_mm"
        in payloads["simulation_blocking_report"]["missing_fields_by_scope"][
            "policy_training"
        ]
    )

    audit = payloads["procedure_sim_parameter_audit"]
    assert audit["field_count"] == 47
    assert audit["mapped_field_count"] == 47
    mapping = audit["mappings"]["travel_speed_mm_per_min"]
    assert mapping["usd_metadata_path"].endswith(".procedure.travel_speed_mm_per_min")
    assert (
        mapping["isaac_replay_parameter"]
        == "procedure_parameter_inputs.travel_speed_mm_per_min"
    )
    assert "domain_randomization_recipe" in mapping["domain_randomization_usage"]
    missing_conditional_mappings = [
        mapping
        for mapping in audit["mappings"].values()
        if mapping["coverage_status"] == "missing_conditional"
    ]
    assert missing_conditional_mappings
    for mapping in missing_conditional_mappings:
        assert mapping.get("required_when") or mapping.get("condition_unresolved")

    stage = payloads["openusd_stage_usda"]
    for required in (
        "#usda 1.0",
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
    assert (
        validation["procedure_metadata_checks"]["procedure_parameter_set_refs"]
        == "present"
    )

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
        "tcp_pose_trace",
        "weld_seam_annotation",
        "procedure_parameter_overlay",
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
        "report_cli_status",
        "default_dependency_boundary",
        "source_artifact_refs",
        "validation_commands",
    ):
        assert key in repro
    assert repro["command"] == (
        "builder_only: "
        "weldcore.skill_asset.nv01_b_experiment_base."
        "build_nv01_b_experiment_payloads(source_nv01a_dir)"
    )
    assert "nv01_b_experiment_base_report" not in repro["command"]
    assert repro["report_cli_status"] == "pending_task_2_report_cli"
    assert repro["source_nv01a_root_ref"] == "source_nv01a"
    assert repro["validation_commands"] == [
        "pytest tests/test_nv01_b_experiment_base.py -q"
    ]
    assert all("uv run" not in command for command in repro["validation_commands"])
    assert "no_isaac_sim_default_dependency" in repro["default_dependency_boundary"]


def test_openusd_stage_status_custom_data_uses_canonical_nv01_b_statuses(tmp_path):
    artifacts = load_nv01a_artifacts(_source_nv01a(tmp_path))
    payloads = build_nv01_b_experiment_payloads(artifacts)

    values_by_key = _stage_status_values(payloads["openusd_stage_usda"])

    assert values_by_key
    for values in values_by_key.values():
        assert values <= CANONICAL_NV01B_STATUS


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
        path
        for path in payloads["openusd_stage_validation_report"]["required_prim_paths"]
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
