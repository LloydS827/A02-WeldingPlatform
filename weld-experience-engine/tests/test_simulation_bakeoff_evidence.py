import json

from weldcore.model import SimulationRunStatus
from weldcore.simulation_bakeoff import (
    attempt_gazebo_moveit,
    build_simulation_evidence_bundle,
    default_simulation_task_specs,
    run_simlite_reference,
)


def test_completed_adapter_result_builds_existing_run_record_and_dataset():
    task_spec = default_simulation_task_specs()[0]
    adapter_result = run_simlite_reference(task_spec)

    bundle = build_simulation_evidence_bundle(task_spec, adapter_result)
    data = bundle.to_dict()

    assert bundle.run_record.status == SimulationRunStatus.COMPLETED
    assert bundle.run_record.input_id == task_spec.task_id
    assert bundle.dataset is not None
    assert bundle.dataset.source_type.value == "simulation"
    assert bundle.dataset.task == task_spec.unit_id
    assert data["adapter_result"]["status"] == "completed"
    assert data["dataset"]["samples"][0]["metadata"]["task_spec"]["task_id"] == task_spec.task_id
    assert (
        data["dataset"]["samples"][0]["metadata"]["adapter_result"]["adapter_name"]
        == "simlite_reference"
    )
    assert "not WPS/PQR" in data["dataset"]["samples"][0]["metadata"]["generation_boundary"]
    assert data["rerun_replay_status"] == "not_attempted"
    assert data["rerun_replay_uri"] is None
    assert "rerun_optional" in " ".join(data["rerun_notes"])


def test_failed_adapter_result_builds_failure_evidence_without_dataset_samples():
    task_spec = default_simulation_task_specs()[0]
    adapter_result = attempt_gazebo_moveit(task_spec)

    bundle = build_simulation_evidence_bundle(task_spec, adapter_result)

    if adapter_result.status == "failed":
        assert bundle.run_record.status == SimulationRunStatus.FAILED
        assert bundle.dataset is None
        assert bundle.adapter_result.failure_boundary
        assert "not final simulator selection" in " ".join(bundle.run_record.boundary_notes)


def test_evidence_bundle_excludes_forbidden_physics_terms():
    task_spec = default_simulation_task_specs()[0]
    bundle = build_simulation_evidence_bundle(task_spec, run_simlite_reference(task_spec))
    payload = json.dumps(bundle.to_dict(), ensure_ascii=False).lower()

    for forbidden in ("molten", "weld_pool", "thermal", "metallurgy", "熔池", "热过程", "冶金"):
        assert forbidden not in payload
