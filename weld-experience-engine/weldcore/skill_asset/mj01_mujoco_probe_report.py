from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .mj01_mujoco_probe import (
    READINESS_BOUNDARY,
    build_mj01_a_nv01_c0_payloads,
    load_readiness_artifacts,
)
from .nv01_c_mj01_readiness_report import run_nv01_c_mj01_readiness_report


REPORT_ID = "mj01-a-local-mujoco-probe-nv01-c0-preflight"
TOP_LEVEL_PAYLOAD_FILES = {
    "mujoco_runtime_probe_report": "mj01_mujoco_runtime_probe_report.json",
    "mujoco_model_input_resolution_report": (
        "mj01_mujoco_model_input_resolution_report.json"
    ),
    "mujoco_probe_report": "mj01_mujoco_probe_report.json",
    "isaac_remote_preflight_report": "nv01_c0_isaac_remote_preflight_report.json",
}
TASK_PAYLOAD_FILES = {
    "mj01_task_trajectory_dry_run_input": "mj01_task_trajectory_dry_run_input.json",
    "nv01_c0_task_isaac_remote_preflight_input": (
        "nv01_c0_task_isaac_remote_preflight_input.json"
    ),
}


def run_mj01_mujoco_probe_report(
    outdir: str | Path,
    source_readiness_dir: str | Path | None = None,
) -> dict[str, Any]:
    output_dir = Path(outdir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_dir, source_summary, source_generated_artifacts = _ensure_source_readiness(
        output_dir,
        source_readiness_dir,
    )
    artifacts = load_readiness_artifacts(source_dir)
    payloads = build_mj01_a_nv01_c0_payloads(artifacts)

    generated_artifacts = _managed_generated_artifacts(
        source_generated_artifacts,
        payloads["task_payloads"],
        artifacts,
    )
    payloads["reproducibility_manifest"] = _build_reproducibility_manifest(
        payloads["reproducibility_manifest"],
        source_summary,
        generated_artifacts,
    )
    summary = _build_summary(source_summary, artifacts, payloads, generated_artifacts)

    for payload_name, filename in TOP_LEVEL_PAYLOAD_FILES.items():
        _write_json_artifact(output_dir, filename, payloads[payload_name])
    _write_task_payloads(output_dir, payloads["task_payloads"])
    _write_json_artifact(
        output_dir,
        "mj01_a_reproducibility_manifest.json",
        payloads["reproducibility_manifest"],
    )
    _write_text_artifact(output_dir, "mj01_a_summary.md", _render_markdown(summary))
    _write_json_artifact(output_dir, "mj01_a_summary.json", summary)

    return summary


def main(argv: list[str] | None = None) -> dict[str, Any]:
    parser = argparse.ArgumentParser(
        description="Generate the MJ01-A MuJoCo probe and NV01-C0 Isaac preflight pack."
    )
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--source-readiness-dir", default=None)
    args = parser.parse_args(argv)

    summary = run_mj01_mujoco_probe_report(
        outdir=args.outdir,
        source_readiness_dir=args.source_readiness_dir,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def _ensure_source_readiness(
    output_dir: Path,
    source_readiness_dir: str | Path | None,
) -> tuple[Path, dict[str, str], list[str]]:
    if source_readiness_dir is None:
        source_dir = output_dir / "_source_readiness"
        source_report = run_nv01_c_mj01_readiness_report(outdir=source_dir)
        return (
            source_dir,
            {
                "source_mode": "generated_default",
                "source_readiness_root_ref": "_source_readiness",
            },
            [
                f"_source_readiness/{artifact}"
                for artifact in source_report["generated_artifacts"]
            ],
        )

    return (
        Path(source_readiness_dir),
        {
            "source_mode": "external_source_readiness",
            "source_readiness_root_ref": "<source-readiness-dir>",
        },
        [],
    )


def _write_task_payloads(
    output_dir: Path,
    task_payloads: dict[str, dict[str, Any]],
) -> None:
    for task_id, task_payload in task_payloads.items():
        task_dir_name = _task_output_dir_name(task_id)
        for payload_name, filename in TASK_PAYLOAD_FILES.items():
            _write_json_artifact(
                output_dir,
                f"{task_dir_name}/{filename}",
                task_payload[payload_name],
            )


def _managed_generated_artifacts(
    source_generated_artifacts: list[str],
    task_payloads: dict[str, dict[str, Any]],
    artifacts: dict[str, Any],
) -> list[str]:
    relative_paths = set(source_generated_artifacts)
    relative_paths.update(
        {
            "mj01_a_summary.md",
            "mj01_a_summary.json",
            "mj01_a_reproducibility_manifest.json",
            *TOP_LEVEL_PAYLOAD_FILES.values(),
        }
    )
    for task_id in task_payloads:
        task_dir_name = _task_output_dir_name(task_id)
        relative_paths.update(
            f"{task_dir_name}/{filename}" for filename in TASK_PAYLOAD_FILES.values()
        )
    return sorted(_sanitize_artifact_ref(path, artifacts) for path in relative_paths)


def _build_summary(
    source_summary: dict[str, str],
    artifacts: dict[str, Any],
    payloads: dict[str, Any],
    generated_artifacts: list[str],
) -> dict[str, Any]:
    runtime = payloads["mujoco_runtime_probe_report"]
    probe = payloads["mujoco_probe_report"]
    isaac = payloads["isaac_remote_preflight_report"]
    tasks = artifacts["summary"]["tasks"]
    return {
        "report_id": REPORT_ID,
        "overall_status": "blocked_for_runtime_probe_or_preflight",
        "mujoco_runtime_status": runtime["runtime_probe_status"],
        "mujoco_probe_status": probe["real_urdf_load_status"],
        "isaac_remote_preflight_status": isaac["remote_runtime_status"],
        "source_readiness": source_summary,
        "task_count": len(tasks),
        "tasks": [
            {
                "task_id": task["task_id"],
                "task_output_dir": _task_output_dir_name(task["task_id"]),
            }
            for task in tasks
        ],
        "generated_artifacts": generated_artifacts,
        "readiness_boundary": READINESS_BOUNDARY,
        "next_step_recommendation": (
            "Install the optional MuJoCo extra for local runtime probing, and run "
            "Isaac Sim validation on a separate remote/server runtime before any "
            "simulation or robot execution claim."
        ),
    }


def _build_reproducibility_manifest(
    base_manifest: dict[str, Any],
    source_summary: dict[str, str],
    generated_artifacts: list[str],
) -> dict[str, Any]:
    manifest = dict(base_manifest)
    source_root_ref = source_summary["source_readiness_root_ref"]
    source_arg = (
        " --source-readiness-dir <source-readiness-dir>"
        if source_summary["source_mode"] == "external_source_readiness"
        else ""
    )
    manifest.update(
        {
            "source_readiness_root_ref": source_root_ref,
            "source_readiness_summary_ref": (
                f"{source_root_ref}/nv01_c_mj01_summary.json"
            ),
            "generated_artifacts": generated_artifacts,
            "builder": "weldcore/skill_asset/mj01_mujoco_probe_report.py",
            "payload_builder": "weldcore.skill_asset.mj01_mujoco_probe",
            "command": (
                "python -m weldcore.skill_asset.mj01_mujoco_probe_report "
                f"--outdir <output-dir>{source_arg}"
            ),
            "report_cli_status": "implemented",
            "validation_commands": [
                "pytest tests/test_mj01_mujoco_probe.py "
                "tests/test_mj01_mujoco_probe_report.py -q",
            ],
        }
    )
    return manifest


def _sanitize_artifact_ref(relative_path: str, artifacts: dict[str, Any]) -> str:
    source_urdf = artifacts["robot_body_asset_report"].get("source_urdf")
    sanitized = str(relative_path)
    if source_urdf:
        sanitized = sanitized.replace(str(source_urdf), "<robot-body-source-urdf>")
    return sanitized


def _render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# MJ01-A Local MuJoCo Probe + NV01-C0 Remote Isaac Preflight",
        "",
        f"Report ID: `{summary['report_id']}`",
        f"Overall status: `{summary['overall_status']}`",
        f"MuJoCo runtime status: `{summary['mujoco_runtime_status']}`",
        f"MuJoCo probe status: `{summary['mujoco_probe_status']}`",
        (
            "Isaac remote preflight status: "
            f"`{summary['isaac_remote_preflight_status']}`"
        ),
        f"Task count: `{summary['task_count']}`",
        "",
        "## Boundaries",
        "",
        "- 不是 MuJoCo 动力学验证；当前只做本地 runtime/probe 输入检查。",
        "- 不是 Isaac runtime 验证；当前只生成远端 preflight 契约。",
        "- 不是策略训练；未运行 Isaac Lab、MuJoCo policy 或任何训练流程。",
        "- 不是正式 WPS/PQR；仍缺正式工艺评定和审批输入。",
        "- 不可直接机器人执行；仍缺真实机器人、工位、TCP/tool/workpiece 和安全验证。",
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


def _task_output_dir_name(task_id: str) -> str:
    return task_id if task_id.startswith("task-") else f"task-{task_id}"


if __name__ == "__main__":
    main()
