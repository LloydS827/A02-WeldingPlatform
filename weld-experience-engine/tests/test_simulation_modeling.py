from dataclasses import replace

from weldcore.simulation_bakeoff import (
    BatchModelingSpec,
    ModeledSimulationTask,
    TaskModelingVariation,
    build_modeled_simulation_tasks,
    build_modeling_validation_report,
    default_batch_modeling_spec,
    default_maniskill_batch_spec,
    default_simulation_task_specs,
    iter_batch_sample_plans,
    modeled_task_specs,
    modeling_batch_spec_compatibility,
    simulation_task_specs_from_modeling_payload,
)


def _modeled_with_ids(task, *, modeled_id, task_spec_id, variation_id):
    variation = TaskModelingVariation(
        source_task_id=task.source_task_id,
        modeled_task_id=variation_id,
        variation_index=task.variation.variation_index,
        variation_descriptor={
            **task.variation.variation_descriptor,
            "modeled_task_id": variation_id,
        },
        assumption_notes=task.variation.assumption_notes,
        evidence_notes=task.variation.evidence_notes,
    )
    return ModeledSimulationTask(
        modeled_task_id=modeled_id,
        source_task_id=task.source_task_id,
        variation=variation,
        task_spec=replace(task.task_spec, task_id=task_spec_id),
        path_geometry_changed=task.path_geometry_changed,
    )


def test_default_batch_modeling_spec_generates_eight_modeled_tasks():
    spec = default_batch_modeling_spec(
        modeling_batch_id="modeling-test",
        variants_per_task=4,
    )

    modeled = build_modeled_simulation_tasks(spec)

    assert isinstance(spec, BatchModelingSpec)
    assert spec.variants_per_task == 4
    assert len(spec.source_task_specs) == 2
    assert len(modeled) == 8
    assert all(isinstance(task, ModeledSimulationTask) for task in modeled)
    assert len({task.task_spec.task_id for task in modeled}) == 8
    assert all(task.task_spec.task_id.startswith("modeled-") for task in modeled)


def test_modeled_tasks_change_path_geometry_not_only_metadata():
    source_by_id = {task.task_id: task for task in default_simulation_task_specs()}
    modeled = build_modeled_simulation_tasks(default_batch_modeling_spec())

    for task in modeled:
        source = source_by_id[task.source_task_id]
        assert task.path_geometry_changed is True
        assert task.task_spec.seam_path != source.seam_path
        assert len(task.task_spec.seam_path) == len(source.seam_path)
        assert task.variation.modeled_task_id == task.task_spec.task_id
        assert (
            task.variation.variation_descriptor["policy"]
            == "deterministic_geometry_variation"
        )
        assert "simulation_modeling_assumption" in task.variation.assumption_notes
        assert "not_real_welding_process_parameter" in task.variation.evidence_notes


def test_modeling_validation_report_is_ready_and_lists_candidates():
    spec = default_batch_modeling_spec(modeling_batch_id="modeling-test")
    modeled = build_modeled_simulation_tasks(spec)

    report = build_modeling_validation_report(spec, modeled)

    assert report.status == "ready_for_simulation_batch"
    assert report.source_task_count == 2
    assert report.modeled_task_count == 8
    assert report.valid_modeled_task_count == 8
    assert report.expert_review_candidate_count == 8
    assert report.expert_review_candidate_ratio == 1.0
    assert report.expert_review_candidate_task_ids == tuple(
        task.task_spec.task_id for task in modeled
    )
    assert report.issues == ()
    assert report.coverage_summary.modeled_task_per_source_task == {
        task.task_id: 4 for task in spec.source_task_specs
    }
    assert "not_final_simulator_selection" in report.known_limitations


def test_modeled_task_specs_feed_existing_batch_spec_layer():
    modeled = build_modeled_simulation_tasks(default_batch_modeling_spec())
    task_specs = modeled_task_specs(modeled)

    batch_spec = default_maniskill_batch_spec(
        batch_id="modeled-batch",
        task_specs=task_specs,
        samples_per_task=2,
    )
    sample_plans = tuple(iter_batch_sample_plans(batch_spec))

    assert len(batch_spec.task_specs) == 8
    assert len(sample_plans) == 16
    assert {plan.task_id for plan in sample_plans} == {
        task.task_id for task in task_specs
    }


def test_modeling_batch_spec_compatibility_summary():
    modeled = build_modeled_simulation_tasks(default_batch_modeling_spec())

    compatibility = modeling_batch_spec_compatibility(
        modeled,
        samples_per_task=2,
    )

    assert compatibility["batch_task_count"] == 8
    assert compatibility["requested_sample_count"] == 16
    assert compatibility["compatible_with"] == "default_maniskill_batch_spec"


def test_validation_report_blocks_incomplete_modeling_batch():
    spec = default_batch_modeling_spec()
    modeled = build_modeled_simulation_tasks(spec)

    report = build_modeling_validation_report(spec, (modeled[0],))

    issues = {issue.issue for issue in report.issues}
    assert report.status == "blocked_by_modeling_issue"
    assert "missing_modeled_task:modeled-task-long-straight-horizontal-tracking-v01" in issues
    assert "missing_modeled_task:modeled-task-corner-horizontal-transition-v00" in issues
    assert report.expert_review_candidate_count == 0
    assert report.expert_review_candidate_ratio == 0.0


def test_validation_report_blocks_duplicate_and_inconsistent_modeled_ids():
    spec = default_batch_modeling_spec()
    modeled = build_modeled_simulation_tasks(spec)
    inconsistent = _modeled_with_ids(
        modeled[1],
        modeled_id=modeled[0].modeled_task_id,
        task_spec_id="different-task-spec-id",
        variation_id="different-variation-id",
    )

    report = build_modeling_validation_report(spec, (modeled[0], inconsistent))

    issues = {issue.issue for issue in report.issues}
    assert report.status == "blocked_by_modeling_issue"
    assert "modeled_task_id_not_unique" in issues
    assert "modeled_task_id_mismatch" in issues
    assert report.expert_review_candidate_ratio == 0.0


def test_validation_report_blocks_invalid_modeled_task_contract():
    spec = default_batch_modeling_spec()
    modeled = build_modeled_simulation_tasks(spec)
    invalid_spec = replace(
        modeled[0].task_spec,
        expected_outputs=(),
        evaluation_metrics=(),
        out_of_scope=(),
    )
    invalid = ModeledSimulationTask(
        modeled_task_id=modeled[0].modeled_task_id,
        source_task_id="missing-source-task",
        variation=modeled[0].variation,
        task_spec=invalid_spec,
        path_geometry_changed=False,
    )

    report = build_modeling_validation_report(spec, (invalid,))

    issues = {issue.issue for issue in report.issues}
    assert "source_task_id_not_found" in issues
    assert "missing_expected_output:tcp_trajectory" in issues
    assert "missing_metric:path_continuity" in issues
    assert "missing_out_of_scope:real_welding_quality" in issues
    assert "path_geometry_not_changed" in issues


def test_build_modeled_tasks_rejects_empty_source_path():
    source = default_simulation_task_specs()[0]
    empty_path_source = replace(source, seam_path=())
    spec = default_batch_modeling_spec(source_task_specs=(empty_path_source,))

    try:
        build_modeled_simulation_tasks(spec)
    except ValueError as exc:
        assert str(exc) == "source task seam_path must not be empty"
    else:
        raise AssertionError("expected empty source seam_path to fail clearly")


def test_modeling_payload_round_trips_to_batch_task_specs():
    modeled = build_modeled_simulation_tasks(default_batch_modeling_spec())
    payload = [task.to_dict() for task in modeled_task_specs(modeled)]

    restored = simulation_task_specs_from_modeling_payload(payload)
    batch_spec = default_maniskill_batch_spec(
        batch_id="restored-modeled-batch",
        task_specs=restored,
        samples_per_task=2,
    )
    sample_plans = tuple(iter_batch_sample_plans(batch_spec))

    assert len(restored) == 8
    assert restored[0].seam_path[0].x == modeled[0].task_spec.seam_path[0].x
    assert len(sample_plans) == 16
