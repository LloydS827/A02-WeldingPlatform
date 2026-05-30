from __future__ import annotations

import numpy as np

from ..model.weave import WAVEFORMS, WeaveType


def detect_amplitude(residual: np.ndarray) -> float:
    """鲁棒摆幅估计，保留模板峰值同时降低少量离群点影响。"""
    return float((np.percentile(residual, 99) - np.percentile(residual, 1)) / 2)


def detect_frequency(residual: np.ndarray, t: np.ndarray) -> float:
    """用 FFT 主峰估计摆频。"""
    centered = residual - residual.mean()
    n = len(centered)
    dt = float(np.median(np.diff(t)))
    spec = np.abs(np.fft.rfft(centered * np.hanning(n)))
    spec[0] = 0.0
    freqs = np.fft.rfftfreq(n, dt)
    return float(freqs[np.argmax(spec)])


def _harmonic_ratio(sig: np.ndarray, t: np.ndarray, freq: float) -> float:
    n = len(sig)
    dt = float(np.median(np.diff(t)))
    spec = np.abs(np.fft.rfft((sig - sig.mean()) * np.hanning(n)))
    freqs = np.fft.rfftfreq(n, dt)

    def amp(fk: float) -> float:
        return float(spec[np.argmin(np.abs(freqs - fk))])

    h1 = amp(freq) or 1e-9
    return amp(3 * freq) / h1


def classify_type(residual: np.ndarray, t: np.ndarray, freq: float) -> WeaveType:
    """用参考模板谐波特征做相位无关分类。"""
    target = _harmonic_ratio(residual, t, freq)
    phase = 2 * np.pi * freq * t
    best = None
    best_distance = np.inf

    for wtype, fn in WAVEFORMS.items():
        distance = abs(_harmonic_ratio(fn(phase), t, freq) - target)
        if distance < best_distance:
            best = wtype
            best_distance = distance

    return best
