from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from weldcore.simulation_bakeoff.accumulation import (
    SimulationAccumulationShardSpec,
    build_simulation_accumulation_shard_report,
    build_simulation_accumulation_report,
    build_simulation_dataset_index,
    default_maniskill_accumulation_spec,
    default_maniskill_sharded_accumulation_spec,
    iter_accumulation_shard_specs,
    validate_batch_result_matches_shard,
)
from weldcore.simulation_bakeoff.batch import (
    SimulationBatchResult,
    SimulationSampleRun,
    summarize_sample_runs,
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
    shards: int = 1,
    force: bool = False,
) -> dict[str, Any]:
    output_root = Path(outdir)
    acc_dir = output_root / accumulation_id
    if shards == 1:
        spec = default_maniskill_accumulation_spec(
            accumulation_id=accumulation_id,
            output_root=str(outdir),
            samples_per_task=samples_per_task,
            seed_start=seed_start,
        )
        shard_specs = (_phase_one_shard_spec(spec),)
    else:
        spec = default_maniskill_sharded_accumulation_spec(
            accumulation_id=accumulation_id,
            output_root=str(outdir),
            samples_per_task=samples_per_task,
            seed_start=seed_start,
            shard_count=shards,
        )
        shard_specs = iter_accumulation_shard_specs(spec)
    write_json_artifact(acc_dir / "accumulation_spec.json", spec)

    batch_results: list[SimulationBatchResult] = []
    shard_reports = []
    for shard in shard_specs:
        batch_result_path = acc_dir / shard.batch_result_uri
        if batch_result_path.exists() and not force:
            try:
                batch_result = _read_batch_result(batch_result_path)
                validate_batch_result_matches_shard(
                    batch_result=batch_result,
                    shard_spec=shard,
                    route_id=spec.route_id,
                    task_count=len(spec.task_specs),
                )
                shard_status = "reused_existing_result"
            except Exception:
                batch_result = _failed_to_load_existing_result(
                    shard,
                    route_id=spec.route_id,
                    task_ids=tuple(task.task_id for task in spec.task_specs),
                    variation_policy=spec.variation_policy,
                )
                shard_status = "failed_to_load_existing_result"
        else:
            batch_payload = run_maniskill_batch_pipeline(
                acc_dir / "batches",
                batch_id=shard.batch_id,
                samples_per_task=shard.samples_per_task,
                seed_start=shard.seed_start,
            )
            batch_result = _batch_result_from_payload(batch_payload)
            validate_batch_result_matches_shard(
                batch_result=batch_result,
                shard_spec=shard,
                route_id=spec.route_id,
                task_count=len(spec.task_specs),
            )
            shard_status = "rerun_forced" if force else "completed_new_run"

        batch_results.append(batch_result)
        shard_reports.append(
            build_simulation_accumulation_shard_report(
                shard_spec=shard,
                batch_result=batch_result,
                status=shard_status,
            )
        )

    dataset_index = build_simulation_dataset_index(
        accumulation_id=spec.accumulation_id,
        batch_results=tuple(batch_results),
        batch_root_uris={
            shard.batch_id: shard.batch_root_uri for shard in shard_specs
        },
        batch_result_uris={
            shard.batch_id: shard.batch_result_uri for shard in shard_specs
        },
    )
    write_json_artifact(acc_dir / "dataset_index.json", dataset_index)

    report = build_simulation_accumulation_report(
        dataset_index=dataset_index,
        dataset_index_uri="dataset_index.json",
        shard_reports=tuple(shard_reports),
    )
    payload = report.to_dict()
    write_json_artifact(acc_dir / "accumulation_report.json", payload)
    return payload


def _phase_one_shard_spec(spec) -> SimulationAccumulationShardSpec:
    batch_id = f"{spec.batch_id_prefix}-{spec.accumulation_id}"
    batch_root_uri = f"batches/{batch_id}"
    return SimulationAccumulationShardSpec(
        shard_id="shard-000",
        batch_id=batch_id,
        samples_per_task=spec.samples_per_task,
        requested_sample_count=spec.target_requested_sample_count,
        seed_start=spec.seed_start,
        batch_root_uri=batch_root_uri,
        batch_result_uri=f"{batch_root_uri}/batch_result.json",
        reuse_policy=spec.resume_policy,
    )


def _read_batch_result(path: Path) -> SimulationBatchResult:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return _batch_result_from_payload(payload)


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


def _failed_to_load_existing_result(
    shard: SimulationAccumulationShardSpec,
    *,
    route_id: str,
    task_ids: tuple[str, ...],
    variation_policy: str,
) -> SimulationBatchResult:
    sample_runs = []
    seed = shard.seed_start
    for task_id in task_ids:
        for _ in range(shard.samples_per_task):
            sample_id = f"sample-{shard.batch_id}-{route_id}-{task_id}-{seed}"
            failure_artifact_uri = f"samples/{sample_id}/failure_artifact.json"
            sample_runs.append(
                SimulationSampleRun(
                    batch_id=shard.batch_id,
                    sample_id=sample_id,
                    task_id=task_id,
                    route_id=route_id,
                    seed=seed,
                    variation_policy=variation_policy,
                    variation_descriptor={"policy": variation_policy, "seed": seed},
                    status="failed",
                    raw_artifact_uri=failure_artifact_uri,
                    adapter_result_uri=None,
                    evidence_bundle_uri=None,
                    experience_dataset_uri=None,
                    failure_boundary=("data_contract_incomplete",),
                    evidence_notes=("failed_to_load_existing_batch_result",),
                    failure_artifact_uri=failure_artifact_uri,
                )
            )
            seed += 1
    return summarize_sample_runs(
        batch_id=shard.batch_id,
        route_id=route_id,
        task_count=len(task_ids),
        requested_sample_count=shard.requested_sample_count,
        sample_runs=sample_runs,
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
    parser.add_argument("--shards", type=int, default=1)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    result = run_maniskill_accumulation_pipeline(
        args.outdir,
        accumulation_id=args.accumulation_id,
        samples_per_task=args.samples_per_task,
        seed_start=args.seed_start,
        shards=args.shards,
        force=args.force,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
