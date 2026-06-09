from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from weldcore.simulation_bakeoff.batch import VariationPolicy, _model_dict
from weldcore.simulation_bakeoff.model import SimulationTaskSpec
from weldcore.simulation_bakeoff.task_specs import default_simulation_task_specs

AccumulationStatus = Literal[
    "accumulating_completed_samples",
    "accumulating_with_failures",
    "blocked_by_environment",
    "blocked_by_pipeline_failure",
    "ready_to_scale_with_conditions",
]

DEFAULT_ACCUMULATION_STAGE_BOUNDARY = (
    "simulation_accumulation_not_real_welding_quality"
)
DEFAULT_ACCUMULATION_SCALE_PLAN = (
    "phase_1_100_requested_samples_then_phase_2_500_requested_samples"
)


@dataclass(frozen=True)
class SimulationAccumulationBatchSpec:
    accumulation_id: str
    route_id: str
    task_specs: tuple[SimulationTaskSpec, ...]
    samples_per_task: int
    target_requested_sample_count: int
    batch_id_prefix: str
    output_root: str
    seed_start: int
    variation_policy: VariationPolicy
    scale_phase: str
    scale_plan: str
    resume_policy: str
    stage_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


def default_maniskill_accumulation_spec(
    *,
    accumulation_id: str = "maniskill-sapien-accumulation-phase-1",
    route_id: str = "maniskill_sapien",
    task_specs: tuple[SimulationTaskSpec, ...] | None = None,
    samples_per_task: int = 50,
    target_requested_sample_count: int | None = None,
    batch_id_prefix: str = "maniskill-sapien-accumulation",
    output_root: str = "artifacts/simulation/maniskill-sapien-accumulations",
    seed_start: int = 0,
    variation_policy: VariationPolicy = "deterministic_micro_offset",
    scale_phase: str = "phase_1_accumulation_start",
    scale_plan: str = DEFAULT_ACCUMULATION_SCALE_PLAN,
    resume_policy: str = "reuse_existing_batch_result_unless_force",
    stage_boundary: str = DEFAULT_ACCUMULATION_STAGE_BOUNDARY,
) -> SimulationAccumulationBatchSpec:
    resolved_task_specs = (
        default_simulation_task_specs() if task_specs is None else task_specs
    )
    if samples_per_task <= 0:
        raise ValueError("samples_per_task must be positive")
    if not resolved_task_specs:
        raise ValueError("task_specs must not be empty")
    derived_target = len(resolved_task_specs) * samples_per_task
    if target_requested_sample_count is not None:
        if target_requested_sample_count != derived_target:
            raise ValueError(
                "target_requested_sample_count must equal "
                "len(task_specs) * samples_per_task"
            )
    return SimulationAccumulationBatchSpec(
        accumulation_id=accumulation_id,
        route_id=route_id,
        task_specs=resolved_task_specs,
        samples_per_task=samples_per_task,
        target_requested_sample_count=derived_target,
        batch_id_prefix=batch_id_prefix,
        output_root=output_root,
        seed_start=seed_start,
        variation_policy=variation_policy,
        scale_phase=scale_phase,
        scale_plan=scale_plan,
        resume_policy=resume_policy,
        stage_boundary=stage_boundary,
    )


def determine_accumulation_status(
    *,
    requested_sample_count: int,
    completed_sample_count: int,
    failed_sample_count: int,
    skipped_sample_count: int,
    failure_boundaries: tuple[str, ...],
) -> AccumulationStatus:
    if requested_sample_count <= 0:
        raise ValueError("requested_sample_count must be positive")
    if completed_sample_count == 0 and "environment_missing" in failure_boundaries:
        return "blocked_by_environment"
    if completed_sample_count == 0:
        return "blocked_by_pipeline_failure"
    if failed_sample_count > 0 or skipped_sample_count > 0:
        return "accumulating_with_failures"
    if (
        completed_sample_count == requested_sample_count
        and failed_sample_count == 0
        and skipped_sample_count == 0
        and not failure_boundaries
    ):
        return "ready_to_scale_with_conditions"
    return "accumulating_completed_samples"
