from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .nvidia_digital_twin_report import run_nvidia_digital_twin_report
from .nv01_b_experiment_base import (
    READINESS_BOUNDARY,
    REPORT_ID,
    build_nv01_b_experiment_payloads,
    load_nv01a_artifacts,
)


TOP_LEVEL_PAYLOAD_FILES = {
    "openusd_stage_validation_report": "openusd_stage_validation_report.json",
    "isaac_replay_fixture": "isaac_replay_fixture.json",
    "procedure_sim_parameter_audit": "procedure_sim_parameter_audit.json",
    "sensor_annotation_manifest": "sensor_annotation_manifest.json",
    "simulation_blocking_report": "simulation_blocking_report.json",
    "experiment_reproducibility_manifest": "experiment_reproducibility_manifest.json",
}

TASK_PAYLOAD_FILES = {
    "openusd_task_stage_fragment": "openusd_task_stage_fragment.usda",
    "isaac_replay_task_fixture": "isaac_replay_task_fixture.json",
    "procedure_sim_parameter_audit": "procedure_sim_parameter_audit.json",
    "sensor_annotation_manifest": "sensor_annotation_manifest.json",
    "simulation_blocking_report": "simulation_blocking_report.json",
}


def run_nv01_b_experiment_base_report(
    outdir: str | Path,
    source_nv01a_dir: str | Path | None = None,
) -> dict[str, Any]:
    output_dir = Path(outdir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_dir, source_summary, source_generated_artifacts = _ensure_source_nv01a(
        output_dir,
        source_nv01a_dir,
    )
    artifacts = load_nv01a_artifacts(source_dir)
    payloads = build_nv01_b_experiment_payloads(artifacts)

    _write_text_artifact(output_dir, "openusd_stage.usda", payloads["openusd_stage_usda"])
    _write_task_payloads(output_dir, payloads)

    managed_artifacts = _managed_generated_artifacts(
        source_generated_artifacts,
        payloads["task_payloads"],
    )
    summary = _build_summary(source_summary, payloads, managed_artifacts)
    payloads["experiment_reproducibility_manifest"] = (
        _build_reproducibility_manifest(payloads, source_summary, managed_artifacts)
    )

    for payload_name, filename in TOP_LEVEL_PAYLOAD_FILES.items():
        _write_json_artifact(output_dir, filename, payloads[payload_name])

    _write_text_artifact(output_dir, "nv01_b_summary.md", _render_markdown(summary))
    _write_json_artifact(output_dir, "nv01_b_summary.json", summary)

    return summary


def main(argv: list[str] | None = None) -> dict[str, Any]:
    parser = argparse.ArgumentParser(
        description="Generate the NV01-B OpenUSD / Isaac reproducible experiment base."
    )
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--source-nv01a-dir", default=None)
    args = parser.parse_args(argv)

    summary = run_nv01_b_experiment_base_report(
        outdir=args.outdir,
        source_nv01a_dir=args.source_nv01a_dir,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def _ensure_source_nv01a(
    output_dir: Path,
    source_nv01a_dir: str | Path | None,
) -> tuple[Path, dict[str, str], list[str]]:
    if source_nv01a_dir is None:
        source_dir = output_dir / "_source_nv01a"
        source_report = run_nvidia_digital_twin_report(outdir=source_dir)
        return (
            source_dir,
            {
                "source_mode": "generated_default",
                "source_nv01a_root_ref": "_source_nv01a",
            },
            [
                f"_source_nv01a/{artifact}"
                for artifact in source_report["generated_artifacts"]
            ],
        )

    return (
        Path(source_nv01a_dir),
        {
            "source_mode": "external_source_nv01a",
            "source_nv01a_root_ref": "<source-nv01a-dir>",
        },
        [],
    )


def _write_task_payloads(output_dir: Path, payloads: dict[str, Any]) -> None:
    fixture = payloads["isaac_replay_fixture"]
    audit = payloads["procedure_sim_parameter_audit"]
    sensor = payloads["sensor_annotation_manifest"]
    blocking = payloads["simulation_blocking_report"]
    for task_id, task_payload in payloads["task_payloads"].items():
        task_dir_name = _task_output_dir_name(task_id)
        task_dir = output_dir / task_dir_name
        task_dir.mkdir(parents=True, exist_ok=True)
        task_artifacts = {
            "openusd_task_stage_fragment": _render_task_stage_fragment(task_payload),
            "isaac_replay_task_fixture": {
                "fixture_id": f"nv01-b-isaac-replay-fixture-{task_payload['task_prim']}",
                **fixture["task_fixtures"][task_id],
                "runtime_status": fixture["runtime_status"],
                "blocked_by": fixture["blocked_by"],
                "readiness_boundary": fixture["readiness_boundary"],
            },
            "procedure_sim_parameter_audit": {
                **audit,
                "audit_id": f"{audit['audit_id']}-{task_payload['task_prim']}",
                "task_id": task_id,
            },
            "sensor_annotation_manifest": {
                **sensor,
                "manifest_id": f"{sensor['manifest_id']}-{task_payload['task_prim']}",
                "task_id": task_id,
            },
            "simulation_blocking_report": {
                **blocking,
                "report_id": f"{blocking['report_id']}-{task_payload['task_prim']}",
                "task_id": task_id,
            },
        }
        for payload_name, filename in TASK_PAYLOAD_FILES.items():
            if filename.endswith(".usda"):
                _write_text_artifact(task_dir, filename, task_artifacts[payload_name])
            else:
                _write_json_artifact(task_dir, filename, task_artifacts[payload_name])


def _managed_generated_artifacts(
    source_generated_artifacts: list[str],
    task_payloads: dict[str, dict[str, Any]],
) -> list[str]:
    relative_paths = set(source_generated_artifacts)
    relative_paths.update(
        {
            "nv01_b_summary.md",
            "nv01_b_summary.json",
            "openusd_stage.usda",
            *TOP_LEVEL_PAYLOAD_FILES.values(),
        }
    )
    for task_id in task_payloads:
        task_dir_name = _task_output_dir_name(task_id)
        relative_paths.update(
            f"{task_dir_name}/{filename}" for filename in TASK_PAYLOAD_FILES.values()
        )
    return sorted(relative_paths)


def _build_summary(
    source_summary: dict[str, str],
    payloads: dict[str, Any],
    generated_artifacts: list[str],
) -> dict[str, Any]:
    task_payloads = payloads["task_payloads"]
    validation = payloads["openusd_stage_validation_report"]
    blocking = payloads["simulation_blocking_report"]
    return {
        "report_id": REPORT_ID,
        "overall_status": blocking["overall_status"],
        "openusd_authoring_status": validation["validation_status"],
        "task_count": len(task_payloads),
        "source_nv01a": source_summary,
        "generated_artifacts": generated_artifacts,
        "tasks": [
            {
                "task_id": task_id,
                "task_output_dir": _task_output_dir_name(task_id),
            }
            for task_id in task_payloads
        ],
        "readiness_boundary": READINESS_BOUNDARY,
        "next_step_recommendation": (
            "Proceed to NV01-C Isaac Sim runtime import/static replay validation only "
            "after required runtime, calibration, and real process inputs are available."
        ),
    }


def _build_reproducibility_manifest(
    payloads: dict[str, Any],
    source_summary: dict[str, str],
    generated_artifacts: list[str],
) -> dict[str, Any]:
    manifest = dict(payloads["experiment_reproducibility_manifest"])
    source_root_ref = source_summary["source_nv01a_root_ref"]
    source_arg = (
        " --source-nv01a-dir <source-nv01a-dir>"
        if source_summary["source_mode"] == "external_source_nv01a"
        else ""
    )
    manifest.update(
        {
            "source_nv01a_root_ref": source_root_ref,
            "source_nv01a_summary_ref": f"{source_root_ref}/nv01_summary.json",
            "generated_artifacts": generated_artifacts,
            "command": (
                "python -m weldcore.skill_asset.nv01_b_experiment_base_report "
                f"--outdir <output-dir>{source_arg}"
            ),
            "report_cli_status": "implemented",
            "validation_commands": [
                "pytest tests/test_nv01_b_experiment_base.py "
                "tests/test_nv01_b_experiment_base_report.py -q",
            ],
        }
    )
    return manifest


def _render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# NV01-B OpenUSD / Isaac Sim Reproducible Experiment Base",
        "",
        f"Report ID: `{summary['report_id']}`",
        f"Overall status: `{summary['overall_status']}`",
        f"OpenUSD authoring status: `{summary['openusd_authoring_status']}`",
        f"Task count: `{summary['task_count']}`",
        "",
        "## Boundaries",
        "",
        "- 不是 Isaac Sim runtime 验证；当前只做静态 OpenUSD / JSON artifact gate。",
        "- 不是 policy training 结果；未运行 Isaac Lab 或任何策略训练。",
        "- 不是正式 WPS/PQR；仍缺正式工艺评定和审批输入。",
        "- 不是 ready_for_robot_execution；仍缺真实机器人、工位、TCP/tool/workpiece 和安全验证。",
        "",
        "## Generated Artifacts",
        "",
        *[f"- `{artifact}`" for artifact in summary["generated_artifacts"]],
        "",
        "## Tasks",
        "",
    ]
    for task in summary["tasks"]:
        lines.append(f"- `{task['task_id']}` -> `{task['task_output_dir']}`")
    lines.extend(["", "## Next Step", "", summary["next_step_recommendation"]])
    return "\n".join(lines)


def _render_task_stage_fragment(task: dict[str, Any]) -> str:
    return "\n".join(
        [
            "#usda 1.0",
            "",
            f'def Xform "{task["task_prim"]}"',
            "{",
            '    def Xform "SeamPath" {}',
            '    def Xform "TcpTrajectoryCandidate" {}',
            '    def Xform "Torch" {}',
            '    def Xform "Sensors" {}',
            '    def Xform "SafetyBoundary" {}',
            "}",
            "",
        ]
    )


def _write_json_artifact(output_dir: Path, relative_path: str, data: Any) -> None:
    path = output_dir / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text_artifact(output_dir: Path, relative_path: str, text: str) -> None:
    path = output_dir / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _relative_files(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())


def _task_output_dir_name(task_id: str) -> str:
    return task_id if task_id.startswith("task-") else f"task-{task_id}"


if __name__ == "__main__":
    main()
