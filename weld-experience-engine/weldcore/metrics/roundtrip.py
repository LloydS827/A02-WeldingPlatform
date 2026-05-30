from __future__ import annotations

import numpy as np

from ..model.process import WeldProcess
from ..model.trajectory import Trajectory


def trajectory_rms(a: Trajectory, b: Trajectory) -> float:
    """两条轨迹重采样到公共时间网格后的 TCP 位置 RMS 误差。"""
    tg = np.linspace(max(a.t[0], b.t[0]), min(a.t[-1], b.t[-1]), min(len(a), len(b)))
    aa = np.column_stack([np.interp(tg, a.t, a.xyz[:, i]) for i in range(3)])
    bb = np.column_stack([np.interp(tg, b.t, b.xyz[:, i]) for i in range(3)])
    return float(np.sqrt(np.mean(np.sum((aa - bb) ** 2, axis=1))))


def param_errors(true: WeldProcess, recovered: WeldProcess) -> dict:
    """结构化参数恢复误差，对比合成数据 ground truth。"""
    return {
        "travel_speed_err": abs(true.travel_speed - recovered.travel_speed),
        "amplitude_err": abs(true.weave.amplitude - recovered.weave.amplitude),
        "frequency_err": abs(true.weave.frequency - recovered.weave.frequency),
        "type_correct": true.weave.type == recovered.weave.type,
    }
