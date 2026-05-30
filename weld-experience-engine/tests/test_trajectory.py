import numpy as np
from weldcore.model.trajectory import Trajectory, TrajectorySample

def test_from_arrays_roundtrips_to_numpy():
    t = np.array([0.0, 0.01, 0.02])
    xyz = np.array([[0,0,0],[1,0.5,0],[2,0,0]], float)
    rpy = np.array([[10,20,0]]*3, float)
    tr = Trajectory.from_arrays(t, xyz, rpy)
    assert len(tr) == 3
    np.testing.assert_allclose(tr.t, t)
    np.testing.assert_allclose(tr.xyz, xyz)
    np.testing.assert_allclose(tr.rpy, rpy)
    assert isinstance(tr.samples[0], TrajectorySample)
    assert tr.samples[1].y == 0.5
