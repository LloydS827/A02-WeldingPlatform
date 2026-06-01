from __future__ import annotations

from ..datagen.synth import synthesize
from ..model.process import Posture, WeldProcess
from ..model.skill import ProcessSignal, SkillDataset, SkillSample, SourceType
from ..model.weave import WeaveTemplate, WeaveType
from .task import WeldingTask


def generate_straight_flat_dataset(
    task: WeldingTask,
    sample_id: str = "sim-001",
) -> SkillDataset:
    weave = WeaveTemplate(WeaveType.CRESCENT, amplitude=2.0, frequency=1.5)
    process = WeldProcess(
        travel_speed=5.0,
        weave=weave,
        posture=Posture(work_angle_deg=0.0, travel_angle_deg=10.0, stickout_mm=12.0),
        length_mm=task.source_condition.length_mm,
    )
    trajectory = synthesize(process, fs=50.0)
    signals = [
        ProcessSignal(
            t=sample.t,
            current=180.0,
            voltage=24.0,
            wire_feed=6.0,
            travel_speed=5.0,
        )
        for sample in trajectory.samples
    ]
    sample = SkillSample(
        sample_id=sample_id,
        weld_condition=task.source_condition,
        trajectory=trajectory,
        process_signals=signals,
    )
    return SkillDataset(
        dataset_id=f"{task.name}-dataset",
        source_type=SourceType.SIMULATION,
        task=task.name,
        samples=[sample],
        license_and_rights="internal synthetic MVP data",
    )
