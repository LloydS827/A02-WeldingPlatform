from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ..knowledge.manifest import DEFAULT_FOUNDATION_ROOT
from ..simulation_bakeoff import run_minimal_simulation_bakeoff
from ..simulation_bakeoff.model import SimulationEvidenceBundle
from ..viz.rerun_bridge import log_simulation_dataset_evidence


DEFAULT_DOCS_REPORT_DIR = DEFAULT_FOUNDATION_ROOT / "reports"


ROUTE_LABELS = {
    "simlite_reference": "R0 / simlite reference",
    "maniskill_sapien": "ManiSkill/SAPIEN",
    "gazebo_moveit": "Gazebo/MoveIt",
}


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_simulation_bakeoff_report(
    outdir: str | Path = "simulation_bakeoff_report_out",
    docs_report_dir: str | Path | None = DEFAULT_DOCS_REPORT_DIR,
) -> dict[str, Any]:
    outpath = Path(outdir)
    outpath.mkdir(parents=True, exist_ok=True)

    result = run_minimal_simulation_bakeoff()
    tasks = [task_spec.to_dict() for task_spec in result.task_specs]
    evidence_bundles = [bundle.to_dict() for bundle in result.evidence_bundles]
    scorecard = result.scorecard.to_dict()
    rerun_replay = _attempt_first_rerun_replay(result.evidence_bundles)

    evidence = {
        "tasks": tasks,
        "evidence_bundles": evidence_bundles,
        "scorecard": scorecard,
        "rerun_replay": rerun_replay,
    }

    _write_json(outpath / "tasks.json", tasks)
    _write_json(outpath / "evidence_bundles.json", evidence_bundles)
    _write_json(outpath / "scorecard.json", scorecard)
    _write_report_markdown(outpath / "report.md", evidence)

    if docs_report_dir is not None:
        docs_path = Path(docs_report_dir)
        docs_path.mkdir(parents=True, exist_ok=True)
        _write_report_markdown(docs_path / "simulation_bakeoff_evidence.md", evidence)

    print("=== WeldSkillUnit 仿真 bake-off 证据摘要 ===")
    print(f"task_count: {len(tasks)}")
    print(f"evidence_bundle_count: {len(evidence_bundles)}")
    print(f"final_simulator_selected: {scorecard['final_simulator_selected']}")
    print(f"rerun_replay_status: {rerun_replay['status']}")
    print(f"报告目录: {outpath}")
    return evidence


def _attempt_first_rerun_replay(
    evidence_bundles: tuple[SimulationEvidenceBundle, ...],
) -> dict[str, Any]:
    for bundle in evidence_bundles:
        if bundle.adapter_result.status == "completed" and bundle.dataset is not None:
            try:
                logged = log_simulation_dataset_evidence(
                    bundle.dataset,
                    bundle.run_record,
                    spawn=False,
                )
            except Exception as exc:  # pragma: no cover - exact optional SDK failures vary.
                return {
                    "attempted": True,
                    "status": "skipped",
                    "uri": None,
                    "skip_reason": f"{exc.__class__.__name__}: {exc}",
                    "bundle_id": bundle.bundle_id,
                    "dataset_id": bundle.dataset.dataset_id,
                    "task_id": bundle.task_spec.task_id,
                    "adapter_name": bundle.adapter_result.adapter_name,
                }

            if logged:
                uri = f"rerun://weld-simulation-evidence-{bundle.dataset.dataset_id}"
                return {
                    "attempted": True,
                    "status": "logged",
                    "uri": uri,
                    "skip_reason": None,
                    "bundle_id": bundle.bundle_id,
                    "dataset_id": bundle.dataset.dataset_id,
                    "task_id": bundle.task_spec.task_id,
                    "adapter_name": bundle.adapter_result.adapter_name,
                }

            return {
                "attempted": True,
                "status": "skipped",
                "uri": None,
                "skip_reason": "rerun_sdk_unavailable_or_logging_skipped",
                "bundle_id": bundle.bundle_id,
                "dataset_id": bundle.dataset.dataset_id,
                "task_id": bundle.task_spec.task_id,
                "adapter_name": bundle.adapter_result.adapter_name,
            }

    return {
        "attempted": False,
        "status": "skipped",
        "uri": None,
        "skip_reason": "no_completed_dataset_bundle",
        "bundle_id": None,
        "dataset_id": None,
        "task_id": None,
        "adapter_name": None,
    }


def _write_report_markdown(path: Path, evidence: dict[str, Any]) -> None:
    tasks = evidence["tasks"]
    evidence_bundles = evidence["evidence_bundles"]
    scorecard = evidence["scorecard"]
    rerun_replay = evidence["rerun_replay"]
    bundles_by_route = _group_bundles_by_route(evidence_bundles)

    lines = [
        "# WeldSkillUnit Simulation Bake-off Evidence",
        "",
        "## Summary",
        "",
        f"- task_count: {len(tasks)}",
        f"- evidence_bundle_count: {len(evidence_bundles)}",
        f"- final_simulator_selected: {scorecard['final_simulator_selected']}",
        f"- recommendation: `{scorecard['recommendation']}`",
        f"- rerun_replay_status: `{rerun_replay['status']}`",
        "",
        "本报告用于记录 WeldSkillUnit 最小仿真 bake-off 证据；当前结论不是最终仿真器选择。",
        "外部仿真器失败被记录为 failure boundary，不作为默认工作流错误。",
        "",
        "## WeldSkillUnit Tasks",
        "",
        "| task_id | unit_id | name |",
        "| --- | --- | --- |",
    ]
    for task in tasks:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{task['task_id']}`",
                    f"`{task['unit_id']}`",
                    _escape_markdown_table(str(task["name"])),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Route Summary",
            "",
            "| route | task_count | completed | failed | score | failure_boundaries |",
            "| --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for route_name in ("simlite_reference", "maniskill_sapien", "gazebo_moveit"):
        route_bundles = bundles_by_route.get(route_name, [])
        completed = sum(
            1 for bundle in route_bundles if bundle["adapter_result"]["status"] == "completed"
        )
        failed = sum(
            1 for bundle in route_bundles if bundle["adapter_result"]["status"] == "failed"
        )
        boundaries = sorted(
            {
                boundary
                for bundle in route_bundles
                for boundary in bundle["adapter_result"].get("failure_boundary", [])
            }
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    ROUTE_LABELS[route_name],
                    str(len(route_bundles)),
                    str(completed),
                    str(failed),
                    str(scorecard["route_scores"][route_name]),
                    _escape_markdown_table(", ".join(boundaries) if boundaries else "none"),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Scorecard",
            "",
            "| route | digital_asset_writeback | robot_executability | skill_unit_expression | engineering_access_cost | weighted_score |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for route_name in ("simlite_reference", "maniskill_sapien", "gazebo_moveit"):
        dimensions = scorecard["route_dimension_scores"][route_name]
        lines.append(
            "| "
            + " | ".join(
                [
                    ROUTE_LABELS[route_name],
                    str(dimensions["digital_asset_writeback"]),
                    str(dimensions["robot_executability"]),
                    str(dimensions["skill_unit_expression"]),
                    str(dimensions["engineering_access_cost"]),
                    str(scorecard["route_scores"][route_name]),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Rerun Replay",
            "",
            f"- attempted: {rerun_replay['attempted']}",
            f"- Rerun replay status: `{rerun_replay['status']}`",
            f"- rerun_replay_status: `{rerun_replay['status']}`",
            f"- dataset_id: `{rerun_replay['dataset_id']}`",
            f"- bundle_id: `{rerun_replay['bundle_id']}`",
            f"- uri: `{rerun_replay['uri']}`",
            f"- skip_reason: `{rerun_replay['skip_reason']}`",
            "",
            "## Evidence Boundaries",
            "",
            "- 不是最终仿真器选择。",
            "- 不证明真实焊接质量。",
            "- 不替代 WPS/PQR。",
            "- R0/simlite reference 只提供平台内可复现基线。",
            "- ManiSkill/SAPIEN 与 Gazebo/MoveIt 的外部依赖失败记录为 failure boundary，不破坏默认报告命令。",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _group_bundles_by_route(
    evidence_bundles: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    bundles_by_route: dict[str, list[dict[str, Any]]] = {}
    for bundle in evidence_bundles:
        route_name = bundle["adapter_result"]["adapter_name"]
        bundles_by_route.setdefault(route_name, []).append(bundle)
    return bundles_by_route


def _escape_markdown_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="生成仿真 bake-off 证据报告。")
    parser.add_argument("--outdir", default="simulation_bakeoff_report_out")
    parser.add_argument(
        "--docs-report-dir",
        default=str(DEFAULT_DOCS_REPORT_DIR),
        help="同步刷新的 docs 报告目录。",
    )
    parser.add_argument(
        "--no-docs-copy",
        action="store_true",
        help="只写 runtime 输出目录，不刷新 docs 报告副本。",
    )
    args = parser.parse_args(argv)
    docs_report_dir = None if args.no_docs_copy else args.docs_report_dir
    run_simulation_bakeoff_report(args.outdir, docs_report_dir=docs_report_dir)


if __name__ == "__main__":
    main()
