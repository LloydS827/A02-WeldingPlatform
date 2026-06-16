from __future__ import annotations

from weldcore.robot_process.model import RobotContextSpec, RobotFeasibilityResult

from .model import ManipulationSkillAsset, RobotBodyAsset, SceneContextAsset, SkillTransferAssessment


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
    *,
    robot_context: RobotContextSpec | None = None,
    scene_context: SceneContextAsset | None = None,
    feasibility_result: RobotFeasibilityResult | None = None,
    contextual_precheck_requested: bool = False,
) -> SkillTransferAssessment:
    passed_checks = []
    blocking_gaps = []
    warning_gaps = list(DEFAULT_WARNING_GAPS)

    motion_gap = _skill_motion_gap(skill_asset)
    if motion_gap is None:
        passed_checks.append("skill_motion_present")
    else:
        blocking_gaps.append(motion_gap)

    if robot_body_asset.validation_status == "usable_as_robot_body_context":
        passed_checks.append("robot_body_asset_usable")
    else:
        blocking_gaps.append("robot_body_asset_issue")
        blocking_gaps.extend(
            f"robot_body_asset_issue:{issue}" for issue in robot_body_asset.validation_issues
        )
        warning_gaps.extend(robot_body_asset.validation_issues)

    if motion_gap is not None:
        status = "blocked_by_missing_skill_motion"
    elif "robot_body_asset_issue" in blocking_gaps:
        status = "blocked_by_robot_body_asset_issue"
    elif (
        robot_context is None
        and scene_context is None
        and feasibility_result is None
        and not contextual_precheck_requested
    ):
        status = "ready_for_contextual_precheck"
    elif robot_context is None:
        status = "blocked_by_missing_robot_context"
        blocking_gaps.append("missing_robot_context")
        if scene_context is None:
            blocking_gaps.append("missing_scene_context")
    elif scene_context is None:
        status = "blocked_by_missing_scene_context"
        blocking_gaps.append("missing_scene_context")
    elif feasibility_result is None:
        status = "ready_for_lightweight_feasibility_precheck"
    elif feasibility_binding_gaps := _feasibility_binding_gaps(
        skill_asset,
        robot_context,
        feasibility_result,
    ):
        status = "blocked_by_incomplete_feasibility_result"
        blocking_gaps.extend(feasibility_binding_gaps)
    elif _has_failed_feasibility_check(feasibility_result):
        status = "blocked_by_failed_feasibility_check"
        blocking_gaps.extend(feasibility_result.blocking_reasons)
    elif feasibility_result.status == "incomplete" or feasibility_result.blocking_reasons:
        status = "blocked_by_incomplete_feasibility_result"
        blocking_gaps.extend(feasibility_result.blocking_reasons)
    else:
        status = "ready_for_expert_review"
        passed_checks.append("lightweight_feasibility_precheck_passed")

    return SkillTransferAssessment(
        assessment_id=f"transfer-assessment-{skill_asset.asset_id}-{robot_body_asset.robot_id}",
        skill_asset_id=skill_asset.asset_id,
        robot_body_asset_id=robot_body_asset.robot_id,
        status=status,
        passed_checks=_dedupe_text(*passed_checks),
        blocking_gaps=_dedupe_text(*blocking_gaps),
        warning_gaps=_dedupe_text(*warning_gaps),
        evidence_boundary=_dedupe_text(
            *BASE_EVIDENCE_BOUNDARY,
            *skill_asset.quality_boundary,
            *skill_asset.evidence.evidence_boundary,
            *robot_body_asset.evidence_boundary,
            *(robot_context.evidence_notes if robot_context is not None else ()),
            *(scene_context.evidence_boundary if scene_context is not None else ()),
            *(feasibility_result.evidence_boundary if feasibility_result is not None else ()),
        ),
        next_step_recommendation=NEXT_STEP_RECOMMENDATION,
        evidence_notes=("contextual_precheck_only",),
    )


def _skill_motion_gap(skill_asset: ManipulationSkillAsset) -> str | None:
    motion = skill_asset.motion or {}
    tcp_trajectory = motion.get("tcp_trajectory")
    if not tcp_trajectory:
        return "missing_tcp_trajectory"

    point_count = motion.get("trajectory_point_count")
    if not isinstance(point_count, int) or point_count <= 0:
        return "invalid_trajectory_point_count"
    if point_count != len(tcp_trajectory):
        return "trajectory_point_count_mismatch"

    tool_orientation = motion.get("tool_orientation")
    if not tool_orientation:
        return "missing_tool_orientation"

    orientation_point_count = motion.get("orientation_point_count")
    if not isinstance(orientation_point_count, int) or orientation_point_count <= 0:
        return "invalid_orientation_point_count"
    if orientation_point_count != len(tool_orientation):
        return "orientation_point_count_mismatch"
    if orientation_point_count != point_count:
        return "trajectory_orientation_count_mismatch"
    return None


def _dedupe_text(*values: str) -> tuple[str, ...]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return tuple(deduped)


def _has_failed_feasibility_check(feasibility_result: RobotFeasibilityResult) -> bool:
    return feasibility_result.status == "failed" or "failed" in (
        feasibility_result.reachability_status,
        feasibility_result.collision_status,
        feasibility_result.joint_limit_status,
        feasibility_result.path_continuity_status,
        feasibility_result.orientation_feasibility_status,
    )


def _feasibility_binding_gaps(
    skill_asset: ManipulationSkillAsset,
    robot_context: RobotContextSpec,
    feasibility_result: RobotFeasibilityResult,
) -> tuple[str, ...]:
    gaps = []
    if feasibility_result.draft_id != skill_asset.asset_id:
        gaps.append("feasibility_result_skill_mismatch")
    if feasibility_result.context_id != robot_context.context_id:
        gaps.append("feasibility_result_context_mismatch")
    return tuple(gaps)
