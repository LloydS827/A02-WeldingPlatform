import json

from weldcore.simulation_bakeoff import (
    SimulationSampleRun,
    default_maniskill_batch_spec,
    iter_batch_sample_plans,
    run_maniskill_accumulation_pipeline,
    summarize_sample_runs,
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


def _completed_batch_payload(outdir, batch_id, *, samples_per_task, seed_start):
    spec = default_maniskill_batch_spec(
        batch_id=batch_id,
        output_root=str(outdir),
        samples_per_task=samples_per_task,
        seed_start=seed_start,
    )
    sample_runs = tuple(
        SimulationSampleRun(
            batch_id=plan.batch_id,
            sample_id=plan.sample_id,
            task_id=plan.task_id,
            route_id=plan.route_id,
            seed=plan.seed,
            variation_policy=plan.variation_policy,
            variation_descriptor=plan.variation_descriptor,
            status="completed",
            raw_artifact_uri=f"samples/{plan.sample_id}/raw_artifact.json",
            adapter_result_uri=f"samples/{plan.sample_id}/adapter_result.json",
            evidence_bundle_uri=f"samples/{plan.sample_id}/evidence_bundle.json",
            experience_dataset_uri=(
                f"samples/{plan.sample_id}/experience_dataset.json"
            ),
            failure_boundary=(),
            evidence_notes=plan.evidence_notes,
        )
        for plan in iter_batch_sample_plans(spec)
    )
    return summarize_sample_runs(
        batch_id=spec.batch_id,
        route_id=spec.route_id,
        task_count=len(spec.task_specs),
        requested_sample_count=len(sample_runs),
        sample_runs=sample_runs,
    ).to_dict()


def _fake_completed_runner(outdir, batch_id, *, samples_per_task, seed_start):
    payload = _completed_batch_payload(
        outdir,
        batch_id,
        samples_per_task=samples_per_task,
        seed_start=seed_start,
    )
    batch_dir = outdir / batch_id
    batch_dir.mkdir(parents=True, exist_ok=True)
    (batch_dir / "batch_result.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    return payload


def _assert_referenced_failure_batch(acc_dir, index, batch_id, requested_count):
    batch_result_uri = index["batch_result_uris"][batch_id]
    payload = json.loads((acc_dir / batch_result_uri).read_text(encoding="utf-8"))
    assert payload["batch_id"] == batch_id
    assert payload["requested_sample_count"] == requested_count
    assert payload["failed_sample_count"] == requested_count
    assert payload["failure_boundaries"] == ["data_contract_incomplete"]
    assert len(payload["sample_runs"]) == requested_count
    assert all(
        sample["failure_boundary"] == ["data_contract_incomplete"]
        for sample in payload["sample_runs"]
    )
    assert any(
        "failed_to_load_existing_batch_result" in sample["evidence_notes"]
        for sample in payload["sample_runs"]
    )
    assert any(
        "existing_result_error_type" in note
        for sample in payload["sample_runs"]
        for note in sample["evidence_notes"]
    )
    return payload


def _assert_index_failure_artifacts_exist(acc_dir, index):
    for item in index["index_items"]:
        failure_artifact_uri = item["failure_artifact_uri"]
        if failure_artifact_uri is None:
            continue
        artifact_path = (
            acc_dir / index["batch_root_uris"][item["batch_id"]] / failure_artifact_uri
        )
        assert artifact_path.exists()
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        assert artifact["failure_boundary"] == ["data_contract_incomplete"]
        assert "failed_to_load_existing_batch_result" in artifact["evidence_notes"]
        assert any(
            "existing_result_error_type" in note
            for note in artifact["evidence_notes"]
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


def test_accumulation_pipeline_cli_accepts_shards_and_force(
    tmp_path,
    monkeypatch,
    capsys,
):
    from weldcore.simulation_bakeoff import maniskill_accumulation_pipeline

    calls = {"count": 0}

    def counting_runner(outdir, batch_id, *, samples_per_task, seed_start):
        calls["count"] += 1
        return _fake_completed_runner(
            outdir,
            batch_id,
            samples_per_task=samples_per_task,
            seed_start=seed_start,
        )

    monkeypatch.setattr(
        maniskill_accumulation_pipeline,
        "run_maniskill_batch_pipeline",
        counting_runner,
    )

    maniskill_accumulation_pipeline.main(
        [
            "--outdir",
            str(tmp_path),
            "--accumulation-id",
            "acc-cli-shards",
            "--shards",
            "2",
            "--samples-per-task",
            "1",
            "--force",
        ]
    )

    printed = json.loads(capsys.readouterr().out)
    assert calls["count"] == 2
    assert printed["requested_sample_count"] == 4
    assert printed["completed_sample_count"] == 4
    assert printed["shard_count"] == 2
    assert {report["status"] for report in printed["shard_reports"]} == {
        "completed_new_run"
    }


def test_accumulation_pipeline_runs_phase_two_shards(tmp_path, monkeypatch):
    _mock_completed_backend(monkeypatch)

    result = run_maniskill_accumulation_pipeline(
        outdir=tmp_path,
        accumulation_id="acc-phase-2",
        shards=5,
        samples_per_task=50,
    )

    acc_dir = tmp_path / "acc-phase-2"
    assert result["requested_sample_count"] == 500
    assert result["completed_sample_count"] == 500
    assert result["status"] == "ready_to_scale_with_conditions"
    assert len(result["shard_reports"]) == 5
    assert result["shard_count"] == 5

    index = json.loads((acc_dir / "dataset_index.json").read_text(encoding="utf-8"))
    assert len(index["index_items"]) == 500
    assert len(index["batch_ids"]) == 5
    for batch_id in index["batch_ids"]:
        assert (acc_dir / "batches" / batch_id).exists()


def test_accumulation_pipeline_can_plan_next_batch_one_thousand_samples(
    tmp_path,
    monkeypatch,
):
    from weldcore.simulation_bakeoff import maniskill_accumulation_pipeline

    monkeypatch.setattr(
        maniskill_accumulation_pipeline,
        "run_maniskill_batch_pipeline",
        _fake_completed_runner,
    )

    result = run_maniskill_accumulation_pipeline(
        outdir=tmp_path,
        accumulation_id="acc-next-batch-1000",
        shards=10,
        samples_per_task=50,
    )

    acc_dir = tmp_path / "acc-next-batch-1000"
    assert result["requested_sample_count"] == 1000
    assert result["completed_sample_count"] == 1000
    assert result["status"] == "ready_to_scale_with_conditions"
    assert result["shard_count"] == 10
    assert len(result["shard_reports"]) == 10
    assert result["next_scale_recommendation"].startswith(
        "prepare_next_batch_1000_requested_samples"
    )

    index = json.loads((acc_dir / "dataset_index.json").read_text(encoding="utf-8"))
    assert len(index["index_items"]) == 1000
    assert len(index["batch_ids"]) == 10


def test_accumulation_pipeline_reuses_existing_shards(tmp_path, monkeypatch):
    from weldcore.simulation_bakeoff import maniskill_accumulation_pipeline

    monkeypatch.setattr(
        maniskill_accumulation_pipeline,
        "run_maniskill_batch_pipeline",
        _fake_completed_runner,
    )
    first = run_maniskill_accumulation_pipeline(
        outdir=tmp_path,
        accumulation_id="acc-reuse",
        shards=2,
        samples_per_task=1,
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError("runner should not be called when shards are reusable")

    monkeypatch.setattr(
        maniskill_accumulation_pipeline,
        "run_maniskill_batch_pipeline",
        fail_if_called,
    )
    second = run_maniskill_accumulation_pipeline(
        outdir=tmp_path,
        accumulation_id="acc-reuse",
        shards=2,
        samples_per_task=1,
    )

    assert first["requested_sample_count"] == 4
    assert second["status"] == "ready_to_scale_with_conditions"
    assert second["requested_sample_count"] == 4
    assert second["reused_shard_count"] == 2
    assert {report["status"] for report in second["shard_reports"]} == {
        "reused_existing_result"
    }


def test_accumulation_pipeline_force_reruns_existing_shards(tmp_path, monkeypatch):
    from weldcore.simulation_bakeoff import maniskill_accumulation_pipeline

    monkeypatch.setattr(
        maniskill_accumulation_pipeline,
        "run_maniskill_batch_pipeline",
        _fake_completed_runner,
    )
    run_maniskill_accumulation_pipeline(
        outdir=tmp_path,
        accumulation_id="acc-force",
        shards=1,
        samples_per_task=1,
    )

    calls = {"count": 0}

    def counting_runner(outdir, batch_id, *, samples_per_task, seed_start):
        calls["count"] += 1
        return _fake_completed_runner(
            outdir,
            batch_id,
            samples_per_task=samples_per_task,
            seed_start=seed_start,
        )

    monkeypatch.setattr(
        maniskill_accumulation_pipeline,
        "run_maniskill_batch_pipeline",
        counting_runner,
    )
    result = run_maniskill_accumulation_pipeline(
        outdir=tmp_path,
        accumulation_id="acc-force",
        shards=1,
        samples_per_task=1,
        force=True,
    )

    assert calls["count"] == 1
    assert result["completed_shard_count"] == 1
    assert result["shard_reports"][0]["status"] == "rerun_forced"


def test_accumulation_pipeline_reports_corrupt_existing_result_without_rerun(
    tmp_path,
    monkeypatch,
):
    from weldcore.simulation_bakeoff import maniskill_accumulation_pipeline

    acc_dir = tmp_path / "acc-corrupt"
    batch_id = "maniskill-sapien-accumulation-acc-corrupt"
    batch_dir = acc_dir / "batches" / batch_id
    batch_dir.mkdir(parents=True)
    (batch_dir / "batch_result.json").write_text("{not-json", encoding="utf-8")

    def fail_if_called(*args, **kwargs):
        raise AssertionError("runner should not be called for corrupt existing result")

    monkeypatch.setattr(
        maniskill_accumulation_pipeline,
        "run_maniskill_batch_pipeline",
        fail_if_called,
    )
    result = run_maniskill_accumulation_pipeline(
        outdir=tmp_path,
        accumulation_id="acc-corrupt",
        samples_per_task=50,
    )

    assert result["status"] not in {
        "ready_to_scale_with_conditions",
        "locked_for_next_batch_with_conditions",
    }
    assert result["failed_shard_count"] == 1
    assert result["dominant_failure_boundaries"] == ["data_contract_incomplete"]
    assert result["failure_boundary_counts"] == {"data_contract_incomplete": 100}
    assert result["shard_reports"][0]["status"] == "failed_to_load_existing_result"
    assert result["shard_reports"][0]["failure_boundaries"] == [
        "data_contract_incomplete"
    ]

    index = json.loads((acc_dir / "dataset_index.json").read_text(encoding="utf-8"))
    failure_payload = _assert_referenced_failure_batch(
        acc_dir,
        index,
        batch_id,
        100,
    )
    assert failure_payload["batch_id"] == result["shard_reports"][0]["batch_id"]
    _assert_index_failure_artifacts_exist(acc_dir, index)


def test_accumulation_pipeline_reports_mismatched_existing_result_without_rerun(
    tmp_path,
    monkeypatch,
):
    from weldcore.simulation_bakeoff import maniskill_accumulation_pipeline

    acc_dir = tmp_path / "acc-mismatch"
    batches_dir = acc_dir / "batches"
    shard_000_batch_id = "maniskill-sapien-accumulation-acc-mismatch-shard-000"
    shard_001_batch_id = "maniskill-sapien-accumulation-acc-mismatch-shard-001"
    wrong_payload = _completed_batch_payload(
        batches_dir,
        "wrong-batch-id",
        samples_per_task=1,
        seed_start=0,
    )
    valid_payload = _completed_batch_payload(
        batches_dir,
        shard_001_batch_id,
        samples_per_task=1,
        seed_start=2,
    )
    for batch_id, payload in (
        (shard_000_batch_id, wrong_payload),
        (shard_001_batch_id, valid_payload),
    ):
        batch_dir = batches_dir / batch_id
        batch_dir.mkdir(parents=True, exist_ok=True)
        (batch_dir / "batch_result.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

    def fail_if_called(*args, **kwargs):
        raise AssertionError("runner should not be called for mismatched result")

    monkeypatch.setattr(
        maniskill_accumulation_pipeline,
        "run_maniskill_batch_pipeline",
        fail_if_called,
    )
    result = run_maniskill_accumulation_pipeline(
        outdir=tmp_path,
        accumulation_id="acc-mismatch",
        shards=2,
        samples_per_task=1,
    )

    reports_by_batch_id = {
        report["batch_id"]: report for report in result["shard_reports"]
    }
    assert result["status"] not in {
        "ready_to_scale_with_conditions",
        "locked_for_next_batch_with_conditions",
    }
    assert result["failed_shard_count"] == 1
    assert result["reused_shard_count"] == 1
    assert result["failure_boundary_counts"] == {"data_contract_incomplete": 2}
    assert reports_by_batch_id[shard_000_batch_id]["status"] == (
        "failed_to_load_existing_result"
    )
    assert reports_by_batch_id[shard_000_batch_id]["failure_boundaries"] == [
        "data_contract_incomplete"
    ]
    assert reports_by_batch_id[shard_001_batch_id]["status"] == (
        "reused_existing_result"
    )

    index = json.loads((acc_dir / "dataset_index.json").read_text(encoding="utf-8"))
    failure_payload = _assert_referenced_failure_batch(
        acc_dir,
        index,
        shard_000_batch_id,
        2,
    )
    assert failure_payload["batch_id"] == reports_by_batch_id[shard_000_batch_id][
        "batch_id"
    ]
    _assert_index_failure_artifacts_exist(acc_dir, index)
