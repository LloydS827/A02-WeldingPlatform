from __future__ import annotations

import numpy as np

from ..model.trajectory import Trajectory


def perturb(
    traj: Trajectory,
    *,
    tremor_mm: float = 0.0,
    drift_mm: float = 0.0,
    pause_count: int = 0,
    pause_dur: float = 0.0,
    seed: int = 0,
) -> Trajectory:
    """注入人工示教扰动：手抖、路径漂移和无效停顿。"""
    rng = np.random.default_rng(seed)
    t = traj.t.copy()
    xyz = traj.xyz.copy()
    rpy = traj.rpy.copy()
    n = len(t)
    dt = float(np.median(np.diff(t))) if n > 1 else 0.01

    if tremor_mm > 0:
        xyz[:, :2] += rng.normal(0.0, tremor_mm, size=(n, 2))

    if drift_mm > 0:
        xyz[:, 1] += np.linspace(0.0, drift_mm, n)

    if pause_count > 0 and pause_dur > 0:
        window = max(1, int(round(pause_dur / dt)))
        for _ in range(pause_count):
            start = int(rng.integers(0, max(1, n - window)))
            xyz[start : start + window] = xyz[start]

    return Trajectory.from_arrays(t, xyz, rpy)
