from weldcore.simulation_bakeoff import run_minimal_simulation_bakeoff


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
