from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import math


class GrooveType(str, Enum):
    V = "V"; X = "X"; I = "I"; FILLET = "fillet"


@dataclass
class GrooveGeometry:
    type: GrooveType
    angle_deg: float = 0.0      # 坡口角度
    gap_mm: float = 0.0         # 根部间隙
    root_face_mm: float = 0.0   # 钝边
    depth_mm: float = 0.0       # 深度
    width_mm: float = 0.0       # 宽度

    @property
    def section_area_mm2(self) -> float:
        """V 型坡口断面填充面积近似 = 三角区 + 间隙区。"""
        tri = self.depth_mm**2 * math.tan(math.radians(self.angle_deg/2))
        return tri + self.gap_mm * self.depth_mm
