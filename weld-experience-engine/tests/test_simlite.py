from weldcore.model.skill import SourceType
from weldcore.sim.simlite import generate_straight_flat_dataset
from weldcore.sim.task import straight_flat_task


def test_straight_flat_task_defines_source_and_target_conditions():
    task = straight_flat_task(source_length_mm=100.0, target_length_mm=150.0)

    assert task.name == "straight-flat-single-pass"
    assert task.source_condition.length_mm == 100.0
    assert task.target_condition.length_mm == 150.0
    assert task.target_condition.weld_type == "straight_flat"


def test_simlite_generates_skill_dataset_with_process_signals():
    task = straight_flat_task(source_length_mm=100.0, target_length_mm=150.0)
    dataset = generate_straight_flat_dataset(task=task, sample_id="sim-001")

    assert dataset.source_type is SourceType.SIMULATION
    assert len(dataset.samples) == 1
    sample = dataset.samples[0]
    assert len(sample.trajectory.samples) > 20
    assert sample.weld_condition.length_mm == 100.0
    assert sample.process_signals[0].current is not None
    assert sample.process_signals[0].voltage is not None
