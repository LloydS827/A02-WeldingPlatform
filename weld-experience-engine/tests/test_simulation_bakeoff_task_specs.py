import json

from weldcore.simulation_bakeoff import (
    DEFAULT_SIMULATION_TASK_SPECS,
    default_simulation_task_specs,
)


def test_default_simulation_task_specs_cover_same_two_core_units():
    specs = default_simulation_task_specs()
    task_ids = {spec.task_id for spec in specs}
    unit_ids = {spec.unit_id for spec in specs}

    assert specs is DEFAULT_SIMULATION_TASK_SPECS
    assert len(specs) == 2
    assert task_ids == {
        "task-long-straight-horizontal-tracking",
        "task-corner-horizontal-transition",
    }
    assert unit_ids == {
        "long-straight-horizontal-tracking",
        "corner-horizontal-transition",
    }
    assert "u-seam-vertical-extension" not in unit_ids


def test_task_specs_have_paths_constraints_outputs_and_metrics():
    specs = default_simulation_task_specs()

    for spec in specs:
        data = spec.to_dict()
        assert data["tcp_frame"] == "torch_tcp"
        assert len(data["seam_path"]) >= 5
        assert "tcp_trajectory" in data["expected_outputs"]
        assert "tool_orientation" in data["expected_outputs"]
        assert "task_status" in data["expected_outputs"]
        assert "path_continuity" in data["evaluation_metrics"]
        assert "ik_reachability" in data["robot_constraint"]
        assert "collision_check" in data["robot_constraint"]
        assert "real_welding_quality" in data["out_of_scope"]
        assert "WPS/PQR" in data["out_of_scope"]


def test_long_straight_path_is_straight_with_increasing_x():
    specs = {spec.unit_id: spec for spec in default_simulation_task_specs()}
    path = specs["long-straight-horizontal-tracking"].seam_path

    assert {point.y for point in path} == {path[0].y}
    assert {point.z for point in path} == {path[0].z}
    assert all(left.x < right.x for left, right in zip(path, path[1:]))


def test_corner_path_turns_from_x_axis_to_y_axis():
    specs = {spec.unit_id: spec for spec in default_simulation_task_specs()}
    path = specs["corner-horizontal-transition"].seam_path
    first_leg = path[:3]
    second_leg = path[2:]

    assert {point.y for point in first_leg} == {first_leg[0].y}
    assert all(left.x < right.x for left, right in zip(first_leg, first_leg[1:]))
    assert {point.x for point in second_leg} == {second_leg[0].x}
    assert all(left.y < right.y for left, right in zip(second_leg, second_leg[1:]))


def test_task_specs_exclude_forbidden_physics_terms():
    payload = json.dumps(
        [spec.to_dict() for spec in default_simulation_task_specs()],
        ensure_ascii=False,
    ).lower()

    for forbidden in ("molten", "weld_pool", "thermal", "metallurgy", "熔池", "热过程", "冶金"):
        assert forbidden not in payload
