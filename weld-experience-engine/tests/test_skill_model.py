import json

from weldcore.model.skill import (
    HumanReview,
    ProcessSignal,
    SourceType,
    WeldCondition,
    WeldSkillPackage,
    SkillDataset,
    SkillSample,
    MotionSkill,
    PostureSkill,
    ProcessSkill,
    TransferRuleSpec,
)
from weldcore.model.experiment import TransferDecision, TransferExperiment, TransferMetrics
from weldcore.model.trajectory import Trajectory
from weldcore.model.weave import WeaveTemplate, WeaveType


def test_skill_dataset_carries_source_rights_and_samples():
    condition = WeldCondition(
        weld_type="straight_flat",
        joint_type="butt",
        plate_thickness_mm=8.0,
        groove_width_mm=4.0,
        length_mm=100.0,
    )
    sample = SkillSample(
        sample_id="sim-001",
        weld_condition=condition,
        trajectory=Trajectory.from_arrays(
            [0.0, 1.0],
            [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
            [[0.0, 10.0, 20.0], [30.0, 40.0, 50.0]],
        ),
        process_signals=[
            ProcessSignal(t=0.0, current=180.0, voltage=24.0, wire_feed=6.0)
        ],
        recording_artifact="recordings/sim-001.rrd",
    )
    dataset = SkillDataset(
        dataset_id="dataset-001",
        source_type=SourceType.SIMULATION,
        task="straight-flat-single-pass",
        samples=[sample],
        license_and_rights="internal synthetic data",
    )

    data = dataset.to_dict()

    assert data["source_type"] == "simulation"
    assert data["license_and_rights"] == "internal synthetic data"
    assert data["samples"][0]["weld_condition"]["length_mm"] == 100.0
    assert data["samples"][0]["recording_artifact"] == "recordings/sim-001.rrd"
    assert data["samples"][0]["trajectory"]["samples"][1]["x"] == 4.0
    assert data["samples"][0]["trajectory"]["samples"][1]["rz"] == 50.0
    assert "rerun" not in json.dumps(data, sort_keys=True).lower()


def test_weld_skill_package_is_independent_from_visualization_backend():
    package = WeldSkillPackage(
        package_id="pkg-001",
        source_sample_ids=["sim-001"],
        applicable_conditions={"weld_type": "straight_flat"},
        motion_skill=MotionSkill(
            travel_speed=5.0,
            weave=WeaveTemplate(WeaveType.CRESCENT, amplitude=2.0, frequency=1.5),
        ),
        posture_skill=PostureSkill(work_angle_deg=0.0, travel_angle_deg=10.0, stickout_mm=12.0),
        process_skill=ProcessSkill(current=180.0, voltage=24.0),
        transfer_rule=TransferRuleSpec(max_length_scale=2.0, max_width_delta_mm=2.0),
        human_review=HumanReview(status="pending", reviewer=None, notes=""),
    )

    data = package.to_dict()

    assert data["package_id"] == "pkg-001"
    assert "rerun" not in repr(data).lower()
    assert data["motion_skill"]["weave"]["type"] == "crescent"


def test_transfer_experiment_records_decision_and_metrics():
    exp = TransferExperiment(
        experiment_id="exp-001",
        source_condition={"length_mm": 100.0},
        target_condition={"length_mm": 150.0},
        skill_package_id="pkg-001",
        recomposed_trajectory=Trajectory.from_arrays(
            [0.0, 1.0],
            [[10.0, 20.0, 30.0], [40.0, 50.0, 60.0]],
            [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
        ),
        metrics=TransferMetrics(
            trajectory_rms_mm=0.4,
            posture_error_deg=1.0,
            weave_amplitude_error_mm=0.1,
            weave_frequency_error_hz=0.05,
            process_current_error=3.0,
        ),
        decision=TransferDecision.PASS,
        notes="synthetic MVP",
    )

    assert exp.to_dict()["decision"] == "pass"
    assert exp.to_dict()["recomposed_trajectory"]["samples"][0]["x"] == 10.0
    assert exp.to_dict()["recomposed_trajectory"]["samples"][0]["rz"] == 3.0
    assert exp.metrics.trajectory_rms_mm == 0.4
