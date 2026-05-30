from __future__ import annotations

from ..model.process import WeldProcess
from ..model.trajectory import Trajectory
from ..model.weave import WeaveTemplate
from .centerline import extract_centerline
from .posture import extract_posture
from .weave import classify_type, detect_amplitude, detect_frequency


def decompose(traj: Trajectory) -> WeldProcess:
    """L1：轨迹样本 -> 结构化焊接工艺表达。"""
    origin, direction, travel_speed, residual = extract_centerline(traj)
    freq = detect_frequency(residual, traj.t)
    amp = detect_amplitude(residual)
    wtype = classify_type(residual, traj.t, freq)
    posture = extract_posture(traj)
    proj = (traj.xyz[:, :2] - origin) @ direction

    return WeldProcess(
        travel_speed=travel_speed,
        weave=WeaveTemplate(type=wtype, amplitude=amp, frequency=freq),
        posture=posture,
        length_mm=float(proj.max() - proj.min()),
    )
