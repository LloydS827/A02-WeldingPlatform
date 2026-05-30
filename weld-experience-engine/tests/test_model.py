import json, numpy as np
from weldcore.model.weave import WeaveTemplate, WeaveType, WAVEFORMS
from weldcore.model.groove import GrooveGeometry, GrooveType
from weldcore.model.layerpass import LayerPass
from weldcore.model.process import WeldProcess, Posture

def test_waveform_registry_bounded():
    phase = np.linspace(0, 2*np.pi, 200)
    for wtype, fn in WAVEFORMS.items():
        y = fn(phase)
        assert np.max(np.abs(y)) <= 1.0 + 1e-6, wtype

def test_weave_lateral_scales_by_amplitude():
    w = WeaveTemplate(WeaveType.CRESCENT, amplitude=3.0, frequency=2.0)
    phase = np.array([np.pi/2])          # sin peak
    assert abs(w.lateral(phase)[0] - 3.0) < 1e-6

def test_process_serializes_to_json():
    p = WeldProcess(
        travel_speed=5.0,
        weave=WeaveTemplate(WeaveType.ZIGZAG, 2.0, 1.5, left_dwell=0.1),
        posture=Posture(work_angle_deg=45, travel_angle_deg=10, stickout_mm=15),
        groove=GrooveGeometry(GrooveType.V, angle_deg=60, depth_mm=12),
        layer_pass=LayerPass(layer=1, pass_no=1),
        length_mm=200.0,
    )
    s = p.to_json()
    d = json.loads(s)
    assert d["weave"]["type"] == "zigzag"          # 枚举序列化为字符串
    assert d["groove"]["type"] == "V"
    assert d["travel_speed"] == 5.0
