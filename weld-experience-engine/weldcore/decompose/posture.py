from __future__ import annotations

import numpy as np

from ..model.process import Posture
from ..model.trajectory import Trajectory


def extract_posture(traj: Trajectory) -> Posture:
    """恒定姿态 POC 场景：用中位数估计工作角和行进角。"""
    rpy = traj.rpy
    return Posture(
        work_angle_deg=float(np.median(rpy[:, 0])),
        travel_angle_deg=float(np.median(rpy[:, 1])),
        stickout_mm=0.0,
    )
