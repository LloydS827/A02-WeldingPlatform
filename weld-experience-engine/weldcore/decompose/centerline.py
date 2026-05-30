from __future__ import annotations

import numpy as np

from ..model.trajectory import Trajectory


def extract_centerline(traj: Trajectory):
    """直线焊缝场景：PCA 提取中心线、行进速度和侧向残差。"""
    xy = traj.xyz[:, :2]
    origin = xy.mean(axis=0)
    _, _, vt = np.linalg.svd(xy - origin, full_matrices=False)
    direction = vt[0]
    if direction[0] < 0:
        direction = -direction

    perp = np.array([-direction[1], direction[0]])
    proj = (xy - origin) @ direction
    residual = (xy - origin) @ perp

    dproj = np.gradient(proj, traj.t)
    active = dproj > 1e-6
    travel_speed = float(np.median(dproj[active])) if active.any() else 0.0

    return origin, direction, travel_speed, residual
