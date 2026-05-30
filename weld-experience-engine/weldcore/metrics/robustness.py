from __future__ import annotations

import numpy as np

from ..datagen.perturb import perturb
from ..datagen.synth import synthesize
from ..decompose.engine import decompose
from ..model.process import WeldProcess
from .roundtrip import param_errors


def robustness_sweep(process: WeldProcess, tremor_levels, fs: float = 100.0, seed: int = 0):
    """逐级注入手抖，记录参数恢复误差和模板分类是否正确。"""
    ideal = synthesize(process, fs=fs)
    amp_err = []
    freq_err = []
    type_ok = []

    for level in tremor_levels:
        recovered = decompose(perturb(ideal, tremor_mm=level, seed=seed))
        errors = param_errors(process, recovered)
        amp_err.append(errors["amplitude_err"])
        freq_err.append(errors["frequency_err"])
        type_ok.append(bool(errors["type_correct"]))

    return (
        np.asarray(tremor_levels, float),
        np.asarray(amp_err, float),
        np.asarray(freq_err, float),
        np.asarray(type_ok, bool),
    )


def breakdown_level(levels, errors, threshold: float) -> float:
    """误差首次超过阈值的扰动级别；若未超过则返回 inf。"""
    over = np.where(np.asarray(errors) > threshold)[0]
    return float(np.asarray(levels, float)[over[0]]) if len(over) else float("inf")
