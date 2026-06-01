from __future__ import annotations

import numpy as np

from ..model.experiment import TransferDecision, TransferExperiment, TransferMetrics
from ..model.skill import WeldCondition, WeldSkillPackage
from ..model.trajectory import Trajectory
from .rules import apply_transfer


def evaluate_transfer(
    experiment_id: str,
    package: WeldSkillPackage,
    source_condition: WeldCondition,
    target_condition: WeldCondition,
    transferred: Trajectory,
) -> TransferExperiment:
    actual = transferred.xyz
    reference = apply_transfer(package, target_condition)
    reference_xyz = reference.xyz
    if len(actual) == 0 or len(reference_xyz) == 0:
        trajectory_error = float("inf")
    else:
        completeness_penalty = max(
            float(np.linalg.norm(actual[-1] - reference_xyz[-1])),
            _time_coverage_gap(transferred, reference) * _path_length(reference_xyz),
        )
        trajectory_error = float(
            np.hypot(
                _trajectory_rms_for_transfer(transferred, reference),
                completeness_penalty,
            )
        )

    metrics = TransferMetrics(
        trajectory_rms_mm=trajectory_error,
        posture_error_deg=0.0,
        weave_amplitude_error_mm=0.0,
        weave_frequency_error_hz=0.0,
        process_current_error=0.0,
    )
    decision = _decision(metrics)
    return TransferExperiment(
        experiment_id=experiment_id,
        source_condition=source_condition.__dict__,
        target_condition=target_condition.__dict__,
        skill_package_id=package.package_id,
        recomposed_trajectory=transferred,
        metrics=metrics,
        decision=decision,
        notes="synthetic MVP transfer evaluation",
    )


def _decision(metrics: TransferMetrics) -> TransferDecision:
    if metrics.trajectory_rms_mm <= 1.0 and metrics.posture_error_deg <= 2.0:
        return TransferDecision.PASS
    if metrics.trajectory_rms_mm <= 3.0:
        return TransferDecision.REVIEW
    return TransferDecision.FAIL


def _path_length(xyz: np.ndarray) -> float:
    if len(xyz) < 2:
        return 0.0
    return float(np.sum(np.linalg.norm(np.diff(xyz, axis=0), axis=1)))


def _trajectory_rms_for_transfer(actual: Trajectory, reference: Trajectory) -> float:
    sample_count = max(len(actual), len(reference))
    tg = np.linspace(
        max(actual.t[0], reference.t[0]),
        min(actual.t[-1], reference.t[-1]),
        sample_count,
    )
    actual_xyz = np.column_stack(
        [np.interp(tg, actual.t, actual.xyz[:, i]) for i in range(3)]
    )
    reference_xyz = np.column_stack(
        [np.interp(tg, reference.t, reference.xyz[:, i]) for i in range(3)]
    )
    return float(np.sqrt(np.mean(np.sum((actual_xyz - reference_xyz) ** 2, axis=1))))


def _time_coverage_gap(actual: Trajectory, reference: Trajectory) -> float:
    reference_duration = reference.t[-1] - reference.t[0]
    if reference_duration <= 0.0:
        return 0.0
    actual_duration = actual.t[-1] - actual.t[0]
    return float(abs(actual_duration - reference_duration) / reference_duration)
