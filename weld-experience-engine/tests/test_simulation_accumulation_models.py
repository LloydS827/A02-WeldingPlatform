import pytest

from weldcore.simulation_bakeoff import (
    DEFAULT_ACCUMULATION_SCALE_PLAN,
    DEFAULT_ACCUMULATION_STAGE_BOUNDARY,
    SimulationAccumulationBatchSpec,
    default_maniskill_accumulation_spec,
    determine_accumulation_status,
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
