from weldcore.datagen.synth import synthesize
from weldcore.decompose.engine import decompose
from weldcore.metrics.robustness import breakdown_level, robustness_sweep
from weldcore.metrics.roundtrip import param_errors, trajectory_rms
from weldcore.model.process import WeldProcess
from weldcore.model.weave import WeaveTemplate, WeaveType
from weldcore.recompose.interpolate import recompose


def _process():
    return WeldProcess(
        travel_speed=5.0,
        weave=WeaveTemplate(WeaveType.CRESCENT, 3.0, 2.0),
        length_mm=60.0,
    )


def test_roundtrip_near_lossless_on_ideal():
    process = _process()
    ideal = synthesize(process, fs=100.0)
    recomposed = recompose(decompose(ideal), fs=100.0)

    assert trajectory_rms(ideal, recomposed) < 0.2


def test_param_errors_small_on_ideal():
    process = _process()
    errors = param_errors(process, decompose(synthesize(process, fs=100.0)))

    assert errors["type_correct"]
    assert errors["amplitude_err"] < 0.2
    assert errors["travel_speed_err"] < 0.1


def test_robustness_sweep_reports_breakdown_boundary():
    process = _process()
    levels = [0.0, 0.1, 0.2, 0.5, 1.0, 2.0]

    lv, amp_err, freq_err, type_ok = robustness_sweep(process, levels, fs=100.0, seed=5)
    boundary = breakdown_level(lv, amp_err, threshold=0.5)

    assert amp_err[0] < amp_err[-1]
    assert len(freq_err) == len(levels)
    assert len(type_ok) == len(levels)
    assert boundary > 0
