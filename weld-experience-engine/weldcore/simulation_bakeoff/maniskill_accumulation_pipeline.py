from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from weldcore.simulation_bakeoff.accumulation import (
    build_simulation_accumulation_report,
    build_simulation_dataset_index,
    default_maniskill_accumulation_spec,
)
from weldcore.simulation_bakeoff.batch import (
    SimulationBatchResult,
    SimulationSampleRun,
)
from weldcore.simulation_bakeoff.maniskill_batch_pipeline import (
    run_maniskill_batch_pipeline,
)
from weldcore.simulation_bakeoff.maniskill_contract import write_json_artifact


def run_maniskill_accumulation_pipeline(
    outdir: str | Path = "artifacts/simulation/maniskill-sapien-accumulations",
    accumulation_id: str = "maniskill-sapien-accumulation-phase-1",
    *,
    samples_per_task: int = 50,
    seed_start: int = 0,
) -> dict[str, Any]:
    output_root = Path(outdir)
    acc_dir = output_root / accumulation_id
    spec = default_maniskill_accumulation_spec(
        accumulation_id=accumulation_id,
        output_root=str(outdir),
        samples_per_task=samples_per_task,
        seed_start=seed_start,
    )
    write_json_artifact(acc_dir / "accumulation_spec.json", spec)

    batch_id = f"{spec.batch_id_prefix}-{accumulation_id}"
    batch_root = Path("batches") / batch_id
    batch_payload = run_maniskill_batch_pipeline(
        acc_dir / "batches",
        batch_id=batch_id,
        samples_per_task=spec.samples_per_task,
        seed_start=spec.seed_start,
    )
    batch_result = _batch_result_from_payload(batch_payload)
    dataset_index = build_simulation_dataset_index(
        accumulation_id=spec.accumulation_id,
        batch_results=(batch_result,),
        batch_root_uris={batch_id: batch_root.as_posix()},
        batch_result_uris={batch_id: (batch_root / "batch_result.json").as_posix()},
    )
    write_json_artifact(acc_dir / "dataset_index.json", dataset_index)

    report = build_simulation_accumulation_report(
        dataset_index=dataset_index,
        dataset_index_uri="dataset_index.json",
    )
    payload = report.to_dict()
    write_json_artifact(acc_dir / "accumulation_report.json", payload)
    return payload


def _batch_result_from_payload(payload: dict[str, Any]) -> SimulationBatchResult:
    sample_runs = tuple(
        SimulationSampleRun(
            batch_id=sample["batch_id"],
            sample_id=sample["sample_id"],
            task_id=sample["task_id"],
            route_id=sample["route_id"],
            seed=sample["seed"],
            variation_policy=sample["variation_policy"],
            variation_descriptor=sample["variation_descriptor"],
            status=sample["status"],
            raw_artifact_uri=sample["raw_artifact_uri"],
            adapter_result_uri=sample["adapter_result_uri"],
            evidence_bundle_uri=sample["evidence_bundle_uri"],
            experience_dataset_uri=sample["experience_dataset_uri"],
            failure_boundary=tuple(sample["failure_boundary"]),
            evidence_notes=tuple(sample["evidence_notes"]),
            failure_artifact_uri=sample.get("failure_artifact_uri"),
        )
        for sample in payload["sample_runs"]
    )
    return SimulationBatchResult(
        batch_id=payload["batch_id"],
        route_id=payload["route_id"],
        task_count=payload["task_count"],
        requested_sample_count=payload["requested_sample_count"],
        completed_sample_count=payload["completed_sample_count"],
        failed_sample_count=payload["failed_sample_count"],
        skipped_sample_count=payload["skipped_sample_count"],
        sample_runs=sample_runs,
        failure_boundaries=tuple(payload["failure_boundaries"]),
        stage_boundary=payload["stage_boundary"],
        next_step_hint=payload["next_step_hint"],
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--outdir",
        default="artifacts/simulation/maniskill-sapien-accumulations",
    )
    parser.add_argument(
        "--accumulation-id",
        default="maniskill-sapien-accumulation-phase-1",
    )
    parser.add_argument("--samples-per-task", type=int, default=50)
    parser.add_argument("--seed-start", type=int, default=0)
    args = parser.parse_args(argv)
    result = run_maniskill_accumulation_pipeline(
        args.outdir,
        accumulation_id=args.accumulation_id,
        samples_per_task=args.samples_per_task,
        seed_start=args.seed_start,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
