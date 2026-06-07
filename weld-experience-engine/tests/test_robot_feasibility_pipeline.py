from dataclasses import replace

from weldcore.robot_process import (
    RobotContextSpec,
    build_robot_feasibility_result,
    build_robot_process_package_draft,
    default_mock_robot_context,
    update_robot_process_draft_with_feasibility,
)
from weldcore.simulation_bakeoff import (
    attempt_gazebo_moveit,
    build_simulation_evidence_bundle,
    default_simulation_task_specs,
    run_simlite_reference,
)


def _completed_draft():
    task_spec = default_simulation_task_specs()[0]
    bundle = build_simulation_evidence_bundle(task_spec, run_simlite_reference(task_spec))
    return build_robot_process_package_draft(bundle)


def _failed_draft():
    task_spec = default_simulation_task_specs()[0]
    bundle = build_simulation_evidence_bundle(task_spec, attempt_gazebo_moveit(task_spec))
    return build_robot_process_package_draft(bundle)


def _without_robot_model(context: RobotContextSpec) -> RobotContextSpec:
    return replace(context, robot_model=None)


def _without_frame(context: RobotContextSpec) -> RobotContextSpec:
    return replace(context, workpiece_frame=None)


def _without_base_frame(context: RobotContextSpec) -> RobotContextSpec:
    return replace(context, base_frame=None)


def _without_tcp_frame(context: RobotContextSpec) -> RobotContextSpec:
    return replace(context, tcp_frame=None)


def _without_tcp_calibration(context: RobotContextSpec) -> RobotContextSpec:
    return replace(context, tcp_calibration_status=None)


def _with_unknown_tcp_calibration(context: RobotContextSpec) -> RobotContextSpec:
    return replace(context, tcp_calibration_status="unknown")


def test_missing_context_keeps_missing_robot_context_readiness():
    draft = _completed_draft()

    updated = update_robot_process_draft_with_feasibility(draft, None, None)

    assert updated.readiness == "blocked_by_missing_robot_context"
    assert updated.status == "blocked"
    assert "not_ready_for_robot_execution" in updated.evidence_boundary


def test_missing_robot_identity_blocks_with_specific_reason():
    draft = _completed_draft()
    context = _without_robot_model(default_mock_robot_context())

    updated = update_robot_process_draft_with_feasibility(draft, context, None)

    assert updated.readiness == "blocked_by_missing_robot_identity"
    assert "robot_model" in updated.robot_execution_spec.missing_robot_context


def test_missing_frame_context_blocks_with_specific_reason():
    draft = _completed_draft()
    context = _without_frame(default_mock_robot_context())

    updated = update_robot_process_draft_with_feasibility(draft, context, None)

    assert updated.readiness == "blocked_by_missing_frame_context"
    assert "workpiece_frame" in updated.robot_execution_spec.missing_robot_context


def test_missing_base_frame_blocks_with_frame_context_reason():
    draft = _completed_draft()
    context = _without_base_frame(default_mock_robot_context())

    updated = update_robot_process_draft_with_feasibility(draft, context, None)

    assert updated.readiness == "blocked_by_missing_frame_context"
    assert "base_frame" in updated.robot_execution_spec.missing_robot_context


def test_missing_tcp_frame_blocks_with_frame_context_reason():
    draft = _completed_draft()
    context = _without_tcp_frame(default_mock_robot_context())

    updated = update_robot_process_draft_with_feasibility(draft, context, None)

    assert updated.readiness == "blocked_by_missing_frame_context"
    assert updated.robot_execution_spec.tcp_frame is None
    assert "tcp_frame" in updated.robot_execution_spec.missing_robot_context


def test_missing_tcp_calibration_blocks_with_specific_reason():
    draft = _completed_draft()
    context = _without_tcp_calibration(default_mock_robot_context())

    updated = update_robot_process_draft_with_feasibility(draft, context, None)

    assert updated.readiness == "blocked_by_missing_tcp_calibration"
    assert "tcp_calibration" in updated.robot_execution_spec.missing_robot_context


def test_unknown_tcp_calibration_blocks_with_specific_reason():
    draft = _completed_draft()
    context = _with_unknown_tcp_calibration(default_mock_robot_context())

    updated = update_robot_process_draft_with_feasibility(draft, context, None)

    assert updated.readiness == "blocked_by_missing_tcp_calibration"
    assert "tcp_calibration" in updated.robot_execution_spec.missing_robot_context


def test_complete_context_without_feasibility_result_blocks():
    draft = _completed_draft()
    context = default_mock_robot_context()

    updated = update_robot_process_draft_with_feasibility(draft, context, None)

    assert updated.readiness == "blocked_by_missing_feasibility_result"


def test_failed_reachability_blocks_draft():
    draft = _completed_draft()
    context = default_mock_robot_context()
    result = replace(
        build_robot_feasibility_result(draft, context),
        status="failed",
        reachability_status="failed",
        blocking_reasons=("failed_reachability",),
    )

    updated = update_robot_process_draft_with_feasibility(draft, context, result)

    assert updated.readiness == "blocked_by_failed_reachability"


def test_failed_collision_blocks_draft():
    draft = _completed_draft()
    context = default_mock_robot_context()
    result = replace(
        build_robot_feasibility_result(draft, context),
        status="failed",
        collision_status="failed",
        blocking_reasons=("failed_collision_check",),
    )

    updated = update_robot_process_draft_with_feasibility(draft, context, result)

    assert updated.readiness == "blocked_by_failed_collision_check"


def test_failed_joint_limit_blocks_draft():
    draft = _completed_draft()
    context = default_mock_robot_context()
    result = replace(
        build_robot_feasibility_result(draft, context),
        status="failed",
        joint_limit_status="failed",
        blocking_reasons=("failed_joint_limit_check",),
    )

    updated = update_robot_process_draft_with_feasibility(draft, context, result)

    assert updated.readiness == "blocked_by_failed_joint_limit_check"


def test_incomplete_feasibility_result_blocks_without_hiding_result():
    draft = _completed_draft()
    context = default_mock_robot_context()
    result = replace(
        build_robot_feasibility_result(draft, context),
        status="incomplete",
        path_continuity_status="missing",
        blocking_reasons=("missing_path_continuity",),
    )

    updated = update_robot_process_draft_with_feasibility(draft, context, result)

    assert updated.readiness == "blocked_by_incomplete_feasibility_result"
    assert updated.robot_execution_spec.reachability_status == result.reachability_status
    assert "missing_path_continuity" in updated.robot_execution_spec.execution_notes


def test_mock_context_and_passed_lightweight_result_reaches_expert_review_only():
    draft = _completed_draft()
    context = replace(default_mock_robot_context(), tcp_frame="context_torch_tcp")
    result = build_robot_feasibility_result(draft, context)

    updated = update_robot_process_draft_with_feasibility(draft, context, result)

    assert updated.status == "draft"
    assert updated.readiness == "ready_for_expert_review"
    assert updated.readiness != "ready_for_robot_execution"
    assert updated.robot_execution_spec.robot_model == "mock_6axis_welding_robot"
    assert updated.robot_execution_spec.tcp_frame == "context_torch_tcp"
    assert updated.robot_execution_spec.workpiece_frame == "workpiece"
    assert updated.robot_execution_spec.reachability_status == "passed"
    assert updated.robot_execution_spec.collision_status == "assumed"
    assert updated.robot_execution_spec.joint_limit_status == "passed"
    assert updated.robot_execution_spec.missing_robot_context == ()
    assert "mock_robot_context_only" in updated.evidence_boundary
    assert "lightweight_feasibility_precheck_only" in updated.evidence_boundary
    assert "not_ready_for_robot_execution" in updated.evidence_boundary
    assert "ready_for_robot_execution" not in updated.evidence_boundary


def test_prior_failed_simulation_readiness_is_not_overridden():
    draft = _failed_draft()
    context = default_mock_robot_context()
    result = build_robot_feasibility_result(draft, context)

    updated = update_robot_process_draft_with_feasibility(draft, context, result)

    assert updated.readiness == "blocked_by_failed_simulation"
    assert updated.status == "blocked"
