from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
from .weave import WeaveTemplate
from .groove import GrooveGeometry
from .layerpass import LayerPass


@dataclass
class Posture:
    work_angle_deg: float = 0.0     # 工作角
    travel_angle_deg: float = 0.0   # 行进角
    stickout_mm: float = 0.0        # 干伸长度


def _enc(o):
    if isinstance(o, Enum):
        return o.value
    raise TypeError(f"不可序列化: {type(o)}")


@dataclass
class WeldProcess:
    """一条焊缝/单道的完整工艺表达 —— 项目核心资产(工艺包数据内核)。"""
    travel_speed: float                       # mm/s, 行进速度
    weave: WeaveTemplate
    posture: Posture = field(default_factory=Posture)
    groove: GrooveGeometry | None = None
    layer_pass: LayerPass | None = None
    length_mm: float = 100.0                   # 焊缝长度

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2, default=_enc)
