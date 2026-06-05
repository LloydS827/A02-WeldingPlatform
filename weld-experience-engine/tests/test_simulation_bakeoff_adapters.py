import pytest

from weldcore.simulation_bakeoff import (
    attempt_gazebo_moveit,
    attempt_maniskill_sapien,
    default_maniskill_task_configs,
    default_simulation_task_specs,
    generate_rule_based_demo,
    run_maniskill_lightweight,
    run_simlite_reference,
    write_json_artifact,
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


def _mock_completed_backend(monkeypatch):
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._maniskill_backend_available",
        lambda: True,
    )
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._run_backend",
        lambda config, demo: {
            "status": "completed",
            "task_state": {"attempted": True, "backend_invoked": True},
            "metrics": {"task_contract_outputs_ready": 1.0},
        },
    )


def test_maniskill_attempt_uses_completed_raw_artifact(tmp_path, monkeypatch):
    task_spec = default_simulation_task_specs()[0]
    config = default_maniskill_task_configs()[0]
    demo = generate_rule_based_demo(config)
    _mock_completed_backend(monkeypatch)
    artifact = run_maniskill_lightweight(config, demo)
    artifact_path = tmp_path / "raw_artifact.json"
    write_json_artifact(artifact_path, artifact.to_dict())

    result = attempt_maniskill_sapien(task_spec, raw_artifact_path=artifact_path)

    assert result.status == "completed"
    assert result.adapter_name == "maniskill_sapien"
    assert result.failure_boundary == ()
    assert result.planning_result["validated_task_contract"] is True


def test_maniskill_attempt_records_missing_artifact_boundary(tmp_path):
    task_spec = default_simulation_task_specs()[0]

    result = attempt_maniskill_sapien(
        task_spec,
        raw_artifact_path=tmp_path / "missing.json",
    )

    assert result.status == "failed"
    assert "artifact_missing" in result.failure_boundary


def test_maniskill_attempt_records_adapter_conversion_failure(tmp_path):
    task_spec = default_simulation_task_specs()[0]
    artifact_path = tmp_path / "raw_artifact.json"
    artifact_path.write_text("{not-json", encoding="utf-8")

    result = attempt_maniskill_sapien(task_spec, raw_artifact_path=artifact_path)

    assert result.status == "failed"
    assert "adapter_conversion_failed" in result.failure_boundary


def test_maniskill_attempt_does_not_mask_adapter_runtime_errors(tmp_path, monkeypatch):
    task_spec = default_simulation_task_specs()[0]
    config = default_maniskill_task_configs()[0]
    demo = generate_rule_based_demo(config)
    _mock_completed_backend(monkeypatch)
    artifact = run_maniskill_lightweight(config, demo)
    artifact_path = tmp_path / "raw_artifact.json"
    write_json_artifact(artifact_path, artifact.to_dict())

    def raise_adapter_bug(task_spec, artifact):
        raise RuntimeError("bug")

    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.adapters.adapt_maniskill_artifact",
        raise_adapter_bug,
    )

    with pytest.raises(RuntimeError, match="bug"):
        attempt_maniskill_sapien(task_spec, raw_artifact_path=artifact_path)
