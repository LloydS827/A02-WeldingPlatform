import json

from weldcore.skill_asset.asset_report import run_skill_asset_report


def test_skill_asset_report_writes_twelve_artifacts(tmp_path):
    payload = run_skill_asset_report(tmp_path)

    assert payload["skill_asset"]["domain"] == "welding"
    assert payload["skill_asset"]["source_type"] == "simulation_only"
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
    for filename in (
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
    ):
        assert (tmp_path / filename).exists()
    restored = json.loads((tmp_path / "skill_transfer_assessment.json").read_text())
    assert restored["status"] == "ready_for_expert_review"


def test_skill_asset_report_main_prints_json(tmp_path, capsys):
    from weldcore.skill_asset import asset_report

    asset_report.main(["--outdir", str(tmp_path)])

    output = json.loads(capsys.readouterr().out)
    assert output["transfer_assessment"]["status"] == "ready_for_expert_review"
