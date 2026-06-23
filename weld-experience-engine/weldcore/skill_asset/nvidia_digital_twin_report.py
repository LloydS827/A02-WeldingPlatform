from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .demo_report import run_demo_evidence_pack
from .nvidia_digital_twin import build_nvidia_digital_twin_payloads, load_demo_pack
from .procedure_contract import (
    DEFAULT_PROCEDURE_WORKBOOK_PATH,
    build_weld_procedure_knowledge_contract,
)


REPORT_ID = "k01-nv01-a-procedure-constrained-manifest-evidence-pack"
TOP_LEVEL_PAYLOAD_FILES = {
    "weld_procedure_parameter_set": "weld_procedure_parameter_set.json",
    "weld_procedure_validation_report": "weld_procedure_validation_report.json",
    "procedure_to_nv01_mapping_matrix": "procedure_to_nv01_mapping_matrix.json",
    "weld_skill_digital_twin_package": "weld_skill_digital_twin_package.json",
    "openusd_scene_manifest": "openusd_scene_manifest.json",
    "isaac_sim_replay_config": "isaac_sim_replay_config.json",
    "domain_randomization_recipe": "domain_randomization_recipe.json",
    "training_readiness_report": "training_readiness_report.json",
    "nvidia_stack_alignment_matrix": "nvidia_stack_alignment_matrix.json",
}
TASK_PAYLOAD_FILES = {
    "skill_asset_ref": "skill_asset_ref.json",
    "weld_procedure_parameter_set": "weld_procedure_parameter_set.json",
    "weld_procedure_validation_report": "weld_procedure_validation_report.json",
    "openusd_task_manifest": "openusd_task_manifest.json",
    "isaac_replay_task_config": "isaac_replay_task_config.json",
    "sensor_and_annotation_manifest": "sensor_and_annotation_manifest.json",
    "training_task_readiness": "training_task_readiness.json",
}


def run_nvidia_digital_twin_report(
    outdir: str | Path,
    source_demo_dir: str | Path | None = None,
    procedure_workbook_path: str | Path | None = None,
) -> dict[str, Any]:
    output_dir = Path(outdir)
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_artifacts: list[str] = []

    source_dir, source_generated_artifacts, source_demo_summary = _ensure_source_demo_pack(
        output_dir,
        source_demo_dir,
    )
    generated_artifacts.extend(source_generated_artifacts)
    demo_summary = load_demo_pack(source_dir)
    contract = build_weld_procedure_knowledge_contract(
        procedure_workbook_path or DEFAULT_PROCEDURE_WORKBOOK_PATH
    )
    payloads = build_nvidia_digital_twin_payloads(
        source_dir,
        demo_summary,
        contract,
    )
    source_demo_pack_root_ref = _source_demo_pack_root_ref(output_dir, source_dir)
    _annotate_source_demo_refs(payloads, source_demo_pack_root_ref)

    _write_json_artifact(
        output_dir,
        "weld_procedure_knowledge_contract.json",
        contract,
        generated_artifacts,
    )
    for payload_name, filename in TOP_LEVEL_PAYLOAD_FILES.items():
        _write_json_artifact(
            output_dir,
            filename,
            payloads[payload_name],
            generated_artifacts,
        )
    _write_task_payloads(output_dir, payloads["task_payloads"], generated_artifacts)

    _record_generated_artifact("nv01_summary.md", generated_artifacts)
    _record_generated_artifact("nv01_summary.json", generated_artifacts)
    summary = _build_summary(
        demo_summary,
        payloads,
        sorted(generated_artifacts),
        source_demo_summary,
    )
    _write_text_artifact(
        output_dir,
        "nv01_summary.md",
        _render_markdown(summary),
        generated_artifacts,
    )
    _write_json_artifact(output_dir, "nv01_summary.json", summary, generated_artifacts)
    return summary


def main(argv: list[str] | None = None) -> dict[str, Any]:
    parser = argparse.ArgumentParser(
        description="Generate the K01 + NV01-A digital twin evidence report."
    )
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--source-demo-dir", default=None)
    parser.add_argument("--procedure-workbook-path", default=None)
    args = parser.parse_args(argv)

    summary = run_nvidia_digital_twin_report(
        outdir=args.outdir,
        source_demo_dir=args.source_demo_dir,
        procedure_workbook_path=args.procedure_workbook_path,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def _ensure_source_demo_pack(
    output_dir: Path,
    source_demo_dir: str | Path | None,
) -> tuple[Path, list[str], dict[str, Any]]:
    if source_demo_dir is None:
        source_dir = output_dir / "_source_demo_evidence"
        source_summary = run_demo_evidence_pack(source_dir)
        return (
            source_dir,
            _source_demo_generated_artifacts(source_summary),
            {
                "source_demo_mode": "generated_default",
                "source_demo_pack_root_ref": "_source_demo_evidence",
            },
        )

    source_dir = Path(source_demo_dir)
    if not source_dir.exists():
        generated_source_dir = output_dir / "_source_demo_evidence"
        source_summary = run_demo_evidence_pack(generated_source_dir)
        return (
            generated_source_dir,
            _source_demo_generated_artifacts(source_summary),
            {
                "source_demo_mode": "generated_default_for_missing_requested_source",
                "requested_source_demo_dir": str(source_dir),
                "source_demo_pack_root_ref": "_source_demo_evidence",
            },
        )
    return (
        source_dir,
        [],
        {
            "source_demo_mode": "external_source_demo",
            "source_demo_pack_root_ref": str(source_dir.resolve()),
        },
    )


def _source_demo_pack_root_ref(output_dir: Path, source_dir: Path) -> str:
    try:
        return str(source_dir.relative_to(output_dir))
    except ValueError:
        return str(source_dir.resolve())


def _annotate_source_demo_refs(
    payloads: dict[str, Any],
    source_demo_pack_root_ref: str,
) -> None:
    source_demo_pack_ref = f"{source_demo_pack_root_ref}/demo_summary.json"
    for payload_name, payload in payloads.items():
        if payload_name == "task_payloads" or not isinstance(payload, dict):
            continue
        if (
            "canonical_artifact_refs_by_task" in payload
            or payload_name == "weld_skill_digital_twin_package"
        ):
            payload["source_demo_pack_root_ref"] = source_demo_pack_root_ref
            payload["canonical_artifact_root_ref"] = source_demo_pack_root_ref
    package = payloads["weld_skill_digital_twin_package"]
    package["source_demo_pack_ref"] = source_demo_pack_ref

    for task_payload in payloads["task_payloads"].values():
        task_payload["canonical_artifact_root_ref"] = source_demo_pack_root_ref
        task_payload["skill_asset_ref"]["canonical_artifact_root_ref"] = (
            source_demo_pack_root_ref
        )


def _source_demo_generated_artifacts(source_summary: dict[str, Any]) -> list[str]:
    artifacts = [
        "demo_summary.md",
        "demo_summary.html",
        "demo_summary.json",
    ]
    artifacts.extend(
        artifact_ref
        for task in source_summary["tasks"]
        for artifact_ref in task["artifact_refs"].values()
    )
    return sorted(f"_source_demo_evidence/{artifact}" for artifact in artifacts)


def _write_task_payloads(
    output_dir: Path,
    task_payloads: dict[str, dict[str, Any]],
    generated_artifacts: list[str],
) -> None:
    for task_id, task_payload in task_payloads.items():
        task_dir_name = _task_output_dir_name(task_id)
        (output_dir / task_dir_name).mkdir(parents=True, exist_ok=True)
        for payload_name, filename in TASK_PAYLOAD_FILES.items():
            _write_json_artifact(
                output_dir,
                f"{task_dir_name}/{filename}",
                task_payload[payload_name],
                generated_artifacts,
            )


def _build_summary(
    demo_summary: dict[str, Any],
    payloads: dict[str, Any],
    generated_artifacts: list[str],
    source_demo_summary: dict[str, Any],
) -> dict[str, Any]:
    task_payloads = payloads["task_payloads"]
    return {
        "report_id": REPORT_ID,
        "task_count": demo_summary["task_count"],
        "overall_status": "ready_for_simulation_replay_package_design",
        "readiness_states": [
            "ready_for_procedure_contract_review",
            "ready_for_simulation_replay_package_design",
            "ready_for_training_design_review",
            "not_ready_for_policy_training",
        ],
        "readiness_boundary": [
            "not_formal_WPS_PQR",
            "not_ready_for_robot_execution",
            "not_isaac_sim_runtime_validation",
            "not_policy_training_result",
        ],
        "source_demo": source_demo_summary,
        "generated_artifacts": generated_artifacts,
        "tasks": _task_summaries(task_payloads),
        "next_step_recommendation": (
            "Proceed to NV01-B OpenUSD Authoring Spike after expert review of K01 gaps."
        ),
    }


def _task_summaries(task_payloads: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "task_id": task_id,
            "task_output_dir": _task_output_dir_name(task_id),
        }
        for task_id in task_payloads
    ]


def _task_output_dir_name(task_id: str) -> str:
    return task_id if task_id.startswith("task-") else f"task-{task_id}"


def _render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# K01 + NV01-A Procedure-Constrained Manifest Evidence Pack",
        "",
        f"Report ID: `{summary['report_id']}`",
        f"Overall status: `{summary['overall_status']}`",
        f"Task count: `{summary['task_count']}`",
        "",
        "## Readiness States",
        "",
        *[f"- `{state}`" for state in summary["readiness_states"]],
        "",
        "## Boundaries",
        "",
        "- 不是正式 WPS/PQR；K01 Excel 只提供字段合同和审查输入。",
        "- 不是 ready_for_robot_execution；仍缺真实机器人、工位和焊接质量验证。",
        "- 不是 Isaac Sim runtime 验证；当前只生成 replay/package design artifacts。",
        "- 不是 policy training 结果；仅达到 training design review 输入阶段。",
        "- 缺失的人审字段和 workcell logged 字段是显式 gap，不用默认值伪造通过。",
        "- 已存在的 source demo 目录会被当作证据输入；缺少引用 artifact 时抛出 missing_canonical_artifacts。",
        "",
        "## Generated Artifacts",
        "",
        *[f"- `{artifact}`" for artifact in summary["generated_artifacts"]],
        "",
        "## Tasks",
        "",
    ]
    for task in summary["tasks"]:
        lines.extend(
            [
                f"- `{task['task_id']}` -> `{task['task_output_dir']}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Next Step",
            "",
            summary["next_step_recommendation"],
        ]
    )
    return "\n".join(lines)


def _write_json_artifact(
    output_dir: Path,
    relative_path: str,
    data: Any,
    generated_artifacts: list[str],
) -> None:
    _write_json(output_dir / relative_path, data)
    _record_generated_artifact(relative_path, generated_artifacts)


def _write_text_artifact(
    output_dir: Path,
    relative_path: str,
    text: str,
    generated_artifacts: list[str],
) -> None:
    _write_text(output_dir / relative_path, text)
    _record_generated_artifact(relative_path, generated_artifacts)


def _record_generated_artifact(
    relative_path: str,
    generated_artifacts: list[str],
) -> None:
    if relative_path not in generated_artifacts:
        generated_artifacts.append(relative_path)


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
