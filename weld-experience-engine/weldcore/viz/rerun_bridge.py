from __future__ import annotations

from ..model.experiment import TransferExperiment
from ..model.skill import SkillSample, WeldSkillPackage


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
        rr.set_time_seconds("weld_time", point.t)
        rr.log(
            "source/tcp",
            rr.Points3D([[point.x, point.y, point.z]], colors=[[0, 128, 255]]),
        )

    for point in experiment.recomposed_trajectory.samples:
        rr.set_time_seconds("weld_time", point.t)
        rr.log(
            "target/transferred_tcp",
            rr.Points3D([[point.x, point.y, point.z]], colors=[[255, 128, 0]]),
        )

    rr.log("skill/package_id", rr.TextDocument(package.package_id))
    rr.log("skill/decision", rr.TextDocument(experiment.decision.value))
    return True
