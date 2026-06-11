from weldcore.skill_asset import (
    ManipulationSkillAsset,
    SkillAssetEvidence,
    SkillTransferContract,
    build_manipulation_skill_asset_from_simulation_bundle,
)
from weldcore.simulation_bakeoff import (
    attempt_gazebo_moveit,
    build_simulation_evidence_bundle,
    default_simulation_task_specs,
    run_simlite_reference,
)


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
