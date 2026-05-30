from __future__ import annotations
import numpy as np
from ..model.process import WeldProcess
from ..model.trajectory import Trajectory

def synthesize(process: WeldProcess, fs: float = 100.0) -> Trajectory:
    """正向：工艺参数 → 理想轨迹。fs 采样率 Hz(100=10ms)。
    平焊直线坡口：x 沿行进方向匀速，y 为摆动侧向，z=0，姿态恒定。"""
    duration = process.length_mm / process.travel_speed
    n = int(round(duration * fs)) + 1
    t = np.arange(n) / fs
    x = process.travel_speed * t
    phase = 2*np.pi * process.weave.frequency * t
    y = process.weave.lateral(phase)
    z = np.zeros_like(t)
    xyz = np.column_stack([x, y, z])
    rpy = np.tile([process.posture.work_angle_deg,
                   process.posture.travel_angle_deg, 0.0], (n, 1))
    return Trajectory.from_arrays(t, xyz, rpy)
