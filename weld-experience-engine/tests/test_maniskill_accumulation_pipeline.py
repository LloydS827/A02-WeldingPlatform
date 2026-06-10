import json

from weldcore.simulation_bakeoff import run_maniskill_accumulation_pipeline


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


def test_accumulation_pipeline_writes_phase_one_completed_outputs(
    tmp_path,
    monkeypatch,
):
    _mock_completed_backend(monkeypatch)

    result = run_maniskill_accumulation_pipeline(
        outdir=tmp_path,
        accumulation_id="acc-test",
    )

    acc_dir = tmp_path / "acc-test"
    assert result["accumulation_id"] == "acc-test"
    assert result["status"] == "ready_to_scale_with_conditions"
    assert result["requested_sample_count"] == 100
    assert result["completed_sample_count"] == 100
    assert (acc_dir / "accumulation_spec.json").exists()
    assert (acc_dir / "dataset_index.json").exists()
    assert (acc_dir / "accumulation_report.json").exists()
    assert (acc_dir / "batches" / "maniskill-sapien-accumulation-acc-test").exists()

    index = json.loads((acc_dir / "dataset_index.json").read_text(encoding="utf-8"))
    assert index["requested_sample_count"] == 100
    assert len(index["index_items"]) == 100
    assert index["batch_root_uris"] == {
        "maniskill-sapien-accumulation-acc-test": (
            "batches/maniskill-sapien-accumulation-acc-test"
        )
    }


def test_accumulation_pipeline_reports_environment_blocked(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._maniskill_backend_available",
        lambda: False,
    )

    result = run_maniskill_accumulation_pipeline(
        outdir=tmp_path,
        accumulation_id="acc-env",
    )

    assert result["status"] == "blocked_by_environment"
    assert result["requested_sample_count"] == 100
    assert result["failed_sample_count"] == 100
    assert result["dominant_failure_boundaries"] == ["environment_missing"]


def test_accumulation_pipeline_cli_prints_report(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._maniskill_backend_available",
        lambda: False,
    )

    from weldcore.simulation_bakeoff import maniskill_accumulation_pipeline

    maniskill_accumulation_pipeline.main(
        ["--outdir", str(tmp_path), "--accumulation-id", "acc-cli"]
    )

    printed = json.loads(capsys.readouterr().out)
    assert printed["accumulation_id"] == "acc-cli"
    assert printed["requested_sample_count"] == 100
    assert printed["status"] == "blocked_by_environment"
    assert (tmp_path / "acc-cli" / "accumulation_report.json").exists()
