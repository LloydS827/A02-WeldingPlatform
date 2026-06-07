from weldcore.robot_process import (
    RobotContextSpec,
    RobotFeasibilityProbe,
    RobotFeasibilityResult,
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
