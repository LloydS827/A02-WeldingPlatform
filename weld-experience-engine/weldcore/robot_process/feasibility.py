from __future__ import annotations

from .model import (
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
