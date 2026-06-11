from __future__ import annotations

from .model import ManipulationSkillAsset, RobotBodyAsset, SkillTransferAssessment


DEFAULT_WARNING_GAPS = (
    "requires_robot_context_spec",
    "requires_tcp_calibration",
    "requires_workpiece_frame",
    "requires_scene_context_asset",
)
NEXT_STEP_RECOMMENDATION = (
    "Bind RobotContextSpec and SceneContextAsset before any IK, collision, "
    "or real robot validation claim."
)
BASE_EVIDENCE_BOUNDARY = (
    "not_ready_for_robot_execution",
    "not_ik_validated",
    "not_collision_validated",
    "not_real_robot_validated",
)


def build_skill_transfer_assessment(
    skill_asset: ManipulationSkillAsset,
    robot_body_asset: RobotBodyAsset,
) -> SkillTransferAssessment:
    passed_checks = []
    blocking_gaps = []
    warning_gaps = list(DEFAULT_WARNING_GAPS)

    if _has_skill_motion(skill_asset):
        passed_checks.append("skill_motion_present")
    else:
        blocking_gaps.append("missing_tcp_trajectory")

    if robot_body_asset.validation_status == "usable_as_robot_body_context":
        passed_checks.append("robot_body_asset_usable")
    else:
        blocking_gaps.append("robot_body_asset_issue")
        warning_gaps.extend(robot_body_asset.validation_issues)

    if "missing_tcp_trajectory" in blocking_gaps:
        status = "blocked_by_missing_skill_motion"
    elif "robot_body_asset_issue" in blocking_gaps:
        status = "blocked_by_robot_body_asset_issue"
    else:
        status = "ready_for_contextual_precheck"

    return SkillTransferAssessment(
        assessment_id=f"transfer-assessment-{skill_asset.asset_id}-{robot_body_asset.robot_id}",
        skill_asset_id=skill_asset.asset_id,
        robot_body_asset_id=robot_body_asset.robot_id,
        status=status,
        passed_checks=tuple(passed_checks),
        blocking_gaps=tuple(blocking_gaps),
        warning_gaps=tuple(warning_gaps),
        evidence_boundary=_dedupe_text(
            *BASE_EVIDENCE_BOUNDARY,
            *skill_asset.quality_boundary,
            *skill_asset.evidence.evidence_boundary,
            *robot_body_asset.evidence_boundary,
        ),
        next_step_recommendation=NEXT_STEP_RECOMMENDATION,
        evidence_notes=("contextual_precheck_only",),
    )


def _has_skill_motion(skill_asset: ManipulationSkillAsset) -> bool:
    motion = skill_asset.motion or {}
    tcp_trajectory = motion.get("tcp_trajectory")
    if not tcp_trajectory:
        return False
    return motion.get("trajectory_point_count") != 0


def _dedupe_text(*values: str) -> tuple[str, ...]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return tuple(deduped)
