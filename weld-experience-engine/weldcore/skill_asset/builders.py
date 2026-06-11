from __future__ import annotations

from weldcore.simulation_bakeoff.model import SimulationEvidenceBundle

from .model import ManipulationSkillAsset, SkillAssetEvidence, SkillTransferContract


DEFAULT_TRANSFER_CHECKS = (
    "reachability",
    "collision",
    "joint_limits",
    "tcp_calibration",
    "workpiece_frame",
    "path_continuity",
    "orientation_feasibility",
    "expert_review",
)


def build_manipulation_skill_asset_from_simulation_bundle(
    bundle: SimulationEvidenceBundle,
) -> ManipulationSkillAsset:
    task_spec = bundle.task_spec
    adapter_result = bundle.adapter_result
    dataset_id = bundle.dataset.dataset_id if bundle.dataset is not None else None

    evidence = SkillAssetEvidence(
        source_type="simulation",
        source_id=bundle.bundle_id,
        adapter_name=adapter_result.adapter_name,
        status=adapter_result.status,
        metrics=dict(adapter_result.metrics),
        artifact_refs=dict(adapter_result.artifacts),
        evidence_boundary=_dedupe_text(
            "simulation_only",
            *bundle.run_record.boundary_notes,
            *adapter_result.failure_boundary,
            "not_ready_for_robot_execution",
        ),
        review_status="not_reviewed",
    )
    contract = SkillTransferContract(
        required_robot_context=("robot_body", "tcp_calibration", "workpiece_frame"),
        required_scene_context=("scene_context_asset",),
        required_checks=DEFAULT_TRANSFER_CHECKS,
        transfer_status="requires_contextual_precheck",
        blocking_gaps=(),
        evidence_notes=("not_real_robot_validated",),
    )

    return ManipulationSkillAsset(
        asset_id=f"skill-asset-{task_spec.task_id}",
        name=task_spec.name,
        domain="welding",
        skill_type=task_spec.unit_id,
        source_type="simulation",
        source_refs={
            "bundle_id": bundle.bundle_id,
            "task_id": task_spec.task_id,
            "dataset_id": dataset_id,
            "run_record_id": bundle.run_record.simulation_run_id,
        },
        intent={
            "task": task_spec.name,
            "expected_outputs": task_spec.expected_outputs,
        },
        motion={
            "tcp_trajectory": [point.to_dict() for point in adapter_result.tcp_trajectory],
            "tool_orientation": [point.to_dict() for point in adapter_result.tool_orientation],
            "trajectory_point_count": len(adapter_result.tcp_trajectory),
            "orientation_point_count": len(adapter_result.tool_orientation),
            "metrics": dict(adapter_result.metrics),
        },
        constraints={
            "tool_orientation": task_spec.tool_orientation_constraint,
            "motion": task_spec.motion_constraint,
            "robot": task_spec.robot_constraint,
        },
        context_requirements={
            "tcp_frame": task_spec.tcp_frame,
            "robot_body_required": True,
            "workpiece_frame_required": True,
        },
        evidence=evidence,
        transfer_contract=contract,
        quality_boundary=(
            "not_real_welding_quality_validation",
            "not_WPS_PQR",
            "not_ready_for_robot_execution",
        ),
        version="v0.1",
    )


def _dedupe_text(*values: str) -> tuple[str, ...]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return tuple(deduped)
