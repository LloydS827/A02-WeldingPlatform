from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np

@dataclass
class TrajectorySample:
    t: float                              # s
    x: float; y: float; z: float          # mm, 焊枪末端 TCP 位置
    rx: float; ry: float; rz: float       # deg, 焊枪姿态 (euler XYZ)
    current: float | None = None          # A, 可选
    voltage: float | None = None          # V, 可选
    force: float | None = None            # N, 可选 (力控)

@dataclass
class Trajectory:
    samples: list[TrajectorySample] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.samples)

    @property
    def t(self) -> np.ndarray:
        return np.array([s.t for s in self.samples])

    @property
    def xyz(self) -> np.ndarray:
        return np.array([[s.x, s.y, s.z] for s in self.samples])

    @property
    def rpy(self) -> np.ndarray:
        return np.array([[s.rx, s.ry, s.rz] for s in self.samples])

    @classmethod
    def from_arrays(cls, t, xyz, rpy) -> "Trajectory":
        xyz = np.asarray(xyz, float); rpy = np.asarray(rpy, float)
        return cls([
            TrajectorySample(float(ti), *map(float, p), *map(float, r))
            for ti, p, r in zip(np.asarray(t, float), xyz, rpy)
        ])
