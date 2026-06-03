from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ..ingest import import_simulation_bundle, validate_simulation_bundle
from ..knowledge.manifest import DEFAULT_FOUNDATION_ROOT
from ..knowledge.synthetic_input import (
    SyntheticInputFoundation,
    SyntheticValueStatus,
)
from ..knowledge.synthetic_manifest import load_synthetic_input_foundation
from ..sim import write_simlite_bundle


DEFAULT_DOCS_REPORT_DIR = DEFAULT_FOUNDATION_ROOT / "reports"


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_simulation_ingest_report(
    outdir: str | Path = "simulation_ingest_report_out",
    docs_report_dir: str | Path | None = None,
    input_id: str = "input-panel-butt-001",
) -> dict[str, Any]:
    outpath = Path(outdir)
    outpath.mkdir(parents=True, exist_ok=True)

    foundation = load_synthetic_input_foundation()
    bundle = write_simlite_bundle(
        outpath / "bundles",
        input_id=input_id,
        sample_count=1,
        seed=7,
        foundation=foundation,
    )

    gate = validate_simulation_bundle(bundle, foundation=foundation)
    if not gate.passed:
        raise ValueError("Simulation ingest gate failed: " + "; ".join(gate.issues))

    import_result = import_simulation_bundle(bundle, foundation=foundation)
    run_record = import_result.run_record.to_dict()
    bundle_manifest = _load_json(bundle / "manifest.json")
    dataset = import_result.dataset.to_dict()

    simulation_input = _simulation_input_by_id(foundation, input_id)
    evidence_bindings = [binding.to_dict() for binding in simulation_input.evidence_bindings]
    assumption_bindings = [
        binding
        for binding in evidence_bindings
        if binding["value_status"]
        in {
            SyntheticValueStatus.ASSUMED.value,
            SyntheticValueStatus.GENERATED.value,
            SyntheticValueStatus.UNKNOWN.value,
        }
    ]
    real_validation_bindings = [
        binding
        for binding in evidence_bindings
        if binding["value_status"]
        == SyntheticValueStatus.REQUIRES_REAL_VALIDATION_LATER.value
    ]

    sample_summary = _build_sample_summary(dataset)
    input_alignment = _build_input_alignment(bundle_manifest, dataset, import_result.gate)
    warnings = list(run_record.get("warnings", []))
    errors = list(run_record.get("errors", []))

    evidence = {
        "summary": {
            "simulation_run_id": run_record["simulation_run_id"],
            "bundle_id": bundle_manifest["bundle_id"],
            "input_id": input_id,
            "taxonomy_ref": bundle_manifest["taxonomy_ref"],
            "sample_count": len(dataset["samples"]),
            "dataset_id": dataset["dataset_id"],
            "evidence_binding_count": len(evidence_bindings),
            "assumption_field_count": len(assumption_bindings),
            "real_validation_field_count": len(real_validation_bindings),
            "can_extract_skill_package": _can_extract_skill_package(
                bundle_manifest, dataset, import_result.gate
            ),
        },
        "run_record": run_record,
        "bundle_manifest": bundle_manifest,
        "dataset": dataset,
        "sample_summary": sample_summary,
        "input_alignment": input_alignment,
        "evidence_bindings": evidence_bindings,
        "assumption_bindings": assumption_bindings,
        "real_validation_bindings": real_validation_bindings,
        "warnings": warnings,
        "errors": errors,
    }

    _write_json(outpath / "run_record.json", run_record)
    _write_json(outpath / "bundle_manifest.json", bundle_manifest)
    _write_json(outpath / "dataset.json", dataset)
    _write_evidence_markdown(outpath / "evidence.md", evidence)

    if docs_report_dir is not None:
        docs_path = Path(docs_report_dir)
        docs_path.mkdir(parents=True, exist_ok=True)
        _write_evidence_markdown(docs_path / "simulation_ingest_evidence.md", evidence)

    print("=== 仿真输出接入证据摘要 ===")
    print(f"simulation_run_id: {run_record['simulation_run_id']}")
    print(f"bundle_id: {bundle_manifest['bundle_id']}")
    print(f"input_id: {input_id}")
    print(f"sample_count: {len(dataset['samples'])}")
    print(f"报告目录: {outpath}")
    return evidence


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _simulation_input_by_id(
    foundation: SyntheticInputFoundation,
    input_id: str,
):
    for simulation_input in foundation.simulation_inputs:
        if simulation_input.input_id == input_id:
            return simulation_input
    raise KeyError(input_id)


def _build_sample_summary(dataset: dict[str, Any]) -> dict[str, Any]:
    samples = dataset.get("samples", [])
    sample_rows = []
    trajectory_point_count = 0
    process_signal_count = 0
    for sample in samples:
        trajectory = sample.get("trajectory", {}).get("samples", [])
        process_signals = sample.get("process_signals", [])
        trajectory_count = len(trajectory)
        process_count = len(process_signals)
        trajectory_point_count += trajectory_count
        process_signal_count += process_count
        sample_rows.append(
            {
                "sample_id": sample.get("sample_id", ""),
                "trajectory_point_count": trajectory_count,
                "process_signal_count": process_count,
                "has_quality_observation": sample.get("quality_observation") is not None,
            }
        )

    return {
        "sample_count": len(samples),
        "trajectory_point_count": trajectory_point_count,
        "process_signal_count": process_signal_count,
        "samples": sample_rows,
    }


def _build_input_alignment(
    bundle_manifest: dict[str, Any],
    dataset: dict[str, Any],
    gate: Any,
) -> dict[str, Any]:
    sample_count_matches = len(dataset.get("samples", [])) == bundle_manifest.get("sample_count")
    return {
        "bundle_input_id": bundle_manifest.get("input_id"),
        "dataset_source_type": dataset.get("source_type"),
        "dataset_schema_version": dataset.get("schema_version"),
        "bundle_schema_version": bundle_manifest.get("schema_version"),
        "sample_count_matches": sample_count_matches,
        "bundle_is_importable": bool(getattr(gate, "passed", False)),
        "bundle_issues": list(getattr(gate, "issues", [])),
    }


def _can_extract_skill_package(
    bundle_manifest: dict[str, Any],
    dataset: dict[str, Any],
    gate: Any,
) -> bool:
    return bool(
        getattr(gate, "passed", False)
        and bundle_manifest.get("source_type") == "simulation"
        and dataset.get("source_type") == "simulation"
        and dataset.get("schema_version") == "synthetic-v2-dataset-v0.1"
        and len(dataset.get("samples", [])) >= 1
    )


def _binding_table_row(binding: dict[str, Any]) -> str:
    return (
        "| "
        + " | ".join(
            [
                str(binding.get("field_path", "")),
                str(binding.get("source_id", "")),
                str(binding.get("evidence_role", "")),
                str(binding.get("value_status", "")),
                _escape_markdown_table(str(binding.get("notes", ""))),
            ]
        )
        + " |"
    )


def _escape_markdown_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _write_evidence_markdown(path: Path, evidence: dict[str, Any]) -> None:
    summary = evidence["summary"]
    bundle_manifest = evidence["bundle_manifest"]
    dataset = evidence["dataset"]
    sample_summary = evidence["sample_summary"]
    input_alignment = evidence["input_alignment"]

    lines = [
        "# Simulation Ingest Evidence Report",
        "",
        "## Run Summary",
        "",
        f"- simulation_run_id: `{summary['simulation_run_id']}`",
        f"- bundle_id: `{summary['bundle_id']}`",
        f"- input_id: `{summary['input_id']}`",
        f"- taxonomy_ref: `{summary['taxonomy_ref']}`",
        f"- sample_count: `{summary['sample_count']}`",
        f"- dataset_id: `{summary['dataset_id']}`",
        f"- evidence_binding_count: {summary['evidence_binding_count']}",
        f"- assumption_field_count: {summary['assumption_field_count']}",
        f"- real_validation_field_count: {summary['real_validation_field_count']}",
        f"- can_extract_skill_package: {summary['can_extract_skill_package']}",
        "",
        "## Bundle Summary",
        "",
        f"- bundle schema_version: `{bundle_manifest.get('schema_version', '')}`",
        f"- bundle source_type: `{bundle_manifest.get('source_type', '')}`",
        f"- simulator: `{bundle_manifest.get('simulator', '')}`",
        f"- simulator_version: `{bundle_manifest.get('simulator_version', '')}`",
        f"- adapter_version: `{bundle_manifest.get('adapter_version', '')}`",
        f"- generation_boundary: {', '.join(bundle_manifest.get('generation_boundary', []))}",
        "",
        "## Sample Summary",
        "",
        f"- samples: {sample_summary['sample_count']}",
        f"- trajectory points: {sample_summary['trajectory_point_count']}",
        f"- process signal points: {sample_summary['process_signal_count']}",
        "",
        "| sample_id | trajectory points | process signal points | quality observation |",
        "| --- | --- | --- | --- |",
    ]
    for row in sample_summary["samples"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("sample_id", "")),
                    str(row.get("trajectory_point_count", "")),
                    str(row.get("process_signal_count", "")),
                    "yes" if row.get("has_quality_observation") else "no",
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Input Spec Alignment",
            "",
            "| field | value |",
            "| --- | --- |",
            f"| bundle_input_id | `{input_alignment['bundle_input_id']}` |",
            f"| dataset_source_type | `{input_alignment['dataset_source_type']}` |",
            f"| dataset_schema_version | `{input_alignment['dataset_schema_version']}` |",
            f"| bundle_schema_version | `{input_alignment['bundle_schema_version']}` |",
            f"| sample_count_matches | `{input_alignment['sample_count_matches']}` |",
            f"| bundle_is_importable | `{input_alignment['bundle_is_importable']}` |",
        ]
    )

    lines.extend(
        [
            "",
            "## Evidence Binding Summary",
            "",
            "| field_path | source_id | evidence_role | value_status | notes |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for binding in evidence["evidence_bindings"]:
        lines.append(_binding_table_row(binding))

    lines.extend(
        [
            "",
            "## Assumption Fields",
            "",
            "| field_path | source_id | evidence_role | value_status | notes |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for binding in evidence["assumption_bindings"]:
        lines.append(_binding_table_row(binding))

    lines.extend(
        [
            "",
            "## Real-Validation Fields",
            "",
            "| field_path | source_id | evidence_role | value_status | notes |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for binding in evidence["real_validation_bindings"]:
        lines.append(_binding_table_row(binding))

    lines.extend(
        [
            "",
            "## Warnings And Errors",
            "",
            f"- warnings: {len(evidence['warnings'])}",
            f"- errors: {len(evidence['errors'])}",
        ]
    )
    if evidence["warnings"]:
        for warning in evidence["warnings"]:
            lines.append(f"- warning: {warning}")
    if evidence["errors"]:
        for error in evidence["errors"]:
            lines.append(f"- error: {error}")

    lines.extend(
        [
            "",
            "## Skill Package Readiness",
            "",
            "- `SimulationOutputBundle` 已经可以走通导入与抽取链路，说明平台可以接住仿真输出的结构化结果。",
            "- 不是 WPS/PQR，也不证明真实焊接质量。",
            "- 外部仿真器仍然只是可选 adapter；当前报告使用 simlite/mock bundle 验证平台接入能力。",
            "- 前期调研资料继续作为后续焊接知识嵌入底座。",
            "- 目前结论是：平台具备把仿真样本收进 skill package 的基础接口，后续再接真实来源做补强。",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> dict[str, Any]:
    parser = argparse.ArgumentParser(description="生成仿真输出接入证据报告。")
    parser.add_argument("--outdir", default="simulation_ingest_report_out")
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
    return run_simulation_ingest_report(args.outdir, docs_report_dir=docs_report_dir)


if __name__ == "__main__":
    main()
