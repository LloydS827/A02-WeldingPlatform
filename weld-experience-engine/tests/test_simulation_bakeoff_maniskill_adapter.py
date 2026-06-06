from weldcore.model import SkillDataset
from weldcore.simulation_bakeoff import (
    adapt_maniskill_artifact,
    build_maniskill_experience_dataset,
    build_simulation_evidence_bundle,
    default_maniskill_task_configs,
    default_simulation_task_specs,
    generate_rule_based_demo,
    run_maniskill_lightweight,
)


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
            "metrics": {"task_contract_outputs_ready": 1.0, "path_continuity": 1.0},
        },
    )


def test_completed_artifact_converts_to_adapter_result(monkeypatch):
    config = default_maniskill_task_configs()[0]
    task_spec = default_simulation_task_specs()[0]
    demo = generate_rule_based_demo(config)
    _mock_completed_backend(monkeypatch)
    artifact = run_maniskill_lightweight(config, demo)

    result = adapt_maniskill_artifact(task_spec, artifact)

    assert result.adapter_name == "maniskill_sapien"
    assert result.status == "completed"
    assert result.tcp_trajectory == demo.tcp_trajectory
    assert result.failure_boundary == ()
    assert result.metrics["task_contract_outputs_ready"] == 1.0


def test_failed_artifact_keeps_failure_boundary(monkeypatch):
    config = default_maniskill_task_configs()[0]
    task_spec = default_simulation_task_specs()[0]
    demo = generate_rule_based_demo(config)
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._maniskill_backend_available",
        lambda: False,
    )
    artifact = run_maniskill_lightweight(config, demo)

    result = adapt_maniskill_artifact(task_spec, artifact)

    assert result.status == "failed"
    assert "environment_missing" in result.failure_boundary


def test_experience_dataset_and_skilldataset_compatibility_are_built(monkeypatch):
    config = default_maniskill_task_configs()[0]
    task_spec = default_simulation_task_specs()[0]
    demo = generate_rule_based_demo(config)
    _mock_completed_backend(monkeypatch)
    artifact = run_maniskill_lightweight(config, demo)
    result = adapt_maniskill_artifact(task_spec, artifact)

    experience = build_maniskill_experience_dataset(task_spec, artifact)
    bundle = build_simulation_evidence_bundle(task_spec, result)

    assert experience.source_type == "simulation"
    assert "SkillDataset" in experience.compatibility_exports
    assert isinstance(bundle.dataset, SkillDataset)
