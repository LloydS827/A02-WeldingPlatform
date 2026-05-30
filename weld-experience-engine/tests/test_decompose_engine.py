from weldcore.datagen.synth import synthesize
from weldcore.decompose.engine import decompose
from weldcore.model.process import Posture, WeldProcess
from weldcore.model.weave import WeaveTemplate, WeaveType


def test_decompose_recovers_full_process():
    true = WeldProcess(
        travel_speed=4.0,
        weave=WeaveTemplate(WeaveType.ZIGZAG, amplitude=2.5, frequency=1.5),
        posture=Posture(work_angle_deg=45.0, travel_angle_deg=12.0),
        length_mm=120.0,
    )

    recovered = decompose(synthesize(true, fs=200.0))

    assert recovered.weave.type == WeaveType.ZIGZAG
    assert abs(recovered.travel_speed - 4.0) < 0.1
    assert abs(recovered.weave.amplitude - 2.5) < 0.2
    assert abs(recovered.weave.frequency - 1.5) < 0.15
    assert abs(recovered.posture.work_angle_deg - 45.0) < 0.5
    assert abs(recovered.length_mm - 120.0) < 1.0
