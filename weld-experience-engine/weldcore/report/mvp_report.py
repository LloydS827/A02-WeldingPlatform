from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..sim.adapters.maniskill import ManiSkillAdapterSpec
from ..sim.simlite import generate_straight_flat_dataset
from ..sim.task import straight_flat_task
from ..transfer.evaluate import evaluate_transfer
from ..transfer.package import package_from_sample
from ..transfer.rules import apply_transfer
from .generate import _jsonable, _save_plot


def run_mvp_report(outdir: str | Path = "mvp_report_out") -> dict[str, Any]:
    outpath = Path(outdir)
    outpath.mkdir(parents=True, exist_ok=True)

    task = straight_flat_task()
    dataset = generate_straight_flat_dataset(task)
    sample = dataset.samples[0]
    package = package_from_sample(sample, "pkg-straight-flat-001")
    transferred = apply_transfer(package, task.target_condition)
    experiment = evaluate_transfer(
        "exp-straight-flat-001",
        package,
        task.source_condition,
        task.target_condition,
        transferred,
    )
    adapter = ManiSkillAdapterSpec()

    evidence = {
        "dataset": dataset.to_dict(),
        "skill_package": package.to_dict(),
        "experiment": experiment.to_dict(),
        "rerun_boundary": {
            "runtime_required": False,
            "module": "weldcore.viz.rerun_bridge.log_skill_transfer",
            "purpose": "optional playback and annotation boundary",
        },
        "maniskill_boundary": {
            "name": adapter.name,
            "required_dependency": adapter.required_dependency,
            "mvp_role": adapter.mvp_role,
            "runtime_required": adapter.runtime_required,
        },
    }

    with (outpath / "evidence.json").open("w", encoding="utf-8") as f:
        json.dump(_jsonable(evidence), f, ensure_ascii=False, indent=2)

    with (outpath / "metrics.csv").open("w", encoding="utf-8") as f:
        f.write("experiment_id,decision,trajectory_rms_mm,posture_error_deg,process_current_error\n")
        f.write(
            f"{experiment.experiment_id},{experiment.decision.value},"
            f"{experiment.metrics.trajectory_rms_mm},"
            f"{experiment.metrics.posture_error_deg},"
            f"{experiment.metrics.process_current_error}\n"
        )

    _save_plot(
        str(outpath / "transfer_summary.png"),
        [
            ([(p.x, p.y) for p in sample.trajectory.samples], "source"),
            ([(p.x, p.y) for p in transferred.samples], "target transfer"),
        ],
        xlabel="travel x (mm)",
        ylabel="weave y (mm)",
        title=f"MVP transfer decision={experiment.decision.value}",
    )

    (outpath / "ip_notes.md").write_text(
        "\n".join(
            [
                "# 焊接技能迁移 MVP IP Notes",
                "",
                "## 专利线索",
                "- 结构化焊接技能包与条件迁移规则。",
                "- 仿真样本、专家知识与可选真机数据融合的技能迁移方法。",
                "- 基于 Rerun 边界的多源焊接数据回放与人机确认流程。",
                "",
                "## 论文线索",
                "- 仿真驱动的焊接机器人技能数据集构建方法。",
                "- 焊接动作、姿态与工艺参数联合迁移的轻量评测协议。",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print("=== 焊接技能迁移 MVP 证据摘要 ===")
    print(f"数据集: {dataset.dataset_id}")
    print(f"技能包: {package.package_id}")
    print(f"迁移决策: {experiment.decision.value}")
    print(f"轨迹 RMS: {experiment.metrics.trajectory_rms_mm:.4f} mm")
    return evidence


if __name__ == "__main__":
    run_mvp_report()
