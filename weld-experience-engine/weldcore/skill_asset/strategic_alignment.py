from __future__ import annotations

from typing import Any

from weldcore.robot_process.model import RobotContextSpec, RobotFeasibilityResult

from .model import (
    A01B06SkillAssetMapping,
    A02ToA01ProductValidationHandoff,
    EvidenceSourceCatalogEntry,
    ExpertReviewRecord,
    IPDisclosureSupportMatrix,
    ManipulationSkillAsset,
    SceneContextAsset,
)


EXECUTION_BOUNDARY = (
    "candidate_artifact_only",
    "not_ready_for_robot_execution",
)


def build_default_evidence_source_catalog(
    skill_asset: ManipulationSkillAsset,
) -> tuple[EvidenceSourceCatalogEntry, ...]:
    return (
        EvidenceSourceCatalogEntry(
            source_type="simulation_only",
            role="baseline modeled evidence for skill asset candidates",
            status="available_from_default_builder",
            expected_fields=("task_spec", "tcp_trajectory", "tool_orientation", "metrics"),
            evidence_boundary=(
                "simulation_only",
                "not_real_robot_log",
                "not_real_welding_quality_validation",
            ),
            next_step_recommendation="Keep as baseline evidence and require expert review before real transfer.",
        ),
        EvidenceSourceCatalogEntry(
            source_type="human_demo",
            role="future human demonstration evidence for trajectory and correction labels",
            status="not_connected",
            expected_fields=("task_context", "trajectory", "human_correction", "quality_labels"),
            evidence_boundary=EXECUTION_BOUNDARY,
            next_step_recommendation="Collect demonstrations as review input, not robot programs.",
        ),
        EvidenceSourceCatalogEntry(
            source_type="real_robot_log",
            role="future real workcell execution evidence",
            status="not_connected",
            expected_fields=("execution_log", "robot_pose", "torch_pose", "anomaly", "quality_result"),
            evidence_boundary=EXECUTION_BOUNDARY,
            next_step_recommendation="Bind real logs after A01/H300 field validation is available.",
        ),
        EvidenceSourceCatalogEntry(
            source_type="h300_workcell_run",
            role="A01 H300 workcell run evidence for product validation",
            status="contract_defined_not_connected",
            expected_fields=("task", "weld_seam", "path_points", "manual_correction", "quality_result"),
            evidence_boundary=("not_WPS_PQR",) + EXECUTION_BOUNDARY,
            next_step_recommendation="Use as A01 evidence mapping once real workcell callbacks exist.",
        ),
        EvidenceSourceCatalogEntry(
            source_type="expert_annotation",
            role="expert review decision and blocking context",
            status="record_schema_available",
            expected_fields=("review_status", "blocking_reasons", "required_real_context", "next_actions"),
            evidence_boundary=EXECUTION_BOUNDARY,
            next_step_recommendation="Attach reviewer conclusion after real context evidence is supplied.",
        ),
    )


def build_a01_b06_skill_asset_mapping(
    skill_asset: ManipulationSkillAsset,
) -> A01B06SkillAssetMapping:
    return A01B06SkillAssetMapping(
        mapping_id=f"a01-b06-map-{skill_asset.asset_id}",
        source_system="A01_H300_workcell_and_B06_Physical_AI_Package",
        target_skill_asset_id=skill_asset.asset_id,
        evidence_source_type="h300_workcell_run",
        workcell_fields=(
            "task",
            "weld_seam",
            "workpiece",
            "path_points",
            "robot_pose",
            "torch_pose",
            "process_parameters",
            "manual_correction",
            "execution_log",
            "anomaly",
            "quality_result",
        ),
        package_fields=(
            "physical_ai_package_profile",
            "task_context",
            "coordinate_frames",
            "frames",
            "events",
            "labels",
            "trajectory",
            "human_correction",
            "metrics",
            "quality_labels",
            "rerun_replay_ref",
        ),
        skill_asset_field_mapping={
            "task": "intent",
            "weld_seam": "intent.seam",
            "workpiece": "SceneContextAsset",
            "path_points": "motion.tcp_trajectory",
            "robot_pose": "RobotContextSpec",
            "torch_pose": "motion.tool_orientation",
            "process_parameters": "constraints",
            "manual_correction": "evidence.review_input",
            "execution_log": "evidence.artifact_refs",
            "anomaly": "evidence.evidence_boundary",
            "task_context": "intent",
            "coordinate_frames": "RobotContextSpec_and_SceneContextAsset",
            "trajectory": "motion.tcp_trajectory",
            "human_correction": "evidence.review_input",
            "metrics": "evidence.metrics",
            "quality_labels": "quality_feedback_evidence",
            "rerun_replay_ref": "artifact_refs",
        },
        context_mapping={
            "coordinate_frames": "robot_context_and_scene_context",
            "workpiece": "scene_context.workpiece_frame",
            "robot_pose": "robot_context.base_frame",
        },
        quality_feedback_mapping={
            "quality_result": "quality_feedback_evidence",
            "quality_labels": "quality_feedback_evidence",
        },
        artifact_refs={
            "physical_ai_package_profile": "B06_Physical_AI_Package",
            "rerun_replay_ref": "external_artifact_ref_only",
        },
        evidence_boundary=(
            "mapping_contract_only",
            "not_A01_connector",
            "not_B06_parser",
            "not_WPS_PQR",
            "not_ready_for_robot_execution",
        ),
        next_step_recommendation=(
            "Use this field contract to map H300 run callbacks and Physical AI Package artifacts "
            "into skill asset review evidence."
        ),
    )


def build_default_expert_review_record(
    skill_asset: ManipulationSkillAsset,
    robot_context: RobotContextSpec,
    scene_context: SceneContextAsset,
    feasibility_result: RobotFeasibilityResult,
) -> ExpertReviewRecord:
    return ExpertReviewRecord(
        review_id=f"expert-review-{skill_asset.asset_id}",
        skill_asset_id=skill_asset.asset_id,
        robot_context_id=robot_context.context_id,
        scene_context_id=scene_context.scene_id,
        feasibility_result_id=feasibility_result.result_id,
        robot_context_snapshot={
            "context_id": robot_context.context_id,
            "robot_model": robot_context.robot_model,
            "tcp_calibration_status": robot_context.tcp_calibration_status,
            "workpiece_frame": robot_context.workpiece_frame,
            "joint_limits_source": robot_context.joint_limits_source,
            "evidence_notes": tuple(robot_context.evidence_notes)
            + ("not_ready_for_robot_execution",),
        },
        scene_context_snapshot={
            "scene_id": scene_context.scene_id,
            "workpiece_frame": scene_context.workpiece_frame,
            "validation_status": scene_context.validation_status,
            "validation_issues": scene_context.validation_issues,
            "evidence_boundary": scene_context.evidence_boundary,
        },
        feasibility_status_snapshot={
            "result_id": feasibility_result.result_id,
            "status": feasibility_result.status,
            "reachability_status": feasibility_result.reachability_status,
            "collision_status": feasibility_result.collision_status,
            "joint_limit_status": feasibility_result.joint_limit_status,
            "path_continuity_status": feasibility_result.path_continuity_status,
            "orientation_feasibility_status": feasibility_result.orientation_feasibility_status,
            "blocking_reasons": feasibility_result.blocking_reasons,
            "warning_reasons": feasibility_result.warning_reasons,
            "evidence_boundary": feasibility_result.evidence_boundary,
        },
        source_evidence_summary={
            "source_type": skill_asset.source_type,
            "source_id": skill_asset.evidence.source_id,
            "review_status": skill_asset.evidence.review_status,
            "evidence_boundary": skill_asset.evidence.evidence_boundary,
        },
        review_status="pending_expert_review",
        review_conclusion=None,
        blocking_reasons=(
            "missing_real_tcp_calibration",
            "missing_workpiece_frame_measurement",
            "missing_robot_identity_confirmation",
            "missing_vendor_joint_limits_confirmation",
        ),
        required_real_context=_required_real_context(),
        next_actions=(
            "collect_real_tcp_calibration",
            "measure_workpiece_frame",
            "confirm_robot_model_identity",
            "confirm_joint_limits_source",
            "expert_review_before_robot_execution",
        ),
        review_boundary=(
            "expert_review_candidate_only",
            "not_ready_for_robot_execution",
            "not_collision_validated",
            "not_full_ik_solver",
        ),
        reviewer_role="welding_robotics_domain_expert",
    )


def build_a02_to_a01_product_validation_handoff(
    skill_asset: ManipulationSkillAsset,
) -> A02ToA01ProductValidationHandoff:
    return A02ToA01ProductValidationHandoff(
        handoff_id=f"a02-to-a01-handoff-{skill_asset.asset_id}",
        skill_asset_id=skill_asset.asset_id,
        target_product="A01_H300_workcell",
        candidate_outputs=(
            "skill_package_candidate",
            "trajectory_candidate",
            "torch_posture_suggestion",
            "process_parameter_hint",
            "failure_boundary_summary",
        ),
        trajectory_candidate_ref="motion.tcp_trajectory",
        posture_parameter_suggestions={
            "torch_orientation_ref": "motion.tool_orientation",
            "process_parameter_ref": "constraints",
            "status": "candidate_hint_only",
        },
        failure_boundaries=(
            "not_direct_robot_program",
            "not_ready_for_robot_execution",
            "not_collision_validated",
            "not_full_ik_solver",
            "not_WPS_PQR",
        ),
        required_confirmations=(
            "real_tcp_calibration",
            "workpiece_frame_measurement",
            "robot_model_identity",
            "joint_limits_source",
            "expert_review_conclusion",
        ),
        not_ready_reasons=(
            "candidate_handoff_only",
            "requires_A01_product_validation",
            "requires_real_workcell_evidence",
        ),
        evidence_refs=tuple(
            ref for ref in skill_asset.source_refs.values() if ref is not None
        ),
        handoff_boundary=(
            "candidate_handoff_only",
            "not_direct_robot_program",
            "not_production_dispatch_package",
            "not_ready_for_robot_execution",
        ),
        next_step_recommendation=(
            "Use this handoff as A01 product validation input and prompt material, not as a "
            "controller-downloadable robot program."
        ),
    )


def build_ip_disclosure_support_matrix(
    skill_asset: ManipulationSkillAsset,
) -> IPDisclosureSupportMatrix:
    return IPDisclosureSupportMatrix(
        support_id=f"ip-support-{skill_asset.asset_id}",
        skill_asset_id=skill_asset.asset_id,
        items=(
            {
                "patent_item_id": "P0-02",
                "patent_item_name": "焊接技能包",
                "supporting_objects": (
                    "ManipulationSkillAsset",
                    "SkillAssetEvidence",
                    "ExpertReviewRecord",
                    "SkillAssetEvidenceWritebackSummary",
                ),
                "supporting_reports": (
                    "skill_asset_report.json",
                    "expert_review_record.json",
                    "skill_asset_evidence_writeback_summary.json",
                ),
                "evidence_boundaries": ("candidate_skill_package_only", "not_WPS_PQR"),
                "missing_real_world_evidence": (
                    "expert_review_conclusion",
                    "real_workcell_quality_feedback",
                    "real_robot_execution_log",
                ),
                "next_evidence_actions": (
                    "complete_expert_review",
                    "bind_real_A01_H300_workcell_run",
                ),
            },
            {
                "patent_item_id": "P0-03",
                "patent_item_name": "焊接轨迹结构化转换",
                "supporting_objects": (
                    "motion.tcp_trajectory",
                    "motion.tool_orientation",
                    "A01_B06_mapping.path_points",
                    "A01_B06_mapping.robot_pose",
                    "A01_B06_mapping.torch_pose",
                    "A01_B06_mapping.manual_correction",
                ),
                "supporting_reports": (
                    "skill_asset_report.json",
                    "a01_b06_skill_asset_mapping.json",
                ),
                "evidence_boundaries": ("mapping_contract_only", "not_direct_robot_program"),
                "missing_real_world_evidence": (
                    "real_path_points_from_H300",
                    "manual_correction_records",
                    "real_pose_alignment_evidence",
                ),
                "next_evidence_actions": (
                    "collect_H300_path_pose_callbacks",
                    "attach_manual_correction_samples",
                ),
            },
            {
                "patent_item_id": "P0-04",
                "patent_item_name": "仿真优先焊接技能数据集",
                "supporting_objects": (
                    "SimulationEvidenceBundle",
                    "modeled_task_specs",
                    "100_requested_samples",
                    "500_requested_samples",
                    "1000_requested_samples",
                    "SkillAssetEvidenceWritebackSummary",
                ),
                "supporting_reports": (
                    "skill_asset_report.json",
                    "skill_asset_evidence_writeback_summary.json",
                    "skill_asset_evidence_source_catalog.json",
                ),
                "evidence_boundaries": ("simulation_only", "not_real_robot_log"),
                "missing_real_world_evidence": (
                    "real_workcell_return_samples",
                    "expert_reviewed_quality_labels",
                    "real_welding_quality_feedback",
                ),
                "next_evidence_actions": (
                    "cross_check_simulation_candidates_with_real_workcell_data",
                    "add_expert_quality_labels",
                ),
            },
        ),
        evidence_boundary=(
            "ip_disclosure_support_only",
            "not_claim_chart",
            "not_ready_for_robot_execution",
        ),
        next_step_recommendation=(
            "Use the matrix as a disclosure evidence checklist and fill missing real-world "
            "evidence before formal claim drafting."
        ),
    )


def _required_real_context() -> tuple[dict[str, Any], ...]:
    return (
        {
            "field": "real_tcp_calibration",
            "current_status": "nominal_from_asset_not_calibrated",
            "required_evidence": (
                "TCP calibration record, tool coordinate frame version, calibration time or source"
            ),
            "blocking_if_missing": True,
        },
        {
            "field": "workpiece_frame_measurement",
            "current_status": "default_scene_context_not_measured",
            "required_evidence": (
                "Workpiece frame measurement record, coordinate frame source, measurement time or source"
            ),
            "blocking_if_missing": True,
        },
        {
            "field": "robot_model_identity",
            "current_status": "urdf_asset_identity_only",
            "required_evidence": "Real robot model, serial number or internal asset ID matching the URDF",
            "blocking_if_missing": True,
        },
        {
            "field": "joint_limits_source",
            "current_status": "urdf_joint_limits_not_vendor_validated",
            "required_evidence": "Vendor, controller or confirmed joint limit source",
            "blocking_if_missing": True,
        },
    )
