import json

from weldcore.robot_process import (
    BASE_ROBOT_PROCESS_EVIDENCE_BOUNDARY,
    ProcessParameterStatus,
    RobotExecutionSpec,
    RobotProcessPackageDraft,
)
from weldcore.simulation_bakeoff import SimulationPathPoint


def test_robot_process_package_draft_serializes_minimal_contract():
    point = SimulationPathPoint(t=0.0, x=0.0, y=0.0, z=0.12, rx=0.0, ry=90.0, rz=0.0)
    execution_spec = RobotExecutionSpec(
        robot_model=None,
        tcp_frame="torch_tcp",
        workpiece_frame=None,
        trajectory=(point,),
        tool_orientation=(point,),
        travel_speed=None,
        reachability_status="missing",
        collision_status="missing",
        joint_limit_status="missing",
        execution_notes=("simulation_only",),
        missing_robot_context=("robot_model", "workpiece_frame"),
    )
    process_status = ProcessParameterStatus(
        group_name="process_parameters",
        statuses=("missing_required", "requires_expert_review", "requires_real_validation"),
        available_fields=(),
        missing_fields=("welding_current", "welding_voltage"),
        required_future_sources=("expert_review", "welder_process_data"),
        evidence_notes=("not_filled_from_manual_json",),
    )
    draft = RobotProcessPackageDraft(
        draft_id="draft-evidence-simlite-task-a",
        source_bundle_id="evidence-simlite-task-a",
        source_task_id="task-a",
        source_type="simulation",
        status="blocked",
        source_evidence={"adapter_name": "simlite_reference"},
        process_parameter_status=(process_status,),
        robot_execution_spec=execution_spec,
        readiness="blocked_by_missing_robot_context",
        evidence_boundary=BASE_ROBOT_PROCESS_EVIDENCE_BOUNDARY,
    )

    data = draft.to_dict()

    assert data["draft_id"] == "draft-evidence-simlite-task-a"
    assert data["source_type"] == "simulation"
    assert data["status"] == "blocked"
    assert data["readiness"] == "blocked_by_missing_robot_context"
    assert data["robot_execution_spec"]["tcp_frame"] == "torch_tcp"
    assert data["process_parameter_status"][0]["statuses"] == [
        "missing_required",
        "requires_expert_review",
        "requires_real_validation",
    ]
    assert "not_WPS_PQR" in data["evidence_boundary"]
    assert "ready_for_robot_execution" not in json.dumps(data)


def test_process_parameter_status_keeps_statuses_and_readiness_separate():
    status = ProcessParameterStatus(
        group_name="robot_context",
        statuses=("requires_robot_context",),
        available_fields=("tcp_frame",),
        missing_fields=("robot_model", "workpiece_frame"),
        required_future_sources=("real_robot_log",),
        evidence_notes=("readiness_is_not_a_parameter_status",),
    )

    data = status.to_dict()

    assert data["statuses"] == ["requires_robot_context"]
    assert "blocked_by_missing_robot_context" not in data["statuses"]


def test_base_evidence_boundary_declares_non_production_limits():
    assert "simulation_only" in BASE_ROBOT_PROCESS_EVIDENCE_BOUNDARY
    assert "not_robot_process_package" in BASE_ROBOT_PROCESS_EVIDENCE_BOUNDARY
    assert "not_ready_for_robot_execution" in BASE_ROBOT_PROCESS_EVIDENCE_BOUNDARY
    assert "not_real_welding_quality_validation" in BASE_ROBOT_PROCESS_EVIDENCE_BOUNDARY
    assert "not_WPS_PQR" in BASE_ROBOT_PROCESS_EVIDENCE_BOUNDARY
