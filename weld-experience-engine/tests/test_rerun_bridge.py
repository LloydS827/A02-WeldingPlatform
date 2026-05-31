from weldcore.sim.simlite import generate_straight_flat_dataset
from weldcore.sim.task import straight_flat_task
from weldcore.transfer.evaluate import evaluate_transfer
from weldcore.transfer.package import package_from_sample
from weldcore.transfer.rules import apply_transfer
from weldcore.viz.rerun_bridge import log_skill_transfer


def test_rerun_bridge_returns_bool_without_requiring_rerun():
    task = straight_flat_task()
    sample = generate_straight_flat_dataset(task).samples[0]
    package = package_from_sample(sample, "pkg-001")
    transferred = apply_transfer(package, task.target_condition)
    experiment = evaluate_transfer(
        "exp-001",
        package,
        task.source_condition,
        task.target_condition,
        transferred,
    )

    result = log_skill_transfer(sample, package, experiment, spawn=False)

    assert result in {True, False}
