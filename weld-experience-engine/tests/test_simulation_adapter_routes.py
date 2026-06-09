import pytest

from weldcore.simulation_bakeoff import (
    SimulationAdapterRoute,
    default_simulation_adapter_routes,
    default_simulation_task_specs,
    get_default_batch_route,
    run_adapter_route,
    run_comparison_routes,
)


def test_default_simulation_adapter_routes_declares_current_route_roles():
    routes = default_simulation_adapter_routes()
    by_id = {route.route_id: route for route in routes}

    assert tuple(by_id) == (
        "simlite_reference",
        "maniskill_sapien",
        "gazebo_moveit",
    )
    assert by_id["simlite_reference"].role == "baseline"
    assert by_id["simlite_reference"].default_for_batch is False
    assert by_id["maniskill_sapien"].role == "default_candidate"
    assert by_id["maniskill_sapien"].default_for_batch is True
    assert by_id["gazebo_moveit"].role == "planning_candidate"
    assert by_id["gazebo_moveit"].default_for_batch is False
    assert "not_final_simulator_selection" in by_id["maniskill_sapien"].evidence_boundary


def test_get_default_batch_route_returns_maniskill_candidate_without_locking_it():
    route = get_default_batch_route()

    assert route.route_id == "maniskill_sapien"
    assert route.role == "default_candidate"
    assert route.default_for_batch is True
    assert "not_locked_for_robot_execution" in route.evidence_boundary


def test_route_to_dict_omits_runner_and_listifies_boundaries():
    route = default_simulation_adapter_routes()[0]

    data = route.to_dict()

    assert "runner" not in data
    assert data["dependency_boundary"] == list(route.dependency_boundary)
    assert data["evidence_boundary"] == list(route.evidence_boundary)


def test_run_adapter_route_executes_selected_route_and_returns_simlite_result():
    task_spec = default_simulation_task_specs()[0]

    result = run_adapter_route("simlite_reference", task_spec)

    assert result.adapter_name == "simlite_reference"
    assert result.task_id == task_spec.task_id
    assert result.status == "completed"
    assert result.planning_result["validated_task_contract"] is True


def test_run_adapter_route_rejects_unknown_route_ids():
    task_spec = default_simulation_task_specs()[0]

    with pytest.raises(ValueError, match="Unknown simulation adapter route"):
        run_adapter_route("unknown_route", task_spec)


def test_run_adapter_route_converts_unexpected_runner_runtime_error_to_failed_result():
    task_spec = default_simulation_task_specs()[0]

    def broken_runner(_task_spec):
        raise RuntimeError("simulator exploded")

    routes = (
        SimulationAdapterRoute(
            route_id="broken_route",
            display_name="Broken route",
            role="baseline",
            status="available",
            runner=broken_runner,
            default_for_batch=False,
            dependency_boundary=(),
            evidence_boundary=(),
        ),
    )

    result = run_adapter_route("broken_route", task_spec, routes=routes)

    assert result.adapter_name == "broken_route"
    assert result.task_id == task_spec.task_id
    assert result.status == "failed"
    assert result.failure_boundary == ("simulation_run_failed",)
    assert result.planning_result["attempted"] is True
    assert result.planning_result["validated_task_contract"] is False
    assert result.metrics["same_task_attempted"] == 1.0
    assert result.metrics["task_contract_outputs_ready"] == 0.0
    assert result.evidence_notes == ("not_final_simulator_selection",)


def test_run_comparison_routes_returns_result_for_each_current_route():
    task_spec = default_simulation_task_specs()[0]

    results = run_comparison_routes(task_spec)

    assert tuple(result.adapter_name for result in results) == (
        "simlite_reference",
        "maniskill_sapien",
        "gazebo_moveit",
    )
