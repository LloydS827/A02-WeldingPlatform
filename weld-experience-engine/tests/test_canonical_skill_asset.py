from dataclasses import replace
from pathlib import Path

from weldcore.skill_asset import (
    ManipulationSkillAsset,
    SkillAssetEvidence,
    SkillTransferContract,
    build_robot_body_asset_from_urdf,
    build_manipulation_skill_asset_from_simulation_bundle,
    build_skill_transfer_assessment,
)
from weldcore.simulation_bakeoff import (
    attempt_gazebo_moveit,
    build_simulation_evidence_bundle,
    default_simulation_task_specs,
    run_simlite_reference,
)


ROOT = Path(__file__).resolve().parents[2]
URDF = ROOT / "docs" / "real-urdf" / "robot.urdf"


def test_manipulation_skill_asset_serializes_core_contract():
    evidence = SkillAssetEvidence(
        source_type="simulation",
        source_id="bundle-1",
        adapter_name="simlite_reference",
        status="completed",
        metrics={"path_continuity": 1.0},
        artifact_refs={"bundle": "memory://bundle-1"},
        evidence_boundary=("simulation_only", "not_ready_for_robot_execution"),
        review_status="not_reviewed",
    )
    contract = SkillTransferContract(
        required_robot_context=("robot_body", "tcp_calibration", "workpiece_frame"),
        required_scene_context=("scene_context_asset",),
        required_checks=(
            "reachability",
            "collision",
            "joint_limits",
            "tcp_calibration",
            "workpiece_frame",
            "path_continuity",
            "orientation_feasibility",
            "expert_review",
        ),
        transfer_status="requires_contextual_precheck",
        blocking_gaps=(),
        evidence_notes=("not_real_robot_validated",),
    )
    asset = ManipulationSkillAsset(
        asset_id="skill-asset-1",
        name="Long straight tracking",
        domain="welding",
        skill_type="seam_tracking",
        source_type="simulation",
        source_refs={"bundle_id": "bundle-1"},
        intent={"task": "follow seam"},
        motion={"tcp_trajectory": [], "tool_orientation": []},
        constraints={"path_continuity": True},
        context_requirements={"tcp_frame": "torch_tcp"},
        evidence=evidence,
        transfer_contract=contract,
        quality_boundary=("not_real_welding_quality_validation", "not_WPS_PQR"),
        version="v0.1",
    )

    data = asset.to_dict()

    assert data["asset_id"] == "skill-asset-1"
    assert data["evidence"]["source_type"] == "simulation"
    assert "expert_review" in data["transfer_contract"]["required_checks"]
    assert data["transfer_contract"]["transfer_status"] == "requires_contextual_precheck"


def test_simulation_evidence_bundle_builds_manipulation_skill_asset():
    task_spec = default_simulation_task_specs()[0]
    bundle = build_simulation_evidence_bundle(task_spec, run_simlite_reference(task_spec))

    asset = build_manipulation_skill_asset_from_simulation_bundle(bundle)
    data = asset.to_dict()

    assert asset.domain == "welding"
    assert asset.source_type == "simulation"
    assert asset.source_refs["bundle_id"] == bundle.bundle_id
    assert asset.motion["trajectory_point_count"] == len(bundle.adapter_result.tcp_trajectory)
    assert asset.motion["orientation_point_count"] == len(bundle.adapter_result.tool_orientation)
    assert asset.context_requirements["tcp_frame"] == task_spec.tcp_frame
    assert asset.transfer_contract.transfer_status == "requires_contextual_precheck"
    assert asset.transfer_contract.required_checks == (
        "reachability",
        "collision",
        "joint_limits",
        "tcp_calibration",
        "workpiece_frame",
        "path_continuity",
        "orientation_feasibility",
        "expert_review",
    )
    assert "simulation_only" in asset.evidence.evidence_boundary
    assert "not_ready_for_robot_execution" in asset.quality_boundary
    assert data["evidence"]["review_status"] == "not_reviewed"


def test_failed_simulation_bundle_deduplicates_evidence_boundary():
    task_spec = default_simulation_task_specs()[0]
    adapter_result = attempt_gazebo_moveit(task_spec)
    bundle = build_simulation_evidence_bundle(task_spec, adapter_result)

    asset = build_manipulation_skill_asset_from_simulation_bundle(bundle)

    for boundary in adapter_result.failure_boundary:
        assert asset.evidence.evidence_boundary.count(boundary) == 1


def _default_skill_asset():
    task_spec = default_simulation_task_specs()[0]
    bundle = build_simulation_evidence_bundle(task_spec, run_simlite_reference(task_spec))
    return build_manipulation_skill_asset_from_simulation_bundle(bundle)


def test_skill_and_robot_body_are_ready_for_contextual_precheck():
    skill = _default_skill_asset()
    robot = build_robot_body_asset_from_urdf(URDF)

    assessment = build_skill_transfer_assessment(skill, robot)

    assert assessment.status == "ready_for_contextual_precheck"
    assert assessment.blocking_gaps == ()
    assert assessment.passed_checks == ("skill_motion_present", "robot_body_asset_usable")
    assert assessment.warning_gaps == (
        "requires_robot_context_spec",
        "requires_tcp_calibration",
        "requires_workpiece_frame",
        "requires_scene_context_asset",
    )
    assert "requires_tcp_calibration" in assessment.warning_gaps
    assert "requires_scene_context_asset" in assessment.warning_gaps
    assert assessment.next_step_recommendation == (
        "Bind RobotContextSpec and SceneContextAsset before any IK, collision, "
        "or real robot validation claim."
    )
    assert "not_ready_for_robot_execution" in assessment.evidence_boundary
    assert "not_ik_validated" in assessment.evidence_boundary
    assert "not_collision_validated" in assessment.evidence_boundary
    assert "not_real_robot_validated" in assessment.evidence_boundary


def test_transfer_assessment_blocks_missing_skill_motion():
    robot = build_robot_body_asset_from_urdf(URDF)
    base_skill = _default_skill_asset()

    for motion in (
        {},
        {**base_skill.motion, "tcp_trajectory": []},
        {**base_skill.motion, "trajectory_point_count": 0},
        {key: value for key, value in base_skill.motion.items() if key != "trajectory_point_count"},
        {**base_skill.motion, "trajectory_point_count": -1},
        {**base_skill.motion, "trajectory_point_count": len(base_skill.motion["tcp_trajectory"]) + 1},
    ):
        skill = replace(base_skill, motion=motion)
        assessment = build_skill_transfer_assessment(skill, robot)

        assert assessment.status == "blocked_by_missing_skill_motion"
        assert any(
            gap
            in {
                "missing_tcp_trajectory",
                "invalid_trajectory_point_count",
                "trajectory_point_count_mismatch",
            }
            for gap in assessment.blocking_gaps
        )


def test_transfer_assessment_blocks_robot_body_asset_issue():
    skill = _default_skill_asset()
    robot = replace(
        build_robot_body_asset_from_urdf(URDF),
        validation_status="blocked_by_asset_issue",
        validation_issues=("missing_mesh:meshes/missing.stl",),
    )

    assessment = build_skill_transfer_assessment(skill, robot)

    assert assessment.status == "blocked_by_robot_body_asset_issue"
    assert "robot_body_asset_issue" in assessment.blocking_gaps
    assert "robot_body_asset_issue:missing_mesh:meshes/missing.stl" in assessment.blocking_gaps
    assert "missing_mesh:meshes/missing.stl" in assessment.warning_gaps


def test_transfer_assessment_deduplicates_warning_gaps():
    skill = _default_skill_asset()
    robot = replace(
        build_robot_body_asset_from_urdf(URDF),
        validation_status="blocked_by_asset_issue",
        validation_issues=("requires_tcp_calibration", "requires_tcp_calibration"),
    )

    assessment = build_skill_transfer_assessment(skill, robot)

    assert assessment.warning_gaps.count("requires_tcp_calibration") == 1
