import dataclasses

import pytest

from weldcore.simulation_bakeoff import (
    DEFAULT_ACCUMULATION_SCALE_PLAN,
    DEFAULT_ACCUMULATION_STAGE_BOUNDARY,
    SimulationAccumulationBatchSpec,
    SimulationSampleRun,
    build_simulation_accumulation_report,
    build_simulation_dataset_index,
    default_maniskill_accumulation_spec,
    determine_accumulation_status,
    summarize_sample_runs,
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
