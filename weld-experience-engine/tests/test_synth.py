import numpy as np
from weldcore.model.weave import WeaveTemplate, WeaveType
from weldcore.model.process import WeldProcess
from weldcore.datagen.synth import synthesize

def _proc():
    return WeldProcess(travel_speed=5.0,
                       weave=WeaveTemplate(WeaveType.CRESCENT, amplitude=3.0, frequency=2.0),
                       length_mm=50.0)

def test_synth_forward_travel_speed():
    tr = synthesize(_proc(), fs=100.0)
    # x 末值应 ≈ 长度；行进速度 = dx/dt ≈ 5
    assert abs(tr.xyz[-1,0] - 50.0) < 0.1
    v = np.gradient(tr.xyz[:,0], tr.t)
    assert abs(np.median(v) - 5.0) < 1e-6

def test_synth_weave_amplitude():
    tr = synthesize(_proc(), fs=100.0)
    y = tr.xyz[:,1]
    assert abs(y.max() - 3.0) < 0.1 and abs(y.min() + 3.0) < 0.1

def test_synth_sampling_rate():
    tr = synthesize(_proc(), fs=100.0)         # 100Hz = 10ms
    dt = np.diff(tr.t)
    assert abs(np.median(dt) - 0.01) < 1e-9
