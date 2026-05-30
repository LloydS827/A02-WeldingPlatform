from __future__ import annotations

from ..datagen.synth import synthesize
from ..model.process import WeldProcess
from ..model.trajectory import Trajectory


def recompose(process: WeldProcess, fs: float = 100.0, smooth: bool = True) -> Trajectory:
    """结构化工艺参数 -> 连续机器人轨迹。"""
    traj = synthesize(process, fs=fs)
    if not smooth:
        return traj

    try:
        from scipy.interpolate import make_interp_spline
    except ImportError:
        return traj

    t = traj.t
    k = min(3, len(t) - 1)
    spline = make_interp_spline(t, traj.xyz, k=k)
    return Trajectory.from_arrays(t, spline(t), traj.rpy)
