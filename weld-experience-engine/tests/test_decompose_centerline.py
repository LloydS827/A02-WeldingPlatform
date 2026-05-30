import numpy as np

from weldcore.datagen.perturb import perturb
from weldcore.datagen.synth import synthesize
from weldcore.decompose.centerline import extract_centerline
from weldcore.model.process import WeldProcess
from weldcore.model.weave import WeaveTemplate, WeaveType


def _ideal(v=5.0):
    process = WeldProcess(
        travel_speed=v,
        weave=WeaveTemplate(WeaveType.CRESCENT, 3.0, 2.0),
        length_mm=50.0,
    )
    return synthesize(process, fs=100.0)


def test_centerline_recovers_travel_speed():
    _, direction, speed, residual = extract_centerline(_ideal(5.0))

    assert abs(speed - 5.0) < 0.1
    assert abs(direction[0]) > 0.99
    assert abs((np.percentile(residual, 95) - np.percentile(residual, 5)) / 2 - 3.0) < 0.3


def test_travel_speed_robust_to_pause():
    noisy = perturb(_ideal(5.0), pause_count=2, pause_dur=0.3, seed=2)

    _, _, speed, _ = extract_centerline(noisy)

    assert abs(speed - 5.0) < 0.3
