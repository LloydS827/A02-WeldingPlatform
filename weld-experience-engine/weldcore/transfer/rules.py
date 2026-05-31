from __future__ import annotations

from ..datagen.synth import synthesize
from ..model.process import Posture, WeldProcess
from ..model.skill import WeldCondition, WeldSkillPackage
from ..model.trajectory import Trajectory


def apply_transfer(package: WeldSkillPackage, target_condition: WeldCondition) -> Trajectory:
    source_max = package.applicable_conditions.get("max_length_mm")
    source_min = package.applicable_conditions.get("min_length_mm")
    if source_min is not None and target_condition.length_mm < source_min:
        raise ValueError("length scale outside applicable range")
    if source_max is not None and target_condition.length_mm > source_max:
        raise ValueError("length scale outside applicable range")
    source_length = package.applicable_conditions.get("source_length_mm")
    if source_length is None and source_max is not None:
        # package_from_sample stores max_length_mm as source_length * 2.0.
        source_length = source_max / 2.0
    if (
        source_length is not None
        and target_condition.length_mm
        > float(source_length) * package.transfer_rule.max_length_scale
    ):
        raise ValueError("length scale outside applicable range")

    width_delta = abs(
        target_condition.groove_width_mm
        - float(
            package.applicable_conditions.get(
                "groove_width_mm", target_condition.groove_width_mm
            )
        )
    )
    if width_delta > package.transfer_rule.max_width_delta_mm:
        raise ValueError("width delta outside applicable range")

    process = WeldProcess(
        travel_speed=package.motion_skill.travel_speed,
        weave=package.motion_skill.weave,
        posture=Posture(
            work_angle_deg=package.posture_skill.work_angle_deg,
            travel_angle_deg=package.posture_skill.travel_angle_deg,
            stickout_mm=package.posture_skill.stickout_mm,
        ),
        length_mm=target_condition.length_mm,
    )
    return synthesize(process, fs=50.0)
