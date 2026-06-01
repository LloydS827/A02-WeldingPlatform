from __future__ import annotations

from dataclasses import dataclass

from ..model.skill import WeldCondition


@dataclass
class WeldingTask:
    name: str
    source_condition: WeldCondition
    target_condition: WeldCondition


def straight_flat_task(
    source_length_mm: float = 100.0,
    target_length_mm: float = 150.0,
    source_width_mm: float = 4.0,
    target_width_mm: float = 5.0,
) -> WeldingTask:
    source = WeldCondition(
        weld_type="straight_flat",
        joint_type="butt",
        plate_thickness_mm=8.0,
        groove_width_mm=source_width_mm,
        length_mm=source_length_mm,
        position="flat",
        material="synthetic_steel",
    )
    target = WeldCondition(
        weld_type="straight_flat",
        joint_type="butt",
        plate_thickness_mm=8.0,
        groove_width_mm=target_width_mm,
        length_mm=target_length_mm,
        position="flat",
        material="synthetic_steel",
    )
    return WeldingTask("straight-flat-single-pass", source, target)
