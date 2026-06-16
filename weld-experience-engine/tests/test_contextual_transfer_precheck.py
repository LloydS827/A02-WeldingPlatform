from weldcore.skill_asset import (
    SceneContextAsset,
    SkillAssetEvidenceWritebackSummary,
)


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
