import json

from weldcore.simulation_bakeoff import run_maniskill_batch_pipeline


def _mock_completed_backend(monkeypatch):
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._maniskill_backend_available",
        lambda: True,
    )
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._run_backend",
        lambda config, demo: {
            "status": "completed",
            "task_state": {
                "attempted": True,
                "task_status": "completed",
                "backend_invoked": True,
            },
            "metrics": {
                "task_contract_outputs_ready": 1.0,
                "path_continuity": 1.0,
                "backend_invocation_ready": 1.0,
            },
        },
    )


def test_batch_pipeline_writes_twenty_completed_primary_samples(tmp_path, monkeypatch):
    _mock_completed_backend(monkeypatch)

    result = run_maniskill_batch_pipeline(outdir=tmp_path, batch_id="batch-test")

    assert result["batch_id"] == "batch-test"
    assert result["route_id"] == "maniskill_sapien"
    assert result["task_count"] == 2
    assert result["requested_sample_count"] == 20
    assert result["completed_sample_count"] == 20
    assert result["failed_sample_count"] == 0
    assert result["skipped_sample_count"] == 0
    assert result["failure_boundaries"] == []
    assert (tmp_path / "batch-test" / "batch_spec.json").exists()
    result_path = tmp_path / "batch-test" / "batch_result.json"
    assert result_path.exists()
    assert json.loads(result_path.read_text(encoding="utf-8")) == result
    assert len(result["sample_runs"]) == 20

    for sample_run in result["sample_runs"]:
        assert sample_run["status"] == "completed"
        sample_dir = tmp_path / "batch-test" / "samples" / sample_run["sample_id"]
        assert (sample_dir / "task_config.json").exists()
        assert (sample_dir / "demo.json").exists()
        assert (sample_dir / "raw_artifact.json").exists()
        assert (sample_dir / "adapter_result.json").exists()
        assert (sample_dir / "evidence_bundle.json").exists()
        assert (sample_dir / "experience_dataset.json").exists()
        assert not (sample_dir / "failure_artifact.json").exists()


def test_batch_pipeline_records_environment_missing_as_twenty_failed_samples(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._maniskill_backend_available",
        lambda: False,
    )

    result = run_maniskill_batch_pipeline(outdir=tmp_path, batch_id="batch-test")

    assert result["requested_sample_count"] == 20
    assert result["completed_sample_count"] == 0
    assert result["failed_sample_count"] == 20
    assert result["failure_boundaries"] == ["environment_missing"]
    assert len(result["sample_runs"]) == 20
    for sample_run in result["sample_runs"]:
        sample_dir = tmp_path / "batch-test" / "samples" / sample_run["sample_id"]
        assert sample_run["status"] == "failed"
        assert sample_run["experience_dataset_uri"] is None
        assert sample_run["failure_boundary"] == ["environment_missing"]
        assert sample_run["raw_artifact_uri"].endswith("raw_artifact.json")
        assert (sample_dir / "raw_artifact.json").exists()
        assert (sample_dir / "failure_artifact.json").exists()


def test_batch_pipeline_uses_failure_artifact_uri_when_task_generation_fails(
    tmp_path,
    monkeypatch,
):
    def fail_task_generation(task_spec):
        raise ValueError("bad task")

    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_batch_pipeline."
        "maniskill_task_config_from_spec",
        fail_task_generation,
    )

    result = run_maniskill_batch_pipeline(outdir=tmp_path, batch_id="batch-test")

    assert result["failed_sample_count"] == 20
    assert result["failure_boundaries"] == ["task_generation_failed"]
    assert len(result["sample_runs"]) == 20
    for sample_run in result["sample_runs"]:
        sample_dir = tmp_path / "batch-test" / "samples" / sample_run["sample_id"]
        assert sample_run["status"] == "failed"
        assert sample_run["raw_artifact_uri"].endswith("failure_artifact.json")
        assert (sample_dir / "failure_artifact.json").exists()
        assert not (sample_dir / "raw_artifact.json").exists()


def test_batch_pipeline_keeps_comparison_routes_as_metadata_only(tmp_path, monkeypatch):
    _mock_completed_backend(monkeypatch)

    def fail_if_called(task_spec):
        raise AssertionError("comparison route should not run")

    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.routes.run_simlite_reference",
        fail_if_called,
    )
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.adapters.run_simlite_reference",
        fail_if_called,
    )

    result = run_maniskill_batch_pipeline(outdir=tmp_path, batch_id="batch-test")

    batch_spec = json.loads(
        (tmp_path / "batch-test" / "batch_spec.json").read_text(encoding="utf-8")
    )
    assert result["requested_sample_count"] == 20
    assert batch_spec["comparison_route_ids"] == ["simlite_reference"]
    assert {sample["route_id"] for sample in result["sample_runs"]} == {
        "maniskill_sapien"
    }
