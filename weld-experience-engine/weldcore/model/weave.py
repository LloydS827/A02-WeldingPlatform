from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import numpy as np


class WeaveType(str, Enum):
    CRESCENT = "crescent"      # 月牙形
    ZIGZAG = "zigzag"          # 锯齿形
    TRAPEZOID = "trapezoid"    # 梯形摆弧
    FIGURE8 = "figure8"        # 8字形 (Task 11 扩展)


def _crescent(phase):                    # 正弦 → 月牙
    return np.sin(phase)


def _zigzag(phase):                      # 三角波 → 锯齿
    return 2/np.pi * np.arcsin(np.sin(phase))


def _trapezoid(phase, plateau: float = 0.3):   # 削顶正弦 → 梯形(边缘停留)
    k = 1.0/(1.0-plateau)
    return np.clip(k*np.sin(phase), -1.0, 1.0)


# 可生长注册表：新增摆动模板只需在此登记
WAVEFORMS = {
    WeaveType.CRESCENT: _crescent,
    WeaveType.ZIGZAG: _zigzag,
    WeaveType.TRAPEZOID: _trapezoid,
}


@dataclass
class WeaveTemplate:
    type: WeaveType
    amplitude: float           # mm, 摆幅(半峰峰)
    frequency: float           # Hz, 摆频
    left_dwell: float = 0.0    # s, 左停留
    right_dwell: float = 0.0   # s, 右停留

    def lateral(self, phase: np.ndarray) -> np.ndarray:
        return self.amplitude * WAVEFORMS[self.type](np.asarray(phase, float))
