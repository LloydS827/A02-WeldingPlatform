from pathlib import Path

from weldcore.robot_process import build_robot_context_from_body_asset
from weldcore.skill_asset import (
    build_a01_b06_skill_asset_mapping,
    build_a02_to_a01_product_validation_handoff,
    build_contextual_feasibility_result,
    build_default_evidence_source_catalog,
    build_default_expert_review_record,
    build_default_scene_context_asset,
    build_ip_disclosure_support_matrix,
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


def test_default_simulation_skill_asset_uses_canonical_simulation_only_source():
    skill = _default_skill_asset()

    assert skill.source_type == "simulation_only"
    assert skill.evidence.source_type == "simulation_only"
    assert "simulation_only" in skill.evidence.evidence_boundary


def test_evidence_source_catalog_contains_strategic_sources():
    skill = _default_skill_asset()
    catalog = build_default_evidence_source_catalog(skill)
    source_types = {entry.source_type for entry in catalog}

    assert {
        "simulation_only",
        "human_demo",
        "real_robot_log",
        "h300_workcell_run",
        "expert_annotation",
    } <= source_types


def test_a01_b06_mapping_carries_workcell_and_package_field_contract():
    skill = _default_skill_asset()
    mapping = build_a01_b06_skill_asset_mapping(skill)
    data = mapping.to_dict()

    assert data["evidence_source_type"] == "h300_workcell_run"
    assert {
        "task",
        "weld_seam",
        "workpiece",
        "path_points",
        "robot_pose",
        "torch_pose",
        "process_parameters",
        "manual_correction",
        "execution_log",
        "anomaly",
        "quality_result",
    } <= set(data["workcell_fields"])
    assert {
        "physical_ai_package_profile",
        "task_context",
        "coordinate_frames",
        "frames",
        "events",
        "labels",
        "trajectory",
        "human_correction",
        "metrics",
        "quality_labels",
        "rerun_replay_ref",
    } <= set(data["package_fields"])
    assert data["skill_asset_field_mapping"]["path_points"] == "motion.tcp_trajectory"
    assert data["skill_asset_field_mapping"]["manual_correction"] == "evidence.review_input"
    assert data["quality_feedback_mapping"]["quality_result"] == "quality_feedback_evidence"
    assert "not_WPS_PQR" in data["evidence_boundary"]


def test_expert_review_record_requires_real_context_and_snapshots():
    skill = _default_skill_asset()
    robot = build_robot_body_asset_from_urdf(URDF)
    robot_context = build_robot_context_from_body_asset(robot)
    scene = build_default_scene_context_asset(skill)
    feasibility = build_contextual_feasibility_result(skill, robot_context, scene)

    review = build_default_expert_review_record(skill, robot_context, scene, feasibility)
    data = review.to_dict()
    required_fields = {item["field"] for item in data["required_real_context"]}
    required_keys = {"field", "current_status", "required_evidence", "blocking_if_missing"}

    assert data["review_status"] == "pending_expert_review"
    assert {
        "real_tcp_calibration",
        "workpiece_frame_measurement",
        "robot_model_identity",
        "joint_limits_source",
    } <= required_fields
    assert all(required_keys <= set(item) for item in data["required_real_context"])
    assert all(item["blocking_if_missing"] is True for item in data["required_real_context"])
    assert any(
        item["field"] == "real_tcp_calibration"
        and item["current_status"] == "nominal_from_asset_not_calibrated"
        for item in data["required_real_context"]
    )
    assert data["robot_context_snapshot"]["context_id"] == robot_context.context_id
    assert data["robot_context_snapshot"]["tcp_calibration_status"] == "nominal_from_asset_not_calibrated"
    assert "not_ready_for_robot_execution" in data["robot_context_snapshot"]["evidence_notes"]
    assert data["scene_context_snapshot"]["scene_id"] == scene.scene_id
    assert data["scene_context_snapshot"]["validation_status"] == scene.validation_status
    assert "not_collision_validated" in data["scene_context_snapshot"]["evidence_boundary"]
    assert data["feasibility_status_snapshot"]["result_id"] == feasibility.result_id
    assert data["feasibility_status_snapshot"]["status"] == feasibility.status
    assert "not_full_ik_solver" in data["feasibility_status_snapshot"]["evidence_boundary"]
    assert "not_ready_for_robot_execution" in data["review_boundary"]


def test_a02_to_a01_handoff_and_ip_support_keep_execution_boundary():
    skill = _default_skill_asset()
    handoff = build_a02_to_a01_product_validation_handoff(skill)
    support = build_ip_disclosure_support_matrix(skill)

    assert "trajectory_candidate" in handoff.candidate_outputs
    assert "not_direct_robot_program" in handoff.handoff_boundary
    assert {item["patent_item_id"] for item in support.items} == {"P0-02", "P0-03", "P0-04"}
    assert all(item["supporting_objects"] for item in support.items)
    assert all(item["supporting_reports"] for item in support.items)
    assert all(item["missing_real_world_evidence"] for item in support.items)

    by_id = {item["patent_item_id"]: item for item in support.items}
    assert "ManipulationSkillAsset" in by_id["P0-02"]["supporting_objects"]
    assert "ExpertReviewRecord" in by_id["P0-02"]["supporting_objects"]
    assert "motion.tcp_trajectory" in by_id["P0-03"]["supporting_objects"]
    assert "SimulationEvidenceBundle" in by_id["P0-04"]["supporting_objects"]
