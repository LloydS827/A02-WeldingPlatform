import numpy as np

from weldcore.model.process import WeldProcess
from weldcore.model.weave import WeaveTemplate, WeaveType
from weldcore.recompose.interpolate import recompose


def test_recompose_matches_forward_model():
    process = WeldProcess(
        travel_speed=5.0,
        weave=WeaveTemplate(WeaveType.CRESCENT, 3.0, 2.0),
        length_mm=50.0,
    )

    traj = recompose(process, fs=100.0, smooth=True)
    step = np.linalg.norm(np.diff(traj.xyz, axis=0), axis=1)

    assert abs(traj.xyz[-1, 0] - 50.0) < 0.1
    assert abs(traj.xyz[:, 1].max() - 3.0) < 0.2
    assert step.max() < 5 * np.median(step)
