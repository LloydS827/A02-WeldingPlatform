from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .nv01_b_experiment_base_report import run_nv01_b_experiment_base_report
from .nv01_c_mj01_readiness import (
    MissingNV01BArtifactError,
    build_nv01_c_mj01_readiness_payloads,
    load_nv01b_artifacts,
)


REPORT_ID = "nv01-c-mj01-runtime-replay-readiness-pack"
TOP_LEVEL_PAYLOAD_FILES = {
    "isaac_runtime_validation_input_manifest": (
        "isaac_runtime_validation_input_manifest.json"
    ),
    "mujoco_lightweight_replay_feasibility_report": (
        "mujoco_lightweight_replay_feasibility_report.json"
    ),
    "runtime_replay_blocking_report": "runtime_replay_blocking_report.json",
    "readiness_reproducibility_manifest": "readiness_reproducibility_manifest.json",
}
TASK_PAYLOAD_FILES = {
    "isaac_runtime_task_validation_input": "isaac_runtime_task_validation_input.json",
    "mujoco_task_replay_feasibility": "mujoco_task_replay_feasibility.json",
    "runtime_replay_task_blocking_report": "runtime_replay_task_blocking_report.json",
}


def run_nv01_c_mj01_readiness_report(
    outdir: str | Path,
    source_nv01b_dir: str | Path | None = None,
) -> dict[str, Any]:
    output_dir = Path(outdir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_dir, source_summary, source_generated_artifacts = _ensure_source_nv01b(
        output_dir,
        source_nv01b_dir,
    )
    artifacts = load_nv01b_artifacts(source_dir)
    payloads = build_nv01_c_mj01_readiness_payloads(artifacts)

    generated_artifacts = _managed_generated_artifacts(
        source_generated_artifacts,
        payloads["task_payloads"],
    )
    payloads["readiness_reproducibility_manifest"] = (
        _build_reproducibility_manifest(source_summary, generated_artifacts)
    )
    summary = _build_summary(source_summary, payloads, generated_artifacts)

    for payload_name, filename in TOP_LEVEL_PAYLOAD_FILES.items():
        _write_json_artifact(output_dir, filename, payloads[payload_name])
    _write_task_payloads(output_dir, payloads["task_payloads"])
    _write_text_artifact(output_dir, "nv01_c_mj01_summary.md", _render_markdown(summary))
    _write_json_artifact(output_dir, "nv01_c_mj01_summary.json", summary)

    return summary


def main(argv: list[str] | None = None) -> dict[str, Any]:
    parser = argparse.ArgumentParser(
        description="Generate the NV01-C + MJ01 runtime/replay readiness pack."
    )
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--source-nv01b-dir", default=None)
    args = parser.parse_args(argv)

    summary = run_nv01_c_mj01_readiness_report(
        outdir=args.outdir,
        source_nv01b_dir=args.source_nv01b_dir,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def _ensure_source_nv01b(
    output_dir: Path,
    source_nv01b_dir: str | Path | None,
) -> tuple[Path, dict[str, str], list[str]]:
    if source_nv01b_dir is None:
        source_dir = output_dir / "_source_nv01b"
        source_report = run_nv01_b_experiment_base_report(outdir=source_dir)
        return (
            source_dir,
            {
                "source_mode": "generated_default",
                "source_nv01b_root_ref": "_source_nv01b",
            },
            [
                f"_source_nv01b/{artifact}"
                for artifact in source_report["generated_artifacts"]
            ],
        )

    source_dir = Path(source_nv01b_dir)
    if not source_dir.exists():
        raise MissingNV01BArtifactError("missing_source_nv01b_dir")
    return (
        source_dir,
        {
            "source_mode": "external_source_nv01b",
            "source_nv01b_root_ref": "<source-nv01b-dir>",
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
) -> list[str]:
    relative_paths = set(source_generated_artifacts)
    relative_paths.update(
        {
            "nv01_c_mj01_summary.md",
            "nv01_c_mj01_summary.json",
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
    blocking = payloads["runtime_replay_blocking_report"]
    isaac = payloads["isaac_runtime_validation_input_manifest"]
    mujoco = payloads["mujoco_lightweight_replay_feasibility_report"]
    task_payloads = payloads["task_payloads"]
    return {
        "report_id": REPORT_ID,
        "overall_status": blocking["overall_status"],
        "isaac_status": isaac["runtime_status"],
        "mujoco_status": mujoco["runtime_status"],
        "source_nv01b": source_summary,
        "task_count": len(task_payloads),
        "tasks": [
            {
                "task_id": task_id,
                "task_output_dir": _task_output_dir_name(task_id),
            }
            for task_id in task_payloads
        ],
        "generated_artifacts": generated_artifacts,
        "readiness_boundary": blocking["readiness_boundary"],
        "next_step_recommendation": (
            "Proceed to separate NV01-C Isaac Sim runtime runner and MJ01 MuJoCo "
            "lightweight replay runner only after runtime environments and real "
            "calibration/process inputs are available."
        ),
    }


def _build_reproducibility_manifest(
    source_summary: dict[str, str],
    generated_artifacts: list[str],
) -> dict[str, Any]:
    source_root_ref = source_summary["source_nv01b_root_ref"]
    source_arg = (
        " --source-nv01b-dir <source-nv01b-dir>"
        if source_summary["source_mode"] == "external_source_nv01b"
        else ""
    )
    return {
        "manifest_id": "nv01-c-mj01-readiness-reproducibility-manifest",
        "source_nv01b_root_ref": source_root_ref,
        "source_nv01b_summary_ref": f"{source_root_ref}/nv01_b_summary.json",
        "generated_artifacts": generated_artifacts,
        "command": (
            "python -m weldcore.skill_asset.nv01_c_mj01_readiness_report "
            f"--outdir <output-dir>{source_arg}"
        ),
        "runtime_dependencies": [],
        "report_cli_status": "implemented",
        "validation_commands": [
            "pytest tests/test_nv01_c_mj01_readiness.py "
            "tests/test_nv01_c_mj01_readiness_report.py -q",
        ],
        "readiness_boundary": [
            "not_isaac_sim_runtime_validation",
            "not_mujoco_dynamics_validation",
            "not_policy_training_result",
            "not_formal_WPS_PQR",
            "not_ready_for_robot_execution",
        ],
    }


def _render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# NV01-C + MJ01 Runtime Replay Readiness Pack",
        "",
        f"Report ID: `{summary['report_id']}`",
        f"Overall status: `{summary['overall_status']}`",
        f"Isaac status: `{summary['isaac_status']}`",
        f"MuJoCo status: `{summary['mujoco_status']}`",
        f"Task count: `{summary['task_count']}`",
        "",
        "## Boundaries",
        "",
        "- 不是 Isaac Sim runtime 验证；当前只生成 runtime validation input manifest。",
        "- 不是 MuJoCo dynamics validation；当前只生成 lightweight replay feasibility input。",
        "- 不是 policy training 结果；未运行 Isaac Lab、MuJoCo policy 或任何策略训练。",
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
