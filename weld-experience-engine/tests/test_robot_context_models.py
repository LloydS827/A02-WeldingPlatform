from dataclasses import replace

from weldcore.robot_process import (
    RobotContextSpec,
    RobotFeasibilityProbe,
    RobotFeasibilityResult,
    build_robot_feasibility_result,
    build_robot_process_package_draft,
    default_mock_robot_context,
)
from weldcore.simulation_bakeoff import (
    build_simulation_evidence_bundle,
    default_simulation_task_specs,
    run_simlite_reference,
)


def test_robot_context_spec_serializes_minimal_contract():
    context = RobotContextSpec(
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
        evidence_notes=("mock_robot_context_only", "not_real_robot_model"),
    )

    data = context.to_dict()

    assert data["robot_model"] == "mock_6axis_welding_robot"
    assert data["tool_payload"]["mass_kg"] == 3.2
    assert "mock_robot_context_only" in data["evidence_notes"]
    assert "not_real_robot_model" in data["evidence_notes"]


def test_robot_feasibility_probe_serializes_adapter_hint():
    probe = RobotFeasibilityProbe(
        probe_id="probe-draft-001",
        draft_id="draft-001",
        context_id="mock-context-001",
        strategy="lightweight_rule",
        requested_checks=(
            "reachability",
            "collision",
            "joint_limits",
            "path_continuity",
            "orientation_feasibility",
        ),
        adapter_hint="moveit_future",
        evidence_notes=("future_adapter_contract",),
    )

    data = probe.to_dict()

    assert data["strategy"] == "lightweight_rule"
    assert "reachability" in data["requested_checks"]
    assert data["adapter_hint"] == "moveit_future"


def test_robot_feasibility_result_serializes_statuses_and_boundaries():
    result = RobotFeasibilityResult(
        result_id="result-probe-001",
        probe_id="probe-draft-001",
        draft_id="draft-001",
        context_id="mock-context-001",
        status="passed",
        reachability_status="passed",
        collision_status="assumed",
        joint_limit_status="passed",
        path_continuity_status="passed",
        orientation_feasibility_status="passed",
        blocking_reasons=(),
        warning_reasons=("mock_context_only",),
        evidence_source="lightweight_rule",
        adapter_hint="moveit_future",
        evidence_boundary=(
            "lightweight_feasibility_precheck_only",
            "not_moveit_validated",
            "not_ready_for_robot_execution",
        ),
        metrics={"trajectory_points": 2},
    )

    data = result.to_dict()

    assert data["status"] == "passed"
    assert data["collision_status"] == "assumed"
    assert data["blocking_reasons"] == []
    assert "not_ready_for_robot_execution" in data["evidence_boundary"]


def _completed_draft():
    task_spec = default_simulation_task_specs()[0]
    bundle = build_simulation_evidence_bundle(task_spec, run_simlite_reference(task_spec))
    return build_robot_process_package_draft(bundle)


def test_default_mock_robot_context_has_required_boundaries():
    context = default_mock_robot_context()

    assert context.robot_model == "mock_6axis_welding_robot"
    assert context.robot_family == "six_axis_industrial_arm"
    assert context.base_frame == "robot_base"
    assert context.tcp_frame == "torch_tcp"
    assert context.tcp_calibration_status == "mock_calibrated"
    assert context.workpiece_frame == "workpiece"
    assert context.context_source == "mock"
    assert "mock_robot_context_only" in context.evidence_notes
    assert "not_real_robot_model" in context.evidence_notes
    assert "not_ready_for_robot_execution" in context.evidence_notes


def test_lightweight_feasibility_result_passes_with_mock_context_and_complete_motion():
    draft = _completed_draft()
    context = default_mock_robot_context()

    result = build_robot_feasibility_result(draft, context)

    assert result.status == "passed"
    assert result.adapter_hint == "lightweight_rule"
    assert result.reachability_status == "passed"
    assert result.collision_status == "assumed"
    assert result.joint_limit_status == "passed"
    assert result.path_continuity_status == "passed"
    assert result.orientation_feasibility_status == "passed"
    assert result.blocking_reasons == ()
    assert "mock_context_only" in result.warning_reasons
    assert result.metrics["trajectory_points"] == len(draft.robot_execution_spec.trajectory)
    assert "lightweight_feasibility_precheck_only" in result.evidence_boundary
    assert "not_moveit_validated" in result.evidence_boundary
    assert "not_gazebo_validated" in result.evidence_boundary
    assert "not_ready_for_robot_execution" in result.evidence_boundary


def test_lightweight_feasibility_result_marks_missing_robot_context_incomplete():
    draft = _completed_draft()

    result = build_robot_feasibility_result(draft, None)

    assert result.status == "incomplete"
    assert result.context_id == "missing-context"
    assert result.reachability_status == "missing"
    assert result.collision_status == "not_checked"
    assert result.joint_limit_status == "missing"
    assert result.path_continuity_status == "missing"
    assert result.orientation_feasibility_status == "missing"
    assert "missing_robot_context" in result.blocking_reasons


def test_lightweight_feasibility_result_marks_missing_trajectory_incomplete():
    draft = _completed_draft()
    execution_spec = replace(draft.robot_execution_spec, trajectory=())
    draft = replace(draft, robot_execution_spec=execution_spec)

    result = build_robot_feasibility_result(draft, default_mock_robot_context())

    assert result.status == "incomplete"
    assert result.reachability_status == "missing"
    assert "missing_trajectory" in result.blocking_reasons


def test_lightweight_feasibility_result_marks_missing_orientation_incomplete():
    draft = _completed_draft()
    execution_spec = replace(draft.robot_execution_spec, tool_orientation=())
    draft = replace(draft, robot_execution_spec=execution_spec)

    result = build_robot_feasibility_result(draft, default_mock_robot_context())

    assert result.status == "incomplete"
    assert result.orientation_feasibility_status == "missing"
    assert "missing_tool_orientation" in result.blocking_reasons
