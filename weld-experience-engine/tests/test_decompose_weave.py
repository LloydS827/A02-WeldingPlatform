import numpy as np
import pytest

from weldcore.datagen.synth import synthesize
from weldcore.decompose.centerline import extract_centerline
from weldcore.decompose.weave import classify_type, detect_amplitude, detect_frequency
from weldcore.model.process import WeldProcess
from weldcore.model.weave import WeaveTemplate, WeaveType


def _residual(wtype, amp=3.0, freq=2.0):
    process = WeldProcess(
        travel_speed=5.0,
        weave=WeaveTemplate(wtype, amp, freq),
        length_mm=80.0,
    )
    traj = synthesize(process, fs=200.0)
    _, _, _, residual = extract_centerline(traj)
    return residual, traj.t


def test_amplitude_and_frequency():
    residual, t = _residual(WeaveType.CRESCENT, amp=3.0, freq=2.0)

    assert abs(detect_amplitude(residual) - 3.0) < 0.2
    assert abs(detect_frequency(residual, t) - 2.0) < 0.15


@pytest.mark.parametrize(
    "wtype",
    [WeaveType.CRESCENT, WeaveType.ZIGZAG, WeaveType.TRAPEZOID],
)
def test_classify_each_template(wtype):
    residual, t = _residual(wtype)
    freq = detect_frequency(residual, t)

    assert classify_type(residual, t, freq) == wtype
