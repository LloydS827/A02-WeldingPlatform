import numpy as np

from weldcore.model.weave import WAVEFORMS, WeaveType


def test_figure8_registered():
    assert WeaveType.FIGURE8 in WAVEFORMS

    phase = np.linspace(0, 2 * np.pi, 200)
    y = WAVEFORMS[WeaveType.FIGURE8](phase)

    assert np.max(np.abs(y)) <= 1.0 + 1e-6
