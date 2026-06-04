import json

from weldcore.model import SimulationRunRecord, SimulationRunStatus, SimulatorName
from weldcore.simulation_bakeoff import (
    BakeoffScorecard,
    SimulationEvidenceBundle,
    SimulationPathPoint,
    SimulationTaskSpec,
    SimulatorAdapterResult,
)


def test_simulation_task_spec_serializes_minimal_contract():
    spec = SimulationTaskSpec(
        task_id="task-long-straight-horizontal-tracking",
        unit_id="long-straight-horizontal-tracking",
        name="长直横焊沿缝跟踪仿真任务",
        seam_path=(
            SimulationPathPoint(t=0.0, x=0.0, y=0.0, z=0.0, rx=0.0, ry=10.0, rz=0.0),
            SimulationPathPoint(t=1.0, x=100.0, y=0.0, z=0.0, rx=0.0, ry=10.0, rz=0.0),
        ),
        tcp_frame="torch_tcp",
        tool_orientation_constraint=("work_angle_stable", "travel_angle_stable"),
        motion_constraint=("path_continuity", "speed_stability"),
        robot_constraint=("ik_reachability", "collision_check"),
        expected_outputs=("tcp_trajectory", "tool_orientation", "task_status"),
        evaluation_metrics=("path_continuity", "posture_stability", "speed_stability"),
        out_of_scope=("real_welding_quality", "WPS/PQR"),
    )

    data = spec.to_dict()

    assert data["task_id"] == "task-long-straight-horizontal-tracking"
    assert data["unit_id"] == "long-straight-horizontal-tracking"
    assert data["seam_path"][1]["x"] == 100.0
    assert data["tool_orientation_constraint"] == [
        "work_angle_stable",
        "travel_angle_stable",
    ]
    assert data["out_of_scope"] == ["real_welding_quality", "WPS/PQR"]


def test_adapter_result_serializes_success_and_failure_boundary():
    result = SimulatorAdapterResult(
        adapter_name="gazebo_moveit",
        task_id="task-corner-horizontal-transition",
        status="failed",
        tcp_trajectory=(),
        tool_orientation=(),
        planning_result={"attempted": True},
        failure_boundary=("optional_dependency_missing", "no_moveit_runtime"),
        metrics={"path_continuity": 0.0},
        artifacts={"report": "simulation_bakeoff_report_out/report.md"},
        evidence_notes=("same_task_attempted", "not_final_simulator_selection"),
    )

    data = result.to_dict()

    assert data["adapter_name"] == "gazebo_moveit"
    assert data["status"] == "failed"
    assert data["failure_boundary"] == [
        "optional_dependency_missing",
        "no_moveit_runtime",
    ]
    assert data["metrics"]["path_continuity"] == 0.0


def test_evidence_bundle_reuses_existing_run_record_contract():
    task = SimulationTaskSpec(
        task_id="task-long-straight-horizontal-tracking",
        unit_id="long-straight-horizontal-tracking",
        name="长直横焊沿缝跟踪仿真任务",
        seam_path=(SimulationPathPoint(t=0.0, x=0.0, y=0.0, z=0.0, rx=0.0, ry=0.0, rz=0.0),),
        tcp_frame="torch_tcp",
        tool_orientation_constraint=("stable",),
        motion_constraint=("continuous",),
        robot_constraint=("ik",),
        expected_outputs=("tcp_trajectory",),
        evaluation_metrics=("path_continuity",),
        out_of_scope=("real_welding_quality", "WPS/PQR"),
    )
    result = SimulatorAdapterResult(
        adapter_name="simlite_reference",
        task_id=task.task_id,
        status="completed",
        tcp_trajectory=task.seam_path,
        tool_orientation=task.seam_path,
        planning_result={"attempted": True, "task_status": "completed"},
        failure_boundary=(),
        metrics={"path_continuity": 1.0},
        artifacts={},
        evidence_notes=("r0_baseline",),
    )
    run_record = SimulationRunRecord(
        simulation_run_id="run-simlite-reference-task-long-straight-horizontal-tracking",
        input_id=task.task_id,
        simulator=SimulatorName.SIMLITE,
        simulator_version="0.1",
        adapter_version="bakeoff-v0.1",
        seed=None,
        sample_count=1,
        status=SimulationRunStatus.COMPLETED,
        created_at="2026-06-04T00:00:00Z",
        completed_at="2026-06-04T00:00:00Z",
        output_bundle_uris=[],
        boundary_notes=["not final simulator selection"],
    )
    bundle = SimulationEvidenceBundle(
        bundle_id="evidence-simlite-reference-task-long-straight-horizontal-tracking",
        task_spec=task,
        adapter_result=result,
        run_record=run_record,
        dataset=None,
        rerun_replay_uri=None,
        rerun_replay_status="not_attempted",
        rerun_notes=("rerun_optional_not_attempted_by_evidence_builder",),
        bakeoff_score={"digital_asset_score": 1.0},
    )

    data = bundle.to_dict()

    assert data["run_record"]["simulator"] == "simlite"
    assert data["adapter_result"]["status"] == "completed"
    assert data["dataset"] is None
    assert data["rerun_replay_status"] == "not_attempted"
    assert data["rerun_notes"] == ["rerun_optional_not_attempted_by_evidence_builder"]
    assert "SimulationOutputBundle" not in json.dumps(data)


def test_scorecard_declares_no_final_selection():
    scorecard = BakeoffScorecard(
        dimension_weights={
            "digital_asset_writeback": 0.35,
            "robot_executability": 0.30,
            "skill_unit_expression": 0.20,
            "engineering_access_cost": 0.15,
        },
        route_dimension_scores={
            "simlite_reference": {
                "digital_asset_writeback": 1.0,
                "robot_executability": 0.4,
                "skill_unit_expression": 1.0,
                "engineering_access_cost": 1.0,
            },
            "maniskill_sapien": {
                "digital_asset_writeback": 0.0,
                "robot_executability": 0.25,
                "skill_unit_expression": 1.0,
                "engineering_access_cost": 0.25,
            },
        },
        route_scores={"simlite_reference": 0.82, "maniskill_sapien": 0.3125},
        attempted_task_ids=("task-a", "task-b"),
        recommendation="continue_with_r0_baseline_and_external_spikes",
        final_simulator_selected=False,
        evidence_notes=("not_final_simulator_selection",),
    )

    data = scorecard.to_dict()

    assert data["final_simulator_selected"] is False
    assert data["attempted_task_ids"] == ["task-a", "task-b"]
    assert data["dimension_weights"] == {
        "digital_asset_writeback": 0.35,
        "robot_executability": 0.30,
        "skill_unit_expression": 0.20,
        "engineering_access_cost": 0.15,
    }
    assert data["route_dimension_scores"]["simlite_reference"]["digital_asset_writeback"] == 1.0
