from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
from typing import Any, Iterable, Literal

from weldcore.simulation_bakeoff.model import SimulationTaskSpec
from weldcore.simulation_bakeoff.task_specs import default_simulation_task_specs

VariationPolicy = Literal["none", "deterministic_micro_offset"]
SampleRunStatus = Literal["completed", "failed", "skipped"]

DEFAULT_BATCH_STAGE_BOUNDARY = "simulation_only_not_real_welding_quality"
DEFAULT_BATCH_NEXT_STEP_HINT = (
    "Review completed and failed sample evidence before promoting any simulator route."
)
SAMPLE_PLAN_EVIDENCE_NOTES = (
    "simulation_only_not_real_welding_quality",
    "not_final_simulator_selection",
    "not_real_welding_process_variation",
)


def _jsonable(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


def _model_dict(value: Any) -> dict[str, Any]:
    payload = asdict(value)
    return {key: _jsonable(getattr(value, key)) for key in payload}


@dataclass(frozen=True)
class SimulationBatchSpec:
    batch_id: str
    route_id: str
    task_specs: tuple[SimulationTaskSpec, ...]
    samples_per_task: int
    sample_variation_policy: VariationPolicy
    seed_start: int
    output_root: str
    comparison_route_ids: tuple[str, ...]
    stage_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class SimulationSamplePlan:
    batch_id: str
    sample_id: str
    task_id: str
    route_id: str
    seed: int
    variation_policy: VariationPolicy
    variation_descriptor: dict[str, Any]
    evidence_notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class SimulationSampleRun:
    batch_id: str
    sample_id: str
    task_id: str
    route_id: str
    seed: int
    variation_policy: VariationPolicy
    variation_descriptor: dict[str, Any]
    status: SampleRunStatus
    raw_artifact_uri: str
    adapter_result_uri: str | None
    evidence_bundle_uri: str | None
    experience_dataset_uri: str | None
    failure_boundary: tuple[str, ...]
    evidence_notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class SimulationBatchResult:
    batch_id: str
    route_id: str
    task_count: int
    requested_sample_count: int
    completed_sample_count: int
    failed_sample_count: int
    skipped_sample_count: int
    sample_runs: tuple[SimulationSampleRun, ...]
    failure_boundaries: tuple[str, ...]
    stage_boundary: str
    next_step_hint: str

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


def default_maniskill_batch_spec(
    *,
    batch_id: str = "maniskill-sapien-default-batch",
    route_id: str = "maniskill_sapien",
    task_specs: tuple[SimulationTaskSpec, ...] | None = None,
    samples_per_task: int = 10,
    sample_variation_policy: VariationPolicy = "deterministic_micro_offset",
    seed_start: int = 0,
    output_root: str = "artifacts/simulation/maniskill-sapien-batches",
    comparison_route_ids: tuple[str, ...] = ("simlite_reference",),
    stage_boundary: str = DEFAULT_BATCH_STAGE_BOUNDARY,
) -> SimulationBatchSpec:
    return SimulationBatchSpec(
        batch_id=batch_id,
        route_id=route_id,
        task_specs=(
            default_simulation_task_specs() if task_specs is None else task_specs
        ),
        samples_per_task=samples_per_task,
        sample_variation_policy=sample_variation_policy,
        seed_start=seed_start,
        output_root=output_root,
        comparison_route_ids=comparison_route_ids,
        stage_boundary=stage_boundary,
    )


def iter_batch_sample_plans(
    spec: SimulationBatchSpec,
) -> Iterable[SimulationSamplePlan]:
    seed = spec.seed_start
    for task_spec in spec.task_specs:
        for _ in range(spec.samples_per_task):
            yield SimulationSamplePlan(
                batch_id=spec.batch_id,
                sample_id=(
                    f"sample-{spec.batch_id}-{spec.route_id}-{task_spec.task_id}-{seed}"
                ),
                task_id=task_spec.task_id,
                route_id=spec.route_id,
                seed=seed,
                variation_policy=spec.sample_variation_policy,
                variation_descriptor=_variation_descriptor(
                    spec.sample_variation_policy,
                    seed,
                ),
                evidence_notes=SAMPLE_PLAN_EVIDENCE_NOTES,
            )
            seed += 1


def summarize_sample_runs(
    *,
    batch_id: str,
    route_id: str,
    task_count: int,
    requested_sample_count: int,
    sample_runs: Iterable[SimulationSampleRun],
    stage_boundary: str = DEFAULT_BATCH_STAGE_BOUNDARY,
    next_step_hint: str = DEFAULT_BATCH_NEXT_STEP_HINT,
) -> SimulationBatchResult:
    runs = tuple(sample_runs)
    failure_boundaries = []
    seen_failure_boundaries = set()
    for run in runs:
        for boundary in run.failure_boundary:
            if boundary not in seen_failure_boundaries:
                failure_boundaries.append(boundary)
                seen_failure_boundaries.add(boundary)

    return SimulationBatchResult(
        batch_id=batch_id,
        route_id=route_id,
        task_count=task_count,
        requested_sample_count=requested_sample_count,
        completed_sample_count=sum(1 for run in runs if run.status == "completed"),
        failed_sample_count=sum(1 for run in runs if run.status == "failed"),
        skipped_sample_count=sum(1 for run in runs if run.status == "skipped"),
        sample_runs=runs,
        failure_boundaries=tuple(failure_boundaries),
        stage_boundary=stage_boundary,
        next_step_hint=next_step_hint,
    )


def _variation_descriptor(policy: VariationPolicy, seed: int) -> dict[str, Any]:
    descriptor: dict[str, Any] = {"policy": policy, "seed": seed}
    if policy == "deterministic_micro_offset":
        descriptor["offset"] = _deterministic_micro_offset(seed)
    return descriptor


def _deterministic_micro_offset(seed: int) -> dict[str, float | str]:
    x_index = seed % 5 - 2
    y_index = seed // 5 % 5 - 2
    z_index = seed // 25 % 3 - 1
    return {
        "source": "seed_modulo_micro_offset_metadata_only",
        "x_m": round(x_index * 0.0005, 6),
        "y_m": round(y_index * 0.0005, 6),
        "z_m": round(z_index * 0.00025, 6),
    }
