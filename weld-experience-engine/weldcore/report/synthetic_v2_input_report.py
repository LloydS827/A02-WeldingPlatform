from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from ..knowledge.manifest import DEFAULT_FOUNDATION_ROOT
from ..knowledge.synthetic_input import (
    FORBIDDEN_POOL_TERMS,
    SyntheticInputFoundation,
    SyntheticValueStatus,
)
from ..knowledge.synthetic_manifest import load_synthetic_input_foundation


DEFAULT_DOCS_REPORT_DIR = DEFAULT_FOUNDATION_ROOT / "reports"


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _summary(foundation: SyntheticInputFoundation) -> dict[str, int]:
    return {
        "task_taxonomy_count": len(foundation.task_taxonomy),
        "ready_task_count": sum(entry.ready_for_plan() for entry in foundation.task_taxonomy),
        "procedure_field_count": len(foundation.procedure_fields),
        "required_procedure_field_count": sum(
            field.required for field in foundation.procedure_fields
        ),
        "simulation_input_count": len(foundation.simulation_inputs),
        "evidence_binding_count": sum(
            len(simulation_input.evidence_bindings)
            for simulation_input in foundation.simulation_inputs
        ),
    }


def run_synthetic_v2_input_report(
    outdir: str | Path = "synthetic_v2_input_report_out",
    foundation: SyntheticInputFoundation | None = None,
    docs_report_dir: str | Path | None = None,
) -> dict[str, Any]:
    outpath = Path(outdir)
    outpath.mkdir(parents=True, exist_ok=True)

    synthetic_foundation = foundation or load_synthetic_input_foundation()
    gate = synthetic_foundation.validate()
    structural_issues = _structural_gate_issues(synthetic_foundation)
    issues = [*gate.issues, *structural_issues]
    if issues:
        raise ValueError("Synthetic v2 input gate failed: " + "; ".join(issues))

    summary = _summary(synthetic_foundation)
    task_taxonomy = [entry.to_dict() for entry in synthetic_foundation.task_taxonomy]
    procedure_fields = [field.to_dict() for field in synthetic_foundation.procedure_fields]
    simulation_inputs = [
        simulation_input.to_dict()
        for simulation_input in synthetic_foundation.simulation_inputs
    ]
    _raise_if_forbidden_runtime_json(
        {
            "task_taxonomy": task_taxonomy,
            "procedure_fields": procedure_fields,
            "simulation_inputs": simulation_inputs,
        }
    )

    evidence = {
        "summary": summary,
        "task_taxonomy": task_taxonomy,
        "procedure_fields": procedure_fields,
        "simulation_inputs": simulation_inputs,
    }

    _write_json(outpath / "task_taxonomy.json", task_taxonomy)
    _write_json(outpath / "procedure_fields.json", procedure_fields)
    _write_json(outpath / "simulation_inputs.json", simulation_inputs)
    _write_evidence_bindings_csv(
        outpath / "evidence_bindings.csv",
        synthetic_foundation,
    )
    _write_evidence_markdown(outpath / "evidence.md", synthetic_foundation, summary)

    if docs_report_dir is not None:
        docs_path = Path(docs_report_dir)
        docs_path.mkdir(parents=True, exist_ok=True)
        _write_evidence_markdown(
            docs_path / "synthetic_v2_input_evidence.md",
            synthetic_foundation,
            summary,
        )

    print("=== SyntheticSkillDataset v2 输入证据摘要 ===")
    print(f"任务分类总数: {summary['task_taxonomy_count']}")
    print(f"ready 任务族: {summary['ready_task_count']}")
    print(f"工艺字段总数: {summary['procedure_field_count']}")
    print(f"首批仿真输入: {summary['simulation_input_count']}")
    print(f"证据绑定总数: {summary['evidence_binding_count']}")
    print(f"报告目录: {outpath}")
    return evidence


def _structural_gate_issues(foundation: SyntheticInputFoundation) -> list[str]:
    issues: list[str] = []
    if not foundation.task_taxonomy:
        issues.append("missing task taxonomy")
    if not foundation.procedure_fields:
        issues.append("missing procedure fields")
    if not foundation.simulation_inputs:
        issues.append("missing simulation inputs")
    if not any(entry.ready_for_plan() for entry in foundation.task_taxonomy):
        issues.append("no ready task taxonomy entries")
    return issues


def _raise_if_forbidden_runtime_json(data: Any) -> None:
    text = json.dumps(data, ensure_ascii=False).lower()
    matches = [term for term in FORBIDDEN_POOL_TERMS if term in text]
    if matches:
        raise ValueError(
            "Synthetic v2 input gate failed: forbidden runtime JSON term "
            + ", ".join(matches)
        )


def _write_evidence_bindings_csv(
    path: Path,
    foundation: SyntheticInputFoundation,
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "input_id",
                "taxonomy_ref",
                "field_path",
                "source_id",
                "evidence_role",
                "value_status",
                "notes",
            ]
        )
        for simulation_input in foundation.simulation_inputs:
            for binding in simulation_input.evidence_bindings:
                writer.writerow(
                    [
                        simulation_input.input_id,
                        simulation_input.taxonomy_ref,
                        binding.field_path,
                        binding.source_id,
                        binding.evidence_role.value,
                        binding.value_status.value,
                        binding.notes,
                    ]
                )


def _write_evidence_markdown(
    path: Path,
    foundation: SyntheticInputFoundation,
    summary: dict[str, int],
) -> None:
    lines = [
        "# SyntheticSkillDataset v2 输入证据报告",
        "",
        "## Summary",
        "",
        "- 本报告把通过 Task 3 manifest/loader 门禁的 synthetic v2 输入整理为可审计报告。",
        "- 这些输入用于 SyntheticSkillDataset v2 首批生成前设计，不是 WPS/PQR。",
        "- 本报告不证明真实焊接质量，不替代真实工艺评定、船厂实测数据或设备控制程序确认。",
        "",
        f"- 任务分类总数：{summary['task_taxonomy_count']}",
        f"- ready 任务族：{summary['ready_task_count']}",
        f"- 工艺字段总数：{summary['procedure_field_count']}",
        f"- 必填工艺字段：{summary['required_procedure_field_count']}",
        f"- 首批仿真输入：{summary['simulation_input_count']}",
        f"- 证据绑定总数：{summary['evidence_binding_count']}",
        "",
        "## 复现命令",
        "",
        "```bash",
        "python -m weldcore.report.synthetic_v2_input_report",
        "```",
        "",
        "## Task Taxonomy",
        "",
        "| family_id | readiness | joint_type | weld_position | motion_structure | notes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for entry in foundation.task_taxonomy:
        lines.append(
            "| "
            + " | ".join(
                [
                    entry.family_id,
                    entry.readiness.value,
                    entry.joint_type,
                    entry.weld_position,
                    _escape_markdown_table(entry.motion_structure),
                    _escape_markdown_table(entry.notes),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## First-Batch Inputs",
            "",
            "| input_id | taxonomy_ref | procedure fields | evidence bindings | boundaries |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for simulation_input in foundation.simulation_inputs:
        lines.append(
            "| "
            + " | ".join(
                [
                    simulation_input.input_id,
                    simulation_input.taxonomy_ref,
                    str(len(simulation_input.procedure_fields)),
                    str(len(simulation_input.evidence_bindings)),
                    _escape_markdown_table("; ".join(simulation_input.generation_boundary)),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Assumption Fields",
            "",
            "| input_id | field_path | source_id | role | status | notes |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for simulation_input in foundation.simulation_inputs:
        for binding in simulation_input.evidence_bindings:
            if binding.value_status in {
                SyntheticValueStatus.ASSUMED,
                SyntheticValueStatus.GENERATED,
                SyntheticValueStatus.UNKNOWN,
            }:
                lines.append(_binding_table_row(simulation_input.input_id, binding))

    lines.extend(
        [
            "",
            "## Real-Validation Fields",
            "",
            "| input_id | field_path | source_id | role | status | notes |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for simulation_input in foundation.simulation_inputs:
        for binding in simulation_input.evidence_bindings:
            if binding.value_status == SyntheticValueStatus.REQUIRES_REAL_VALIDATION_LATER:
                lines.append(_binding_table_row(simulation_input.input_id, binding))

    lines.extend(
        [
            "",
            "## 边界说明",
            "",
            "- 不是 WPS/PQR：本报告只给出 synthetic v2 输入证据绑定和字段边界。",
            "- 不证明真实焊接质量：quality/inspection/defect 字段只是标签 schema 或待验证占位。",
            "- 不重建客户机器人程序、控制器程序或真实生产参数。",
            "- SyntheticSkillDataset v2 后续样本必须保留 assumption 与 requires_real_validation_later 标记。",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _binding_table_row(input_id: str, binding: Any) -> str:
    return (
        "| "
        + " | ".join(
            [
                input_id,
                binding.field_path,
                binding.source_id,
                binding.evidence_role.value,
                binding.value_status.value,
                _escape_markdown_table(binding.notes),
            ]
        )
        + " |"
    )


def _escape_markdown_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def main(argv: list[str] | None = None) -> dict[str, Any]:
    parser = argparse.ArgumentParser(
        description="生成 SyntheticSkillDataset v2 输入证据报告。"
    )
    parser.add_argument("--outdir", default="synthetic_v2_input_report_out")
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
    return run_synthetic_v2_input_report(args.outdir, docs_report_dir=docs_report_dir)


if __name__ == "__main__":
    main()
