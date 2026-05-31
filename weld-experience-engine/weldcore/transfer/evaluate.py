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
    reference = apply_transfer(package, target_condition).xyz
    n = min(len(actual), len(reference))
    trajectory_rms = float(
        np.sqrt(np.mean(np.sum((actual[:n] - reference[:n]) ** 2, axis=1)))
    )

    metrics = TransferMetrics(
        trajectory_rms_mm=trajectory_rms,
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
