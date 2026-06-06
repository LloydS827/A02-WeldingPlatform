import inspect
from dataclasses import replace

from weldcore.robot_process import build_robot_process_package_draft
from weldcore.simulation_bakeoff import (
    attempt_gazebo_moveit,
    build_simulation_evidence_bundle,
    default_simulation_task_specs,
    run_simlite_reference,
)


EXPECTED_GROUPS = {
    "motion_parameters",
    "process_parameters",
    "material_parameters",
    "joint_parameters",
    "gas_parameters",
    "quality_requirements",
    "procedure_links",
    "robot_context",
    "validation_requirements",
}


def _completed_bundle():
    task_spec = default_simulation_task_specs()[0]
    return build_simulation_evidence_bundle(task_spec, run_simlite_reference(task_spec))


def _failed_bundle():
    task_spec = default_simulation_task_specs()[0]
    return build_simulation_evidence_bundle(task_spec, attempt_gazebo_moveit(task_spec))


def _group(draft, name):
    return next(group for group in draft.process_parameter_status if group.group_name == name)


def test_pipeline_accepts_only_simulation_evidence_bundle_input():
    signature = inspect.signature(build_robot_process_package_draft)

    assert tuple(signature.parameters) == ("evidence_bundle",)


def test_completed_simulation_evidence_builds_blocked_draft_without_robot_context():
    bundle = _completed_bundle()

    draft = build_robot_process_package_draft(bundle)
    data = draft.to_dict()

    assert draft.source_bundle_id == bundle.bundle_id
    assert draft.source_task_id == bundle.task_spec.task_id
    assert draft.source_type == "simulation"
    assert draft.status == "blocked"
    assert draft.readiness == "blocked_by_missing_robot_context"
    assert len(draft.robot_execution_spec.trajectory) == len(bundle.adapter_result.tcp_trajectory)
    assert draft.robot_execution_spec.tcp_frame == bundle.task_spec.tcp_frame
    assert "robot_model" in draft.robot_execution_spec.missing_robot_context
    assert set(group.group_name for group in draft.process_parameter_status) == EXPECTED_GROUPS
    assert "simulation_only" in draft.evidence_boundary
    assert "not_WPS_PQR" in draft.evidence_boundary
    assert "not_real_welding_quality_validation" in draft.evidence_boundary
    assert "not_ready_for_robot_execution" in draft.evidence_boundary
    assert data["source_evidence"]["adapter_name"] == "simlite_reference"


def test_failed_simulation_evidence_builds_failed_blocked_draft():
    bundle = _failed_bundle()

    draft = build_robot_process_package_draft(bundle)

    assert draft.status == "blocked"
    assert draft.readiness == "blocked_by_failed_simulation"
    assert draft.robot_execution_spec.trajectory == ()
    assert draft.robot_execution_spec.tool_orientation == ()
    for boundary in bundle.adapter_result.failure_boundary:
        assert boundary in draft.evidence_boundary


def test_readiness_priority_prefers_failed_simulation_over_missing_dataset():
    bundle = _failed_bundle()

    draft = build_robot_process_package_draft(bundle)

    assert bundle.dataset is None
    assert draft.readiness == "blocked_by_failed_simulation"


def test_readiness_priority_detects_missing_dataset_before_trajectory():
    bundle = _completed_bundle()
    adapter_result = replace(bundle.adapter_result, tcp_trajectory=())
    bundle = replace(bundle, adapter_result=adapter_result, dataset=None)

    draft = build_robot_process_package_draft(bundle)

    assert draft.readiness == "blocked_by_missing_dataset"


def test_readiness_priority_detects_missing_trajectory_before_orientation():
    bundle = _completed_bundle()
    adapter_result = replace(
        bundle.adapter_result,
        tcp_trajectory=(),
        tool_orientation=(),
    )
    bundle = replace(bundle, adapter_result=adapter_result)

    draft = build_robot_process_package_draft(bundle)

    assert draft.readiness == "blocked_by_missing_trajectory"


def test_readiness_priority_detects_missing_orientation_before_robot_context():
    bundle = _completed_bundle()
    adapter_result = replace(bundle.adapter_result, tool_orientation=())
    bundle = replace(bundle, adapter_result=adapter_result)

    draft = build_robot_process_package_draft(bundle)

    assert draft.readiness == "blocked_by_missing_orientation"


def test_process_parameter_groups_record_future_sources_without_manual_json():
    draft = build_robot_process_package_draft(_completed_bundle())

    motion = _group(draft, "motion_parameters")
    process = _group(draft, "process_parameters")
    robot = _group(draft, "robot_context")
    procedure = _group(draft, "procedure_links")

    assert motion.statuses == ("available_from_simulation",)
    assert "tcp_trajectory" in motion.available_fields
    assert "missing_required" in process.statuses
    assert "requires_real_validation" in process.statuses
    assert "expert_review" in process.required_future_sources
    assert robot.statuses == ("requires_robot_context",)
    assert "blocked_by_missing_robot_context" not in robot.statuses
    assert "not_WPS_PQR" in procedure.statuses


def test_pipeline_does_not_make_reserved_readiness_states_reachable():
    draft = build_robot_process_package_draft(_completed_bundle())

    assert draft.readiness not in {
        "needs_review",
        "ready_for_expert_review",
        "ready_for_robot_execution",
    }
