from weldcore.skill_asset import (
    ManipulationSkillAsset,
    SkillAssetEvidence,
    SkillTransferContract,
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
