import json

from weldcore.skill_asset.asset_report import run_skill_asset_report


def test_skill_asset_report_writes_seven_artifacts(tmp_path):
    payload = run_skill_asset_report(tmp_path)

    assert payload["skill_asset"]["domain"] == "welding"
    assert payload["robot_body_asset"]["validation_status"] == "usable_as_robot_body_context"
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
    restored = json.loads((tmp_path / "skill_transfer_assessment.json").read_text())
    assert restored["status"] == "ready_for_expert_review"


def test_skill_asset_report_main_prints_json(tmp_path, capsys):
    from weldcore.skill_asset import asset_report

    asset_report.main(["--outdir", str(tmp_path)])

    output = json.loads(capsys.readouterr().out)
    assert output["transfer_assessment"]["status"] == "ready_for_expert_review"
