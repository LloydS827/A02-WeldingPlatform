import weldcore.simulation_bakeoff.bakeoff as bakeoff_module
from weldcore.simulation_bakeoff import (
    SimulationAdapterRoute,
    SimulatorAdapterResult,
    default_simulation_adapter_routes,
    run_minimal_simulation_bakeoff,
)


def test_minimal_bakeoff_attempts_same_two_tasks_across_routes():
    result = run_minimal_simulation_bakeoff()

    task_ids = {task.task_id for task in result.task_specs}
    assert task_ids == {
        "task-long-straight-horizontal-tracking",
        "task-corner-horizontal-transition",
    }

    attempts_by_adapter = {}
    for bundle in result.evidence_bundles:
        attempts_by_adapter.setdefault(bundle.adapter_result.adapter_name, set()).add(
            bundle.task_spec.task_id
        )

    assert attempts_by_adapter["simlite_reference"] == task_ids
    assert attempts_by_adapter["maniskill_sapien"] == task_ids
    assert attempts_by_adapter["gazebo_moveit"] == task_ids


def test_minimal_bakeoff_has_r0_completed_evidence_and_no_final_selection():
    result = run_minimal_simulation_bakeoff()
    data = result.to_dict()

    assert any(
        bundle.adapter_result.adapter_name == "simlite_reference"
        and bundle.adapter_result.status == "completed"
        and bundle.dataset is not None
        for bundle in result.evidence_bundles
    )
    assert result.scorecard.final_simulator_selected is False
    assert "not_final_simulator_selection" in result.scorecard.evidence_notes
    assert data["scorecard"]["final_simulator_selected"] is False
    assert data["scorecard"]["dimension_weights"] == {
        "digital_asset_writeback": 0.35,
        "robot_executability": 0.30,
        "skill_unit_expression": 0.20,
        "engineering_access_cost": 0.15,
    }
    assert set(data["scorecard"]["route_dimension_scores"]) == {
        "simlite_reference",
        "maniskill_sapien",
        "gazebo_moveit",
    }
    assert result.scorecard.route_dimension_scores["simlite_reference"] == {
        "digital_asset_writeback": 1.0,
        "robot_executability": 0.4,
        "skill_unit_expression": 1.0,
        "engineering_access_cost": 1.0,
    }
    assert result.scorecard.route_scores["simlite_reference"] == 0.82


def test_minimal_bakeoff_scorecard_uses_registered_route_ids():
    result = run_minimal_simulation_bakeoff()

    registered_route_ids = tuple(
        route.route_id for route in default_simulation_adapter_routes()
    )
    evidence_route_ids = tuple(
        dict.fromkeys(
            bundle.adapter_result.adapter_name for bundle in result.evidence_bundles
        )
    )
    evidence_adapter_order = tuple(
        bundle.adapter_result.adapter_name for bundle in result.evidence_bundles
    )
    expected_evidence_adapter_order = tuple(
        route_id for route_id in registered_route_ids for _task in result.task_specs
    )

    assert tuple(result.scorecard.route_dimension_scores) == registered_route_ids
    assert tuple(result.scorecard.route_scores) == registered_route_ids
    assert evidence_route_ids == registered_route_ids
    assert evidence_adapter_order == expected_evidence_adapter_order


def test_minimal_bakeoff_uses_single_registered_route_snapshot(monkeypatch):
    route_id = "snapshot_route"

    def run_snapshot_route(task_spec):
        return SimulatorAdapterResult(
            adapter_name=route_id,
            task_id=task_spec.task_id,
            status="completed",
            tcp_trajectory=task_spec.seam_path,
            tool_orientation=task_spec.seam_path,
            planning_result={
                "attempted": True,
                "validated_task_contract": True,
                "task_status": "completed",
            },
            failure_boundary=(),
            metrics={
                "same_task_attempted": 1.0,
                "task_contract_outputs_ready": 1.0,
            },
            artifacts={},
            evidence_notes=("snapshot_route",),
        )

    routes = (
        SimulationAdapterRoute(
            route_id=route_id,
            display_name="Snapshot route",
            role="planning_candidate",
            status="available",
            runner=run_snapshot_route,
            default_for_batch=False,
            dependency_boundary=(),
            evidence_boundary=("snapshot_route",),
        ),
    )
    monkeypatch.setattr(
        bakeoff_module,
        "default_simulation_adapter_routes",
        lambda: routes,
    )

    result = run_minimal_simulation_bakeoff()

    assert tuple(result.scorecard.route_dimension_scores) == (route_id,)
    assert tuple(result.scorecard.route_scores) == (route_id,)
    assert tuple(
        dict.fromkeys(
            bundle.adapter_result.adapter_name for bundle in result.evidence_bundles
        )
    ) == (route_id,)


def test_minimal_bakeoff_scores_external_failures_as_boundaries():
    result = run_minimal_simulation_bakeoff()

    external_bundles = [
        bundle
        for bundle in result.evidence_bundles
        if bundle.adapter_result.adapter_name in {"maniskill_sapien", "gazebo_moveit"}
    ]
    assert len(external_bundles) == 4

    for bundle in external_bundles:
        assert bundle.adapter_result.status in {"completed", "failed"}
        if bundle.adapter_result.status == "failed":
            assert bundle.adapter_result.failure_boundary
        if bundle.adapter_result.status == "completed":
            assert bundle.adapter_result.planning_result["validated_task_contract"] is True

    expected_external_dimension_scores = {
        "digital_asset_writeback": 0.35,
        "robot_executability": 0.25,
        "skill_unit_expression": 1.0,
        "engineering_access_cost": 0.25,
    }
    assert (
        result.scorecard.route_dimension_scores["maniskill_sapien"]
        == expected_external_dimension_scores
    )
    assert (
        result.scorecard.route_dimension_scores["gazebo_moveit"]
        == expected_external_dimension_scores
    )
    assert result.scorecard.route_scores["maniskill_sapien"] == 0.435
    assert result.scorecard.route_scores["gazebo_moveit"] == 0.435
