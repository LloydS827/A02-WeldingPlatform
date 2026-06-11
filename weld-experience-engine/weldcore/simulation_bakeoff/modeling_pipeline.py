from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from weldcore.simulation_bakeoff.maniskill_contract import write_json_artifact
from weldcore.simulation_bakeoff.modeling import (
    build_modeled_simulation_tasks,
    build_modeling_validation_report,
    default_batch_modeling_spec,
    modeled_task_specs,
    modeling_batch_spec_compatibility,
)


def run_batch_modeling_pipeline(
    outdir: str | Path = "artifacts/simulation/modeling-validation",
    modeling_batch_id: str = "default-batch-modeling-v1",
    *,
    variants_per_task: int = 4,
    batch_samples_per_task: int = 2,
) -> dict[str, Any]:
    output_root = Path(outdir)
    batch_dir = output_root / modeling_batch_id
    spec = default_batch_modeling_spec(
        modeling_batch_id=modeling_batch_id,
        variants_per_task=variants_per_task,
    )
    modeled = build_modeled_simulation_tasks(spec)
    report = build_modeling_validation_report(spec, modeled)
    payload = report.to_dict()
    payload["batch_spec_compatibility"] = modeling_batch_spec_compatibility(
        modeled,
        samples_per_task=batch_samples_per_task,
    )

    write_json_artifact(batch_dir / "modeling_spec.json", spec)
    write_json_artifact(
        batch_dir / "modeled_task_specs.json",
        [task.to_dict() for task in modeled_task_specs(modeled)],
    )
    write_json_artifact(batch_dir / "modeling_validation_report.json", payload)
    return payload


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--outdir",
        default="artifacts/simulation/modeling-validation",
    )
    parser.add_argument(
        "--modeling-batch-id",
        default="default-batch-modeling-v1",
    )
    parser.add_argument("--variants-per-task", type=int, default=4)
    parser.add_argument("--batch-samples-per-task", type=int, default=2)
    args = parser.parse_args(argv)
    result = run_batch_modeling_pipeline(
        args.outdir,
        modeling_batch_id=args.modeling_batch_id,
        variants_per_task=args.variants_per_task,
        batch_samples_per_task=args.batch_samples_per_task,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
