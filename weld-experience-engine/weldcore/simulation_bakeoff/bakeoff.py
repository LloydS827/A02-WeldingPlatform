from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from weldcore.simulation_bakeoff.adapters import (
    attempt_gazebo_moveit,
    attempt_maniskill_sapien,
    run_simlite_reference,
)
from weldcore.simulation_bakeoff.evidence import build_simulation_evidence_bundle
from weldcore.simulation_bakeoff.model import (
    BakeoffScorecard,
    SimulationEvidenceBundle,
    SimulationTaskSpec,
    SimulatorAdapterResult,
)
from weldcore.simulation_bakeoff.task_specs import default_simulation_task_specs


DIMENSION_WEIGHTS = {
    "digital_asset_writeback": 0.35,
    "robot_executability": 0.30,
    "skill_unit_expression": 0.20,
    "engineering_access_cost": 0.15,
}

ROUTE_RUNNERS: tuple[
    tuple[str, Callable[[SimulationTaskSpec], SimulatorAdapterResult]],
    ...,
] = (
    ("simlite_reference", run_simlite_reference),
    ("maniskill_sapien", attempt_maniskill_sapien),
    ("gazebo_moveit", attempt_gazebo_moveit),
)


@dataclass(frozen=True)
class MinimalBakeoffResult:
    task_specs: tuple[SimulationTaskSpec, ...]
    evidence_bundles: tuple[SimulationEvidenceBundle, ...]
    scorecard: BakeoffScorecard

    def to_dict(self) -> dict[str, object]:
        return {
            "task_specs": [task_spec.to_dict() for task_spec in self.task_specs],
            "evidence_bundles": [
                evidence_bundle.to_dict() for evidence_bundle in self.evidence_bundles
            ],
            "scorecard": self.scorecard.to_dict(),
        }


def run_minimal_simulation_bakeoff() -> MinimalBakeoffResult:
    task_specs = default_simulation_task_specs()
    evidence_bundles = tuple(
        build_simulation_evidence_bundle(task_spec, route_runner(task_spec))
        for _route_name, route_runner in ROUTE_RUNNERS
        for task_spec in task_specs
    )
    scorecard = _build_scorecard(task_specs, evidence_bundles)
    return MinimalBakeoffResult(
        task_specs=task_specs,
        evidence_bundles=evidence_bundles,
        scorecard=scorecard,
    )


def _build_scorecard(
    task_specs: tuple[SimulationTaskSpec, ...],
    evidence_bundles: tuple[SimulationEvidenceBundle, ...],
) -> BakeoffScorecard:
    expected_task_ids = tuple(task_spec.task_id for task_spec in task_specs)
    route_dimension_scores = {
        route_name: _score_route(route_name, expected_task_ids, evidence_bundles)
        for route_name, _route_runner in ROUTE_RUNNERS
    }
    route_scores = {
        route_name: _weighted_total(dimension_scores)
        for route_name, dimension_scores in route_dimension_scores.items()
    }
    external_routes_completed = [
        route_name
        for route_name, _route_runner in ROUTE_RUNNERS
        if route_name != "simlite_reference"
        and _route_completed_all_tasks(route_name, expected_task_ids, evidence_bundles)
    ]
    return BakeoffScorecard(
        dimension_weights=dict(DIMENSION_WEIGHTS),
        route_dimension_scores=route_dimension_scores,
        route_scores=route_scores,
        attempted_task_ids=expected_task_ids,
        recommendation=_recommendation(external_routes_completed),
        final_simulator_selected=False,
        evidence_notes=("not_final_simulator_selection",),
    )


def _score_route(
    route_name: str,
    expected_task_ids: tuple[str, ...],
    evidence_bundles: tuple[SimulationEvidenceBundle, ...],
) -> dict[str, float]:
    route_bundles = tuple(
        bundle
        for bundle in evidence_bundles
        if bundle.adapter_result.adapter_name == route_name
    )
    return {
        "digital_asset_writeback": _score_digital_asset_writeback(
            expected_task_ids, route_bundles
        ),
        "robot_executability": _score_robot_executability(route_name, route_bundles),
        "skill_unit_expression": _score_skill_unit_expression(
            expected_task_ids, route_bundles
        ),
        "engineering_access_cost": _score_engineering_access_cost(
            route_name, route_bundles
        ),
    }


def _score_digital_asset_writeback(
    expected_task_ids: tuple[str, ...],
    route_bundles: tuple[SimulationEvidenceBundle, ...],
) -> float:
    if _completed_with_datasets_for_all_tasks(expected_task_ids, route_bundles):
        return 1.0
    if route_bundles and all(
        bundle.adapter_result.status == "failed" and bundle.adapter_result.failure_boundary
        for bundle in route_bundles
    ):
        return 0.35
    return 0.0


def _score_robot_executability(
    route_name: str,
    route_bundles: tuple[SimulationEvidenceBundle, ...],
) -> float:
    if route_name == "simlite_reference" and route_bundles and all(
        bundle.adapter_result.status == "completed" for bundle in route_bundles
    ):
        return 0.4
    if route_name != "simlite_reference" and route_bundles and all(
        _completed_with_validated_task_contract(bundle) for bundle in route_bundles
    ):
        return 1.0
    if route_name != "simlite_reference" and route_bundles and all(
        bundle.adapter_result.status == "failed" and bundle.adapter_result.failure_boundary
        for bundle in route_bundles
    ):
        return 0.25
    return 0.0


def _score_skill_unit_expression(
    expected_task_ids: tuple[str, ...],
    route_bundles: tuple[SimulationEvidenceBundle, ...],
) -> float:
    expected = set(expected_task_ids)
    attempted = {bundle.task_spec.task_id for bundle in route_bundles}
    if attempted == expected:
        return 1.0
    if attempted:
        return 0.5
    return 0.0


def _score_engineering_access_cost(
    route_name: str,
    route_bundles: tuple[SimulationEvidenceBundle, ...],
) -> float:
    if route_name == "simlite_reference" and route_bundles and all(
        bundle.adapter_result.status == "completed" for bundle in route_bundles
    ):
        return 1.0
    if route_name != "simlite_reference" and route_bundles and all(
        bundle.adapter_result.status == "completed" for bundle in route_bundles
    ):
        return 0.75
    if route_name != "simlite_reference" and route_bundles and all(
        bundle.adapter_result.status == "failed" and bundle.adapter_result.failure_boundary
        for bundle in route_bundles
    ):
        return 0.25
    return 0.0


def _weighted_total(dimension_scores: dict[str, float]) -> float:
    return sum(
        dimension_scores[dimension] * weight
        for dimension, weight in DIMENSION_WEIGHTS.items()
    )


def _completed_with_datasets_for_all_tasks(
    expected_task_ids: tuple[str, ...],
    route_bundles: tuple[SimulationEvidenceBundle, ...],
) -> bool:
    completed_task_ids = {
        bundle.task_spec.task_id
        for bundle in route_bundles
        if bundle.adapter_result.status == "completed" and bundle.dataset is not None
    }
    return completed_task_ids == set(expected_task_ids)


def _completed_with_validated_task_contract(bundle: SimulationEvidenceBundle) -> bool:
    return (
        bundle.adapter_result.status == "completed"
        and bundle.adapter_result.planning_result.get("validated_task_contract") is True
    )


def _route_completed_all_tasks(
    route_name: str,
    expected_task_ids: tuple[str, ...],
    evidence_bundles: tuple[SimulationEvidenceBundle, ...],
) -> bool:
    completed_task_ids = {
        bundle.task_spec.task_id
        for bundle in evidence_bundles
        if bundle.adapter_result.adapter_name == route_name
        and _completed_with_validated_task_contract(bundle)
    }
    return completed_task_ids == set(expected_task_ids)


def _recommendation(external_routes_completed: list[str]) -> str:
    if len(external_routes_completed) == 0:
        return "continue_with_r0_baseline_and_prepare_external_dependency_spikes"
    if len(external_routes_completed) == 1:
        return f"candidate_ready_for_next_adapter_plan:{external_routes_completed[0]}"
    return "compare_external_routes_before_final_selection"
