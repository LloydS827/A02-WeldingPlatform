from weldcore.sim.simlite import generate_straight_flat_dataset
from weldcore.sim.task import straight_flat_task
from weldcore.transfer.package import package_from_sample
from weldcore.transfer.rules import apply_transfer


def test_apply_transfer_generates_target_length_trajectory():
    task = straight_flat_task(source_length_mm=100.0, target_length_mm=150.0)
    sample = generate_straight_flat_dataset(task).samples[0]
    package = package_from_sample(sample, "pkg-001")

    result = apply_transfer(package, target_condition=task.target_condition)

    assert len(result.samples) > len(sample.trajectory.samples)
    assert result.samples[-1].x >= 149.0


def test_apply_transfer_rejects_out_of_range_length():
    task = straight_flat_task(source_length_mm=100.0, target_length_mm=260.0)
    sample = generate_straight_flat_dataset(task).samples[0]
    package = package_from_sample(sample, "pkg-001")

    try:
        apply_transfer(package, target_condition=task.target_condition)
    except ValueError as exc:
        assert "length scale" in str(exc)
    else:
        raise AssertionError("expected transfer to reject out-of-range length")
