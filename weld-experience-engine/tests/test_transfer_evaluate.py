from weldcore.model.experiment import TransferDecision
from weldcore.sim.simlite import generate_straight_flat_dataset
from weldcore.sim.task import straight_flat_task
from weldcore.transfer.evaluate import evaluate_transfer
from weldcore.transfer.package import package_from_sample
from weldcore.transfer.rules import apply_transfer


def test_evaluate_transfer_returns_pass_for_in_range_synthetic_case():
    task = straight_flat_task(source_length_mm=100.0, target_length_mm=150.0)
    sample = generate_straight_flat_dataset(task).samples[0]
    package = package_from_sample(sample, "pkg-001")
    transferred = apply_transfer(package, task.target_condition)

    exp = evaluate_transfer(
        experiment_id="exp-001",
        package=package,
        source_condition=task.source_condition,
        target_condition=task.target_condition,
        transferred=transferred,
    )

    assert exp.decision is TransferDecision.PASS
    assert exp.metrics.trajectory_rms_mm < 1.0
    assert exp.metrics.weave_amplitude_error_mm < 0.5


def test_evaluate_transfer_accepts_complete_trajectory_sampled_at_different_rate():
    task = straight_flat_task(source_length_mm=100.0, target_length_mm=150.0)
    sample = generate_straight_flat_dataset(task).samples[0]
    package = package_from_sample(sample, "pkg-001")
    transferred = apply_transfer(package, task.target_condition)
    downsampled = transferred.samples[::2]
    if downsampled[-1] is not transferred.samples[-1]:
        downsampled.append(transferred.samples[-1])
    transferred.samples = downsampled

    exp = evaluate_transfer(
        experiment_id="exp-004",
        package=package,
        source_condition=task.source_condition,
        target_condition=task.target_condition,
        transferred=transferred,
    )

    assert exp.decision is TransferDecision.PASS
    assert exp.metrics.trajectory_rms_mm < 1.0


def test_evaluate_transfer_marks_large_error_for_review():
    task = straight_flat_task(source_length_mm=100.0, target_length_mm=150.0)
    sample = generate_straight_flat_dataset(task).samples[0]
    package = package_from_sample(sample, "pkg-001")
    transferred = apply_transfer(package, task.target_condition)
    for point in transferred.samples:
        point.y += 10.0

    exp = evaluate_transfer(
        experiment_id="exp-002",
        package=package,
        source_condition=task.source_condition,
        target_condition=task.target_condition,
        transferred=transferred,
    )

    assert exp.decision in {TransferDecision.REVIEW, TransferDecision.FAIL}


def test_evaluate_transfer_penalizes_truncated_trajectory():
    task = straight_flat_task(source_length_mm=100.0, target_length_mm=150.0)
    sample = generate_straight_flat_dataset(task).samples[0]
    package = package_from_sample(sample, "pkg-001")
    transferred = apply_transfer(package, task.target_condition)
    transferred.samples = transferred.samples[: len(transferred.samples) // 2]

    exp = evaluate_transfer(
        experiment_id="exp-003",
        package=package,
        source_condition=task.source_condition,
        target_condition=task.target_condition,
        transferred=transferred,
    )

    assert exp.decision is not TransferDecision.PASS
    assert exp.metrics.trajectory_rms_mm > 1.0
