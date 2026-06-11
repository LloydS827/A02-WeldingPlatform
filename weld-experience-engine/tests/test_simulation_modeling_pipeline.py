import json

from weldcore.simulation_bakeoff.modeling_pipeline import (
    run_batch_modeling_pipeline,
)
from weldcore.simulation_bakeoff import (
    default_maniskill_batch_spec,
    iter_batch_sample_plans,
    simulation_task_specs_from_modeling_payload,
)


def test_batch_modeling_pipeline_writes_artifacts(tmp_path):
    result = run_batch_modeling_pipeline(
        tmp_path,
        modeling_batch_id="modeling-test",
        variants_per_task=4,
    )

    batch_dir = tmp_path / "modeling-test"
    assert (batch_dir / "modeling_spec.json").exists()
    assert (batch_dir / "modeled_task_specs.json").exists()
    assert (batch_dir / "modeling_validation_report.json").exists()

    modeled_specs = json.loads(
        (batch_dir / "modeled_task_specs.json").read_text(encoding="utf-8")
    )
    report = json.loads(
        (batch_dir / "modeling_validation_report.json").read_text(encoding="utf-8")
    )

    assert len(modeled_specs) == 8
    assert report["status"] == "ready_for_simulation_batch"
    assert report["expert_review_candidate_count"] == 8
    assert result["status"] == "ready_for_simulation_batch"

    restored_specs = simulation_task_specs_from_modeling_payload(modeled_specs)
    batch_spec = default_maniskill_batch_spec(
        task_specs=restored_specs,
        samples_per_task=2,
    )
    assert len(tuple(iter_batch_sample_plans(batch_spec))) == 16


def test_batch_modeling_pipeline_main_prints_json(tmp_path, capsys):
    from weldcore.simulation_bakeoff import modeling_pipeline

    modeling_pipeline.main(
        [
            "--outdir",
            str(tmp_path),
            "--modeling-batch-id",
            "modeling-cli",
            "--variants-per-task",
            "4",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert output["modeling_batch_id"] == "modeling-cli"
    assert output["status"] == "ready_for_simulation_batch"
