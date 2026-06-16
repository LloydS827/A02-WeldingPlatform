from dataclasses import replace
from pathlib import Path

from weldcore.robot_process import build_robot_context_from_body_asset
from weldcore.skill_asset import (
    SceneContextAsset,
    SkillAssetEvidenceWritebackSummary,
    build_contextual_feasibility_result,
    build_default_evidence_writeback_summary,
    build_default_scene_context_asset,
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


def test_scene_context_asset_serializes_precheck_contract():
    scene = SceneContextAsset(
        scene_id="scene-skill-asset-task-1",
        scene_type="welding_transfer_precheck",
        workpiece_frame="workpiece",
        seam_path=[{"t": 0.0, "x": 0.0, "y": 0.0, "z": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0}],
        fixture_obstacles=(),
        safety_boundary={"max_radius_m": 1.4, "min_clearance_m": 0.05},
        target_region={"frame": "workpiece"},
        source_refs={"task_id": "task-1"},
        validation_status="usable_as_scene_context",
        validation_issues=(),
        evidence_boundary=("scene_context_asset_precheck_only", "not_real_fixture_validated"),
        version="v0.1",
    )

    data = scene.to_dict()

    assert data["workpiece_frame"] == "workpiece"
    assert data["validation_status"] == "usable_as_scene_context"
    assert "not_real_fixture_validated" in data["evidence_boundary"]


def test_evidence_writeback_summary_serializes_candidate_counts():
    summary = SkillAssetEvidenceWritebackSummary(
        summary_id="writeback-skill-asset-task-1",
        skill_asset_id="skill-asset-task-1",
        modeled_task_count=8,
        simulation_sample_count=1000,
        completed_sample_count=1000,
        failed_sample_count=0,
        candidate_evidence_refs=("modeled_task_specs:8", "next_batch_samples:1000"),
        writeback_status="evidence_candidates_identified",
        evidence_boundary=("simulation_evidence_candidate_only", "not_real_robot_validated"),
        next_step_recommendation="Use candidate evidence for expert review selection.",
    )

    data = summary.to_dict()

    assert data["modeled_task_count"] == 8
    assert data["completed_sample_count"] == 1000
    assert "simulation_evidence_candidate_only" in data["evidence_boundary"]


def test_default_scene_context_asset_uses_skill_motion_and_boundaries():
    skill = _default_skill_asset()

    scene = build_default_scene_context_asset(skill)

    assert scene.validation_status == "usable_as_scene_context"
    assert scene.workpiece_frame == "workpiece"
    assert len(scene.seam_path) == skill.motion["trajectory_point_count"]
    assert "scene_context_asset_precheck_only" in scene.evidence_boundary
    assert "not_real_fixture_validated" in scene.evidence_boundary


def test_scene_context_asset_blocks_missing_workpiece_frame_or_seam_path():
    skill = _default_skill_asset()

    missing_frame = build_default_scene_context_asset(skill, workpiece_frame=None)
    assert missing_frame.validation_status == "blocked_by_scene_context_issue"
    assert "missing_workpiece_frame" in missing_frame.validation_issues

    missing_path = build_default_scene_context_asset(
        replace(skill, motion={**skill.motion, "tcp_trajectory": []})
    )
    assert missing_path.validation_status == "blocked_by_scene_context_issue"
    assert "missing_seam_path" in missing_path.validation_issues


def test_robot_context_from_real_body_asset_keeps_tcp_boundary():
    robot = build_robot_body_asset_from_urdf(URDF)

    context = build_robot_context_from_body_asset(robot)

    assert context.robot_model == robot.robot_model
    assert context.robot_family == robot.robot_family
    assert context.joint_limits_source == robot.source_urdf
    assert context.tcp_frame == "torch_tcp_nominal"
    assert context.tcp_calibration_status == "nominal_from_asset_not_calibrated"
    assert "not_tcp_calibrated" in context.evidence_notes
    assert "not_ready_for_robot_execution" in context.evidence_notes


def test_contextual_feasibility_passes_default_context_as_lightweight_precheck():
    skill = _default_skill_asset()
    robot = build_robot_body_asset_from_urdf(URDF)
    robot_context = build_robot_context_from_body_asset(robot)
    scene = build_default_scene_context_asset(skill)

    result = build_contextual_feasibility_result(skill, robot_context, scene)

    assert result.status == "passed"
    assert result.reachability_status == "passed"
    assert result.collision_status == "assumed"
    assert result.joint_limit_status == "passed"
    assert result.path_continuity_status == "passed"
    assert result.orientation_feasibility_status == "passed"
    assert "collision_geometry_not_validated" in result.warning_reasons
    assert "not_full_ik_solver" in result.evidence_boundary
    assert "not_ready_for_robot_execution" in result.evidence_boundary


def test_contextual_feasibility_fails_when_workspace_hint_is_too_small():
    skill = _default_skill_asset()
    robot = build_robot_body_asset_from_urdf(URDF)
    robot_context = replace(
        build_robot_context_from_body_asset(robot),
        workspace_hint={"max_radius_m": 0.001},
    )
    scene = build_default_scene_context_asset(skill)

    result = build_contextual_feasibility_result(skill, robot_context, scene)

    assert result.status == "failed"
    assert result.reachability_status == "failed"
    assert "tcp_trajectory_outside_workspace_hint" in result.blocking_reasons


def test_contextual_feasibility_consumes_blocked_scene_context():
    skill = _default_skill_asset()
    robot = build_robot_body_asset_from_urdf(URDF)
    robot_context = build_robot_context_from_body_asset(robot)
    scene = build_default_scene_context_asset(skill, workpiece_frame=None)

    result = build_contextual_feasibility_result(skill, robot_context, scene)

    assert result.status == "incomplete"
    assert result.collision_status != "passed"
    assert result.path_continuity_status != "passed"
    assert "missing_workpiece_frame" in result.blocking_reasons


def test_contextual_feasibility_marks_missing_orientation_incomplete():
    skill = _default_skill_asset()
    skill = replace(skill, motion={**skill.motion, "tool_orientation": []})
    robot = build_robot_body_asset_from_urdf(URDF)
    robot_context = build_robot_context_from_body_asset(robot)
    scene = build_default_scene_context_asset(skill)

    result = build_contextual_feasibility_result(skill, robot_context, scene)

    assert result.status == "incomplete"
    assert result.orientation_feasibility_status == "missing"
    assert "missing_tool_orientation" in result.blocking_reasons


def test_contextual_feasibility_marks_missing_joint_limit_source_incomplete():
    skill = _default_skill_asset()
    robot = build_robot_body_asset_from_urdf(URDF)
    robot_context = replace(build_robot_context_from_body_asset(robot), joint_limits_source=None)
    scene = build_default_scene_context_asset(skill)

    result = build_contextual_feasibility_result(skill, robot_context, scene)

    assert result.status == "incomplete"
    assert result.joint_limit_status == "missing"
    assert "missing_joint_limits_source" in result.blocking_reasons


def test_contextual_feasibility_marks_single_point_path_continuity_missing():
    skill = _default_skill_asset()
    one_point_motion = {
        **skill.motion,
        "tcp_trajectory": skill.motion["tcp_trajectory"][:1],
        "tool_orientation": skill.motion["tool_orientation"][:1],
        "trajectory_point_count": 1,
        "orientation_point_count": 1,
    }
    skill = replace(skill, motion=one_point_motion)
    robot = build_robot_body_asset_from_urdf(URDF)
    robot_context = build_robot_context_from_body_asset(robot)
    scene = build_default_scene_context_asset(skill)

    result = build_contextual_feasibility_result(skill, robot_context, scene)

    assert result.status == "incomplete"
    assert result.path_continuity_status == "missing"
    assert "missing_path_continuity" in result.blocking_reasons


def test_default_evidence_writeback_summary_links_modeled_tasks_and_next_batch():
    skill = _default_skill_asset()

    summary = build_default_evidence_writeback_summary(skill)

    assert summary.skill_asset_id == skill.asset_id
    assert summary.modeled_task_count == 8
    assert summary.simulation_sample_count == 1000
    assert summary.completed_sample_count == 1000
    assert summary.failed_sample_count == 0
    assert summary.writeback_status == "evidence_candidates_identified"
    assert "modeled_task_specs:8" in summary.candidate_evidence_refs
    assert "next_batch_samples:1000" in summary.candidate_evidence_refs
    assert "not_real_welding_quality_validation" in summary.evidence_boundary
    assert "not_ready_for_robot_execution" in summary.evidence_boundary
