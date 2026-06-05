import json

from weldcore.simulation_bakeoff import run_maniskill_spike_pipeline


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


def test_pipeline_writes_artifacts_for_two_default_tasks(tmp_path, monkeypatch):
    _mock_completed_backend(monkeypatch)

    summary = run_maniskill_spike_pipeline(tmp_path)

    assert summary["task_count"] == 2
    assert summary["completed"] == 2
    assert summary["failed"] == 0
    for task in summary["tasks"]:
        task_dir = tmp_path / task["task_id"]
        assert (task_dir / "task_config.json").exists()
        assert (task_dir / "demo.json").exists()
        assert (task_dir / "raw_artifact.json").exists()
        assert (task_dir / "adapter_result.json").exists()
        assert (task_dir / "experience_dataset.json").exists()
        assert (task_dir / "evidence_bundle.json").exists()


def test_pipeline_summary_records_structured_failures(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._maniskill_backend_available",
        lambda: False,
    )

    summary = run_maniskill_spike_pipeline(tmp_path)

    assert summary["task_count"] == 2
    assert summary["completed"] == 0
    assert summary["failed"] == 2
    assert summary["failure_boundaries"] == ["environment_missing"]
    assert json.loads((tmp_path / "run_summary.json").read_text())["failed"] == 2


def test_pipeline_converts_task_generation_errors_to_failure_artifact(tmp_path, monkeypatch):
    def fail_task_generation(task_spec):
        raise ValueError("bad task")

    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_pipeline.maniskill_task_config_from_spec",
        fail_task_generation,
    )

    summary = run_maniskill_spike_pipeline(tmp_path)

    assert summary["task_count"] == 2
    assert summary["failed"] == 2
    assert summary["failure_boundaries"] == ["task_generation_failed"]
    for task in summary["tasks"]:
        task_dir = tmp_path / task["task_id"]
        assert (task_dir / "raw_artifact.json").exists()


def test_pipeline_converts_adapter_errors_to_failure_artifact(tmp_path, monkeypatch):
    _mock_completed_backend(monkeypatch)
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_pipeline.adapt_maniskill_artifact",
        lambda task_spec, artifact: (_ for _ in ()).throw(ValueError("bad adapter")),
    )

    summary = run_maniskill_spike_pipeline(tmp_path)

    assert summary["task_count"] == 2
    assert summary["failed"] == 2
    assert summary["failure_boundaries"] == ["adapter_conversion_failed"]
    for task in summary["tasks"]:
        task_dir = tmp_path / task["task_id"]
        raw = json.loads((task_dir / "raw_artifact.json").read_text())
        assert raw["failure_boundary"] == ["adapter_conversion_failed"]
