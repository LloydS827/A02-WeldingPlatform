from __future__ import annotations

from dataclasses import replace

from .model import (
    RobotExecutionReadiness,
    RobotContextSpec,
    RobotFeasibilityAdapterHint,
    RobotFeasibilityProbe,
    RobotFeasibilityResult,
    RobotFeasibilityStrategy,
    RobotProcessPackageDraft,
)

DEFAULT_REQUESTED_CHECKS = (
    "reachability",
    "collision",
    "joint_limits",
    "path_continuity",
    "orientation_feasibility",
)

MOCK_CONTEXT_EVIDENCE_BOUNDARY = (
    "mock_robot_context_only",
    "not_real_robot_model",
    "not_vendor_validated",
    "not_ready_for_robot_execution",
)

LIGHTWEIGHT_FEASIBILITY_EVIDENCE_BOUNDARY = (
    "lightweight_feasibility_precheck_only",
    "not_moveit_validated",
    "not_gazebo_validated",
    "not_real_robot_validated",
    "not_ready_for_robot_execution",
)


def default_mock_robot_context() -> RobotContextSpec:
    return RobotContextSpec(
        context_id="mock-context-001",
        robot_model="mock_6axis_welding_robot",
        robot_family="six_axis_industrial_arm",
        base_frame="robot_base",
        tcp_frame="torch_tcp",
        tcp_calibration_status="mock_calibrated",
        workpiece_frame="workpiece",
        tool_payload={"mass_kg": 3.2},
        joint_limits_source="mock_spec",
        workspace_hint={"max_radius_m": 1.4, "z_min_m": -0.2, "z_max_m": 1.5},
        context_source="mock",
        evidence_notes=MOCK_CONTEXT_EVIDENCE_BOUNDARY,
    )


def build_robot_feasibility_result(
    draft: RobotProcessPackageDraft,
    robot_context: RobotContextSpec | None,
    strategy: RobotFeasibilityStrategy = "lightweight_rule",
    adapter_hint: RobotFeasibilityAdapterHint = "lightweight_rule",
) -> RobotFeasibilityResult:
    probe = RobotFeasibilityProbe(
        probe_id=f"probe-{draft.draft_id}",
        draft_id=draft.draft_id,
        context_id=robot_context.context_id if robot_context else "missing-context",
        strategy=strategy,
        requested_checks=DEFAULT_REQUESTED_CHECKS,
        adapter_hint=adapter_hint,
        evidence_notes=("lightweight_precheck_request",),
    )
    trajectory = draft.robot_execution_spec.trajectory
    orientation = draft.robot_execution_spec.tool_orientation
    blocking_reasons: list[str] = []
    warning_reasons = ["lightweight_rule_only"]

    if robot_context is None:
        blocking_reasons.append("missing_robot_context")
        reachability_status = "missing"
        collision_status = "not_checked"
        joint_limit_status = "missing"
        path_continuity_status = "missing"
        orientation_status = "missing"
        result_status = "incomplete"
    else:
        warning_reasons.append("mock_context_only")
        reachability_status = "passed" if trajectory else "missing"
        collision_status = "assumed"
        joint_limit_status = "passed" if robot_context.joint_limits_source else "missing"
        path_continuity_status = "passed" if len(trajectory) >= 2 else "missing"
        orientation_status = "passed" if orientation else "missing"

        if reachability_status == "missing":
            blocking_reasons.append("missing_trajectory")
        if joint_limit_status == "missing":
            blocking_reasons.append("missing_joint_limits_source")
        if path_continuity_status == "missing":
            blocking_reasons.append("missing_path_continuity")
        if orientation_status == "missing":
            blocking_reasons.append("missing_tool_orientation")
        result_status = "passed" if not blocking_reasons else "incomplete"

    return RobotFeasibilityResult(
        result_id=f"result-{probe.probe_id}",
        probe_id=probe.probe_id,
        draft_id=draft.draft_id,
        context_id=probe.context_id,
        status=result_status,
        reachability_status=reachability_status,
        collision_status=collision_status,
        joint_limit_status=joint_limit_status,
        path_continuity_status=path_continuity_status,
        orientation_feasibility_status=orientation_status,
        blocking_reasons=tuple(blocking_reasons),
        warning_reasons=tuple(warning_reasons),
        evidence_source=strategy,
        adapter_hint=adapter_hint,
        evidence_boundary=LIGHTWEIGHT_FEASIBILITY_EVIDENCE_BOUNDARY,
        metrics={
            "trajectory_points": len(trajectory),
            "orientation_points": len(orientation),
        },
    )


def update_robot_process_draft_with_feasibility(
    draft: RobotProcessPackageDraft,
    robot_context: RobotContextSpec | None,
    feasibility_result: RobotFeasibilityResult | None,
) -> RobotProcessPackageDraft:
    readiness = _updated_readiness(draft, robot_context, feasibility_result)
    status = "blocked" if readiness.startswith("blocked_by_") else "draft"
    execution_spec = draft.robot_execution_spec
    missing_context = _missing_context_fields(robot_context)

    if robot_context is not None:
        execution_spec = replace(
            execution_spec,
            robot_model=robot_context.robot_model,
            workpiece_frame=robot_context.workpiece_frame,
            missing_robot_context=missing_context,
        )
    if feasibility_result is not None:
        execution_spec = replace(
            execution_spec,
            reachability_status=feasibility_result.reachability_status,
            collision_status=feasibility_result.collision_status,
            joint_limit_status=feasibility_result.joint_limit_status,
            execution_notes=_append_unique(
                execution_spec.execution_notes,
                (
                    feasibility_result.status,
                    feasibility_result.evidence_source,
                    readiness,
                )
                + feasibility_result.blocking_reasons,
            ),
        )

    return replace(
        draft,
        status=status,
        readiness=readiness,
        robot_execution_spec=execution_spec,
        evidence_boundary=_append_unique(
            draft.evidence_boundary,
            _context_boundaries(robot_context) + _result_boundaries(feasibility_result),
        ),
    )


def _updated_readiness(
    draft: RobotProcessPackageDraft,
    robot_context: RobotContextSpec | None,
    feasibility_result: RobotFeasibilityResult | None,
) -> RobotExecutionReadiness:
    if draft.readiness != "blocked_by_missing_robot_context" and draft.readiness.startswith(
        "blocked_by_"
    ):
        return draft.readiness
    if robot_context is None:
        return "blocked_by_missing_robot_context"

    missing_context = _missing_context_fields(robot_context)
    if "robot_model" in missing_context:
        return "blocked_by_missing_robot_identity"
    if any(field in missing_context for field in ("base_frame", "workpiece_frame", "tcp_frame")):
        return "blocked_by_missing_frame_context"
    if "tcp_calibration" in missing_context:
        return "blocked_by_missing_tcp_calibration"
    if feasibility_result is None:
        return "blocked_by_missing_feasibility_result"
    if feasibility_result.reachability_status == "failed":
        return "blocked_by_failed_reachability"
    if feasibility_result.collision_status == "failed":
        return "blocked_by_failed_collision_check"
    if feasibility_result.joint_limit_status == "failed":
        return "blocked_by_failed_joint_limit_check"
    if feasibility_result.status == "passed" and not feasibility_result.blocking_reasons:
        return "ready_for_expert_review"
    return "blocked_by_incomplete_feasibility_result"


def _missing_context_fields(robot_context: RobotContextSpec | None) -> tuple[str, ...]:
    if robot_context is None:
        return (
            "robot_model",
            "base_frame",
            "workpiece_frame",
            "tcp_frame",
            "tcp_calibration",
            "joint_limits_source",
        )

    missing: list[str] = []
    if robot_context.robot_model is None:
        missing.append("robot_model")
    if robot_context.base_frame is None:
        missing.append("base_frame")
    if robot_context.workpiece_frame is None:
        missing.append("workpiece_frame")
    if robot_context.tcp_frame is None:
        missing.append("tcp_frame")
    if robot_context.tcp_calibration_status in (None, "unknown"):
        missing.append("tcp_calibration")
    if robot_context.joint_limits_source is None:
        missing.append("joint_limits_source")
    return tuple(missing)


def _context_boundaries(robot_context: RobotContextSpec | None) -> tuple[str, ...]:
    return () if robot_context is None else robot_context.evidence_notes


def _result_boundaries(
    feasibility_result: RobotFeasibilityResult | None,
) -> tuple[str, ...]:
    return () if feasibility_result is None else feasibility_result.evidence_boundary


def _append_unique(existing: tuple[str, ...], additions: tuple[str, ...]) -> tuple[str, ...]:
    values = list(existing)
    for item in additions:
        if item not in values:
            values.append(item)
    return tuple(values)
