from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .procedure_contract import (
    build_procedure_to_nv01_mapping_matrix,
    build_weld_procedure_parameter_set,
    build_weld_procedure_validation_report,
)


class MissingCanonicalArtifactError(RuntimeError):
    """Raised when demo_summary artifact refs point to missing files."""


class _SkillAssetView:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.asset_id = payload["asset_id"]
        self.source_type = payload["source_type"]
        self.motion = payload.get("motion", {})


def load_demo_pack(source_demo_dir: str | Path) -> dict[str, Any]:
    summary_path = Path(source_demo_dir) / "demo_summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(summary_path)
    return json.loads(summary_path.read_text(encoding="utf-8"))


def load_task_artifacts(
    source_demo_dir: str | Path,
    task: dict[str, Any],
) -> dict[str, Any]:
    artifacts: dict[str, Any] = {}
    missing: list[str] = []
    for name, ref in task["artifact_refs"].items():
        path = Path(source_demo_dir) / ref
        if not path.exists():
            missing.append(ref)
            continue
        artifacts[name] = json.loads(path.read_text(encoding="utf-8"))
    if missing:
        raise MissingCanonicalArtifactError(
            "missing_canonical_artifacts:" + ",".join(sorted(missing))
        )
    return artifacts


def build_nvidia_digital_twin_payloads(
    source_demo_dir: str | Path,
    demo_summary: dict[str, Any],
    procedure_contract: dict[str, Any],
) -> dict[str, Any]:
    task_payloads: dict[str, dict[str, Any]] = {}
    parameter_sets: dict[str, dict[str, Any]] = {}
    validation_reports: dict[str, dict[str, Any]] = {}
    canonical_refs_by_task: dict[str, dict[str, str]] = {}

    for task in demo_summary["tasks"]:
        artifacts = load_task_artifacts(source_demo_dir, task)
        skill_asset = _SkillAssetView(artifacts["skill_asset_report.json"])
        parameter_set = build_weld_procedure_parameter_set(
            skill_asset,
            procedure_contract,
            task["artifact_refs"],
        )
        validation_report = build_weld_procedure_validation_report(
            parameter_set,
            procedure_contract,
        )
        task_id = task["task_id"]
        parameter_sets[task_id] = parameter_set
        validation_reports[task_id] = validation_report
        canonical_refs_by_task[task_id] = task["artifact_refs"]
        task_payloads[task_id] = _build_task_payload(
            task=task,
            artifacts=artifacts,
            parameter_set=parameter_set,
            validation_report=validation_report,
        )

    first_task_id = demo_summary["tasks"][0]["task_id"]
    mapping_matrix = build_procedure_to_nv01_mapping_matrix(procedure_contract)
    mapping_matrix = {
        **mapping_matrix,
        "procedure_contract_ref": "weld_procedure_knowledge_contract.json",
        "canonical_artifact_refs_by_task": canonical_refs_by_task,
    }
    return {
        "weld_procedure_parameter_set": _top_level_parameter_set(
            parameter_sets[first_task_id],
            parameter_sets,
            canonical_refs_by_task,
        ),
        "weld_procedure_validation_report": _top_level_validation_report(
            validation_reports[first_task_id],
            validation_reports,
            canonical_refs_by_task,
        ),
        "procedure_to_nv01_mapping_matrix": mapping_matrix,
        "weld_skill_digital_twin_package": _build_package(
            demo_summary,
            canonical_refs_by_task,
        ),
        "openusd_scene_manifest": _build_openusd_scene_manifest(
            demo_summary,
            procedure_contract,
            canonical_refs_by_task,
        ),
        "isaac_sim_replay_config": _build_isaac_sim_replay_config(
            demo_summary,
            parameter_sets,
            canonical_refs_by_task,
        ),
        "domain_randomization_recipe": _build_domain_randomization_recipe(
            procedure_contract,
            canonical_refs_by_task,
        ),
        "training_readiness_report": _build_training_readiness_report(
            validation_reports,
            canonical_refs_by_task,
        ),
        "nvidia_stack_alignment_matrix": _build_alignment_matrix(
            procedure_contract,
            canonical_refs_by_task,
        ),
        "task_payloads": task_payloads,
    }


def _build_task_payload(
    *,
    task: dict[str, Any],
    artifacts: dict[str, Any],
    parameter_set: dict[str, Any],
    validation_report: dict[str, Any],
) -> dict[str, Any]:
    skill_asset = artifacts["skill_asset_report.json"]
    robot_body = artifacts["robot_body_asset_report.json"]
    scene_context = artifacts["scene_context_asset_report.json"]
    return {
        "skill_asset_ref": {
            "task_id": task["task_id"],
            "skill_asset_id": skill_asset["asset_id"],
            "canonical_artifact_ref": task["artifact_refs"]["skill_asset_report.json"],
        },
        "weld_procedure_parameter_set": parameter_set,
        "weld_procedure_validation_report": validation_report,
        "openusd_task_manifest": {
            "manifest_type": "openusd_task_manifest_plan",
            "task_id": task["task_id"],
            "root_prim": f"/World/WeldTasks/{task['task_id']}",
            "skill_asset_ref": task["artifact_refs"]["skill_asset_report.json"],
            "robot_body_asset_ref": task["artifact_refs"][
                "robot_body_asset_report.json"
            ],
            "scene_context_asset_ref": task["artifact_refs"][
                "scene_context_asset_report.json"
            ],
            "procedure_parameter_set_ref": (
                f"{task['task_id']}/weld_procedure_parameter_set.json"
            ),
            "process_metadata": {
                "procedure_contract_ref": "weld_procedure_knowledge_contract.json",
                "parameter_set_id": parameter_set["parameter_set_id"],
            },
            "missing_usd_authoring_inputs": [
                "openusd_stage_template",
                "material_and_weld_bead_geometry_authoring",
                "validated_robot_usd_asset",
            ],
        },
        "isaac_replay_task_config": {
            "task_id": task["task_id"],
            "skill_asset_id": skill_asset["asset_id"],
            "robot_model": robot_body["robot_model"],
            "trajectory_source_ref": task["artifact_refs"]["skill_asset_report.json"],
            "procedure_parameter_inputs": parameter_set["values"],
            "not_ready_reasons": ["blocked_by_missing_isaac_runtime"],
        },
        "sensor_and_annotation_manifest": {
            "task_id": task["task_id"],
            "scene_context_ref": task["artifact_refs"]["scene_context_asset_report.json"],
            "annotation_plan": [
                "weld_seam_path",
                "tcp_pose_replay_trace",
                "procedure_parameter_overlay",
            ],
            "missing_inputs": [
                "camera_sensor_layout",
                "arc_glare_smoke_spatter_calibration",
            ],
        },
        "training_task_readiness": {
            "task_id": task["task_id"],
            "design_review_status": "ready_for_training_design_review",
            "training_status": "not_ready_for_policy_training",
            "blocked_by": [
                "blocked_by_missing_isaac_runtime",
                *validation_report["not_ready_reasons"],
            ],
        },
        "canonical_artifact_refs": task["artifact_refs"],
        "canonical_artifact_summary": {
            "scene_id": scene_context["scene_id"],
            "robot_id": robot_body["robot_id"],
            "skill_asset_id": skill_asset["asset_id"],
        },
    }


def _top_level_parameter_set(
    first_parameter_set: dict[str, Any],
    parameter_sets: dict[str, dict[str, Any]],
    canonical_refs_by_task: dict[str, dict[str, str]],
) -> dict[str, Any]:
    payload = dict(first_parameter_set)
    payload["aggregation_scope"] = "first_task_with_all_task_refs"
    payload["task_parameter_set_refs"] = {
        task_id: f"{task_id}/weld_procedure_parameter_set.json"
        for task_id in parameter_sets
    }
    payload["canonical_artifact_refs_by_task"] = canonical_refs_by_task
    return payload


def _top_level_validation_report(
    first_report: dict[str, Any],
    validation_reports: dict[str, dict[str, Any]],
    canonical_refs_by_task: dict[str, dict[str, str]],
) -> dict[str, Any]:
    payload = dict(first_report)
    payload["aggregation_scope"] = "first_task_with_all_task_refs"
    payload["task_validation_report_refs"] = {
        task_id: f"{task_id}/weld_procedure_validation_report.json"
        for task_id in validation_reports
    }
    payload["canonical_artifact_refs_by_task"] = canonical_refs_by_task
    return payload


def _build_package(
    demo_summary: dict[str, Any],
    canonical_refs_by_task: dict[str, dict[str, str]],
) -> dict[str, Any]:
    return {
        "package_id": "nv01-a-weld-skill-digital-twin-foundation",
        "overall_status": "ready_for_simulation_replay_package_design",
        "task_count": demo_summary["task_count"],
        "procedure_contract_ref": "weld_procedure_knowledge_contract.json",
        "source_demo_ref": "demo_summary.json",
        "source_demo_pack_ref": "demo_summary.json",
        "canonical_artifact_refs_by_task": canonical_refs_by_task,
        "readiness_boundary": [
            "ready_for_simulation_replay_package_design",
            "not_ready_for_robot_execution",
            "not_ready_for_policy_training",
            "not_isaac_runtime_replay_ready",
            "not_formal_WPS_PQR",
        ],
    }


def _build_openusd_scene_manifest(
    demo_summary: dict[str, Any],
    procedure_contract: dict[str, Any],
    canonical_refs_by_task: dict[str, dict[str, str]],
) -> dict[str, Any]:
    return {
        "manifest_type": "openusd_scene_manifest_plan",
        "root_prim": "/World",
        "stage_plan_ref": "not_a_usd_file",
        "procedure_contract_ref": "weld_procedure_knowledge_contract.json",
        "procedure_parameter_bindings": [
            {
                "field_id": field["field_id"],
                "display_name": field["display_name"],
                "target_path": field["a02_target_path"],
                "nv01_usage": field["nv01_usage"],
            }
            for field in procedure_contract["fields"]
            if field["nv01_usage"]
        ],
        "task_manifests": {
            task["task_id"]: f"{task['task_id']}/openusd_task_manifest.json"
            for task in demo_summary["tasks"]
        },
        "canonical_artifact_refs_by_task": canonical_refs_by_task,
        "missing_usd_authoring_inputs": [
            "openusd_stage_template",
            "robot_usd_asset_conversion",
            "weld_cell_geometry_and_materials",
            "sensor_and_lighting_layout",
        ],
    }


def _build_isaac_sim_replay_config(
    demo_summary: dict[str, Any],
    parameter_sets: dict[str, dict[str, Any]],
    canonical_refs_by_task: dict[str, dict[str, str]],
) -> dict[str, Any]:
    return {
        "config_type": "isaac_sim_replay_config_plan",
        "runtime_status": "blocked_by_missing_isaac_runtime",
        "procedure_contract_ref": "weld_procedure_knowledge_contract.json",
        "procedure_parameter_inputs": {
            task_id: parameter_set["values"]
            for task_id, parameter_set in parameter_sets.items()
        },
        "replay_tasks": {
            task["task_id"]: {
                "skill_asset_ref": task["artifact_refs"]["skill_asset_report.json"],
                "robot_body_asset_ref": task["artifact_refs"][
                    "robot_body_asset_report.json"
                ],
                "isaac_replay_task_config_ref": (
                    f"{task['task_id']}/isaac_replay_task_config.json"
                ),
            }
            for task in demo_summary["tasks"]
        },
        "canonical_artifact_refs_by_task": canonical_refs_by_task,
        "not_ready_reasons": [
            "blocked_by_missing_isaac_runtime",
            "blocked_by_missing_openusd_stage",
        ],
    }


def _build_domain_randomization_recipe(
    procedure_contract: dict[str, Any],
    canonical_refs_by_task: dict[str, dict[str, str]],
) -> dict[str, Any]:
    _require_contract_fields(
        procedure_contract,
        ["root_gap_mm", "groove_angle_deg", "travel_speed_mm_per_min"],
    )
    return {
        "recipe_id": "nv01-a-domain-randomization-recipe",
        "procedure_contract_ref": "weld_procedure_knowledge_contract.json",
        "canonical_artifact_refs_by_task": canonical_refs_by_task,
        "randomization_items": [
            {
                "name": "groove_gap_variation",
                "category": "joint_geometry",
                "linked_procedure_fields": ["root_gap_mm", "groove_angle_deg"],
                "requires_human_confirmation": True,
            },
            {
                "name": "travel_speed_window",
                "category": "process_parameter",
                "linked_procedure_fields": ["travel_speed_mm_per_min"],
                "requires_human_confirmation": True,
            },
            {
                "name": "arc_glare_smoke_spatter",
                "category": "sensor_degradation",
                "linked_procedure_fields": [],
                "requires_real_calibration": True,
            },
        ],
        "readiness_boundary": [
            "recipe_design_only",
            "not_replicator_dataset",
            "requires_real_weld_sensor_calibration",
        ],
    }


def _build_training_readiness_report(
    validation_reports: dict[str, dict[str, Any]],
    canonical_refs_by_task: dict[str, dict[str, str]],
) -> dict[str, Any]:
    validation_blocks = sorted(
        {
            reason
            for report in validation_reports.values()
            for reason in report["not_ready_reasons"]
        }
    )
    return {
        "design_review_status": "ready_for_training_design_review",
        "training_status": "not_ready_for_policy_training",
        "readiness_scope": "training design review only",
        "procedure_contract_gates": {
            task_id: report["not_ready_reasons"]
            for task_id, report in validation_reports.items()
        },
        "blocked_by": [
            "blocked_by_missing_isaac_runtime",
            "blocked_by_missing_policy_training_dataset",
            *validation_blocks,
        ],
        "canonical_artifact_refs_by_task": canonical_refs_by_task,
        "readiness_boundary": [
            "ready_for_training_design_review",
            "not_ready_for_policy_training",
            "not_robot_execution_ready",
        ],
    }


def _build_alignment_matrix(
    procedure_contract: dict[str, Any],
    canonical_refs_by_task: dict[str, dict[str, str]],
) -> dict[str, Any]:
    return {
        "matrix_id": f"nv01-stack-alignment-{procedure_contract['contract_version']}",
        "procedure_contract_ref": "weld_procedure_knowledge_contract.json",
        "canonical_artifact_refs_by_task": canonical_refs_by_task,
        "a02_object_mappings": {
            "WeldProcedureKnowledgeContract": [
                "OpenUSD process_metadata",
                "Isaac Sim procedure_parameter_inputs",
                "training_readiness_report procedure gates",
            ],
            "ManipulationSkillAsset": [
                "OpenUSD task prim metadata",
                "Isaac Sim trajectory replay plan",
            ],
            "RobotBodyAsset": [
                "robot USD asset conversion input",
                "Isaac Sim articulation input",
            ],
            "RobotContextSpec": [
                "Isaac Sim robot frame and TCP configuration",
            ],
            "SceneContextAsset": [
                "OpenUSD scene geometry plan",
                "sensor and annotation manifest",
            ],
            "ExpertReviewRecord": [
                "procedure and real-context readiness gates",
            ],
        },
    }


def _require_contract_fields(
    procedure_contract: dict[str, Any],
    field_ids: list[str],
) -> None:
    known_ids = {field["field_id"] for field in procedure_contract["fields"]}
    missing = sorted(set(field_ids) - known_ids)
    if missing:
        raise ValueError("unknown_procedure_fields:" + ",".join(missing))
