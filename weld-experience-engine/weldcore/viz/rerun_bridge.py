from __future__ import annotations

import json

from ..model import SimulationRunRecord, SkillDataset
from ..model.experiment import TransferExperiment
from ..model.skill import SkillSample, WeldSkillPackage


def _set_rerun_time_seconds(rr, timeline: str, seconds: float) -> None:
    if hasattr(rr, "set_time_seconds"):
        rr.set_time_seconds(timeline, seconds)
        return
    rr.set_time(timeline, duration=seconds)


def log_skill_transfer(
    sample: SkillSample,
    package: WeldSkillPackage,
    experiment: TransferExperiment,
    spawn: bool = True,
) -> bool:
    try:
        import rerun as rr
    except ImportError:
        print("rerun 未安装，跳过 MVP 交互回放 (pip install rerun-sdk)")
        return False

    rr.init(f"weld-skill-transfer-{experiment.experiment_id}", spawn=spawn)
    for point in sample.trajectory.samples:
        _set_rerun_time_seconds(rr, "weld_time", point.t)
        rr.log(
            "source/tcp",
            rr.Points3D([[point.x, point.y, point.z]], colors=[[0, 128, 255]]),
        )

    for point in experiment.recomposed_trajectory.samples:
        _set_rerun_time_seconds(rr, "weld_time", point.t)
        rr.log(
            "target/transferred_tcp",
            rr.Points3D([[point.x, point.y, point.z]], colors=[[255, 128, 0]]),
        )

    rr.log("skill/package_id", rr.TextDocument(package.package_id))
    rr.log("skill/decision", rr.TextDocument(experiment.decision.value))
    return True


def log_simulation_dataset_evidence(
    dataset: SkillDataset,
    run_record: SimulationRunRecord | None = None,
    spawn: bool = True,
) -> bool:
    try:
        import rerun as rr
    except ImportError:
        print("rerun 未安装，跳过仿真证据回放 (pip install rerun-sdk)")
        return False

    rr.init(f"weld-simulation-evidence-{dataset.dataset_id}", spawn=spawn)
    rr.log("simulation/dataset_id", rr.TextDocument(dataset.dataset_id))
    rr.log("simulation/task", rr.TextDocument(dataset.task))

    if run_record is not None:
        rr.log(
            "simulation/run_record",
            rr.TextDocument(
                json.dumps(run_record.to_dict(), ensure_ascii=False, indent=2)
            ),
        )

    for sample in dataset.samples:
        sample_path = f"simulation/samples/{sample.sample_id}"
        rr.log(
            f"{sample_path}/metadata",
            rr.TextDocument(
                json.dumps(sample.metadata, ensure_ascii=False, indent=2)
            ),
        )
        for point in sample.trajectory.samples:
            _set_rerun_time_seconds(rr, "weld_time", point.t)
            rr.log(
                f"{sample_path}/tcp",
                rr.Points3D([[point.x, point.y, point.z]], colors=[[0, 128, 255]]),
            )

    return True
