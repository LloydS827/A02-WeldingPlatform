from __future__ import annotations

from ..model.trajectory import Trajectory
from .rerun_bridge import _set_rerun_time_seconds


def log_trajectory(ideal: Trajectory, recomposed: Trajectory, name: str = "weld") -> bool:
    """用 rerun 回放理想轨迹与复现轨迹；未安装时返回 False。"""
    try:
        import rerun as rr
    except ImportError:
        print("rerun 未安装，跳过交互可视化 (pip install rerun-sdk)")
        return False

    rr.init(f"weld-experience-{name}", spawn=True)
    for traj, path, color in (
        (ideal, f"{name}/ideal", [0, 128, 255]),
        (recomposed, f"{name}/recomposed", [255, 128, 0]),
    ):
        for sample in traj.samples:
            _set_rerun_time_seconds(rr, "weld_time", sample.t)
            rr.log(path, rr.Points3D([[sample.x, sample.y, sample.z]], colors=[color]))
    return True
