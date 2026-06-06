from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from weldcore.simulation_bakeoff.evidence import build_simulation_evidence_bundle
from weldcore.simulation_bakeoff.maniskill_adapter import (
    adapt_maniskill_artifact,
    build_maniskill_experience_dataset,
)
from weldcore.simulation_bakeoff.maniskill_contract import (
    FailureBoundary,
    RawManiSkillArtifact,
    write_json_artifact,
)
from weldcore.simulation_bakeoff.maniskill_demo import generate_rule_based_demo
from weldcore.simulation_bakeoff.maniskill_runner import run_maniskill_lightweight
from weldcore.simulation_bakeoff.maniskill_tasks import maniskill_task_config_from_spec
from weldcore.simulation_bakeoff.task_specs import default_simulation_task_specs

STAGE_BOUNDARY = "experience_dataset_not_robot_process_package"


def run_maniskill_spike_pipeline(
    outdir: str | Path = "artifacts/simulation/maniskill-sapien",
) -> dict[str, Any]:
    output_dir = Path(outdir)
    task_summaries = []

    for task_spec in default_simulation_task_specs():
        task_dir = output_dir / task_spec.task_id

        try:
            config = maniskill_task_config_from_spec(task_spec)
        except Exception:
            artifact = _stage_failure_artifact(task_spec.task_id, "task_generation_failed")
            write_json_artifact(task_dir / "raw_artifact.json", artifact)
            task_summaries.append(_task_summary(task_spec.task_id, artifact))
            continue
        write_json_artifact(task_dir / "task_config.json", config)

        try:
            demo = generate_rule_based_demo(config)
        except Exception:
            artifact = _stage_failure_artifact(task_spec.task_id, "demo_generation_failed")
            write_json_artifact(task_dir / "raw_artifact.json", artifact)
            task_summaries.append(_task_summary(task_spec.task_id, artifact))
            continue
        write_json_artifact(task_dir / "demo.json", demo)

        artifact = run_maniskill_lightweight(config, demo)
        write_json_artifact(task_dir / "raw_artifact.json", artifact)

        try:
            adapter_result = adapt_maniskill_artifact(task_spec, artifact)
            experience_dataset = build_maniskill_experience_dataset(task_spec, artifact)
            evidence_bundle = build_simulation_evidence_bundle(task_spec, adapter_result)
        except Exception:
            adapter_failure = _stage_failure_artifact(
                task_spec.task_id,
                "adapter_conversion_failed",
            )
            write_json_artifact(task_dir / "adapter_failure.json", adapter_failure)
            task_summaries.append(_task_summary(task_spec.task_id, adapter_failure))
            continue

        write_json_artifact(task_dir / "adapter_result.json", adapter_result)
        write_json_artifact(task_dir / "experience_dataset.json", experience_dataset)
        write_json_artifact(task_dir / "evidence_bundle.json", evidence_bundle)
        task_summaries.append(_task_summary(task_spec.task_id, artifact))

    summary = _summary(task_summaries)
    write_json_artifact(output_dir / "run_summary.json", summary)
    return summary


def _stage_failure_artifact(
    task_id: str,
    boundary: FailureBoundary,
) -> RawManiSkillArtifact:
    return RawManiSkillArtifact(
        run_id=f"maniskill-{task_id}",
        task_id=task_id,
        status="failed",
        tcp_trajectory=(),
        tool_orientation=(),
        task_state={
            "attempted": True,
            "task_status": "failed",
        },
        metrics={
            "same_task_attempted": 1.0,
            "task_contract_outputs_ready": 0.0,
        },
        failure_boundary=(boundary,),
        artifacts={},
        evidence_notes=(STAGE_BOUNDARY,),
    )


def _task_summary(task_id: str, artifact: RawManiSkillArtifact) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "status": artifact.status,
        "failure_boundary": list(artifact.failure_boundary),
    }


def _summary(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    failure_boundaries = []
    for task in tasks:
        for boundary in task["failure_boundary"]:
            if boundary not in failure_boundaries:
                failure_boundaries.append(boundary)

    completed = sum(1 for task in tasks if task["status"] == "completed")
    failed = sum(1 for task in tasks if task["status"] == "failed")
    return {
        "task_count": len(tasks),
        "completed": completed,
        "failed": failed,
        "failure_boundaries": failure_boundaries,
        "tasks": tasks,
        "stage_boundary": STAGE_BOUNDARY,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--outdir",
        default="artifacts/simulation/maniskill-sapien",
    )
    args = parser.parse_args(argv)
    summary = run_maniskill_spike_pipeline(args.outdir)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
