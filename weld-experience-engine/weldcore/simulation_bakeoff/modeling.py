from __future__ import annotations

import json
from dataclasses import dataclass, replace
from typing import Any, Literal

from weldcore.simulation_bakeoff.batch import (
    _model_dict,
    default_maniskill_batch_spec,
    iter_batch_sample_plans,
)
from weldcore.simulation_bakeoff.model import SimulationPathPoint, SimulationTaskSpec
from weldcore.simulation_bakeoff.task_specs import default_simulation_task_specs

ModelingValidationStatus = Literal[
    "ready_for_simulation_batch",
    "blocked_by_modeling_issue",
]

DEFAULT_MODELING_STAGE_BOUNDARY = "simulation_modeling_not_real_welding_quality"
DEFAULT_MODELING_POLICY = "deterministic_geometry_variation"
MODELING_ASSUMPTION_NOTES = (
    "simulation_modeling_assumption",
    "not_real_welding_process_parameter",
)
MODELING_EVIDENCE_NOTES = (
    "simulation_only_not_real_welding_quality",
    "not_final_simulator_selection",
    "not_real_welding_process_parameter",
)
MODELING_KNOWN_LIMITATIONS = (
    "simulation_only_not_real_welding_quality",
    "not_final_simulator_selection",
    "not_WPS_PQR",
    "not_real_robot_execution",
)
FORBIDDEN_MODELING_TERMS = (
    "molten",
    "molten_pool",
    "molten pool",
    "weld_pool",
    "weld pool",
    "thermal",
    "metallurgy",
    "熔池",
    "热过程",
    "冶金",
)


@dataclass(frozen=True)
class BatchModelingSpec:
    modeling_batch_id: str
    source_task_specs: tuple[SimulationTaskSpec, ...]
    variants_per_task: int
    variation_policy: str
    stage_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class TaskModelingVariation:
    source_task_id: str
    modeled_task_id: str
    variation_index: int
    variation_descriptor: dict[str, Any]
    assumption_notes: tuple[str, ...]
    evidence_notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class ModeledSimulationTask:
    modeled_task_id: str
    source_task_id: str
    variation: TaskModelingVariation
    task_spec: SimulationTaskSpec
    path_geometry_changed: bool

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class ModelingValidationIssue:
    modeled_task_id: str
    severity: str
    issue: str

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class ModelingCoverageSummary:
    source_task_count: int
    modeled_task_count: int
    modeled_task_per_source_task: dict[str, int]
    path_length_range_m: dict[str, float]
    geometry_profiles: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


@dataclass(frozen=True)
class ModelingValidationReport:
    modeling_batch_id: str
    status: ModelingValidationStatus
    source_task_count: int
    modeled_task_count: int
    valid_modeled_task_count: int
    expert_review_candidate_count: int
    expert_review_candidate_ratio: float
    source_task_ids: tuple[str, ...]
    modeled_task_ids: tuple[str, ...]
    expert_review_candidate_task_ids: tuple[str, ...]
    coverage_summary: ModelingCoverageSummary
    issues: tuple[ModelingValidationIssue, ...]
    known_limitations: tuple[str, ...]
    next_step_recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return _model_dict(self)


def default_batch_modeling_spec(
    *,
    modeling_batch_id: str = "default-batch-modeling-v1",
    source_task_specs: tuple[SimulationTaskSpec, ...] | None = None,
    variants_per_task: int = 4,
    variation_policy: str = DEFAULT_MODELING_POLICY,
    stage_boundary: str = DEFAULT_MODELING_STAGE_BOUNDARY,
) -> BatchModelingSpec:
    resolved = (
        default_simulation_task_specs() if source_task_specs is None else source_task_specs
    )
    if variants_per_task <= 0:
        raise ValueError("variants_per_task must be positive")
    if not resolved:
        raise ValueError("source_task_specs must not be empty")
    return BatchModelingSpec(
        modeling_batch_id=modeling_batch_id,
        source_task_specs=resolved,
        variants_per_task=variants_per_task,
        variation_policy=variation_policy,
        stage_boundary=stage_boundary,
    )


def build_modeled_simulation_tasks(
    spec: BatchModelingSpec,
) -> tuple[ModeledSimulationTask, ...]:
    modeled: list[ModeledSimulationTask] = []
    for source in spec.source_task_specs:
        if not source.seam_path:
            raise ValueError("source task seam_path must not be empty")
        for index in range(spec.variants_per_task):
            variation = _task_modeling_variation(source, index, spec.variation_policy)
            task_spec = _apply_variation(source, variation)
            modeled.append(
                ModeledSimulationTask(
                    modeled_task_id=task_spec.task_id,
                    source_task_id=source.task_id,
                    variation=variation,
                    task_spec=task_spec,
                    path_geometry_changed=task_spec.seam_path != source.seam_path,
                )
            )
    return tuple(modeled)


def build_modeling_validation_report(
    spec: BatchModelingSpec,
    modeled_tasks: tuple[ModeledSimulationTask, ...],
) -> ModelingValidationReport:
    source_by_id = {task.task_id: task for task in spec.source_task_specs}
    duplicate_ids = _duplicate_modeled_task_ids(modeled_tasks)
    batch_issues = _batch_validation_issues(spec, modeled_tasks)
    issues_by_task: list[tuple[ModelingValidationIssue, ...]] = []
    issues: list[ModelingValidationIssue] = list(batch_issues)
    for task in modeled_tasks:
        task_issues = _validation_issues(source_by_id, task, duplicate_ids)
        issues_by_task.append(task_issues)
        issues.extend(task_issues)

    valid_tasks = tuple(
        task
        for task, task_issues in zip(modeled_tasks, issues_by_task)
        if not task_issues
    )
    candidate_ids = tuple(
        task.modeled_task_id for task in valid_tasks if task.path_geometry_changed
    ) if not issues else ()
    candidate_ratio = (
        round(len(candidate_ids) / len(modeled_tasks), 6) if modeled_tasks else 0.0
    )
    status: ModelingValidationStatus = (
        "blocked_by_modeling_issue" if issues else "ready_for_simulation_batch"
    )
    return ModelingValidationReport(
        modeling_batch_id=spec.modeling_batch_id,
        status=status,
        source_task_count=len(spec.source_task_specs),
        modeled_task_count=len(modeled_tasks),
        valid_modeled_task_count=len(valid_tasks),
        expert_review_candidate_count=len(candidate_ids),
        expert_review_candidate_ratio=candidate_ratio,
        source_task_ids=tuple(task.task_id for task in spec.source_task_specs),
        modeled_task_ids=tuple(task.modeled_task_id for task in modeled_tasks),
        expert_review_candidate_task_ids=candidate_ids,
        coverage_summary=_coverage_summary(spec, modeled_tasks),
        issues=tuple(issues),
        known_limitations=MODELING_KNOWN_LIMITATIONS,
        next_step_recommendation=(
            "Use valid modeled task specs for a small simulation batch before any "
            "expert review decision."
        ),
    )


def modeled_task_specs(
    modeled_tasks: tuple[ModeledSimulationTask, ...],
) -> tuple[SimulationTaskSpec, ...]:
    return tuple(task.task_spec for task in modeled_tasks)


def simulation_task_specs_from_modeling_payload(
    payload: list[dict[str, Any]] | tuple[dict[str, Any], ...],
) -> tuple[SimulationTaskSpec, ...]:
    return tuple(_simulation_task_spec_from_dict(item) for item in payload)


def modeling_batch_spec_compatibility(
    modeled_tasks: tuple[ModeledSimulationTask, ...],
    *,
    samples_per_task: int = 2,
) -> dict[str, Any]:
    batch_spec = default_maniskill_batch_spec(
        task_specs=modeled_task_specs(modeled_tasks),
        samples_per_task=samples_per_task,
    )
    sample_plans = tuple(iter_batch_sample_plans(batch_spec))
    return {
        "compatible_with": "default_maniskill_batch_spec",
        "batch_task_count": len(batch_spec.task_specs),
        "samples_per_task": batch_spec.samples_per_task,
        "requested_sample_count": len(sample_plans),
        "modeled_task_ids": tuple(task.task_id for task in batch_spec.task_specs),
    }


def _task_modeling_variation(
    source: SimulationTaskSpec,
    index: int,
    policy: str,
) -> TaskModelingVariation:
    direction = -1 if index % 2 else 1
    magnitude = index + 1
    modeled_task_id = f"modeled-{source.task_id}-v{index:02d}"
    descriptor = {
        "modeled_task_id": modeled_task_id,
        "policy": policy,
        "variation_index": index,
        "path_length_scale": round(1.0 + direction * 0.01 * magnitude, 6),
        "lateral_offset_m": round(direction * 0.002 * magnitude, 6),
        "vertical_offset_m": round((index % 3 - 1) * 0.001, 6),
        "orientation_rz_delta_deg": round(direction * 2.0 * magnitude, 6),
        "geometry_profile": f"deterministic_geometry_v{index:02d}",
    }
    return TaskModelingVariation(
        source_task_id=source.task_id,
        modeled_task_id=modeled_task_id,
        variation_index=index,
        variation_descriptor=descriptor,
        assumption_notes=MODELING_ASSUMPTION_NOTES,
        evidence_notes=MODELING_EVIDENCE_NOTES,
    )


def _apply_variation(
    source: SimulationTaskSpec,
    variation: TaskModelingVariation,
) -> SimulationTaskSpec:
    descriptor = variation.variation_descriptor
    scale = float(descriptor["path_length_scale"])
    lateral_offset = float(descriptor["lateral_offset_m"])
    vertical_offset = float(descriptor["vertical_offset_m"])
    rz_delta = float(descriptor["orientation_rz_delta_deg"])
    origin = source.seam_path[0]
    seam_path = tuple(
        SimulationPathPoint(
            t=point.t,
            x=round(origin.x + (point.x - origin.x) * scale, 6),
            y=round(origin.y + (point.y - origin.y) * scale + lateral_offset, 6),
            z=round(point.z + vertical_offset, 6),
            rx=point.rx,
            ry=point.ry,
            rz=round(point.rz + rz_delta, 6),
        )
        for point in source.seam_path
    )
    return replace(
        source,
        task_id=variation.modeled_task_id,
        name=f"{source.name} modeled v{variation.variation_index:02d}",
        seam_path=seam_path,
    )


def _duplicate_modeled_task_ids(
    modeled_tasks: tuple[ModeledSimulationTask, ...],
) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for task in modeled_tasks:
        task_id = task.modeled_task_id
        if task_id in seen:
            duplicates.add(task_id)
        seen.add(task_id)
    return duplicates


def _batch_validation_issues(
    spec: BatchModelingSpec,
    modeled_tasks: tuple[ModeledSimulationTask, ...],
) -> tuple[ModelingValidationIssue, ...]:
    expected_ids = set(_expected_modeled_task_ids(spec))
    actual_ids = {task.modeled_task_id for task in modeled_tasks}
    issues: list[ModelingValidationIssue] = []
    for task_id in sorted(expected_ids - actual_ids):
        issues.append(_issue("__modeling_batch__", f"missing_modeled_task:{task_id}"))
    for task_id in sorted(actual_ids - expected_ids):
        issues.append(_issue(task_id, f"unexpected_modeled_task:{task_id}"))
    return tuple(issues)


def _expected_modeled_task_ids(spec: BatchModelingSpec) -> tuple[str, ...]:
    return tuple(
        f"modeled-{source.task_id}-v{index:02d}"
        for source in spec.source_task_specs
        for index in range(spec.variants_per_task)
    )


def _validation_issues(
    source_by_id: dict[str, SimulationTaskSpec],
    modeled_task: ModeledSimulationTask,
    duplicate_ids: set[str],
) -> tuple[ModelingValidationIssue, ...]:
    modeled_task_id = modeled_task.modeled_task_id
    task_spec = modeled_task.task_spec
    issues: list[ModelingValidationIssue] = []
    if modeled_task_id in duplicate_ids:
        issues.append(_issue(modeled_task_id, "modeled_task_id_not_unique"))
    if (
        modeled_task_id != task_spec.task_id
        or modeled_task_id != modeled_task.variation.modeled_task_id
    ):
        issues.append(_issue(modeled_task_id, "modeled_task_id_mismatch"))
    if modeled_task.source_task_id not in source_by_id:
        issues.append(_issue(modeled_task_id, "source_task_id_not_found"))
    if len(task_spec.seam_path) < 5:
        issues.append(_issue(modeled_task_id, "seam_path_has_fewer_than_five_points"))
    if _path_length(task_spec.seam_path) <= 0:
        issues.append(_issue(modeled_task_id, "seam_path_length_not_positive"))
    missing_outputs = {
        "tcp_trajectory",
        "tool_orientation",
        "task_status",
    } - set(task_spec.expected_outputs)
    for output in sorted(missing_outputs):
        issues.append(_issue(modeled_task_id, f"missing_expected_output:{output}"))
    if "path_continuity" not in task_spec.evaluation_metrics:
        issues.append(_issue(modeled_task_id, "missing_metric:path_continuity"))
    missing_boundaries = {"real_welding_quality", "WPS/PQR"} - set(
        task_spec.out_of_scope
    )
    for boundary in sorted(missing_boundaries):
        issues.append(_issue(modeled_task_id, f"missing_out_of_scope:{boundary}"))
    if not modeled_task.path_geometry_changed:
        issues.append(_issue(modeled_task_id, "path_geometry_not_changed"))
    serialized = json.dumps(task_spec.to_dict(), ensure_ascii=False).lower()
    for term in FORBIDDEN_MODELING_TERMS:
        if term.lower() in serialized:
            issues.append(_issue(modeled_task_id, f"forbidden_term:{term}"))
    return tuple(issues)


def _coverage_summary(
    spec: BatchModelingSpec,
    modeled_tasks: tuple[ModeledSimulationTask, ...],
) -> ModelingCoverageSummary:
    modeled_per_source = {task.task_id: 0 for task in spec.source_task_specs}
    for task in modeled_tasks:
        modeled_per_source[task.source_task_id] = (
            modeled_per_source.get(task.source_task_id, 0) + 1
        )
    path_lengths = tuple(_path_length(task.task_spec.seam_path) for task in modeled_tasks)
    path_length_range = (
        {"min": round(min(path_lengths), 6), "max": round(max(path_lengths), 6)}
        if path_lengths
        else {"min": 0.0, "max": 0.0}
    )
    geometry_profiles = tuple(
        sorted(
            {
                str(task.variation.variation_descriptor["geometry_profile"])
                for task in modeled_tasks
            }
        )
    )
    return ModelingCoverageSummary(
        source_task_count=len(spec.source_task_specs),
        modeled_task_count=len(modeled_tasks),
        modeled_task_per_source_task=modeled_per_source,
        path_length_range_m=path_length_range,
        geometry_profiles=geometry_profiles,
    )


def _path_length(path: tuple[SimulationPathPoint, ...]) -> float:
    total = 0.0
    for previous, current in zip(path, path[1:]):
        dx = current.x - previous.x
        dy = current.y - previous.y
        dz = current.z - previous.z
        total += (dx * dx + dy * dy + dz * dz) ** 0.5
    return total


def _issue(modeled_task_id: str, issue: str) -> ModelingValidationIssue:
    return ModelingValidationIssue(
        modeled_task_id=modeled_task_id,
        severity="error",
        issue=issue,
    )


def _simulation_task_spec_from_dict(data: dict[str, Any]) -> SimulationTaskSpec:
    return SimulationTaskSpec(
        task_id=str(data["task_id"]),
        unit_id=str(data["unit_id"]),
        name=str(data["name"]),
        seam_path=tuple(
            SimulationPathPoint(
                t=float(point["t"]),
                x=float(point["x"]),
                y=float(point["y"]),
                z=float(point["z"]),
                rx=float(point["rx"]),
                ry=float(point["ry"]),
                rz=float(point["rz"]),
            )
            for point in data["seam_path"]
        ),
        tcp_frame=str(data["tcp_frame"]),
        tool_orientation_constraint=tuple(data["tool_orientation_constraint"]),
        motion_constraint=tuple(data["motion_constraint"]),
        robot_constraint=tuple(data["robot_constraint"]),
        expected_outputs=tuple(data["expected_outputs"]),
        evaluation_metrics=tuple(data["evaluation_metrics"]),
        out_of_scope=tuple(data["out_of_scope"]),
    )
