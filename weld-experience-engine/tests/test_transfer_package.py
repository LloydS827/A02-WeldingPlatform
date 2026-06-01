from weldcore.sim.simlite import generate_straight_flat_dataset
from weldcore.sim.task import straight_flat_task
from weldcore.transfer.package import package_from_sample


def test_package_from_sample_preserves_motion_posture_and_process():
    task = straight_flat_task()
    dataset = generate_straight_flat_dataset(task)
    sample = dataset.samples[0]
    sample.process_signals[0].current = 181.5
    sample.process_signals[0].voltage = 24.5
    sample.process_signals[0].wire_feed = 6.2
    sample.process_signals[1].current = 190.0
    sample.process_signals[1].voltage = 25.0
    sample.process_signals[1].wire_feed = 7.0

    package = package_from_sample(sample, package_id="pkg-001")

    assert package.package_id == "pkg-001"
    assert package.source_sample_ids == [sample.sample_id]
    assert package.motion_skill.travel_speed > 0
    assert package.motion_skill.weave.amplitude > 0
    assert package.motion_skill.weave.frequency > 0
    assert package.process_skill.current == sample.process_signals[0].current
    assert package.process_skill.voltage == sample.process_signals[0].voltage
    assert package.process_skill.wire_feed == sample.process_signals[0].wire_feed
    assert package.applicable_conditions["weld_type"] == "straight_flat"
    assert package.applicable_conditions["joint_type"] == sample.weld_condition.joint_type
    assert package.applicable_conditions["position"] == sample.weld_condition.position
    assert (
        package.applicable_conditions["groove_width_mm"]
        == sample.weld_condition.groove_width_mm
    )
    assert (
        package.applicable_conditions["min_length_mm"]
        == sample.weld_condition.length_mm * 0.5
    )
    assert (
        package.applicable_conditions["max_length_mm"]
        == sample.weld_condition.length_mm * 2.0
    )
