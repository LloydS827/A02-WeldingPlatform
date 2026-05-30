from __future__ import annotations
from dataclasses import dataclass


@dataclass
class LayerPass:
    layer: int                  # 层序 (1=打底)
    pass_no: int                # 道序
    overlap_mm: float = 0.0     # 道间搭接
    fill_area_mm2: float = 0.0  # 本道填充面积
