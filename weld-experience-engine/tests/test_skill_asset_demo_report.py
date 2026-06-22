import json

from weldcore.skill_asset.demo_report import (
    CANONICAL_TASK_ARTIFACTS,
    EXTRA_TASK_ARTIFACTS,
    run_demo_evidence_pack,
)


REQUIRED_NOT_EXECUTION_GAPS = {
    "real_tcp_calibration",
    "workpiece_frame_measurement",
    "robot_model_identity",
    "joint_limits_source",
    "full_ik_solver",
    "real_collision_validation",
    "real_robot_execution_log",
    "real_welding_quality_feedback",
}

EXPECTED_CANONICAL_TASK_ARTIFACTS = {
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
}

EXPECTED_EXTRA_TASK_ARTIFACTS = {"simulation_evidence_bundle.json"}


def test_demo_evidence_pack_writes_summary_and_per_task_artifacts(tmp_path):
    payload = run_demo_evidence_pack(tmp_path)

    assert payload["demo_id"] == "a02-demo-evidence-pack"
    assert payload["overall_status"] == "ready_for_expert_review_candidate_pack"
    assert payload["task_count"] == 2
    assert "ready_for_expert_review" in payload["readiness_boundary"]
    assert "not_ready_for_robot_execution" in payload["readiness_boundary"]
    assert "simulation_only" in payload["readiness_boundary"]

    for filename in ("demo_summary.md", "demo_summary.json", "demo_summary.html"):
        assert (tmp_path / filename).exists()
        assert filename in payload["generated_artifacts"]

    assert set(CANONICAL_TASK_ARTIFACTS) == EXPECTED_CANONICAL_TASK_ARTIFACTS
    assert set(EXTRA_TASK_ARTIFACTS) == EXPECTED_EXTRA_TASK_ARTIFACTS
    expected_task_files = EXPECTED_CANONICAL_TASK_ARTIFACTS | EXPECTED_EXTRA_TASK_ARTIFACTS
    for task in payload["tasks"]:
        task_dir = tmp_path / task["task_id"]
        assert task_dir.exists()
        assert set(task["artifact_refs"]) == expected_task_files
        for filename in expected_task_files:
            rel_path = f"{task['task_id']}/{filename}"
            assert task["artifact_refs"][filename] == rel_path
            assert rel_path in payload["generated_artifacts"]
            assert (tmp_path / rel_path).exists()
        assert task["transfer_status"] == "ready_for_expert_review"
        assert task["expert_review_status"] == "pending_expert_review"
        assert task["feasibility_status"] == "passed"
        assert task["source_type"] == "simulation_only"
        assert "not_ready_for_robot_execution" in task["boundary_reasons"]
        assert (
            "candidate_handoff_only" in task["boundary_reasons"]
            or "not_direct_robot_program" in task["boundary_reasons"]
        )
        assert "ip_disclosure_support_only" in task["boundary_reasons"]
        gap_text = " ".join(task["why_not_ready_for_robot_execution"])
        assert all(gap in gap_text for gap in REQUIRED_NOT_EXECUTION_GAPS)

    generated_files = sorted(
        str(path.relative_to(tmp_path))
        for path in tmp_path.rglob("*")
        if path.is_file()
    )
    assert sorted(payload["generated_artifacts"]) == generated_files


def test_demo_summary_explains_a01_and_ip_support(tmp_path):
    payload = run_demo_evidence_pack(tmp_path)

    assert "intent" in payload["field_explanation"]
    assert "motion" in payload["field_explanation"]
    assert "context_requirements" in payload["field_explanation"]
    assert "transfer_contract" in payload["field_explanation"]
    assert "quality_boundary" in payload["field_explanation"]
    assert "SimulationEvidenceBundle" in payload["simulation_evidence_explanation"]
    assert "simlite_reference" in payload["simulation_evidence_explanation"]
    assert "metrics" in payload["simulation_evidence_explanation"]
    assert "trajectory_candidate" in payload["a02_to_a01_handoff_summary"]["candidate_outputs"]
    assert "not_ready_for_robot_execution" in payload["a02_to_a01_handoff_summary"]["handoff_boundary"]
    assert {item["patent_item_id"] for item in payload["ip_support_summary"]} == {
        "P0-02",
        "P0-03",
        "P0-04",
    }

    md = (tmp_path / "demo_summary.md").read_text(encoding="utf-8")
    html = (tmp_path / "demo_summary.html").read_text(encoding="utf-8")
    assert "ready_for_expert_review" in md
    assert "not_ready_for_robot_execution" in md
    assert "real_tcp_calibration" in md
    assert "real_welding_quality_feedback" in md
    assert "A02 -> A01" in md
    assert "ManipulationSkillAsset" in md
    assert "P0-03" in md
    assert "P0-02" in html
    assert "workpiece_frame_measurement" in html
    assert "real_robot_execution_log" in html

    restored = json.loads((tmp_path / "demo_summary.json").read_text(encoding="utf-8"))
    assert restored == payload


def test_demo_evidence_pack_repeated_writes_keep_artifact_list_unique(tmp_path):
    run_demo_evidence_pack(tmp_path)
    payload = run_demo_evidence_pack(tmp_path)

    generated_files = sorted(
        str(path.relative_to(tmp_path))
        for path in tmp_path.rglob("*")
        if path.is_file()
    )
    assert len(payload["generated_artifacts"]) == len(set(payload["generated_artifacts"]))
    assert sorted(payload["generated_artifacts"]) == generated_files
