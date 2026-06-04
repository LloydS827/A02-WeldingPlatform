from weldcore.simulation_bakeoff import (
    attempt_gazebo_moveit,
    attempt_maniskill_sapien,
    default_simulation_task_specs,
    run_simlite_reference,
)


def test_simlite_reference_completes_each_default_task():
    for task_spec in default_simulation_task_specs():
        result = run_simlite_reference(task_spec)

        assert result.adapter_name == "simlite_reference"
        assert result.task_id == task_spec.task_id
        assert result.status == "completed"
        assert len(result.tcp_trajectory) == len(task_spec.seam_path)
        assert result.failure_boundary == ()
        assert result.metrics["path_continuity"] == 1.0
        assert result.planning_result["task_status"] == "completed"
        assert "r0_baseline" in result.evidence_notes


def test_external_adapter_spikes_attempt_same_task_and_return_standard_boundary():
    task_spec = default_simulation_task_specs()[0]

    for attempt in (attempt_maniskill_sapien, attempt_gazebo_moveit):
        result = attempt(task_spec)

        assert result.task_id == task_spec.task_id
        assert result.status in {"completed", "failed"}
        assert result.planning_result["attempted"] is True
        assert "not_final_simulator_selection" in result.evidence_notes
        if result.status == "failed":
            assert result.tcp_trajectory == ()
            assert result.failure_boundary
            assert result.failure_boundary[0] in {
                "optional_dependency_missing",
                "external_spike_not_executed",
            }
        if result.status == "completed":
            assert len(result.tcp_trajectory) == len(task_spec.seam_path)
            assert len(result.tool_orientation) == len(task_spec.seam_path)
            assert result.planning_result["validated_task_contract"] is True
            assert result.planning_result["task_status"] == "completed"
            assert result.metrics["same_task_attempted"] == 1.0
            assert result.metrics["task_contract_outputs_ready"] == 1.0


def test_external_adapter_names_are_stable():
    task_spec = default_simulation_task_specs()[0]

    assert attempt_maniskill_sapien(task_spec).adapter_name == "maniskill_sapien"
    assert attempt_gazebo_moveit(task_spec).adapter_name == "gazebo_moveit"
