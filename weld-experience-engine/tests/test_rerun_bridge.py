from pathlib import Path
import sys
from types import SimpleNamespace

from weldcore.ingest import import_simulation_bundle
from weldcore.knowledge.synthetic_manifest import load_synthetic_input_foundation
from weldcore.sim.simlite import generate_straight_flat_dataset
from weldcore.sim import write_simlite_bundle
from weldcore.sim.task import straight_flat_task
from weldcore.transfer.evaluate import evaluate_transfer
from weldcore.transfer.package import package_from_sample
from weldcore.transfer.rules import apply_transfer
from weldcore.viz.rerun_bridge import (
    log_simulation_dataset_evidence,
    log_skill_transfer,
)


class _FakeRerunWithSetTime:
    def __init__(self):
        self.times = []
        self.logged = []

    def init(self, *_args, **_kwargs):
        return None

    def set_time(self, timeline, *, duration):
        self.times.append((timeline, duration))

    def log(self, path, value):
        self.logged.append((path, value))

    def Points3D(self, points, colors):
        return {"points": points, "colors": colors}

    def TextDocument(self, text):
        return text


def test_rerun_bridge_supports_new_set_time_api(monkeypatch):
    fake_rerun = _FakeRerunWithSetTime()
    monkeypatch.setitem(sys.modules, "rerun", fake_rerun)
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

    assert result is True
    assert fake_rerun.times
    assert all(timeline == "weld_time" for timeline, _duration in fake_rerun.times)


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


def test_rerun_bridge_can_attempt_simulation_dataset_evidence_without_rerun(
    tmp_path: Path,
):
    foundation = load_synthetic_input_foundation()
    bundle = write_simlite_bundle(
        tmp_path,
        input_id="input-panel-butt-001",
        sample_count=1,
        seed=21,
        foundation=foundation,
    )
    result = import_simulation_bundle(bundle, foundation=foundation)

    logged = log_simulation_dataset_evidence(
        result.dataset,
        result.run_record,
        spawn=False,
    )

    assert logged in {True, False}
