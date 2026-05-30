import numpy as np

from weldcore.datagen.perturb import perturb
from weldcore.datagen.synth import synthesize
from weldcore.model.process import WeldProcess
from weldcore.model.weave import WeaveTemplate, WeaveType


def _ideal():
    process = WeldProcess(
        travel_speed=5.0,
        weave=WeaveTemplate(WeaveType.CRESCENT, 3.0, 2.0),
        length_mm=50.0,
    )
    return synthesize(process, fs=100.0)


def test_tremor_adds_bounded_noise():
    ideal = _ideal()
    noisy = perturb(ideal, tremor_mm=0.2, seed=1)

    delta = noisy.xyz[:, :2] - ideal.xyz[:, :2]

    assert np.std(delta) > 0
    assert np.std(delta) < 0.5


def test_drift_is_monotone_on_y():
    ideal = _ideal()
    drifted = perturb(ideal, drift_mm=2.0, seed=1)

    extra_y = drifted.xyz[:, 1] - ideal.xyz[:, 1]

    assert extra_y[-1] - extra_y[0] > 1.5


def test_pause_freezes_position():
    ideal = _ideal()
    paused = perturb(ideal, pause_count=1, pause_dur=0.2, seed=3)

    dx = np.abs(np.diff(paused.xyz[:, 0]))

    assert (dx < 1e-9).sum() >= 15
