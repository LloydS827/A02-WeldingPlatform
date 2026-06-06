from __future__ import annotations

from typing import Any

from weldcore.simulation_bakeoff.model import SimulationEvidenceBundle

from .model import (
    BASE_ROBOT_PROCESS_EVIDENCE_BOUNDARY,
    ProcessParameterStatus,
    RobotExecutionReadiness,
    RobotExecutionSpec,
    RobotProcessDraftStatus,
    RobotProcessPackageDraft,
)

REQUIRED_ROBOT_CONTEXT = (
    "robot_model",
    "workpiece_frame",
    "tcp_calibration",
    "reachability_result",
    "collision_result",
    "joint_limit_result",
)


def build_robot_process_package_draft(
    evidence_bundle: SimulationEvidenceBundle,
) -> RobotProcessPackageDraft:
    readiness = _readiness(evidence_bundle)
    status: RobotProcessDraftStatus = (
        "blocked" if readiness.startswith("blocked_by_") else "draft"
    )
    return RobotProcessPackageDraft(
        draft_id=f"draft-{evidence_bundle.bundle_id}",
        source_bundle_id=evidence_bundle.bundle_id,
        source_task_id=evidence_bundle.task_spec.task_id,
        source_type="simulation",
        status=status,
        source_evidence=_source_evidence(evidence_bundle),
        process_parameter_status=_process_parameter_status(evidence_bundle),
        robot_execution_spec=_robot_execution_spec(evidence_bundle, readiness),
        readiness=readiness,
        evidence_boundary=_evidence_boundary(evidence_bundle),
    )


def _readiness(evidence_bundle: SimulationEvidenceBundle) -> RobotExecutionReadiness:
    adapter_result = evidence_bundle.adapter_result
    if adapter_result.status != "completed":
        return "blocked_by_failed_simulation"
    if evidence_bundle.dataset is None:
        return "blocked_by_missing_dataset"
    if not adapter_result.tcp_trajectory:
        return "blocked_by_missing_trajectory"
    if not adapter_result.tool_orientation:
        return "blocked_by_missing_orientation"
    if _missing_robot_context(evidence_bundle):
        return "blocked_by_missing_robot_context"
    return "draft"


def _missing_robot_context(evidence_bundle: SimulationEvidenceBundle) -> tuple[str, ...]:
    planning_result = evidence_bundle.adapter_result.planning_result
    return tuple(
        field
        for field in REQUIRED_ROBOT_CONTEXT
        if not _context_available(planning_result, field)
    )


def _robot_execution_spec(
    evidence_bundle: SimulationEvidenceBundle,
    readiness: RobotExecutionReadiness,
) -> RobotExecutionSpec:
    adapter_result = evidence_bundle.adapter_result
    task_spec = evidence_bundle.task_spec
    planning_result = adapter_result.planning_result
    failed = readiness == "blocked_by_failed_simulation"
    return RobotExecutionSpec(
        robot_model=planning_result.get("robot_model"),
        tcp_frame=task_spec.tcp_frame,
        workpiece_frame=planning_result.get("workpiece_frame"),
        trajectory=() if failed else adapter_result.tcp_trajectory,
        tool_orientation=() if failed else adapter_result.tool_orientation,
        travel_speed=adapter_result.metrics.get("travel_speed"),
        reachability_status=_context_status(planning_result, "reachability_result"),
        collision_status=_context_status(planning_result, "collision_result"),
        joint_limit_status=_context_status(planning_result, "joint_limit_result"),
        execution_notes=(
            "simulation_only",
            "not_ready_for_robot_execution",
            readiness,
        ),
        missing_robot_context=_missing_robot_context(evidence_bundle),
    )


def _context_status(planning_result: dict[str, Any], key: str) -> str:
    return "available" if _context_available(planning_result, key) else "missing"


def _context_available(planning_result: dict[str, Any], key: str) -> bool:
    return key in planning_result and planning_result[key] is not None


def _source_evidence(evidence_bundle: SimulationEvidenceBundle) -> dict[str, Any]:
    dataset_id = evidence_bundle.dataset.dataset_id if evidence_bundle.dataset else None
    return {
        "bundle_id": evidence_bundle.bundle_id,
        "task_id": evidence_bundle.task_spec.task_id,
        "adapter_name": evidence_bundle.adapter_result.adapter_name,
        "adapter_status": evidence_bundle.adapter_result.status,
        "run_record_id": evidence_bundle.run_record.simulation_run_id,
        "dataset_id": dataset_id,
        "failure_boundary": list(evidence_bundle.adapter_result.failure_boundary),
        "metrics": dict(evidence_bundle.adapter_result.metrics),
    }


def _process_parameter_status(
    evidence_bundle: SimulationEvidenceBundle,
) -> tuple[ProcessParameterStatus, ...]:
    adapter_result = evidence_bundle.adapter_result
    motion_available = bool(adapter_result.tcp_trajectory and adapter_result.tool_orientation)
    motion_statuses = (
        ("available_from_simulation",)
        if motion_available
        else ("missing_required",)
    )
    return (
        ProcessParameterStatus(
            group_name="motion_parameters",
            statuses=motion_statuses,
            available_fields=(
                "tcp_trajectory",
                "tool_orientation",
                "motion_constraint",
                "task_status",
                "metrics",
            )
            if motion_available
            else (),
            missing_fields=() if motion_available else ("tcp_trajectory", "tool_orientation"),
            required_future_sources=(),
            evidence_notes=("from_simulation_evidence",),
        ),
        ProcessParameterStatus(
            group_name="process_parameters",
            statuses=(
                "missing_required",
                "requires_expert_review",
                "requires_real_validation",
            ),
            available_fields=(),
            missing_fields=(
                "welding_current",
                "welding_voltage",
                "wire_feed_speed",
                "heat_input",
                "real_travel_speed",
            ),
            required_future_sources=(
                "expert_review",
                "welder_process_data",
                "quality_feedback",
            ),
            evidence_notes=("simulation_motion_is_not_process_parameter_validation",),
        ),
        ProcessParameterStatus(
            group_name="material_parameters",
            statuses=("missing_required", "requires_expert_review"),
            available_fields=(),
            missing_fields=("base_material_grade", "base_material_thickness", "filler_model"),
            required_future_sources=("expert_review",),
            evidence_notes=("not_filled_from_manual_parameter_table",),
        ),
        ProcessParameterStatus(
            group_name="joint_parameters",
            statuses=("partially_available_from_simulation", "requires_expert_review"),
            available_fields=("task_id", "unit_id"),
            missing_fields=("joint_type", "groove_type", "root_gap", "leg_size"),
            required_future_sources=("expert_review",),
            evidence_notes=("unit_id_is_not_full_joint_definition",),
        ),
        ProcessParameterStatus(
            group_name="gas_parameters",
            statuses=("conditionally_missing", "requires_expert_review"),
            available_fields=(),
            missing_fields=("shielding_gas_type", "gas_composition", "gas_flow"),
            required_future_sources=("expert_review",),
            evidence_notes=("gas_fields_not_required_for_current_simulation_task",),
        ),
        ProcessParameterStatus(
            group_name="quality_requirements",
            statuses=("requires_real_validation",),
            available_fields=(),
            missing_fields=("visual_inspection_standard", "ndt_method", "ndt_level"),
            required_future_sources=("quality_feedback",),
            evidence_notes=("simulation_does_not_prove_welding_quality",),
        ),
        ProcessParameterStatus(
            group_name="procedure_links",
            statuses=("missing_required", "not_WPS_PQR", "requires_expert_review"),
            available_fields=(),
            missing_fields=("wps_id", "pqr_id", "applicable_equipment_model"),
            required_future_sources=("expert_review",),
            evidence_notes=("system_does_not_generate_or_replace_wps_pqr",),
        ),
        ProcessParameterStatus(
            group_name="robot_context",
            statuses=("requires_robot_context",),
            available_fields=("tcp_frame",),
            missing_fields=_missing_robot_context(evidence_bundle),
            required_future_sources=("real_robot_log", "robot_context"),
            evidence_notes=("readiness_state_is_recorded_separately",),
        ),
        ProcessParameterStatus(
            group_name="validation_requirements",
            statuses=("requires_expert_review", "requires_real_validation"),
            available_fields=(),
            missing_fields=("expert_review", "real_robot_validation", "quality_feedback"),
            required_future_sources=(
                "expert_review",
                "real_robot_log",
                "quality_feedback",
            ),
            evidence_notes=("future_validation_not_part_of_v1_pipeline",),
        ),
    )


def _evidence_boundary(evidence_bundle: SimulationEvidenceBundle) -> tuple[str, ...]:
    boundaries = list(BASE_ROBOT_PROCESS_EVIDENCE_BOUNDARY)
    for boundary in evidence_bundle.adapter_result.failure_boundary:
        if boundary not in boundaries:
            boundaries.append(boundary)
    return tuple(boundaries)
