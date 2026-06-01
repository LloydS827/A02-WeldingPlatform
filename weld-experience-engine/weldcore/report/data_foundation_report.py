from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from ..knowledge.foundation import (
    DataFoundation,
    PublicAccess,
    ShipbuildingRelevanceLevel,
)
from ..knowledge.manifest import DEFAULT_FOUNDATION_ROOT, load_data_foundation


DEFAULT_DOCS_REPORT_DIR = DEFAULT_FOUNDATION_ROOT / "reports"


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _summary(foundation: DataFoundation) -> dict[str, int]:
    source_by_id = {source.source_id: source for source in foundation.sources}
    return {
        "source_count": len(foundation.sources),
        "public_source_count": sum(
            source.public_access == PublicAccess.PUBLIC for source in foundation.sources
        ),
        "strong_shipbuilding_source_count": sum(
            source.shipbuilding_relevance_level == ShipbuildingRelevanceLevel.STRONG
            for source in foundation.sources
        ),
        "dataset_count": len(foundation.datasets),
        "public_dataset_count": sum(
            dataset.source_id in source_by_id
            and source_by_id[dataset.source_id].public_access == PublicAccess.PUBLIC
            for dataset in foundation.datasets
        ),
        "ready_task_count": sum(entry.ready_for_plan() for entry in foundation.task_evidence),
    }


def run_data_foundation_report(
    outdir: str | Path = "data_foundation_report_out",
    foundation: DataFoundation | None = None,
    docs_report_dir: str | Path | None = None,
) -> dict[str, Any]:
    outpath = Path(outdir)
    outpath.mkdir(parents=True, exist_ok=True)

    data_foundation = foundation or load_data_foundation()
    gate = data_foundation.validate()
    if not gate.passed:
        raise ValueError("Data foundation gate failed: " + "; ".join(gate.issues))

    summary = _summary(data_foundation)
    sources = [source.to_dict() for source in data_foundation.sources]
    datasets = [dataset.to_dict() for dataset in data_foundation.datasets]
    field_coverage = [row.to_dict() for row in data_foundation.field_coverage or []]
    tasks = [entry.to_dict() for entry in data_foundation.task_evidence]
    evidence = {
        "summary": summary,
        "sources": sources,
        "datasets": datasets,
        "field_coverage": field_coverage,
        "task_evidence": tasks,
    }

    _write_json(outpath / "sources.json", sources)
    _write_json(outpath / "datasets.json", datasets)
    _write_json(outpath / "task_evidence_map.json", tasks)
    _write_field_coverage_csv(outpath / "field_coverage.csv", data_foundation)
    _write_evidence_markdown(outpath / "evidence.md", data_foundation, summary)
    _write_plan_input(
        outpath / "synthetic_skilldataset_v2_plan_input.md",
        data_foundation,
        summary,
    )

    if docs_report_dir is not None:
        docs_path = Path(docs_report_dir)
        docs_path.mkdir(parents=True, exist_ok=True)
        _write_evidence_markdown(
            docs_path / "data_foundation_evidence.md",
            data_foundation,
            summary,
        )
        _write_plan_input(
            docs_path / "synthetic_skilldataset_v2_plan_input.md",
            data_foundation,
            summary,
        )

    print("=== 数据集与资料底座证据摘要 ===")
    print(f"资料来源总数: {summary['source_count']}")
    print(f"公开资料来源: {summary['public_source_count']}")
    print(f"强船舶相关来源: {summary['strong_shipbuilding_source_count']}")
    print(f"数据集总数: {summary['dataset_count']}")
    print(f"公开数据集: {summary['public_dataset_count']}")
    print(f"可进入 SyntheticSkillDataset v2 规划的任务族: {summary['ready_task_count']}")
    print(f"报告目录: {outpath}")
    return evidence


def _write_field_coverage_csv(path: Path, foundation: DataFoundation) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["field_name", "source_ids", "dataset_ids", "coverage_role", "notes"]
        )
        for row in foundation.field_coverage or []:
            writer.writerow(
                [
                    row.field_name,
                    ";".join(row.source_ids),
                    ";".join(row.dataset_ids),
                    row.coverage_role,
                    row.notes,
                ]
            )


def _write_evidence_markdown(
    path: Path,
    foundation: DataFoundation,
    summary: dict[str, int],
) -> None:
    lines = [
        "# 数据集与资料底座证据报告",
        "",
        "## 结论",
        "",
        "- 本报告是资料、数据集、字段覆盖和任务证据门禁，用于后续 SyntheticSkillDataset v2 规划。",
        "- 本报告不声称真实焊接质量验证，不替代船厂 WPS、实测生产数据或设备控制参数确认。",
        "- 公开来源仅作为场景、字段、schema 和任务边界证据；内部资料仅作为项目字段定义和需求边界。",
        "",
        "## 汇总",
        "",
        f"- 资料来源总数：{summary['source_count']}",
        f"- 公开资料来源：{summary['public_source_count']}",
        f"- 强船舶相关来源：{summary['strong_shipbuilding_source_count']}",
        f"- 数据集总数：{summary['dataset_count']}",
        f"- 公开数据集：{summary['public_dataset_count']}",
        f"- 可进入 SyntheticSkillDataset v2 规划的任务族：{summary['ready_task_count']}",
        "",
        "## 资料来源证据",
        "",
        "| source_id | title | url | 船舶相关性 | 使用边界 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for source in foundation.sources:
        lines.append(
            "| "
            + " | ".join(
                [
                    source.source_id,
                    _escape_markdown_table(source.title),
                    source.url,
                    _escape_markdown_table(source.shipbuilding_relevance),
                    _escape_markdown_table(source.use_boundary),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## 数据集证据",
            "",
            "| dataset_id | source_id | 模态 | schema 摘要 | 使用边界 |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for dataset in foundation.datasets:
        lines.append(
            "| "
            + " | ".join(
                [
                    dataset.dataset_id,
                    dataset.source_id,
                    ", ".join(modality.value for modality in dataset.modalities),
                    _escape_markdown_table(dataset.schema_summary),
                    _escape_markdown_table(dataset.use_boundary),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## 任务证据门禁",
            "",
            "| family_id | readiness | 支撑来源 | 支撑数据集 | 下一步 |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for entry in foundation.task_evidence:
        lines.append(
            "| "
            + " | ".join(
                [
                    entry.family_id,
                    entry.readiness.value,
                    "<br>".join(entry.supporting_source_ids),
                    "<br>".join(entry.supporting_dataset_ids) or "无",
                    _escape_markdown_table(entry.next_action),
                ]
            )
            + " |"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_plan_input(
    path: Path,
    foundation: DataFoundation,
    summary: dict[str, int],
) -> None:
    ready_entries = [entry for entry in foundation.task_evidence if entry.ready_for_plan()]
    source_by_id = {source.source_id: source for source in foundation.sources}
    dataset_by_id = {dataset.dataset_id: dataset for dataset in foundation.datasets}

    lines = [
        "# SyntheticSkillDataset v2 规划输入",
        "",
        "## 使用边界",
        "",
        "- 该文件只把通过资料底座门禁的任务族整理为后续合成数据规划输入。",
        "- 参数值、质量结论和设备控制策略仍需后续真实工艺、仿真和人工审核确认。",
        "- 假设字段必须在样本 schema 中显式标注，不得包装成实测字段。",
        "",
        "## 门禁汇总",
        "",
        f"- 资料来源总数：{summary['source_count']}",
        f"- 公开数据集：{summary['public_dataset_count']}",
        f"- ready 任务族：{summary['ready_task_count']}",
        "",
        "## ready 任务族输入",
        "",
    ]
    for index, entry in enumerate(ready_entries, start=1):
        lines.extend(
            [
                f"### {index}. {entry.family_id}",
                "",
                f"- readiness：{entry.readiness.value}",
                f"- 必需字段：{', '.join(entry.required_fields)}",
                f"- 已覆盖字段：{', '.join(entry.covered_required_fields)}",
                f"- 假设字段：{', '.join(entry.assumption_fields) or '无'}",
                "- 支撑来源：",
            ]
        )
        for source_id in entry.supporting_source_ids:
            source = source_by_id[source_id]
            lines.append(
                f"  - {source.source_id}｜{source.title}｜边界：{source.use_boundary}"
            )
        lines.append("- 支撑数据集：")
        if entry.supporting_dataset_ids:
            for dataset_id in entry.supporting_dataset_ids:
                dataset = dataset_by_id[dataset_id]
                lines.append(
                    f"  - {dataset.dataset_id}｜{dataset.schema_summary}｜边界：{dataset.use_boundary}"
                )
        else:
            lines.append("  - 无")
        lines.extend(
            [
                f"- 下一步：{entry.next_action}",
                "",
            ]
        )

    path.write_text("\n".join(lines), encoding="utf-8")


def _escape_markdown_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def main(argv: list[str] | None = None) -> dict[str, Any]:
    parser = argparse.ArgumentParser(description="生成数据集与资料底座证据报告。")
    parser.add_argument("--outdir", default="data_foundation_report_out")
    parser.add_argument(
        "--docs-report-dir",
        default=str(DEFAULT_DOCS_REPORT_DIR),
        help="同步刷新的 docs 报告目录；传入空字符串可跳过。",
    )
    args = parser.parse_args(argv)
    docs_report_dir = args.docs_report_dir or None
    return run_data_foundation_report(args.outdir, docs_report_dir=docs_report_dir)


if __name__ == "__main__":
    main()
