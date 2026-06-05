import json
from typing import Literal, get_type_hints

from weldcore.simulation_bakeoff import (
    ExperienceDataset,
    ManiSkillTaskConfig,
    RawManiSkillArtifact,
    RuleBasedDemo,
    SimulationPathPoint,
    read_json_artifact,
    write_json_artifact,
)


def test_maniskill_task_config_serializes_without_private_simulator_objects():
    config = ManiSkillTaskConfig(
        task_id="task-long-straight-horizontal-tracking",
        unit_id="long-straight-horizontal-tracking",
        task_name="长直横焊沿缝跟踪",
        seam_path=(SimulationPathPoint(0.0, 0.0, 0.0, 0.12, 0.0, 90.0, 0.0),),
        tcp_frame="torch_tcp",
        orientation_constraint=("keep_torch_posture_stable",),
        motion_constraint=("constant_tracking_speed",),
        expected_outputs=("tcp_trajectory", "tool_orientation", "task_status"),
        out_of_scope=("real_welding_quality", "WPS/PQR"),
        source_task_spec_id="task-long-straight-horizontal-tracking",
    )

    data = config.to_dict()

    assert data["task_id"] == "task-long-straight-horizontal-tracking"
    assert data["seam_path"][0]["z"] == 0.12
    assert "sapien" not in json.dumps(data).lower()


def test_rule_based_demo_and_raw_artifact_preserve_failure_boundary():
    point = SimulationPathPoint(0.0, 0.0, 0.0, 0.12, 0.0, 90.0, 0.0)
    demo = RuleBasedDemo(
        demo_id="demo-task-long-straight-horizontal-tracking",
        task_id="task-long-straight-horizontal-tracking",
        tcp_trajectory=(point,),
        tool_orientation=(point,),
        generation_method="rule_based_seam_path_following",
        evidence_notes=("not_human_demonstration",),
    )
    artifact = RawManiSkillArtifact(
        run_id="maniskill-task-long-straight-horizontal-tracking",
        task_id=demo.task_id,
        status="failed",
        tcp_trajectory=(),
        tool_orientation=(),
        task_state={"attempted": True},
        metrics={"task_contract_outputs_ready": 0.0},
        failure_boundary=("environment_missing",),
        artifacts={"demo": "demo.json"},
        evidence_notes=("real_simulator_not_completed",),
    )

    assert demo.to_dict()["generation_method"] == "rule_based_seam_path_following"
    assert artifact.to_dict()["failure_boundary"] == ["environment_missing"]


def test_raw_maniskill_artifact_status_contract_is_completed_or_failed():
    hints = get_type_hints(RawManiSkillArtifact)

    assert hints["status"] == Literal["completed", "failed"]


def test_experience_dataset_declares_skilldataset_as_compatibility_export():
    dataset = ExperienceDataset(
        dataset_id="experience-maniskill-task-long-straight-horizontal-tracking",
        source_type="simulation",
        task_id="task-long-straight-horizontal-tracking",
        samples=("sample-1",),
        review_status="not_reviewed",
        validation_status="simulation_only",
        quality_feedback_status="not_available",
        compatibility_exports=("SkillDataset",),
        evidence_boundary=(
            "not_robot_process_package",
            "not_real_welding_quality_validation",
        ),
    )

    data = dataset.to_dict()

    assert data["compatibility_exports"] == ["SkillDataset"]
    assert "not_robot_process_package" in data["evidence_boundary"]


def test_json_artifact_round_trips(tmp_path):
    path = tmp_path / "artifact.json"
    write_json_artifact(path, {"task_id": "task-a"})

    assert read_json_artifact(path)["task_id"] == "task-a"


def test_write_json_artifact_creates_parent_directories(tmp_path):
    path = tmp_path / "nested" / "artifact.json"
    write_json_artifact(path, {"task_id": "task-a"})

    assert read_json_artifact(path)["task_id"] == "task-a"
