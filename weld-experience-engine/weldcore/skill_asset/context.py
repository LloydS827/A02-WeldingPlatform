from __future__ import annotations

from math import sqrt
from typing import Any

from weldcore.robot_process.model import RobotContextSpec, RobotFeasibilityResult

from .model import (
    ManipulationSkillAsset,
    SceneContextAsset,
    SkillAssetEvidenceWritebackSummary,
    SkillAssetEvidenceWritebackStatus,
)


SCENE_CONTEXT_EVIDENCE_BOUNDARY = (
    "scene_context_asset_precheck_only",
    "not_real_fixture_validated",
    "not_collision_validated",
    "not_ready_for_robot_execution",
)
CONTEXTUAL_FEASIBILITY_EVIDENCE_BOUNDARY = (
    "lightweight_feasibility_precheck_only",
    "not_full_ik_solver",
    "not_collision_validated",
    "not_moveit_validated",
    "not_gazebo_validated",
    "not_real_robot_validated",
    "not_ready_for_robot_execution",
)
EVIDENCE_WRITEBACK_BOUNDARY = (
    "simulation_evidence_candidate_only",
    "modeled_task_specs_not_expert_reviewed",
    "not_real_welding_quality_validation",
    "not_ready_for_robot_execution",
)


def build_default_scene_context_asset(
    skill_asset: ManipulationSkillAsset,
    *,
    workpiece_frame: str | None = "workpiece",
) -> SceneContextAsset:
    seam_path = list(skill_asset.motion.get("tcp_trajectory") or [])
    validation_issues: list[str] = []
    if not workpiece_frame:
        validation_issues.append("missing_workpiece_frame")
    if not seam_path:
        validation_issues.append("missing_seam_path")

    return SceneContextAsset(
        scene_id=f"scene-{skill_asset.asset_id}",
        scene_type="welding_transfer_precheck",
        workpiece_frame=workpiece_frame or "",
        seam_path=seam_path,
        fixture_obstacles=(),
        safety_boundary={"max_radius_m": 1.4, "min_clearance_m": 0.05},
        target_region={"frame": workpiece_frame or ""},
        source_refs={key: value for key, value in skill_asset.source_refs.items() if value is not None},
        validation_status=(
            "blocked_by_scene_context_issue"
            if validation_issues
            else "usable_as_scene_context"
        ),
        validation_issues=tuple(validation_issues),
        evidence_boundary=SCENE_CONTEXT_EVIDENCE_BOUNDARY,
    )


def build_contextual_feasibility_result(
    skill_asset: ManipulationSkillAsset,
    robot_context: RobotContextSpec | None,
    scene_context: SceneContextAsset | None,
) -> RobotFeasibilityResult:
    tcp_trajectory = list(skill_asset.motion.get("tcp_trajectory") or [])
    tool_orientation = list(skill_asset.motion.get("tool_orientation") or [])
    context_id = robot_context.context_id if robot_context is not None else "missing-context"
    blocking_reasons: list[str] = []
    warning_reasons: list[str] = []

    reachability_status = "passed"
    collision_status = "assumed"
    joint_limit_status = "passed"
    path_continuity_status = "passed"
    orientation_status = "passed"

    if robot_context is None:
        blocking_reasons.append("missing_robot_context")
        reachability_status = "missing"
        collision_status = "not_checked"
        joint_limit_status = "missing"
        path_continuity_status = "missing"
        orientation_status = "missing"
    else:
        if not tcp_trajectory:
            blocking_reasons.append("missing_tcp_trajectory")
            reachability_status = "missing"
        elif _outside_workspace_hint(tcp_trajectory, robot_context.workspace_hint):
            blocking_reasons.append("tcp_trajectory_outside_workspace_hint")
            reachability_status = "failed"

        if "robot_body_asset_issue" in robot_context.evidence_notes:
            blocking_reasons.extend(
                issue
                for issue in robot_context.evidence_notes
                if issue == "robot_body_asset_issue" or ":" in issue
            )

        if robot_context.joint_limits_source is None:
            blocking_reasons.append("missing_joint_limits_source")
            joint_limit_status = "missing"

    if scene_context is None:
        blocking_reasons.append("missing_scene_context")
        collision_status = "missing"
        path_continuity_status = "missing"
    elif scene_context.validation_status != "usable_as_scene_context":
        blocking_reasons.extend(scene_context.validation_issues or ("blocked_scene_context",))
        collision_status = "missing"
        path_continuity_status = "missing"
    else:
        warning_reasons.append("collision_geometry_not_validated")

    if robot_context is not None:
        if not tool_orientation:
            blocking_reasons.append("missing_tool_orientation")
            orientation_status = "missing"

        seam_path = scene_context.seam_path if scene_context is not None else []
        if len(tcp_trajectory) < 2 or len(seam_path) < 2:
            blocking_reasons.append("missing_path_continuity")
            path_continuity_status = "missing"

    result_status = _feasibility_status(
        blocking_reasons,
        reachability_status=reachability_status,
        collision_status=collision_status,
        joint_limit_status=joint_limit_status,
        path_continuity_status=path_continuity_status,
        orientation_status=orientation_status,
    )

    return RobotFeasibilityResult(
        result_id=f"result-contextual-{skill_asset.asset_id}",
        probe_id=f"probe-contextual-{skill_asset.asset_id}",
        draft_id=skill_asset.asset_id,
        context_id=context_id,
        status=result_status,
        reachability_status=reachability_status,
        collision_status=collision_status,
        joint_limit_status=joint_limit_status,
        path_continuity_status=path_continuity_status,
        orientation_feasibility_status=orientation_status,
        blocking_reasons=_dedupe_text(blocking_reasons),
        warning_reasons=_dedupe_text(warning_reasons),
        evidence_source="lightweight_rule",
        adapter_hint="lightweight_rule",
        evidence_boundary=CONTEXTUAL_FEASIBILITY_EVIDENCE_BOUNDARY,
        metrics={
            "trajectory_points": len(tcp_trajectory),
            "orientation_points": len(tool_orientation),
            "scene_seam_points": len(scene_context.seam_path) if scene_context else 0,
        },
    )


def build_default_evidence_writeback_summary(
    skill_asset: ManipulationSkillAsset,
    *,
    modeled_task_count: int = 8,
    simulation_sample_count: int = 1000,
    completed_sample_count: int = 1000,
    failed_sample_count: int = 0,
) -> SkillAssetEvidenceWritebackSummary:
    has_candidates = modeled_task_count > 0 and simulation_sample_count > 0
    status: SkillAssetEvidenceWritebackStatus = (
        "evidence_candidates_identified"
        if has_candidates
        else "blocked_by_missing_evidence_source"
    )

    return SkillAssetEvidenceWritebackSummary(
        summary_id=f"writeback-{skill_asset.asset_id}",
        skill_asset_id=skill_asset.asset_id,
        modeled_task_count=modeled_task_count,
        simulation_sample_count=simulation_sample_count,
        completed_sample_count=completed_sample_count,
        failed_sample_count=failed_sample_count,
        candidate_evidence_refs=_candidate_evidence_refs(
            modeled_task_count,
            simulation_sample_count,
        ),
        writeback_status=status,
        evidence_boundary=EVIDENCE_WRITEBACK_BOUNDARY,
        next_step_recommendation=(
            "Treat these candidates as inputs for expert review and future asset evidence "
            "selection, not as proof for robot execution."
        ),
    )


def _outside_workspace_hint(
    tcp_trajectory: list[dict[str, Any]],
    workspace_hint: dict[str, Any],
) -> bool:
    max_radius = workspace_hint.get("max_radius_m")
    z_min = workspace_hint.get("z_min_m")
    z_max = workspace_hint.get("z_max_m")
    return any(
        (max_radius is not None and _point_radius(point) > max_radius)
        or (z_min is not None and float(point.get("z", 0.0)) < z_min)
        or (z_max is not None and float(point.get("z", 0.0)) > z_max)
        for point in tcp_trajectory
    )


def _point_radius(point: dict[str, Any]) -> float:
    return sqrt(
        float(point.get("x", 0.0)) ** 2
        + float(point.get("y", 0.0)) ** 2
        + float(point.get("z", 0.0)) ** 2
    )


def _feasibility_status(
    blocking_reasons: list[str],
    *,
    reachability_status: str,
    collision_status: str,
    joint_limit_status: str,
    path_continuity_status: str,
    orientation_status: str,
) -> str:
    if "failed" in (
        reachability_status,
        collision_status,
        joint_limit_status,
        path_continuity_status,
        orientation_status,
    ):
        return "failed"
    if "missing" in (
        reachability_status,
        collision_status,
        joint_limit_status,
        path_continuity_status,
        orientation_status,
    ):
        return "incomplete"
    return "incomplete" if blocking_reasons else "passed"


def _candidate_evidence_refs(
    modeled_task_count: int,
    simulation_sample_count: int,
) -> tuple[str, ...]:
    refs = []
    if modeled_task_count > 0:
        refs.append(f"modeled_task_specs:{modeled_task_count}")
    if simulation_sample_count > 0:
        refs.append(f"next_batch_samples:{simulation_sample_count}")
    return tuple(refs)


def _dedupe_text(values: list[str]) -> tuple[str, ...]:
    deduped: list[str] = []
    for value in values:
        if value not in deduped:
            deduped.append(value)
    return tuple(deduped)
