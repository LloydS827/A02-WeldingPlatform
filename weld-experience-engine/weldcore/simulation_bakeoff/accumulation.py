from __future__ import annotations

import dataclasses
import posixpath
from dataclasses import dataclass
from typing import Any, Literal

from weldcore.simulation_bakeoff.batch import (
    SimulationBatchResult,
    SimulationSampleRun,
    VariationPolicy,
    _model_dict,
)
from weldcore.simulation_bakeoff.model import SimulationTaskSpec
from weldcore.simulation_bakeoff.task_specs import default_simulation_task_specs

AccumulationStatus = Literal[
    "accumulating_completed_samples",
    "accumulating_with_failures",
    "blocked_by_environment",
    "blocked_by_pipeline_failure",
    "locked_for_next_batch_with_conditions",
    "ready_to_scale_with_conditions",
]
ShardRunStatus = Literal[
    "completed_new_run",
    "reused_existing_result",
    "failed_to_load_existing_result",
    "rerun_forced",
]

ALLOWED_LOCK_FAILURE_BOUNDARIES = frozenset(
    {"environment_missing", "simulation_run_failed"}
)

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
    shard_count: int
    samples_per_shard: int
    variation_policy: VariationPolicy
    scale_phase: str
    scale_plan: str
    resume_policy: str
    stage_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class SimulationAccumulationShardSpec:
    shard_id: str
    batch_id: str
    samples_per_task: int
    requested_sample_count: int
    seed_start: int
    batch_root_uri: str
    batch_result_uri: str
    reuse_policy: str

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class SimulationDatasetIndexItem:
    accumulation_id: str
    batch_id: str
    sample_id: str
    task_id: str
    route_id: str
    seed: int
    variation_policy: VariationPolicy
    status: str
    raw_artifact_uri: str
    adapter_result_uri: str | None
    experience_dataset_uri: str | None
    evidence_bundle_uri: str | None
    failure_boundary: tuple[str, ...]
    failure_artifact_uri: str | None

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class SimulationFieldCoverageSummary:
    requested_sample_coverage: dict[str, float]
    completed_sample_coverage: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class SimulationDatasetIndex:
    accumulation_id: str
    route_id: str
    batch_ids: tuple[str, ...]
    requested_sample_count: int
    completed_sample_count: int
    failed_sample_count: int
    skipped_sample_count: int
    index_items: tuple[SimulationDatasetIndexItem, ...]
    failure_boundaries: tuple[str, ...]
    dataset_uris: tuple[str, ...]
    evidence_bundle_uris: tuple[str, ...]
    batch_root_uris: dict[str, str]
    batch_result_uris: dict[str, str]
    field_coverage_summary: SimulationFieldCoverageSummary
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class SimulationAccumulationShardReport:
    shard_id: str
    batch_id: str
    status: ShardRunStatus
    requested_sample_count: int
    completed_sample_count: int
    failed_sample_count: int
    skipped_sample_count: int
    batch_result_uri: str
    failure_boundaries: tuple[str, ...]
    field_coverage: SimulationFieldCoverageSummary

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class SimulationAccumulationReport:
    accumulation_id: str
    status: AccumulationStatus
    requested_sample_count: int
    completed_sample_count: int
    failed_sample_count: int
    skipped_sample_count: int
    completion_ratio: float
    dominant_failure_boundaries: tuple[str, ...]
    dataset_index_uri: str
    batch_result_uris: tuple[str, ...]
    shard_count: int
    completed_shard_count: int
    reused_shard_count: int
    failed_shard_count: int
    shard_reports: tuple[SimulationAccumulationShardReport, ...]
    shard_result_uris: tuple[str, ...]
    failure_boundary_counts: dict[str, int]
    field_coverage_trend: dict[str, dict[str, float]]
    readiness_for_next_scale: str
    next_scale_recommendation: str
    known_limitations: tuple[str, ...]

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
        shard_count=1,
        samples_per_shard=derived_target,
        variation_policy=variation_policy,
        scale_phase=scale_phase,
        scale_plan=scale_plan,
        resume_policy=resume_policy,
        stage_boundary=stage_boundary,
    )


def default_maniskill_sharded_accumulation_spec(
    *,
    accumulation_id: str = "maniskill-sapien-accumulation-phase-2",
    samples_per_task: int = 50,
    shard_count: int = 5,
    seed_start: int = 0,
    **kwargs: Any,
) -> SimulationAccumulationBatchSpec:
    if shard_count <= 0:
        raise ValueError("shard_count must be positive")
    base = default_maniskill_accumulation_spec(
        accumulation_id=accumulation_id,
        samples_per_task=samples_per_task,
        seed_start=seed_start,
        target_requested_sample_count=None,
        scale_phase="phase_2_scale_sharded_accumulation",
        **kwargs,
    )
    return dataclasses.replace(
        base,
        shard_count=shard_count,
        samples_per_shard=len(base.task_specs) * samples_per_task,
        target_requested_sample_count=(
            len(base.task_specs) * samples_per_task * shard_count
        ),
    )


def iter_accumulation_shard_specs(
    spec: SimulationAccumulationBatchSpec,
) -> tuple[SimulationAccumulationShardSpec, ...]:
    shards: list[SimulationAccumulationShardSpec] = []
    seed = spec.seed_start
    for index in range(spec.shard_count):
        shard_id = f"shard-{index:03d}"
        batch_id = f"{spec.batch_id_prefix}-{spec.accumulation_id}-{shard_id}"
        batch_root_uri = f"batches/{batch_id}"
        shards.append(
            SimulationAccumulationShardSpec(
                shard_id=shard_id,
                batch_id=batch_id,
                samples_per_task=spec.samples_per_task,
                requested_sample_count=spec.samples_per_shard,
                seed_start=seed,
                batch_root_uri=batch_root_uri,
                batch_result_uri=f"{batch_root_uri}/batch_result.json",
                reuse_policy=spec.resume_policy,
            )
        )
        seed += spec.samples_per_shard
    return tuple(shards)


def validate_batch_result_matches_shard(
    *,
    batch_result: SimulationBatchResult,
    shard_spec: SimulationAccumulationShardSpec,
    route_id: str,
    task_count: int,
) -> None:
    if batch_result.batch_id != shard_spec.batch_id:
        raise ValueError("batch_result batch_id does not match shard")
    if batch_result.route_id != route_id:
        raise ValueError("batch_result route_id does not match shard")
    if batch_result.requested_sample_count != shard_spec.requested_sample_count:
        raise ValueError("batch_result requested_sample_count does not match shard")
    if batch_result.task_count != task_count:
        raise ValueError("batch_result task_count does not match shard")
    if len(batch_result.sample_runs) != shard_spec.requested_sample_count:
        raise ValueError("batch_result sample_runs do not match shard")
    expected_seeds = set(
        range(
            shard_spec.seed_start,
            shard_spec.seed_start + shard_spec.requested_sample_count,
        )
    )
    actual_seeds = {run.seed for run in batch_result.sample_runs}
    if actual_seeds != expected_seeds:
        raise ValueError("batch_result seed range does not match shard")
    sample_ids = [run.sample_id for run in batch_result.sample_runs]
    if len(set(sample_ids)) != len(sample_ids):
        raise ValueError("batch_result sample_ids must be unique")
    for run in batch_result.sample_runs:
        if run.batch_id != shard_spec.batch_id or run.route_id != route_id:
            raise ValueError("sample run identity does not match shard")
        expected_sample_id = (
            f"sample-{shard_spec.batch_id}-{route_id}-{run.task_id}-{run.seed}"
        )
        if run.sample_id != expected_sample_id:
            raise ValueError("sample run sample_id does not match shard")


def build_simulation_accumulation_shard_report(
    *,
    shard_spec: SimulationAccumulationShardSpec,
    batch_result: SimulationBatchResult,
    status: ShardRunStatus,
) -> SimulationAccumulationShardReport:
    index_items = tuple(
        _dataset_index_item(shard_spec.shard_id, sample_run)
        for sample_run in batch_result.sample_runs
    )
    return SimulationAccumulationShardReport(
        shard_id=shard_spec.shard_id,
        batch_id=shard_spec.batch_id,
        status=status,
        requested_sample_count=batch_result.requested_sample_count,
        completed_sample_count=batch_result.completed_sample_count,
        failed_sample_count=batch_result.failed_sample_count,
        skipped_sample_count=batch_result.skipped_sample_count,
        batch_result_uri=shard_spec.batch_result_uri,
        failure_boundaries=batch_result.failure_boundaries,
        field_coverage=_field_coverage_summary(index_items),
    )


def build_simulation_dataset_index(
    *,
    accumulation_id: str,
    batch_results: tuple[SimulationBatchResult, ...],
    batch_root_uris: dict[str, str],
    batch_result_uris: dict[str, str],
    created_at: str = "not_recorded",
) -> SimulationDatasetIndex:
    if not batch_results:
        raise ValueError("batch_results must not be empty")
    batch_ids = tuple(result.batch_id for result in batch_results)
    _validate_uri_map_keys("batch_root_uris", batch_root_uris, batch_ids)
    _validate_uri_map_keys("batch_result_uris", batch_result_uris, batch_ids)

    index_items: list[SimulationDatasetIndexItem] = []
    dataset_uris: list[str] = []
    evidence_bundle_uris: list[str] = []
    failure_boundaries: list[str] = []
    seen_failure_boundaries: set[str] = set()

    for batch_result in batch_results:
        for boundary in batch_result.failure_boundaries:
            if boundary not in seen_failure_boundaries:
                failure_boundaries.append(boundary)
                seen_failure_boundaries.add(boundary)

        for sample_run in batch_result.sample_runs:
            item = _dataset_index_item(accumulation_id, sample_run)
            index_items.append(item)
            if item.experience_dataset_uri is not None:
                dataset_uris.append(item.experience_dataset_uri)
            if item.evidence_bundle_uri is not None:
                evidence_bundle_uris.append(item.evidence_bundle_uri)

    items = tuple(index_items)
    return SimulationDatasetIndex(
        accumulation_id=accumulation_id,
        route_id=batch_results[0].route_id,
        batch_ids=batch_ids,
        requested_sample_count=sum(
            result.requested_sample_count for result in batch_results
        ),
        completed_sample_count=sum(
            result.completed_sample_count for result in batch_results
        ),
        failed_sample_count=sum(result.failed_sample_count for result in batch_results),
        skipped_sample_count=sum(
            result.skipped_sample_count for result in batch_results
        ),
        index_items=items,
        failure_boundaries=tuple(failure_boundaries),
        dataset_uris=tuple(dataset_uris),
        evidence_bundle_uris=tuple(evidence_bundle_uris),
        batch_root_uris=dict(batch_root_uris),
        batch_result_uris=dict(batch_result_uris),
        field_coverage_summary=_field_coverage_summary(items),
        created_at=created_at,
    )


def build_simulation_accumulation_report(
    *,
    dataset_index: SimulationDatasetIndex,
    dataset_index_uri: str,
    shard_reports: tuple[SimulationAccumulationShardReport, ...] = (),
) -> SimulationAccumulationReport:
    _validate_shard_reports_match_dataset_index(dataset_index, shard_reports)
    status = _determine_dataset_index_status(dataset_index)
    return SimulationAccumulationReport(
        accumulation_id=dataset_index.accumulation_id,
        status=status,
        requested_sample_count=dataset_index.requested_sample_count,
        completed_sample_count=dataset_index.completed_sample_count,
        failed_sample_count=dataset_index.failed_sample_count,
        skipped_sample_count=dataset_index.skipped_sample_count,
        completion_ratio=round(
            dataset_index.completed_sample_count
            / dataset_index.requested_sample_count,
            6,
        ),
        dominant_failure_boundaries=dataset_index.failure_boundaries,
        dataset_index_uri=dataset_index_uri,
        batch_result_uris=tuple(
            dataset_index.batch_result_uris[batch_id]
            for batch_id in dataset_index.batch_ids
        ),
        shard_count=len(shard_reports),
        completed_shard_count=sum(
            1
            for report in shard_reports
            if report.status in {"completed_new_run", "rerun_forced"}
        ),
        reused_shard_count=sum(
            1 for report in shard_reports if report.status == "reused_existing_result"
        ),
        failed_shard_count=sum(
            1
            for report in shard_reports
            if report.status == "failed_to_load_existing_result"
        ),
        shard_reports=tuple(shard_reports),
        shard_result_uris=tuple(report.batch_result_uri for report in shard_reports),
        failure_boundary_counts=_failure_boundary_counts(dataset_index.index_items),
        field_coverage_trend={
            report.shard_id: dict(report.field_coverage.completed_sample_coverage)
            for report in shard_reports
        },
        readiness_for_next_scale=_readiness_for_next_scale(status),
        next_scale_recommendation=(
            "continue_phase_1_then_review_before_"
            "phase_2_500_requested_samples"
        ),
        known_limitations=(
            "simulation_accumulation_not_real_welding_quality",
            "not_real_welding_quality",
            "not_final_simulator_selection",
            "not_robot_execution_validation",
        ),
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


def _determine_dataset_index_status(
    dataset_index: SimulationDatasetIndex,
) -> AccumulationStatus:
    base = determine_accumulation_status(
        requested_sample_count=dataset_index.requested_sample_count,
        completed_sample_count=dataset_index.completed_sample_count,
        failed_sample_count=dataset_index.failed_sample_count,
        skipped_sample_count=dataset_index.skipped_sample_count,
        failure_boundaries=dataset_index.failure_boundaries,
    )
    if base in {"blocked_by_environment", "blocked_by_pipeline_failure"}:
        return base
    if dataset_index.skipped_sample_count > 0:
        return "accumulating_with_failures"
    if (
        dataset_index.completed_sample_count == dataset_index.requested_sample_count
        and dataset_index.failed_sample_count == 0
        and not dataset_index.failure_boundaries
    ):
        return "ready_to_scale_with_conditions"
    if _is_locked_for_next_batch(dataset_index):
        return "locked_for_next_batch_with_conditions"
    if dataset_index.failed_sample_count > 0:
        return "accumulating_with_failures"
    return base


def _is_locked_for_next_batch(dataset_index: SimulationDatasetIndex) -> bool:
    if dataset_index.requested_sample_count < 500:
        return False
    if dataset_index.completed_sample_count <= 0:
        return False
    if dataset_index.failed_sample_count <= 0:
        return False
    coverage = dataset_index.field_coverage_summary.completed_sample_coverage
    required_fields = (
        "adapter_result_uri",
        "experience_dataset_uri",
        "evidence_bundle_uri",
    )
    if any(coverage.get(field, 0.0) != 1.0 for field in required_fields):
        return False
    failed_items = tuple(
        item for item in dataset_index.index_items if item.status == "failed"
    )
    if not failed_items:
        return False
    for item in failed_items:
        if not item.failure_boundary:
            return False
        if any(
            boundary not in ALLOWED_LOCK_FAILURE_BOUNDARIES
            for boundary in item.failure_boundary
        ):
            return False
    return True


def _validate_shard_reports_match_dataset_index(
    dataset_index: SimulationDatasetIndex,
    shard_reports: tuple[SimulationAccumulationShardReport, ...],
) -> None:
    if not shard_reports:
        return
    report_batch_ids = tuple(report.batch_id for report in shard_reports)
    if (
        len(report_batch_ids) != len(set(report_batch_ids))
        or set(report_batch_ids) != set(dataset_index.batch_ids)
    ):
        raise ValueError("shard_reports must match dataset batch_ids")


def _dataset_index_item(
    accumulation_id: str,
    sample_run: SimulationSampleRun,
) -> SimulationDatasetIndexItem:
    artifact_uris = (
        sample_run.raw_artifact_uri,
        sample_run.adapter_result_uri,
        sample_run.experience_dataset_uri,
        sample_run.evidence_bundle_uri,
        sample_run.failure_artifact_uri,
    )
    for artifact_uri in artifact_uris:
        _validate_relative_batch_root_uri(artifact_uri)

    return SimulationDatasetIndexItem(
        accumulation_id=accumulation_id,
        batch_id=sample_run.batch_id,
        sample_id=sample_run.sample_id,
        task_id=sample_run.task_id,
        route_id=sample_run.route_id,
        seed=sample_run.seed,
        variation_policy=sample_run.variation_policy,
        status=sample_run.status,
        raw_artifact_uri=sample_run.raw_artifact_uri,
        adapter_result_uri=sample_run.adapter_result_uri,
        experience_dataset_uri=sample_run.experience_dataset_uri,
        evidence_bundle_uri=sample_run.evidence_bundle_uri,
        failure_boundary=sample_run.failure_boundary,
        failure_artifact_uri=_failure_artifact_uri(sample_run),
    )


def _validate_relative_batch_root_uri(artifact_uri: str | None) -> None:
    if artifact_uri is None:
        return
    if (
        artifact_uri.startswith("/")
        or artifact_uri.startswith("../")
        or "/../" in artifact_uri
        or "\\" in artifact_uri
        or "://" in artifact_uri
    ):
        raise ValueError("item artifact URIs must be relative batch root paths")


def _failure_artifact_uri(sample_run: SimulationSampleRun) -> str | None:
    if sample_run.status == "completed":
        return None
    if sample_run.failure_artifact_uri is not None:
        return sample_run.failure_artifact_uri
    if "failure_artifact" in sample_run.raw_artifact_uri:
        return sample_run.raw_artifact_uri
    sample_dir = posixpath.dirname(sample_run.raw_artifact_uri)
    if not sample_dir:
        return "failure_artifact.json"
    return posixpath.join(sample_dir, "failure_artifact.json")


def _validate_uri_map_keys(
    map_name: str,
    uri_map: dict[str, str],
    batch_ids: tuple[str, ...],
) -> None:
    expected = set(batch_ids)
    actual = set(uri_map)
    if actual != expected:
        raise ValueError(f"{map_name} must cover exactly the indexed batch_ids")


def _field_coverage_summary(
    index_items: tuple[SimulationDatasetIndexItem, ...],
) -> SimulationFieldCoverageSummary:
    completed_items = tuple(item for item in index_items if item.status == "completed")
    return SimulationFieldCoverageSummary(
        requested_sample_coverage=_coverage_for_items(index_items),
        completed_sample_coverage=_coverage_for_items(completed_items),
    )


def _coverage_for_items(
    index_items: tuple[SimulationDatasetIndexItem, ...],
) -> dict[str, float]:
    coverage_fields = (
        "raw_artifact_uri",
        "adapter_result_uri",
        "experience_dataset_uri",
        "evidence_bundle_uri",
        "failure_artifact_uri",
    )
    denominator = len(index_items)
    if denominator == 0:
        return {field: 0.0 for field in coverage_fields}
    return {
        field: round(
            sum(1 for item in index_items if _coverage_field_present(item, field))
            / denominator,
            6,
        )
        for field in coverage_fields
    }


def _coverage_field_present(item: SimulationDatasetIndexItem, field: str) -> bool:
    value = getattr(item, field)
    if value is None:
        return False
    if field == "raw_artifact_uri":
        return posixpath.basename(value) == "raw_artifact.json"
    return True


def _failure_boundary_counts(
    index_items: tuple[SimulationDatasetIndexItem, ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in index_items:
        for boundary in item.failure_boundary:
            counts[boundary] = counts.get(boundary, 0) + 1
    return counts


def _readiness_for_next_scale(status: AccumulationStatus) -> str:
    readiness_by_status = {
        "ready_to_scale_with_conditions": "ready_with_conditions",
        "locked_for_next_batch_with_conditions": "locked_with_conditions",
        "accumulating_with_failures": "continue_accumulating_with_failure_review",
        "blocked_by_environment": "blocked_until_environment_available",
        "blocked_by_pipeline_failure": "blocked_until_pipeline_failure_resolved",
        "accumulating_completed_samples": "continue_accumulating_until_target_reached",
    }
    return readiness_by_status[status]
