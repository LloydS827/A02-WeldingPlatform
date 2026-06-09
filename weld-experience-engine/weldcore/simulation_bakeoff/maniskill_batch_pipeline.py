from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from weldcore.simulation_bakeoff.batch import (
    SimulationSamplePlan,
    SimulationSampleRun,
    default_maniskill_batch_spec,
    iter_batch_sample_plans,
    summarize_sample_runs,
)
from weldcore.simulation_bakeoff.evidence import build_simulation_evidence_bundle
from weldcore.simulation_bakeoff.maniskill_adapter import (
    adapt_maniskill_artifact,
    build_maniskill_experience_dataset,
)
from weldcore.simulation_bakeoff.maniskill_contract import (
    ExperienceDataset,
    FailureBoundary,
    RawManiSkillArtifact,
    write_json_artifact,
)
from weldcore.simulation_bakeoff.maniskill_demo import generate_rule_based_demo
from weldcore.simulation_bakeoff.maniskill_runner import run_maniskill_lightweight
from weldcore.simulation_bakeoff.maniskill_tasks import maniskill_task_config_from_spec
from weldcore.simulation_bakeoff.model import (
    SimulationEvidenceBundle,
    SimulatorAdapterResult,
)


def run_maniskill_batch_pipeline(
    outdir: str | Path = "artifacts/simulation/maniskill-sapien-batches",
    batch_id: str = "maniskill-sapien-default-batch",
    *,
    samples_per_task: int = 10,
    seed_start: int = 0,
) -> dict[str, Any]:
    output_root = Path(outdir)
    spec = default_maniskill_batch_spec(
        batch_id=batch_id,
        output_root=str(outdir),
        samples_per_task=samples_per_task,
        seed_start=seed_start,
    )
    batch_dir = output_root / batch_id
    write_json_artifact(batch_dir / "batch_spec.json", spec)

    task_specs_by_id = {task.task_id: task for task in spec.task_specs}
    sample_plans = tuple(iter_batch_sample_plans(spec))
    sample_runs = []
    for plan in sample_plans:
        task_spec = task_specs_by_id[plan.task_id]
        sample_dir = batch_dir / "samples" / plan.sample_id
        raw_artifact_path = sample_dir / "raw_artifact.json"

        try:
            config = maniskill_task_config_from_spec(task_spec)
            write_json_artifact(sample_dir / "task_config.json", config)
        except Exception:
            failure_boundary = ("task_generation_failed",)
            failure_artifact_uri, run_failure_boundary = _write_failure_artifact(
                sample_dir,
                plan,
                failure_boundary,
            )
            sample_runs.append(
                _failed_sample_run(
                    plan,
                    run_failure_boundary,
                    failure_artifact_uri,
                )
            )
            continue

        try:
            demo = generate_rule_based_demo(config)
            write_json_artifact(sample_dir / "demo.json", demo)
        except Exception:
            failure_boundary = ("demo_generation_failed",)
            failure_artifact_uri, run_failure_boundary = _write_failure_artifact(
                sample_dir,
                plan,
                failure_boundary,
            )
            sample_runs.append(
                _failed_sample_run(
                    plan,
                    run_failure_boundary,
                    failure_artifact_uri,
                )
            )
            continue

        try:
            artifact = run_maniskill_lightweight(config, demo)
        except Exception:
            failure_boundary = ("simulation_run_failed",)
            failure_artifact_uri, run_failure_boundary = _write_failure_artifact(
                sample_dir,
                plan,
                failure_boundary,
            )
            sample_runs.append(
                _failed_sample_run(
                    plan,
                    run_failure_boundary,
                    failure_artifact_uri,
                )
            )
            continue
        artifact = _sample_scoped_raw_artifact(plan, artifact)

        try:
            write_json_artifact(raw_artifact_path, artifact)
        except Exception:
            # Without a persisted raw artifact, the failure artifact is the stable
            # per-sample URI and records that the sample data contract is incomplete.
            failure_boundary = ("data_contract_incomplete",)
            failure_artifact_uri, run_failure_boundary = _write_failure_artifact(
                sample_dir,
                plan,
                failure_boundary,
            )
            sample_runs.append(
                _failed_sample_run(
                    plan,
                    run_failure_boundary,
                    failure_artifact_uri,
                )
            )
            continue

        raw_artifact_uri = _sample_uri(plan.sample_id, "raw_artifact.json")
        if artifact.status == "failed":
            failure_artifact_uri, run_failure_boundary = _write_failure_artifact(
                sample_dir,
                plan,
                artifact.failure_boundary,
                source_artifact=artifact,
            )
            sample_runs.append(
                _failed_sample_run(
                    plan,
                    run_failure_boundary,
                    raw_artifact_uri,
                    extra_evidence_notes=_unavailable_evidence_notes(
                        failure_artifact_uri,
                    ),
                )
            )
            continue

        adapter_result_path = sample_dir / "adapter_result.json"
        try:
            adapter_result = adapt_maniskill_artifact(task_spec, artifact)
            adapter_result = _sample_scoped_adapter_result(plan, adapter_result)
            write_json_artifact(adapter_result_path, adapter_result)
        except Exception:
            failure_boundary = ("adapter_conversion_failed",)
            failure_artifact_uri, run_failure_boundary = _write_failure_artifact(
                sample_dir,
                plan,
                failure_boundary,
            )
            sample_runs.append(
                _failed_sample_run(
                    plan,
                    run_failure_boundary,
                    raw_artifact_uri,
                    extra_evidence_notes=_unavailable_evidence_notes(
                        failure_artifact_uri,
                    ),
                )
            )
            continue

        experience_dataset_path = sample_dir / "experience_dataset.json"
        try:
            experience_dataset = build_maniskill_experience_dataset(task_spec, artifact)
            experience_dataset = _sample_scoped_experience_dataset(
                plan,
                experience_dataset,
            )
            write_json_artifact(experience_dataset_path, experience_dataset)
        except Exception:
            failure_boundary = ("experience_dataset_export_failed",)
            failure_artifact_uri, run_failure_boundary = _write_failure_artifact(
                sample_dir,
                plan,
                failure_boundary,
            )
            sample_runs.append(
                _failed_sample_run(
                    plan,
                    run_failure_boundary,
                    raw_artifact_uri,
                    adapter_result_uri=_sample_uri(
                        plan.sample_id,
                        "adapter_result.json",
                    ),
                    extra_evidence_notes=_unavailable_evidence_notes(
                        failure_artifact_uri,
                    ),
                )
            )
            continue

        evidence_bundle_path = sample_dir / "evidence_bundle.json"
        try:
            evidence_bundle = build_simulation_evidence_bundle(task_spec, adapter_result)
            evidence_bundle = _sample_scoped_evidence_bundle(plan, evidence_bundle)
            write_json_artifact(evidence_bundle_path, evidence_bundle)
        except Exception:
            failure_boundary = ("data_contract_incomplete",)
            failure_artifact_uri, run_failure_boundary = _write_failure_artifact(
                sample_dir,
                plan,
                failure_boundary,
            )
            sample_runs.append(
                _failed_sample_run(
                    plan,
                    run_failure_boundary,
                    raw_artifact_uri,
                    adapter_result_uri=_sample_uri(
                        plan.sample_id,
                        "adapter_result.json",
                    ),
                    experience_dataset_uri=_sample_uri(
                        plan.sample_id,
                        "experience_dataset.json",
                    ),
                    extra_evidence_notes=_unavailable_evidence_notes(
                        failure_artifact_uri,
                    ),
                )
            )
            continue

        sample_runs.append(
            SimulationSampleRun(
                batch_id=plan.batch_id,
                sample_id=plan.sample_id,
                task_id=plan.task_id,
                route_id=plan.route_id,
                seed=plan.seed,
                variation_policy=plan.variation_policy,
                variation_descriptor=plan.variation_descriptor,
                status="completed",
                raw_artifact_uri=raw_artifact_uri,
                adapter_result_uri=_sample_uri(plan.sample_id, "adapter_result.json"),
                evidence_bundle_uri=_sample_uri(plan.sample_id, "evidence_bundle.json"),
                experience_dataset_uri=_sample_uri(
                    plan.sample_id,
                    "experience_dataset.json",
                ),
                failure_boundary=(),
                evidence_notes=plan.evidence_notes,
            )
        )

    result = summarize_sample_runs(
        batch_id=spec.batch_id,
        route_id=spec.route_id,
        task_count=len(spec.task_specs),
        requested_sample_count=len(sample_plans),
        sample_runs=sample_runs,
        stage_boundary=spec.stage_boundary,
    )
    payload = result.to_dict()
    write_json_artifact(batch_dir / "batch_result.json", payload)
    return payload


def _sample_uri(sample_id: str, artifact_name: str) -> str:
    return str(Path("samples") / sample_id / artifact_name)


def _sample_metadata(plan: SimulationSamplePlan) -> dict[str, Any]:
    return {
        "batch_id": plan.batch_id,
        "sample_id": plan.sample_id,
        "seed": plan.seed,
        "variation_policy": plan.variation_policy,
        "variation_descriptor": plan.variation_descriptor,
    }


def _sample_artifact_metadata(plan: SimulationSamplePlan) -> dict[str, str]:
    return {
        "batch_id": plan.batch_id,
        "sample_id": plan.sample_id,
        "seed": str(plan.seed),
        "variation_policy": plan.variation_policy,
    }


def _sample_scoped_raw_artifact(
    plan: SimulationSamplePlan,
    artifact: RawManiSkillArtifact,
) -> RawManiSkillArtifact:
    return replace(
        artifact,
        run_id=f"maniskill-{plan.sample_id}",
        task_state={**artifact.task_state, **_sample_metadata(plan)},
        artifacts={**artifact.artifacts, **_sample_artifact_metadata(plan)},
    )


def _sample_scoped_adapter_result(
    plan: SimulationSamplePlan,
    adapter_result: SimulatorAdapterResult,
) -> SimulatorAdapterResult:
    return replace(
        adapter_result,
        planning_result={
            **adapter_result.planning_result,
            **_sample_metadata(plan),
        },
        artifacts={**adapter_result.artifacts, **_sample_artifact_metadata(plan)},
    )


def _sample_scoped_experience_dataset(
    plan: SimulationSamplePlan,
    experience_dataset: ExperienceDataset,
) -> ExperienceDataset:
    return replace(
        experience_dataset,
        dataset_id=f"experience-maniskill-{plan.sample_id}",
        samples=(plan.sample_id,),
    )


def _sample_scoped_evidence_bundle(
    plan: SimulationSamplePlan,
    evidence_bundle: SimulationEvidenceBundle,
) -> SimulationEvidenceBundle:
    run_record = replace(
        evidence_bundle.run_record,
        simulation_run_id=f"run-maniskill_sapien-{plan.sample_id}",
        seed=plan.seed,
        output_bundle_uris=[_sample_uri(plan.sample_id, "evidence_bundle.json")],
    )
    dataset = evidence_bundle.dataset
    if dataset is not None:
        samples = [
            replace(
                sample,
                sample_id=plan.sample_id,
                metadata={**sample.metadata, **_sample_metadata(plan)},
            )
            for sample in dataset.samples
        ]
        dataset = replace(
            dataset,
            dataset_id=f"dataset-maniskill_sapien-{plan.sample_id}",
            samples=samples,
        )
    return replace(
        evidence_bundle,
        bundle_id=f"evidence-maniskill-{plan.sample_id}",
        run_record=run_record,
        dataset=dataset,
    )


def _write_failure_artifact(
    sample_dir: Path,
    plan: SimulationSamplePlan,
    failure_boundary: tuple[FailureBoundary, ...],
    *,
    source_artifact: RawManiSkillArtifact | None = None,
) -> tuple[str, tuple[FailureBoundary, ...]]:
    failure_artifact = _failure_artifact(
        plan,
        failure_boundary,
        source_artifact=source_artifact,
    )
    try:
        write_json_artifact(sample_dir / "failure_artifact.json", failure_artifact)
        return _sample_uri(plan.sample_id, "failure_artifact.json"), failure_boundary
    except Exception:
        fallback_failure_boundary = _with_data_contract_incomplete(failure_boundary)
        fallback_artifact = _failure_artifact(
            plan,
            fallback_failure_boundary,
            source_artifact=source_artifact,
            extra_evidence_notes=("failure_artifact_write_failed",),
        )
        try:
            write_json_artifact(
                sample_dir / "failure_artifact_write_failed.json",
                fallback_artifact,
            )
            return (
                _sample_uri(plan.sample_id, "failure_artifact_write_failed.json"),
                fallback_failure_boundary,
            )
        except Exception:
            return (
                _sample_uri(plan.sample_id, "failure_artifact_unavailable.json"),
                fallback_failure_boundary,
            )


def _failed_sample_run(
    plan: SimulationSamplePlan,
    failure_boundary: tuple[FailureBoundary, ...],
    raw_artifact_uri: str,
    *,
    adapter_result_uri: str | None = None,
    evidence_bundle_uri: str | None = None,
    experience_dataset_uri: str | None = None,
    extra_evidence_notes: tuple[str, ...] = (),
) -> SimulationSampleRun:
    return SimulationSampleRun(
        batch_id=plan.batch_id,
        sample_id=plan.sample_id,
        task_id=plan.task_id,
        route_id=plan.route_id,
        seed=plan.seed,
        variation_policy=plan.variation_policy,
        variation_descriptor=plan.variation_descriptor,
        status="failed",
        raw_artifact_uri=raw_artifact_uri,
        adapter_result_uri=adapter_result_uri,
        evidence_bundle_uri=evidence_bundle_uri,
        experience_dataset_uri=experience_dataset_uri,
        failure_boundary=failure_boundary,
        evidence_notes=(
            *plan.evidence_notes,
            *_unavailable_evidence_notes(raw_artifact_uri),
            *extra_evidence_notes,
        ),
    )


def _failure_artifact(
    plan: SimulationSamplePlan,
    failure_boundary: tuple[FailureBoundary, ...],
    *,
    source_artifact: RawManiSkillArtifact | None = None,
    extra_evidence_notes: tuple[str, ...] = (),
) -> RawManiSkillArtifact:
    task_state = {}
    metrics: dict[str, float] = {
        "same_task_attempted": 1.0,
        "task_contract_outputs_ready": 0.0,
    }
    if source_artifact is not None:
        task_state.update(source_artifact.task_state)
        metrics.update(source_artifact.metrics)
    task_state.update(
        {
            "attempted": True,
            "batch_id": plan.batch_id,
            "sample_id": plan.sample_id,
            "seed": plan.seed,
            "variation_policy": plan.variation_policy,
            "variation_descriptor": plan.variation_descriptor,
            "task_status": "failed",
        }
    )
    metrics["task_contract_outputs_ready"] = 0.0

    return RawManiSkillArtifact(
        run_id=f"maniskill-{plan.sample_id}",
        task_id=plan.task_id,
        status="failed",
        tcp_trajectory=(),
        tool_orientation=(),
        task_state=task_state,
        metrics=metrics,
        failure_boundary=failure_boundary,
        artifacts={},
        evidence_notes=(*plan.evidence_notes, *extra_evidence_notes),
    )


def _unavailable_evidence_notes(artifact_uri: str) -> tuple[str, ...]:
    if artifact_uri.endswith("failure_artifact_unavailable.json"):
        return ("failure_artifact_unavailable",)
    return ()


def _with_data_contract_incomplete(
    failure_boundary: tuple[FailureBoundary, ...],
) -> tuple[FailureBoundary, ...]:
    if "data_contract_incomplete" in failure_boundary:
        return failure_boundary
    return (*failure_boundary, "data_contract_incomplete")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--outdir",
        default="artifacts/simulation/maniskill-sapien-batches",
    )
    parser.add_argument("--batch-id", default="maniskill-sapien-default-batch")
    parser.add_argument("--samples-per-task", type=int, default=10)
    parser.add_argument("--seed-start", type=int, default=0)
    args = parser.parse_args(argv)
    result = run_maniskill_batch_pipeline(
        args.outdir,
        batch_id=args.batch_id,
        samples_per_task=args.samples_per_task,
        seed_start=args.seed_start,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
