from __future__ import annotations

from ..decompose.engine import decompose
from ..model.skill import (
    HumanReview,
    MotionSkill,
    PostureSkill,
    ProcessSkill,
    SkillSample,
    TransferRuleSpec,
    WeldSkillPackage,
)


def package_from_sample(sample: SkillSample, package_id: str) -> WeldSkillPackage:
    process = decompose(sample.trajectory)
    first_signal = sample.process_signals[0] if sample.process_signals else None
    return WeldSkillPackage(
        package_id=package_id,
        source_sample_ids=[sample.sample_id],
        applicable_conditions={
            "weld_type": sample.weld_condition.weld_type,
            "joint_type": sample.weld_condition.joint_type,
            "position": sample.weld_condition.position,
            "groove_width_mm": sample.weld_condition.groove_width_mm,
            "min_length_mm": sample.weld_condition.length_mm * 0.5,
            "max_length_mm": sample.weld_condition.length_mm * 2.0,
        },
        motion_skill=MotionSkill(
            travel_speed=process.travel_speed,
            weave=process.weave,
        ),
        posture_skill=PostureSkill(
            work_angle_deg=process.posture.work_angle_deg,
            travel_angle_deg=process.posture.travel_angle_deg,
            stickout_mm=process.posture.stickout_mm,
        ),
        process_skill=ProcessSkill(
            current=first_signal.current if first_signal else None,
            voltage=first_signal.voltage if first_signal else None,
            wire_feed=first_signal.wire_feed if first_signal else None,
        ),
        transfer_rule=TransferRuleSpec(),
        human_review=HumanReview(status="pending"),
    )
