from __future__ import annotations

import os
import json
import math
import struct
import zlib

from ..datagen.synth import synthesize
from ..decompose.engine import decompose
from ..metrics.robustness import breakdown_level, robustness_sweep
from ..metrics.roundtrip import param_errors, trajectory_rms
from ..model.process import Posture, WeldProcess
from ..model.weave import WeaveTemplate, WeaveType
from ..recompose.interpolate import recompose


def _draw_line(img, width, height, x0, y0, x1, y1, color):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        if 0 <= x0 < width and 0 <= y0 < height:
            img[y0][x0] = color
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def _write_png(path, img):
    height = len(img)
    width = len(img[0])
    raw = b"".join(b"\x00" + bytes(channel for pixel in row for channel in pixel) for row in img)

    def chunk(kind, data):
        payload = kind + data
        return struct.pack(">I", len(data)) + payload + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(raw)))
        f.write(chunk(b"IEND", b""))


def _save_fallback_plot(path, series):
    width, height = 960, 360
    margin = 40
    img = [[(255, 255, 255) for _ in range(width)] for _ in range(height)]
    _draw_line(img, width, height, margin, height - margin, width - margin, height - margin, (40, 40, 40))
    _draw_line(img, width, height, margin, margin, margin, height - margin, (40, 40, 40))

    xs = [x for points, _ in series for x, _ in points]
    ys = [y for points, _ in series for _, y in points]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    if xmin == xmax:
        xmax = xmin + 1
    if ymin == ymax:
        ymax = ymin + 1

    colors = [(0, 112, 192), (230, 126, 34), (180, 30, 30)]
    for idx, (points, _) in enumerate(series):
        color = colors[idx % len(colors)]
        mapped = []
        for x, y in points:
            px = margin + int((x - xmin) / (xmax - xmin) * (width - 2 * margin))
            py = height - margin - int((y - ymin) / (ymax - ymin) * (height - 2 * margin))
            mapped.append((px, py))
        for (x0, y0), (x1, y1) in zip(mapped, mapped[1:]):
            _draw_line(img, width, height, x0, y0, x1, y1, color)

    _write_png(path, img)


def _save_plot(path, series, *, xlabel, ylabel, title):
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        _save_fallback_plot(path, series)
        return

    fig, ax = plt.subplots(figsize=(8, 3))
    for points, label in series:
        xs = [x for x, _ in points]
        ys = [y for _, y in points]
        ax.plot(xs, ys, label=label)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def _jsonable(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _demo_process(wtype=WeaveType.CRESCENT):
    return WeldProcess(
        travel_speed=5.0,
        weave=WeaveTemplate(wtype, amplitude=3.0, frequency=2.0),
        posture=Posture(work_angle_deg=45.0, travel_angle_deg=10.0),
        length_mm=80.0,
    )


def run_report(outdir: str = "report_out", show_rerun: bool = False) -> dict:
    os.makedirs(outdir, exist_ok=True)
    result: dict = {}

    process = _demo_process()
    ideal = synthesize(process, fs=100.0)
    recovered_process = decompose(ideal)
    recomposed = recompose(recovered_process, fs=100.0)
    result["ideal_roundtrip_rms"] = trajectory_rms(ideal, recomposed)
    result["ideal_param_errors"] = param_errors(process, recovered_process)

    _save_plot(
        os.path.join(outdir, "roundtrip.png"),
        [
            (list(zip(ideal.xyz[:, 0], ideal.xyz[:, 1])), "ideal"),
            (list(zip(recomposed.xyz[:, 0], recomposed.xyz[:, 1])), "recomposed"),
        ],
        xlabel="travel x (mm)",
        ylabel="weave y (mm)",
        title=f"roundtrip RMS={result['ideal_roundtrip_rms']:.3f} mm",
    )

    result["classified_ok"] = {}
    for wtype in [WeaveType.CRESCENT, WeaveType.ZIGZAG, WeaveType.TRAPEZOID]:
        recovered = decompose(synthesize(_demo_process(wtype), fs=200.0))
        result["classified_ok"][wtype.value] = recovered.weave.type == wtype

    levels = [0.0, 0.1, 0.2, 0.3, 0.5, 0.8, 1.2, 2.0]
    lv, amp_err, freq_err, type_ok = robustness_sweep(process, levels, fs=100.0, seed=7)
    result["robustness_levels_mm"] = lv.tolist()
    result["amplitude_errors_mm"] = amp_err.tolist()
    result["frequency_errors_hz"] = freq_err.tolist()
    result["type_ok"] = type_ok.tolist()
    result["amp_breakdown_mm"] = breakdown_level(lv, amp_err, threshold=0.5)
    result["freq_breakdown_mm"] = breakdown_level(lv, freq_err, threshold=0.3)

    _save_plot(
        os.path.join(outdir, "robustness.png"),
        [
            (list(zip(lv, amp_err)), "amplitude error (mm)"),
            (list(zip(lv, freq_err)), "frequency error (Hz)"),
        ],
        xlabel="injected tremor std (mm)",
        ylabel="recovered parameter error",
        title=f"amplitude breakdown ~= {result['amp_breakdown_mm']} mm",
    )

    with open(os.path.join(outdir, "evidence.json"), "w", encoding="utf-8") as f:
        json.dump(_jsonable(result), f, ensure_ascii=False, indent=2)

    with open(os.path.join(outdir, "robustness.csv"), "w", encoding="utf-8") as f:
        f.write("tremor_mm,amplitude_error_mm,frequency_error_hz,type_ok\n")
        for level, amp, freq, ok in zip(lv, amp_err, freq_err, type_ok):
            f.write(f"{level},{amp},{freq},{bool(ok)}\n")

    if show_rerun:
        from ..viz.rerun_view import log_trajectory

        log_trajectory(ideal, recomposed)

    print("=== 经验结构化 POC 证据摘要 ===")
    print(f"理想往返 RMS: {result['ideal_roundtrip_rms']:.4f} mm")
    print(f"模板分类: {result['classified_ok']}")
    print(
        f"摆幅失效边界: {result['amp_breakdown_mm']} mm  "
        f"摆频失效边界: {result['freq_breakdown_mm']} mm"
    )
    return result


if __name__ == "__main__":
    run_report(show_rerun=False)
