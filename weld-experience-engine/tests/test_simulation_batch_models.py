from weldcore.simulation_bakeoff import (
    SimulationBatchResult,
    SimulationBatchSpec,
    SimulationSamplePlan,
    SimulationSampleRun,
    default_maniskill_batch_spec,
    iter_batch_sample_plans,
    summarize_sample_runs,
)


def test_default_batch_spec_requests_twenty_primary_samples():
    spec = default_maniskill_batch_spec(
        batch_id="batch-test",
        output_root="artifacts/simulation/maniskill-sapien-batches",
    )

    samples = tuple(iter_batch_sample_plans(spec))

    assert isinstance(spec, SimulationBatchSpec)
    assert spec.route_id == "maniskill_sapien"
    assert spec.samples_per_task == 10
    assert spec.sample_variation_policy == "deterministic_micro_offset"
    assert spec.comparison_route_ids == ("simlite_reference",)
    assert len(spec.task_specs) == 2
    assert len(samples) == 20
    assert isinstance(samples[0], SimulationSamplePlan)
    assert {sample.route_id for sample in samples} == {"maniskill_sapien"}
    assert samples[0].sample_id == (
        "sample-batch-test-maniskill_sapien-"
        f"{spec.task_specs[0].task_id}-0"
    )


def test_sample_plans_record_seed_and_variation_descriptor():
    spec = default_maniskill_batch_spec(batch_id="batch-test", seed_start=100)

    samples = tuple(iter_batch_sample_plans(spec))

    assert samples[0].seed == 100
    assert samples[1].seed == 101
    assert samples[0].variation_policy == "deterministic_micro_offset"
    assert samples[0].variation_descriptor["policy"] == "deterministic_micro_offset"
    assert samples[0].variation_descriptor["seed"] == 100
    assert "not_real_welding_process_variation" in samples[0].evidence_notes


def test_batch_result_summarizes_completed_failed_and_skipped_samples():
    runs = (
        SimulationSampleRun(
            batch_id="batch-test",
            sample_id="sample-1",
            task_id="task-a",
            route_id="maniskill_sapien",
            seed=1,
            variation_policy="deterministic_micro_offset",
            variation_descriptor={"policy": "deterministic_micro_offset", "seed": 1},
            status="completed",
            raw_artifact_uri="samples/sample-1/raw_artifact.json",
            adapter_result_uri="samples/sample-1/adapter_result.json",
            evidence_bundle_uri="samples/sample-1/evidence_bundle.json",
            experience_dataset_uri="samples/sample-1/experience_dataset.json",
            failure_boundary=(),
            evidence_notes=("simulation_only_not_real_welding_quality",),
        ),
        SimulationSampleRun(
            batch_id="batch-test",
            sample_id="sample-2",
            task_id="task-a",
            route_id="maniskill_sapien",
            seed=2,
            variation_policy="deterministic_micro_offset",
            variation_descriptor={"policy": "deterministic_micro_offset", "seed": 2},
            status="failed",
            raw_artifact_uri="samples/sample-2/failure_artifact.json",
            adapter_result_uri=None,
            evidence_bundle_uri=None,
            experience_dataset_uri=None,
            failure_boundary=("task_generation_failed",),
            evidence_notes=("simulation_only_not_real_welding_quality",),
        ),
        SimulationSampleRun(
            batch_id="batch-test",
            sample_id="sample-3",
            task_id="task-a",
            route_id="maniskill_sapien",
            seed=3,
            variation_policy="deterministic_micro_offset",
            variation_descriptor={"policy": "deterministic_micro_offset", "seed": 3},
            status="skipped",
            raw_artifact_uri="samples/sample-3/failure_artifact.json",
            adapter_result_uri=None,
            evidence_bundle_uri=None,
            experience_dataset_uri=None,
            failure_boundary=("batch_generation_incomplete",),
            evidence_notes=("simulation_only_not_real_welding_quality",),
        ),
    )

    result = summarize_sample_runs(
        batch_id="batch-test",
        route_id="maniskill_sapien",
        task_count=1,
        requested_sample_count=3,
        sample_runs=runs,
    )

    assert isinstance(result, SimulationBatchResult)
    assert result.completed_sample_count == 1
    assert result.failed_sample_count == 1
    assert result.skipped_sample_count == 1
    assert result.failure_boundaries == (
        "task_generation_failed",
        "batch_generation_incomplete",
    )
    payload = result.to_dict()
    assert payload["sample_runs"][0]["status"] == "completed"
    assert payload["sample_runs"][2]["raw_artifact_uri"].endswith(
        "failure_artifact.json"
    )
