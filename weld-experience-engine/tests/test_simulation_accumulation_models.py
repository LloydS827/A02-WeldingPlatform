import dataclasses

import pytest

from weldcore.simulation_bakeoff import (
    DEFAULT_ACCUMULATION_SCALE_PLAN,
    DEFAULT_ACCUMULATION_STAGE_BOUNDARY,
    SimulationAccumulationBatchSpec,
    SimulationAccumulationShardSpec,
    SimulationSampleRun,
    build_simulation_accumulation_shard_report,
    build_simulation_accumulation_report,
    build_simulation_dataset_index,
    default_maniskill_accumulation_spec,
    default_maniskill_sharded_accumulation_spec,
    determine_accumulation_status,
    iter_accumulation_shard_specs,
    summarize_sample_runs,
    validate_batch_result_matches_shard,
)


def test_default_accumulation_spec_requests_one_hundred_samples():
    spec = default_maniskill_accumulation_spec(
        accumulation_id="acc-test",
        output_root="artifacts/simulation/maniskill-sapien-accumulations",
    )

    assert isinstance(spec, SimulationAccumulationBatchSpec)
    assert spec.route_id == "maniskill_sapien"
    assert spec.samples_per_task == 50
    assert len(spec.task_specs) == 2
    assert spec.target_requested_sample_count == 100
    assert spec.scale_phase == "phase_1_accumulation_start"
    assert spec.resume_policy == "reuse_existing_batch_result_unless_force"
    assert spec.stage_boundary == "simulation_accumulation_not_real_welding_quality"
    assert spec.batch_id_prefix == "maniskill-sapien-accumulation"


def test_default_phase_two_sharded_accumulation_spec_requests_five_hundred_samples():
    spec = default_maniskill_sharded_accumulation_spec(
        accumulation_id="acc-phase-2",
        output_root="artifacts/simulation/maniskill-sapien-accumulations",
    )

    assert spec.shard_count == 5
    assert spec.samples_per_task == 50
    assert len(spec.task_specs) == 2
    assert spec.target_requested_sample_count == 500
    assert spec.scale_phase == "phase_2_scale_sharded_accumulation"
    assert spec.resume_policy == "reuse_existing_batch_result_unless_force"


def test_accumulation_shard_specs_have_contiguous_seed_ranges():
    spec = default_maniskill_sharded_accumulation_spec(
        accumulation_id="acc-phase-2",
        seed_start=10,
    )

    shards = tuple(iter_accumulation_shard_specs(spec))

    assert all(isinstance(shard, SimulationAccumulationShardSpec) for shard in shards)
    assert [shard.seed_start for shard in shards] == [10, 110, 210, 310, 410]
    assert [shard.requested_sample_count for shard in shards] == [100] * 5
    assert shards[0].batch_id == "maniskill-sapien-accumulation-acc-phase-2-shard-000"
    assert shards[0].batch_root_uri == (
        "batches/maniskill-sapien-accumulation-acc-phase-2-shard-000"
    )


def test_accumulation_constants_are_public_api():
    assert (
        DEFAULT_ACCUMULATION_STAGE_BOUNDARY
        == "simulation_accumulation_not_real_welding_quality"
    )
    assert (
        DEFAULT_ACCUMULATION_SCALE_PLAN
        == "phase_1_100_requested_samples_then_phase_2_500_requested_samples"
    )


def test_accumulation_spec_rejects_mismatched_requested_count():
    with pytest.raises(ValueError, match="len\\(task_specs\\) \\* samples_per_task"):
        default_maniskill_accumulation_spec(
            samples_per_task=50,
            target_requested_sample_count=99,
        )


def test_accumulation_spec_rejects_zero_samples_per_task():
    with pytest.raises(ValueError, match="samples_per_task must be positive"):
        default_maniskill_accumulation_spec(samples_per_task=0)


def test_accumulation_spec_rejects_empty_task_specs():
    with pytest.raises(ValueError, match="task_specs must not be empty"):
        default_maniskill_accumulation_spec(task_specs=())


@pytest.mark.parametrize(
    (
        "requested",
        "completed",
        "failed",
        "skipped",
        "failure_boundaries",
        "expected",
    ),
    [
        (100, 0, 100, 0, ("environment_missing",), "blocked_by_environment"),
        (100, 0, 100, 0, ("simulation_run_failed",), "blocked_by_pipeline_failure"),
        (100, 80, 20, 0, ("simulation_run_failed",), "accumulating_with_failures"),
        (100, 100, 0, 0, (), "ready_to_scale_with_conditions"),
        (100, 80, 0, 0, (), "accumulating_completed_samples"),
    ],
)
def test_determine_accumulation_status_priority(
    requested,
    completed,
    failed,
    skipped,
    failure_boundaries,
    expected,
):
    assert (
        determine_accumulation_status(
            requested_sample_count=requested,
            completed_sample_count=completed,
            failed_sample_count=failed,
            skipped_sample_count=skipped,
            failure_boundaries=failure_boundaries,
        )
        == expected
    )


def test_determine_accumulation_status_rejects_zero_requested_samples():
    with pytest.raises(ValueError, match="requested_sample_count must be positive"):
        determine_accumulation_status(
            requested_sample_count=0,
            completed_sample_count=0,
            failed_sample_count=0,
            skipped_sample_count=0,
            failure_boundaries=(),
        )


def _sample_run(sample_id, status, *, failure_boundary=(), failure_artifact_uri=None):
    return SimulationSampleRun(
        batch_id="batch-a",
        sample_id=sample_id,
        task_id="task-a",
        route_id="maniskill_sapien",
        seed=1,
        variation_policy="deterministic_micro_offset",
        variation_descriptor={"policy": "deterministic_micro_offset", "seed": 1},
        status=status,
        raw_artifact_uri=f"samples/{sample_id}/raw_artifact.json",
        adapter_result_uri=(
            f"samples/{sample_id}/adapter_result.json"
            if status == "completed"
            else None
        ),
        evidence_bundle_uri=(
            f"samples/{sample_id}/evidence_bundle.json"
            if status == "completed"
            else None
        ),
        experience_dataset_uri=(
            f"samples/{sample_id}/experience_dataset.json"
            if status == "completed"
            else None
        ),
        failure_boundary=failure_boundary,
        evidence_notes=("simulation_only_not_real_welding_quality",),
        failure_artifact_uri=failure_artifact_uri,
    )


def _shard_sample_run(
    batch_id,
    sample_id,
    status,
    seed,
    *,
    failure_boundary=(),
):
    return dataclasses.replace(
        _sample_run(sample_id, status, failure_boundary=failure_boundary),
        batch_id=batch_id,
        seed=seed,
        variation_descriptor={
            "policy": "deterministic_micro_offset",
            "seed": seed,
        },
    )


def _expected_shard_sample_id(batch_id, route_id, task_id, seed):
    return f"sample-{batch_id}-{route_id}-{task_id}-{seed}"


def _shard_batch_result(shard_spec, sample_runs, *, route_id="maniskill_sapien"):
    return summarize_sample_runs(
        batch_id=shard_spec.batch_id,
        route_id=route_id,
        task_count=2,
        requested_sample_count=shard_spec.requested_sample_count,
        sample_runs=tuple(sample_runs),
    )


def _index_from_batch_results(batch_results):
    return build_simulation_dataset_index(
        accumulation_id="acc-phase-2",
        batch_results=tuple(batch_results),
        batch_root_uris={
            result.batch_id: f"batches/{result.batch_id}"
            for result in batch_results
        },
        batch_result_uris={
            result.batch_id: f"batches/{result.batch_id}/batch_result.json"
            for result in batch_results
        },
    )


def test_validate_batch_result_matches_shard_accepts_matching_result():
    shard = SimulationAccumulationShardSpec(
        shard_id="shard-000",
        batch_id="batch-a",
        samples_per_task=1,
        requested_sample_count=2,
        seed_start=10,
        batch_root_uri="batches/batch-a",
        batch_result_uri="batches/batch-a/batch_result.json",
        reuse_policy="reuse_existing_batch_result_unless_force",
    )
    batch_result = _shard_batch_result(
        shard,
        (
            _shard_sample_run(
                "batch-a",
                _expected_shard_sample_id(
                    "batch-a", "maniskill_sapien", "task-a", 10
                ),
                "completed",
                10,
            ),
            _shard_sample_run(
                "batch-a",
                _expected_shard_sample_id(
                    "batch-a", "maniskill_sapien", "task-a", 11
                ),
                "completed",
                11,
            ),
        ),
    )

    validate_batch_result_matches_shard(
        batch_result=batch_result,
        shard_spec=shard,
        route_id="maniskill_sapien",
        task_count=2,
    )


def test_validate_batch_result_matches_shard_rejects_stale_summary_fields():
    shard = SimulationAccumulationShardSpec(
        shard_id="shard-000",
        batch_id="batch-a",
        samples_per_task=1,
        requested_sample_count=2,
        seed_start=10,
        batch_root_uri="batches/batch-a",
        batch_result_uri="batches/batch-a/batch_result.json",
        reuse_policy="reuse_existing_batch_result_unless_force",
    )
    batch_result = _shard_batch_result(
        shard,
        (
            _shard_sample_run(
                "batch-a",
                _expected_shard_sample_id(
                    "batch-a", "maniskill_sapien", "task-a", 10
                ),
                "completed",
                10,
            ),
            _shard_sample_run(
                "batch-a",
                _expected_shard_sample_id(
                    "batch-a", "maniskill_sapien", "task-a", 11
                ),
                "failed",
                11,
                failure_boundary=("data_contract_incomplete",),
            ),
        ),
    )
    stale_batch_result = dataclasses.replace(
        batch_result,
        completed_sample_count=2,
        failed_sample_count=0,
        failure_boundaries=(),
    )

    with pytest.raises(ValueError, match="summary fields do not match sample_runs"):
        validate_batch_result_matches_shard(
            batch_result=stale_batch_result,
            shard_spec=shard,
            route_id="maniskill_sapien",
            task_count=2,
        )


def test_validate_batch_result_matches_shard_rejects_mismatched_batch_id():
    shard = SimulationAccumulationShardSpec(
        shard_id="shard-000",
        batch_id="batch-a",
        samples_per_task=1,
        requested_sample_count=1,
        seed_start=10,
        batch_root_uri="batches/batch-a",
        batch_result_uri="batches/batch-a/batch_result.json",
        reuse_policy="reuse_existing_batch_result_unless_force",
    )
    batch_result = summarize_sample_runs(
        batch_id="batch-b",
        route_id="maniskill_sapien",
        task_count=2,
        requested_sample_count=1,
        sample_runs=(
            _shard_sample_run("batch-b", "sample-10", "completed", 10),
        ),
    )

    with pytest.raises(ValueError, match="batch_id does not match shard"):
        validate_batch_result_matches_shard(
            batch_result=batch_result,
            shard_spec=shard,
            route_id="maniskill_sapien",
            task_count=2,
        )


def test_validate_batch_result_matches_shard_rejects_mismatched_route_id():
    shard = SimulationAccumulationShardSpec(
        shard_id="shard-000",
        batch_id="batch-a",
        samples_per_task=1,
        requested_sample_count=1,
        seed_start=10,
        batch_root_uri="batches/batch-a",
        batch_result_uri="batches/batch-a/batch_result.json",
        reuse_policy="reuse_existing_batch_result_unless_force",
    )
    batch_result = _shard_batch_result(
        shard,
        (
            _shard_sample_run(
                "batch-a",
                _expected_shard_sample_id(
                    "batch-a", "maniskill_sapien", "task-a", 10
                ),
                "completed",
                10,
            ),
        ),
        route_id="simlite_reference",
    )

    with pytest.raises(ValueError, match="route_id does not match shard"):
        validate_batch_result_matches_shard(
            batch_result=batch_result,
            shard_spec=shard,
            route_id="maniskill_sapien",
            task_count=2,
        )


def test_validate_batch_result_matches_shard_rejects_requested_count_mismatch():
    shard = SimulationAccumulationShardSpec(
        shard_id="shard-000",
        batch_id="batch-a",
        samples_per_task=1,
        requested_sample_count=2,
        seed_start=10,
        batch_root_uri="batches/batch-a",
        batch_result_uri="batches/batch-a/batch_result.json",
        reuse_policy="reuse_existing_batch_result_unless_force",
    )
    batch_result = summarize_sample_runs(
        batch_id="batch-a",
        route_id="maniskill_sapien",
        task_count=2,
        requested_sample_count=1,
        sample_runs=(
            _shard_sample_run(
                "batch-a",
                _expected_shard_sample_id(
                    "batch-a", "maniskill_sapien", "task-a", 10
                ),
                "completed",
                10,
            ),
            _shard_sample_run(
                "batch-a",
                _expected_shard_sample_id(
                    "batch-a", "maniskill_sapien", "task-a", 11
                ),
                "completed",
                11,
            ),
        ),
    )

    with pytest.raises(ValueError, match="requested_sample_count does not match shard"):
        validate_batch_result_matches_shard(
            batch_result=batch_result,
            shard_spec=shard,
            route_id="maniskill_sapien",
            task_count=2,
        )


def test_validate_batch_result_matches_shard_rejects_task_count_mismatch():
    shard = SimulationAccumulationShardSpec(
        shard_id="shard-000",
        batch_id="batch-a",
        samples_per_task=1,
        requested_sample_count=1,
        seed_start=10,
        batch_root_uri="batches/batch-a",
        batch_result_uri="batches/batch-a/batch_result.json",
        reuse_policy="reuse_existing_batch_result_unless_force",
    )
    batch_result = _shard_batch_result(
        shard,
        (
            _shard_sample_run(
                "batch-a",
                _expected_shard_sample_id(
                    "batch-a", "maniskill_sapien", "task-a", 10
                ),
                "completed",
                10,
            ),
        ),
    )

    with pytest.raises(ValueError, match="task_count does not match shard"):
        validate_batch_result_matches_shard(
            batch_result=batch_result,
            shard_spec=shard,
            route_id="maniskill_sapien",
            task_count=3,
        )


def test_validate_batch_result_matches_shard_rejects_sample_runs_length_mismatch():
    shard = SimulationAccumulationShardSpec(
        shard_id="shard-000",
        batch_id="batch-a",
        samples_per_task=1,
        requested_sample_count=2,
        seed_start=10,
        batch_root_uri="batches/batch-a",
        batch_result_uri="batches/batch-a/batch_result.json",
        reuse_policy="reuse_existing_batch_result_unless_force",
    )
    batch_result = summarize_sample_runs(
        batch_id="batch-a",
        route_id="maniskill_sapien",
        task_count=2,
        requested_sample_count=2,
        sample_runs=(
            _shard_sample_run(
                "batch-a",
                _expected_shard_sample_id(
                    "batch-a", "maniskill_sapien", "task-a", 10
                ),
                "completed",
                10,
            ),
        ),
    )

    with pytest.raises(ValueError, match="sample_runs do not match shard"):
        validate_batch_result_matches_shard(
            batch_result=batch_result,
            shard_spec=shard,
            route_id="maniskill_sapien",
            task_count=2,
        )


def test_validate_batch_result_matches_shard_rejects_mismatched_seed_set():
    shard = SimulationAccumulationShardSpec(
        shard_id="shard-000",
        batch_id="batch-a",
        samples_per_task=1,
        requested_sample_count=2,
        seed_start=10,
        batch_root_uri="batches/batch-a",
        batch_result_uri="batches/batch-a/batch_result.json",
        reuse_policy="reuse_existing_batch_result_unless_force",
    )
    batch_result = _shard_batch_result(
        shard,
        (
            _shard_sample_run("batch-a", "sample-10", "completed", 10),
            _shard_sample_run("batch-a", "sample-12", "completed", 12),
        ),
    )

    with pytest.raises(ValueError, match="seed range does not match shard"):
        validate_batch_result_matches_shard(
            batch_result=batch_result,
            shard_spec=shard,
            route_id="maniskill_sapien",
            task_count=2,
        )


def test_validate_batch_result_matches_shard_rejects_mismatched_sample_id():
    shard = SimulationAccumulationShardSpec(
        shard_id="shard-000",
        batch_id="batch-a",
        samples_per_task=1,
        requested_sample_count=2,
        seed_start=10,
        batch_root_uri="batches/batch-a",
        batch_result_uri="batches/batch-a/batch_result.json",
        reuse_policy="reuse_existing_batch_result_unless_force",
    )
    batch_result = _shard_batch_result(
        shard,
        (
            _shard_sample_run(
                "batch-a",
                _expected_shard_sample_id(
                    "batch-a", "maniskill_sapien", "task-a", 10
                ),
                "completed",
                10,
            ),
            _shard_sample_run("batch-a", "arbitrary-sample-id", "completed", 11),
        ),
    )

    with pytest.raises(ValueError, match="sample_id does not match shard"):
        validate_batch_result_matches_shard(
            batch_result=batch_result,
            shard_spec=shard,
            route_id="maniskill_sapien",
            task_count=2,
        )


def test_validate_batch_result_matches_shard_rejects_duplicate_sample_ids():
    shard = SimulationAccumulationShardSpec(
        shard_id="shard-000",
        batch_id="batch-a",
        samples_per_task=1,
        requested_sample_count=2,
        seed_start=10,
        batch_root_uri="batches/batch-a",
        batch_result_uri="batches/batch-a/batch_result.json",
        reuse_policy="reuse_existing_batch_result_unless_force",
    )
    duplicate_id = _expected_shard_sample_id(
        "batch-a", "maniskill_sapien", "task-a", 10
    )
    batch_result = _shard_batch_result(
        shard,
        (
            _shard_sample_run("batch-a", duplicate_id, "completed", 10),
            _shard_sample_run("batch-a", duplicate_id, "completed", 11),
        ),
    )

    with pytest.raises(ValueError, match="sample_ids must be unique"):
        validate_batch_result_matches_shard(
            batch_result=batch_result,
            shard_spec=shard,
            route_id="maniskill_sapien",
            task_count=2,
        )


def test_accumulation_report_exposes_shard_summary_fields():
    spec = default_maniskill_sharded_accumulation_spec(
        accumulation_id="acc-phase-2",
        samples_per_task=1,
        shard_count=3,
    )
    shards = iter_accumulation_shard_specs(spec)
    batch_results = tuple(
        _shard_batch_result(
            shard,
            (
                _shard_sample_run(
                    shard.batch_id,
                    f"{shard.shard_id}-completed",
                    "completed",
                    shard.seed_start,
                ),
                _shard_sample_run(
                    shard.batch_id,
                    f"{shard.shard_id}-failed",
                    "failed",
                    shard.seed_start + 1,
                    failure_boundary=("simulation_run_failed",),
                ),
            ),
        )
        for shard in shards
    )
    shard_reports = (
        build_simulation_accumulation_shard_report(
            shard_spec=shards[0],
            batch_result=batch_results[0],
            status="completed_new_run",
        ),
        build_simulation_accumulation_shard_report(
            shard_spec=shards[1],
            batch_result=batch_results[1],
            status="reused_existing_result",
        ),
        build_simulation_accumulation_shard_report(
            shard_spec=shards[2],
            batch_result=batch_results[2],
            status="failed_to_load_existing_result",
        ),
    )
    index = _index_from_batch_results(batch_results)

    report = build_simulation_accumulation_report(
        dataset_index=index,
        dataset_index_uri="dataset_index.json",
        shard_reports=shard_reports,
    )

    assert report.shard_count == 3
    assert report.completed_shard_count == 1
    assert report.reused_shard_count == 1
    assert report.failed_shard_count == 1
    assert report.shard_result_uris == tuple(shard.batch_result_uri for shard in shards)
    assert report.failure_boundary_counts == {"simulation_run_failed": 3}
    assert report.field_coverage_trend == {
        "shard-000": {
            "raw_artifact_uri": 1.0,
            "adapter_result_uri": 1.0,
            "experience_dataset_uri": 1.0,
            "evidence_bundle_uri": 1.0,
            "failure_artifact_uri": 0.0,
        },
        "shard-001": {
            "raw_artifact_uri": 1.0,
            "adapter_result_uri": 1.0,
            "experience_dataset_uri": 1.0,
            "evidence_bundle_uri": 1.0,
            "failure_artifact_uri": 0.0,
        },
        "shard-002": {
            "raw_artifact_uri": 1.0,
            "adapter_result_uri": 1.0,
            "experience_dataset_uri": 1.0,
            "evidence_bundle_uri": 1.0,
            "failure_artifact_uri": 0.0,
        },
    }


def test_accumulation_report_rejects_mismatched_shard_report_batch_ids():
    spec = default_maniskill_sharded_accumulation_spec(
        accumulation_id="acc-phase-2",
        samples_per_task=1,
        shard_count=2,
    )
    shards = iter_accumulation_shard_specs(spec)
    batch_results = tuple(
        _shard_batch_result(
            shard,
            (
                _shard_sample_run(
                    shard.batch_id,
                    f"{shard.shard_id}-completed",
                    "completed",
                    shard.seed_start,
                ),
                _shard_sample_run(
                    shard.batch_id,
                    f"{shard.shard_id}-failed",
                    "failed",
                    shard.seed_start + 1,
                    failure_boundary=("simulation_run_failed",),
                ),
            ),
        )
        for shard in shards
    )
    index = _index_from_batch_results(batch_results)
    mismatched_shard_report = build_simulation_accumulation_shard_report(
        shard_spec=dataclasses.replace(shards[0], batch_id="unexpected-batch"),
        batch_result=dataclasses.replace(batch_results[0], batch_id="unexpected-batch"),
        status="completed_new_run",
    )

    with pytest.raises(ValueError, match="shard_reports must match dataset batch_ids"):
        build_simulation_accumulation_report(
            dataset_index=index,
            dataset_index_uri="dataset_index.json",
            shard_reports=(mismatched_shard_report,),
        )


def test_phase_two_perfect_run_is_ready_to_scale_with_conditions():
    spec = default_maniskill_sharded_accumulation_spec()
    shard = iter_accumulation_shard_specs(spec)[0]
    shard = dataclasses.replace(shard, requested_sample_count=500)
    batch_result = _shard_batch_result(
        shard,
        (
            _shard_sample_run(
                shard.batch_id,
                f"sample-{seed}",
                "completed",
                seed,
            )
            for seed in range(500)
        ),
    )
    index = _index_from_batch_results((batch_result,))

    report = build_simulation_accumulation_report(
        dataset_index=index,
        dataset_index_uri="dataset_index.json",
    )

    assert report.status == "ready_to_scale_with_conditions"


def test_phase_two_run_with_only_simulation_failures_locks_next_batch():
    spec = default_maniskill_sharded_accumulation_spec()
    shard = iter_accumulation_shard_specs(spec)[0]
    shard = dataclasses.replace(shard, requested_sample_count=500)
    batch_result = _shard_batch_result(
        shard,
        tuple(
            _shard_sample_run(
                shard.batch_id,
                f"sample-{seed}",
                "completed",
                seed,
            )
            for seed in range(480)
        )
        + tuple(
            _shard_sample_run(
                shard.batch_id,
                f"sample-{seed}",
                "failed",
                seed,
                failure_boundary=("simulation_run_failed",),
            )
            for seed in range(480, 500)
        ),
    )
    index = _index_from_batch_results((batch_result,))

    report = build_simulation_accumulation_report(
        dataset_index=index,
        dataset_index_uri="dataset_index.json",
    )

    assert report.status == "locked_for_next_batch_with_conditions"


def test_phase_two_failed_sample_without_boundary_keeps_accumulating_failures():
    spec = default_maniskill_sharded_accumulation_spec()
    shard = iter_accumulation_shard_specs(spec)[0]
    shard = dataclasses.replace(shard, requested_sample_count=500)
    batch_result = _shard_batch_result(
        shard,
        tuple(
            _shard_sample_run(
                shard.batch_id,
                f"sample-{seed}",
                "completed",
                seed,
            )
            for seed in range(499)
        )
        + (
            _shard_sample_run(
                shard.batch_id,
                "sample-499",
                "failed",
                499,
                failure_boundary=(),
            ),
        ),
    )
    index = _index_from_batch_results((batch_result,))

    report = build_simulation_accumulation_report(
        dataset_index=index,
        dataset_index_uri="dataset_index.json",
    )

    assert report.status == "accumulating_with_failures"


def test_phase_two_adapter_conversion_failure_keeps_accumulating_failures():
    spec = default_maniskill_sharded_accumulation_spec()
    shard = iter_accumulation_shard_specs(spec)[0]
    shard = dataclasses.replace(shard, requested_sample_count=500)
    batch_result = _shard_batch_result(
        shard,
        tuple(
            _shard_sample_run(
                shard.batch_id,
                f"sample-{seed}",
                "completed",
                seed,
            )
            for seed in range(499)
        )
        + (
            _shard_sample_run(
                shard.batch_id,
                "sample-499",
                "failed",
                499,
                failure_boundary=("adapter_conversion_failed",),
            ),
        ),
    )
    index = _index_from_batch_results((batch_result,))

    report = build_simulation_accumulation_report(
        dataset_index=index,
        dataset_index_uri="dataset_index.json",
    )

    assert report.status == "accumulating_with_failures"


def test_phase_two_skipped_sample_keeps_accumulating_failures():
    spec = default_maniskill_sharded_accumulation_spec()
    shard = iter_accumulation_shard_specs(spec)[0]
    shard = dataclasses.replace(shard, requested_sample_count=500)
    batch_result = _shard_batch_result(
        shard,
        tuple(
            _shard_sample_run(
                shard.batch_id,
                f"sample-{seed}",
                "completed",
                seed,
            )
            for seed in range(479)
        )
        + tuple(
            _shard_sample_run(
                shard.batch_id,
                f"sample-{seed}",
                "failed",
                seed,
                failure_boundary=("simulation_run_failed",),
            )
            for seed in range(479, 499)
        )
        + (
            _shard_sample_run(
                shard.batch_id,
                "sample-499",
                "skipped",
                499,
            ),
        ),
    )
    index = _index_from_batch_results((batch_result,))

    report = build_simulation_accumulation_report(
        dataset_index=index,
        dataset_index_uri="dataset_index.json",
    )

    assert report.status == "accumulating_with_failures"


@pytest.mark.parametrize(
    "failure_boundary",
    [
        "data_contract_incomplete",
        "experience_dataset_export_failed",
    ],
)
def test_phase_two_contract_failures_keep_accumulating_failures(failure_boundary):
    spec = default_maniskill_sharded_accumulation_spec()
    shard = iter_accumulation_shard_specs(spec)[0]
    shard = dataclasses.replace(shard, requested_sample_count=500)
    batch_result = _shard_batch_result(
        shard,
        tuple(
            _shard_sample_run(
                shard.batch_id,
                f"sample-{seed}",
                "completed",
                seed,
            )
            for seed in range(499)
        )
        + (
            _shard_sample_run(
                shard.batch_id,
                "sample-499",
                "failed",
                499,
                failure_boundary=(failure_boundary,),
            ),
        ),
    )
    index = _index_from_batch_results((batch_result,))

    report = build_simulation_accumulation_report(
        dataset_index=index,
        dataset_index_uri="dataset_index.json",
    )

    assert report.status == "accumulating_with_failures"


def test_phase_two_missing_completed_coverage_key_does_not_lock():
    spec = default_maniskill_sharded_accumulation_spec()
    shard = iter_accumulation_shard_specs(spec)[0]
    shard = dataclasses.replace(shard, requested_sample_count=500)
    batch_result = _shard_batch_result(
        shard,
        tuple(
            _shard_sample_run(
                shard.batch_id,
                f"sample-{seed}",
                "completed",
                seed,
            )
            for seed in range(499)
        )
        + (
            _shard_sample_run(
                shard.batch_id,
                "sample-499",
                "failed",
                499,
                failure_boundary=("simulation_run_failed",),
            ),
        ),
    )
    index = _index_from_batch_results((batch_result,))
    sparse_coverage = dataclasses.replace(
        index.field_coverage_summary,
        completed_sample_coverage={
            "adapter_result_uri": 1.0,
            "evidence_bundle_uri": 1.0,
        },
    )
    index = dataclasses.replace(index, field_coverage_summary=sparse_coverage)

    report = build_simulation_accumulation_report(
        dataset_index=index,
        dataset_index_uri="dataset_index.json",
    )

    assert report.status == "accumulating_with_failures"


def test_dataset_index_preserves_completed_and_failed_samples():
    batch_result = summarize_sample_runs(
        batch_id="batch-a",
        route_id="maniskill_sapien",
        task_count=1,
        requested_sample_count=2,
        sample_runs=(
            _sample_run("sample-ok", "completed"),
            _sample_run(
                "sample-failed",
                "failed",
                failure_boundary=("simulation_run_failed",),
            ),
        ),
    )

    index = build_simulation_dataset_index(
        accumulation_id="acc-a",
        batch_results=(batch_result,),
        batch_root_uris={"batch-a": "batches/batch-a"},
        batch_result_uris={"batch-a": "batches/batch-a/batch_result.json"},
    )

    assert index.accumulation_id == "acc-a"
    assert index.requested_sample_count == 2
    assert index.completed_sample_count == 1
    assert index.failed_sample_count == 1
    assert index.failure_boundaries == ("simulation_run_failed",)
    assert index.batch_root_uris == {"batch-a": "batches/batch-a"}
    assert (
        index.index_items[0].raw_artifact_uri
        == "samples/sample-ok/raw_artifact.json"
    )
    assert index.index_items[0].experience_dataset_uri.endswith(
        "experience_dataset.json"
    )
    failed_item = index.index_items[1]
    assert failed_item.failure_boundary == ("simulation_run_failed",)
    assert failed_item.raw_artifact_uri == "samples/sample-failed/raw_artifact.json"
    assert failed_item.failure_artifact_uri == (
        "samples/sample-failed/failure_artifact.json"
    )
    assert (
        index.field_coverage_summary.requested_sample_coverage[
            "experience_dataset_uri"
        ]
        == 0.5
    )
    assert index.field_coverage_summary.requested_sample_coverage[
        "raw_artifact_uri"
    ] == 1.0
    assert index.field_coverage_summary.requested_sample_coverage[
        "failure_artifact_uri"
    ] == 0.5
    assert (
        index.field_coverage_summary.completed_sample_coverage[
            "experience_dataset_uri"
        ]
        == 1.0
    )


def test_dataset_index_rejects_absolute_item_uris():
    batch_result = summarize_sample_runs(
        batch_id="batch-a",
        route_id="maniskill_sapien",
        task_count=1,
        requested_sample_count=1,
        sample_runs=(
            dataclasses.replace(
                _sample_run("sample-abs", "failed", failure_boundary=("x",)),
                raw_artifact_uri="/tmp/raw_artifact.json",
            ),
        ),
    )

    with pytest.raises(ValueError, match="relative batch root"):
        build_simulation_dataset_index(
            accumulation_id="acc-a",
            batch_results=(batch_result,),
            batch_root_uris={"batch-a": "batches/batch-a"},
            batch_result_uris={"batch-a": "batches/batch-a/batch_result.json"},
        )


def test_dataset_index_keeps_existing_failure_artifact_uri():
    batch_result = summarize_sample_runs(
        batch_id="batch-a",
        route_id="maniskill_sapien",
        task_count=1,
        requested_sample_count=1,
        sample_runs=(
            dataclasses.replace(
                _sample_run("sample-failed", "failed", failure_boundary=("x",)),
                raw_artifact_uri=(
                    "samples/sample-failed/failure_artifact_write_failed.json"
                ),
            ),
        ),
    )

    index = build_simulation_dataset_index(
        accumulation_id="acc-a",
        batch_results=(batch_result,),
        batch_root_uris={"batch-a": "batches/batch-a"},
        batch_result_uris={"batch-a": "batches/batch-a/batch_result.json"},
    )

    assert index.index_items[0].failure_artifact_uri == (
        "samples/sample-failed/failure_artifact_write_failed.json"
    )
    assert index.field_coverage_summary.requested_sample_coverage[
        "raw_artifact_uri"
    ] == 0.0


def test_dataset_index_prefers_recorded_failure_artifact_uri():
    batch_result = summarize_sample_runs(
        batch_id="batch-a",
        route_id="maniskill_sapien",
        task_count=1,
        requested_sample_count=1,
        sample_runs=(
            _sample_run(
                "sample-failed",
                "failed",
                failure_boundary=("simulation_run_failed",),
                failure_artifact_uri=(
                    "samples/sample-failed/failure_artifact_write_failed.json"
                ),
            ),
        ),
    )

    index = build_simulation_dataset_index(
        accumulation_id="acc-a",
        batch_results=(batch_result,),
        batch_root_uris={"batch-a": "batches/batch-a"},
        batch_result_uris={"batch-a": "batches/batch-a/batch_result.json"},
    )

    assert index.index_items[0].raw_artifact_uri == (
        "samples/sample-failed/raw_artifact.json"
    )
    assert index.index_items[0].failure_artifact_uri == (
        "samples/sample-failed/failure_artifact_write_failed.json"
    )


def test_dataset_index_validates_batch_uri_maps():
    batch_result = summarize_sample_runs(
        batch_id="batch-a",
        route_id="maniskill_sapien",
        task_count=1,
        requested_sample_count=1,
        sample_runs=(_sample_run("sample-ok", "completed"),),
    )

    with pytest.raises(ValueError, match="batch_root_uris"):
        build_simulation_dataset_index(
            accumulation_id="acc-a",
            batch_results=(batch_result,),
            batch_root_uris={},
            batch_result_uris={"batch-a": "batches/batch-a/batch_result.json"},
        )


def test_accumulation_report_uses_index_status_and_next_scale_fields():
    batch_result = summarize_sample_runs(
        batch_id="batch-a",
        route_id="maniskill_sapien",
        task_count=1,
        requested_sample_count=1,
        sample_runs=(_sample_run("sample-ok", "completed"),),
    )
    index = build_simulation_dataset_index(
        accumulation_id="acc-a",
        batch_results=(batch_result,),
        batch_root_uris={"batch-a": "batches/batch-a"},
        batch_result_uris={"batch-a": "batches/batch-a/batch_result.json"},
    )

    report = build_simulation_accumulation_report(
        dataset_index=index,
        dataset_index_uri="dataset_index.json",
    )

    assert report.accumulation_id == "acc-a"
    assert report.status == "ready_to_scale_with_conditions"
    assert report.completion_ratio == 1.0
    assert report.dataset_index_uri == "dataset_index.json"
    assert report.batch_result_uris == ("batches/batch-a/batch_result.json",)
    assert "phase_2" in report.next_scale_recommendation
    assert "not_real_welding_quality" in report.known_limitations


def test_accumulation_report_uses_batch_id_order_for_result_uris():
    batch_a = summarize_sample_runs(
        batch_id="batch-a",
        route_id="maniskill_sapien",
        task_count=1,
        requested_sample_count=1,
        sample_runs=(_sample_run("sample-a", "completed"),),
    )
    batch_b = summarize_sample_runs(
        batch_id="batch-b",
        route_id="maniskill_sapien",
        task_count=1,
        requested_sample_count=1,
        sample_runs=(
            dataclasses.replace(
                _sample_run("sample-b", "completed"),
                batch_id="batch-b",
            ),
        ),
    )
    index = build_simulation_dataset_index(
        accumulation_id="acc-a",
        batch_results=(batch_a, batch_b),
        batch_root_uris={
            "batch-a": "batches/batch-a",
            "batch-b": "batches/batch-b",
        },
        batch_result_uris={
            "batch-b": "batches/batch-b/batch_result.json",
            "batch-a": "batches/batch-a/batch_result.json",
        },
    )

    report = build_simulation_accumulation_report(
        dataset_index=index,
        dataset_index_uri="dataset_index.json",
    )

    assert report.batch_result_uris == (
        "batches/batch-a/batch_result.json",
        "batches/batch-b/batch_result.json",
    )
