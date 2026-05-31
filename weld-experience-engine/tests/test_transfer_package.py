from weldcore.sim.simlite import generate_straight_flat_dataset
from weldcore.sim.task import straight_flat_task
from weldcore.transfer.package import package_from_sample


def test_package_from_sample_preserves_motion_posture_and_process():
    task = straight_flat_task()
    dataset = generate_straight_flat_dataset(task)
    sample = dataset.samples[0]

    package = package_from_sample(sample, package_id="pkg-001")

    assert package.package_id == "pkg-001"
    assert package.source_sample_ids == [sample.sample_id]
    assert package.motion_skill.travel_speed > 0
    assert package.motion_skill.weave.amplitude > 0
    assert package.motion_skill.weave.frequency > 0
    assert package.process_skill.current == 180.0
    assert package.applicable_conditions["weld_type"] == "straight_flat"
