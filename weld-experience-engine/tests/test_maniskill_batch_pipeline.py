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

    dataset_ids = set()
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

        raw_artifact = json.loads(
            (sample_dir / "raw_artifact.json").read_text(encoding="utf-8")
        )
        experience_dataset = json.loads(
            (sample_dir / "experience_dataset.json").read_text(encoding="utf-8")
        )
        adapter_result = json.loads(
            (sample_dir / "adapter_result.json").read_text(encoding="utf-8")
        )
        evidence_bundle = json.loads(
            (sample_dir / "evidence_bundle.json").read_text(encoding="utf-8")
        )

        sample_id = sample_run["sample_id"]
        assert raw_artifact["run_id"] == f"maniskill-{sample_id}"
        assert raw_artifact["task_state"]["sample_id"] == sample_id
        assert raw_artifact["task_state"]["seed"] == sample_run["seed"]
        assert raw_artifact["task_state"]["batch_id"] == "batch-test"
        assert adapter_result["planning_result"]["sample_id"] == sample_id
        assert adapter_result["planning_result"]["seed"] == sample_run["seed"]
        assert adapter_result["artifacts"]["sample_id"] == sample_id
        assert experience_dataset["dataset_id"] == f"experience-maniskill-{sample_id}"
        assert experience_dataset["samples"] == [sample_id]
        assert evidence_bundle["bundle_id"] == f"evidence-maniskill-{sample_id}"
        assert sample_id in evidence_bundle["run_record"]["simulation_run_id"]
        assert evidence_bundle["run_record"]["seed"] == sample_run["seed"]
        assert evidence_bundle["dataset"]["dataset_id"] == (
            f"dataset-maniskill_sapien-{sample_id}"
        )
        assert evidence_bundle["dataset"]["samples"][0]["sample_id"] == sample_id
        assert evidence_bundle["dataset"]["samples"][0]["metadata"]["sample_id"] == (
            sample_id
        )
        dataset_ids.add(experience_dataset["dataset_id"])

    assert len(dataset_ids) == 20


def test_batch_pipeline_accepts_custom_sample_count_and_seed(
    tmp_path,
    monkeypatch,
):
    _mock_completed_backend(monkeypatch)

    result = run_maniskill_batch_pipeline(
        outdir=tmp_path,
        batch_id="batch-custom",
        samples_per_task=2,
        seed_start=50,
    )

    assert result["requested_sample_count"] == 4
    assert result["completed_sample_count"] == 4
    seeds = [sample["seed"] for sample in result["sample_runs"]]
    assert seeds == [50, 51, 52, 53]
    batch_spec = json.loads(
        (tmp_path / "batch-custom" / "batch_spec.json").read_text(encoding="utf-8")
    )
    assert batch_spec["samples_per_task"] == 2
    assert batch_spec["seed_start"] == 50


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
        assert sample_run["failure_artifact_uri"].endswith("failure_artifact.json")
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
        assert sample_run["failure_artifact_uri"].endswith("failure_artifact.json")
        assert (sample_dir / "failure_artifact.json").exists()
        assert not (sample_dir / "raw_artifact.json").exists()


def test_batch_pipeline_records_runner_exceptions_as_failed_samples(
    tmp_path,
    monkeypatch,
):
    def fail_runner(config, demo):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_batch_pipeline."
        "run_maniskill_lightweight",
        fail_runner,
    )

    result = run_maniskill_batch_pipeline(outdir=tmp_path, batch_id="batch-test")

    assert result["requested_sample_count"] == 20
    assert result["completed_sample_count"] == 0
    assert result["failed_sample_count"] == 20
    assert result["failure_boundaries"] == ["simulation_run_failed"]
    assert (tmp_path / "batch-test" / "batch_result.json").exists()
    for sample_run in result["sample_runs"]:
        sample_dir = tmp_path / "batch-test" / "samples" / sample_run["sample_id"]
        assert sample_run["status"] == "failed"
        assert sample_run["raw_artifact_uri"].endswith("failure_artifact.json")
        assert sample_run["failure_boundary"] == ["simulation_run_failed"]
        assert (sample_dir / "failure_artifact.json").exists()
        assert not (sample_dir / "raw_artifact.json").exists()


def test_batch_pipeline_records_per_sample_demo_write_failures(
    tmp_path,
    monkeypatch,
):
    from weldcore.simulation_bakeoff import maniskill_batch_pipeline

    original_write = maniskill_batch_pipeline.write_json_artifact

    def fail_demo_write(path, data):
        if path.name == "demo.json":
            raise RuntimeError("demo write failed")
        original_write(path, data)

    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_batch_pipeline.write_json_artifact",
        fail_demo_write,
    )

    result = run_maniskill_batch_pipeline(outdir=tmp_path, batch_id="batch-test")

    assert result["requested_sample_count"] == 20
    assert result["completed_sample_count"] == 0
    assert result["failed_sample_count"] == 20
    assert result["failure_boundaries"] == ["demo_generation_failed"]
    assert (tmp_path / "batch-test" / "batch_result.json").exists()
    for sample_run in result["sample_runs"]:
        sample_dir = tmp_path / "batch-test" / "samples" / sample_run["sample_id"]
        assert sample_run["status"] == "failed"
        assert sample_run["raw_artifact_uri"].endswith("failure_artifact.json")
        assert sample_run["failure_boundary"] == ["demo_generation_failed"]
        assert (sample_dir / "failure_artifact.json").exists()
        assert not (sample_dir / "demo.json").exists()


def test_batch_pipeline_uses_fallback_when_failure_artifact_write_fails(
    tmp_path,
    monkeypatch,
):
    from weldcore.simulation_bakeoff import maniskill_batch_pipeline

    original_write = maniskill_batch_pipeline.write_json_artifact

    def fail_failure_artifact_write(path, data):
        if path.name == "failure_artifact.json":
            raise RuntimeError("failure artifact write failed")
        original_write(path, data)

    def fail_runner(config, demo):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_batch_pipeline.write_json_artifact",
        fail_failure_artifact_write,
    )
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_batch_pipeline."
        "run_maniskill_lightweight",
        fail_runner,
    )

    result = run_maniskill_batch_pipeline(outdir=tmp_path, batch_id="batch-test")

    assert result["requested_sample_count"] == 20
    assert result["completed_sample_count"] == 0
    assert result["failed_sample_count"] == 20
    assert result["failure_boundaries"] == [
        "simulation_run_failed",
        "data_contract_incomplete",
    ]
    assert (tmp_path / "batch-test" / "batch_result.json").exists()
    for sample_run in result["sample_runs"]:
        sample_dir = tmp_path / "batch-test" / "samples" / sample_run["sample_id"]
        fallback_path = sample_dir / "failure_artifact_write_failed.json"
        fallback_artifact = json.loads(fallback_path.read_text(encoding="utf-8"))
        assert sample_run["status"] == "failed"
        assert sample_run["raw_artifact_uri"].endswith(
            "failure_artifact_write_failed.json"
        )
        assert sample_run["failure_artifact_uri"].endswith(
            "failure_artifact_write_failed.json"
        )
        assert sample_run["failure_boundary"] == [
            "simulation_run_failed",
            "data_contract_incomplete",
        ]
        assert (sample_dir / "failure_artifact_write_failed.json").exists()
        assert not (sample_dir / "failure_artifact.json").exists()
        assert fallback_artifact["failure_boundary"] == [
            "simulation_run_failed",
            "data_contract_incomplete",
        ]
        assert "failure_artifact_write_failed" in fallback_artifact["evidence_notes"]


def test_batch_pipeline_uses_unavailable_uri_when_failure_artifact_writes_fail(
    tmp_path,
    monkeypatch,
):
    from weldcore.simulation_bakeoff import maniskill_batch_pipeline

    original_write = maniskill_batch_pipeline.write_json_artifact

    def fail_failure_artifact_writes(path, data):
        if path.name in {
            "failure_artifact.json",
            "failure_artifact_write_failed.json",
        }:
            raise RuntimeError("failure artifact write failed")
        original_write(path, data)

    def fail_runner(config, demo):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_batch_pipeline.write_json_artifact",
        fail_failure_artifact_writes,
    )
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_batch_pipeline."
        "run_maniskill_lightweight",
        fail_runner,
    )

    result = run_maniskill_batch_pipeline(outdir=tmp_path, batch_id="batch-test")

    assert result["requested_sample_count"] == 20
    assert result["completed_sample_count"] == 0
    assert result["failed_sample_count"] == 20
    assert result["failure_boundaries"] == [
        "simulation_run_failed",
        "data_contract_incomplete",
    ]
    assert (tmp_path / "batch-test" / "batch_result.json").exists()
    for sample_run in result["sample_runs"]:
        sample_dir = tmp_path / "batch-test" / "samples" / sample_run["sample_id"]
        assert sample_run["status"] == "failed"
        assert sample_run["raw_artifact_uri"].endswith(
            "failure_artifact_unavailable.json"
        )
        assert sample_run["failure_artifact_uri"].endswith(
            "failure_artifact_unavailable.json"
        )
        assert sample_run["failure_boundary"] == [
            "simulation_run_failed",
            "data_contract_incomplete",
        ]
        assert "failure_artifact_unavailable" in sample_run["evidence_notes"]
        assert not (sample_dir / "failure_artifact.json").exists()
        assert not (sample_dir / "failure_artifact_write_failed.json").exists()
        assert not (sample_dir / "failure_artifact_unavailable.json").exists()


def test_batch_pipeline_cli_prints_batch_result(tmp_path, monkeypatch, capsys):
    from weldcore.simulation_bakeoff import maniskill_batch_pipeline

    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._maniskill_backend_available",
        lambda: False,
    )

    maniskill_batch_pipeline.main(
        ["--outdir", str(tmp_path), "--batch-id", "batch-cli-test"]
    )

    printed = json.loads(capsys.readouterr().out)
    assert printed["batch_id"] == "batch-cli-test"
    assert printed["requested_sample_count"] == 20
    assert (tmp_path / "batch-cli-test" / "batch_result.json").exists()


def test_batch_pipeline_cli_accepts_sample_count_and_seed(
    tmp_path,
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._maniskill_backend_available",
        lambda: False,
    )

    from weldcore.simulation_bakeoff import maniskill_batch_pipeline

    maniskill_batch_pipeline.main(
        [
            "--outdir",
            str(tmp_path),
            "--batch-id",
            "batch-cli-custom",
            "--samples-per-task",
            "2",
            "--seed-start",
            "10",
        ]
    )

    printed = json.loads(capsys.readouterr().out)
    assert printed["requested_sample_count"] == 4
    assert [sample["seed"] for sample in printed["sample_runs"]] == [10, 11, 12, 13]


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
