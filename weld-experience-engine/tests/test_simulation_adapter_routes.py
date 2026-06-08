from weldcore.simulation_bakeoff import (
    default_simulation_adapter_routes,
    get_default_batch_route,
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
