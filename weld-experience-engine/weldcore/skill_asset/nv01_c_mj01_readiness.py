from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CANONICAL_NV01C_MJ01_STATUS = {
    "ready_for_isaac_runtime_validation_input_review",
    "ready_for_mj01_lightweight_replay_input_review",
    "blocked_by_missing_isaac_runtime",
    "blocked_by_missing_mujoco_runtime",
    "blocked_for_runtime_replay_validation",
    "not_isaac_sim_runtime_validation",
    "not_mujoco_dynamics_validation",
    "not_policy_training_result",
    "not_formal_WPS_PQR",
    "not_ready_for_robot_execution",
    "not_converted_to_mjcf",
}

READINESS_BOUNDARY = [
    "not_isaac_sim_runtime_validation",
    "not_mujoco_dynamics_validation",
    "not_policy_training_result",
    "not_formal_WPS_PQR",
    "not_ready_for_robot_execution",
]

REQUIRED_NV01B_FILES = {
    "summary": "nv01_b_summary.json",
    "openusd_stage_usda": "openusd_stage.usda",
    "openusd_stage_validation_report": "openusd_stage_validation_report.json",
    "isaac_replay_fixture": "isaac_replay_fixture.json",
    "procedure_sim_parameter_audit": "procedure_sim_parameter_audit.json",
    "sensor_annotation_manifest": "sensor_annotation_manifest.json",
    "simulation_blocking_report": "simulation_blocking_report.json",
    "experiment_reproducibility_manifest": "experiment_reproducibility_manifest.json",
}

REQUIRED_NV01B_TASK_FILES = {
    "isaac_replay_task_fixture": "isaac_replay_task_fixture.json",
    "procedure_sim_parameter_audit": "procedure_sim_parameter_audit.json",
    "sensor_annotation_manifest": "sensor_annotation_manifest.json",
    "simulation_blocking_report": "simulation_blocking_report.json",
}


class MissingNV01BArtifactError(RuntimeError):
    pass


def load_nv01b_artifacts(source_dir: str | Path) -> dict[str, Any]:
    root = Path(source_dir)
    if not root.exists():
        raise MissingNV01BArtifactError(f"missing_source_nv01b_dir:{root}")

    missing = [
        relative_path
        for relative_path in REQUIRED_NV01B_FILES.values()
        if not (root / relative_path).exists()
    ]
    if missing:
        raise MissingNV01BArtifactError(
            "missing_nv01b_artifacts:" + ",".join(sorted(missing))
        )

    artifacts: dict[str, Any] = {}
    for name, relative_path in REQUIRED_NV01B_FILES.items():
        path = root / relative_path
        if path.suffix == ".json":
            artifacts[name] = json.loads(path.read_text(encoding="utf-8"))
        else:
            artifacts[name] = path.read_text(encoding="utf-8")

    tasks = artifacts["summary"]["tasks"]
    artifacts["root"] = root
    artifacts["task_ids"] = [task["task_id"] for task in tasks]
    artifacts["task_dirs"] = {
        task["task_id"]: task["task_output_dir"] for task in tasks
    }
    artifacts["task_artifacts"] = _load_task_artifacts(root, artifacts["task_dirs"])
    artifacts["source_artifact_refs"] = dict(REQUIRED_NV01B_FILES)
    return artifacts


def _load_task_artifacts(
    root: Path,
    task_dirs: dict[str, str],
) -> dict[str, dict[str, Any]]:
    task_artifacts = {}
    for task_id, task_dir_ref in task_dirs.items():
        task_dir = root / task_dir_ref
        missing = [
            f"{task_dir_ref}/{relative_path}"
            for relative_path in REQUIRED_NV01B_TASK_FILES.values()
            if not (task_dir / relative_path).exists()
        ]
        if missing:
            raise MissingNV01BArtifactError(
                "missing_nv01b_task_artifacts:" + ",".join(sorted(missing))
            )
        task_artifacts[task_id] = {
            name: json.loads((task_dir / relative_path).read_text(encoding="utf-8"))
            for name, relative_path in REQUIRED_NV01B_TASK_FILES.items()
        }
    return task_artifacts


def build_nv01_c_mj01_readiness_payloads(
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    task_payloads = _build_task_payloads(artifacts)
    return {
        "isaac_runtime_validation_input_manifest": (
            _build_isaac_runtime_validation_input_manifest(artifacts, task_payloads)
        ),
        "mujoco_lightweight_replay_feasibility_report": (
            _build_mujoco_lightweight_replay_feasibility_report(artifacts, task_payloads)
        ),
        "runtime_replay_blocking_report": _build_runtime_replay_blocking_report(
            artifacts,
            task_payloads,
        ),
        "readiness_reproducibility_manifest": _build_reproducibility_manifest(
            artifacts
        ),
        "task_payloads": task_payloads,
    }


def _build_isaac_runtime_validation_input_manifest(
    artifacts: dict[str, Any],
    task_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    fixture = artifacts["isaac_replay_fixture"]
    validation = artifacts["openusd_stage_validation_report"]
    sensor = artifacts["sensor_annotation_manifest"]
    return {
        "manifest_id": "nv01-c-isaac-runtime-validation-input-manifest",
        "runtime_target": "Isaac Sim",
        "runtime_status": "blocked_by_missing_isaac_runtime",
        "static_input_status": "ready_for_isaac_runtime_validation_input_review",
        "source_stage_ref": "openusd_stage.usda",
        "source_stage_validation_report_ref": "openusd_stage_validation_report.json",
        "source_replay_fixture_ref": "isaac_replay_fixture.json",
        "required_prim_paths": validation["required_prim_paths"],
        "required_metadata_keys": validation["required_metadata_keys"],
        "stage_validation_status": validation["validation_status"],
        "frame_bindings": fixture["frame_bindings"],
        "trajectory_bindings": fixture["trajectory_bindings"],
        "procedure_parameter_bindings": fixture["procedure_parameter_bindings"],
        "sensor_placeholders": sensor["sensor_placeholders"],
        "task_inputs": {
            task_id: payload["isaac_runtime_task_validation_input"]
            for task_id, payload in task_payloads.items()
        },
        "blocked_by": [
            "isaac_sim_runtime",
            "real_tcp_tool_workpiece_calibration",
            "sensor_layout_calibration",
        ],
        "missing_runtime_inputs": ["isaac_sim_runtime"],
        "readiness_boundary": READINESS_BOUNDARY,
    }


def _build_mujoco_lightweight_replay_feasibility_report(
    artifacts: dict[str, Any],
    task_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    fixture = artifacts["isaac_replay_fixture"]
    return {
        "report_id": "mj01-mujoco-lightweight-replay-feasibility",
        "runtime_target": "MuJoCo",
        "runtime_status": "blocked_by_missing_mujoco_runtime",
        "model_input_status": "ready_for_mj01_lightweight_replay_input_review",
        "model_source": "nv01_b_robot_body_asset_ref",
        "mjcf_conversion_status": "not_converted_to_mjcf",
        "source_stage_ref": "openusd_stage.usda",
        "source_replay_fixture_ref": "isaac_replay_fixture.json",
        "urdf_ref": fixture["robot_asset"],
        "frame_binding_inputs": fixture["frame_bindings"],
        "trajectory_replay_inputs": fixture["trajectory_bindings"],
        "contact_and_dynamics_assumptions": [
            "geometry_contact_not_validated",
            "weld_pool_thermal_process_not_modeled",
            "tool_workpiece_collision_not_validated",
            "controller_dynamics_not_identified",
        ],
        "task_reports": {
            task_id: payload["mujoco_task_replay_feasibility"]
            for task_id, payload in task_payloads.items()
        },
        "blocked_by": [
            "mujoco_runtime",
            "mjcf_conversion",
            "real_tcp_tool_workpiece_calibration",
        ],
        "missing_runtime_inputs": ["mujoco_runtime"],
        "readiness_boundary": READINESS_BOUNDARY,
    }


def _build_runtime_replay_blocking_report(
    artifacts: dict[str, Any],
    task_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source_blocking = artifacts["simulation_blocking_report"]
    return {
        "report_id": "nv01-c-mj01-runtime-replay-blocking-report",
        "overall_status": "blocked_for_runtime_replay_validation",
        "scope_status": {
            "isaac_runtime_validation": "blocked_by_missing_isaac_runtime",
            "mujoco_lightweight_replay": "blocked_by_missing_mujoco_runtime",
            "sensor_simulation": "blocked_by_missing_sensor_calibration",
            "replicator_dataset": "blocked_by_missing_sensor_calibration",
            "policy_training": "not_policy_training_result",
            "expert_review": "blocked_by_missing_expert_review",
            "a01_product_validation": "blocked_by_missing_a01_workcell_evidence",
            "wps_pqr_release": "not_formal_WPS_PQR",
            "robot_execution": "not_ready_for_robot_execution",
        },
        "blocking_items": [
            "blocked_by_missing_isaac_runtime",
            "blocked_by_missing_mujoco_runtime",
            "blocked_by_missing_sensor_calibration",
            "blocked_by_missing_real_process_inputs",
        ],
        "source_blocking_report_ref": "simulation_blocking_report.json",
        "source_blocking_items": source_blocking["blocking_items"],
        "missing_runtime_inputs": [
            "isaac_sim_runtime",
            "mujoco_runtime",
        ],
        "missing_calibrations": sorted(
            {
                "tcp_calibration",
                "tool_frame_calibration",
                "workpiece_frame_calibration",
                *source_blocking.get("missing_calibrations", []),
            }
        ),
        "missing_process_inputs": source_blocking.get("next_required_inputs", []),
        "next_required_inputs": [
            "isaac_sim_runtime_validation_environment",
            "mujoco_runtime_validation_environment",
            "real_tcp_tool_workpiece_calibration",
            "sensor_layout_calibration",
            "h300_workstation_logs",
            "expert_review_record",
        ],
        "task_blocking_reports": {
            task_id: payload["runtime_replay_task_blocking_report"]
            for task_id, payload in task_payloads.items()
        },
        "readiness_boundary": READINESS_BOUNDARY,
    }


def _build_reproducibility_manifest(artifacts: dict[str, Any]) -> dict[str, Any]:
    return {
        "manifest_id": "nv01-c-mj01-readiness-reproducibility-manifest",
        "source_nv01b_root_ref": "source_nv01b",
        "source_nv01b_summary_ref": "source_nv01b/nv01_b_summary.json",
        "source_artifact_refs": artifacts["source_artifact_refs"],
        "generated_payloads": [
            "isaac_runtime_validation_input_manifest",
            "mujoco_lightweight_replay_feasibility_report",
            "runtime_replay_blocking_report",
            "readiness_reproducibility_manifest",
            "task_payloads",
        ],
        "command": (
            "builder_only: "
            "weldcore.skill_asset.nv01_c_mj01_readiness."
            "build_nv01_c_mj01_readiness_payloads(source_nv01b_dir)"
        ),
        "default_dependency_boundary": [
            "no_isaac_sim_default_dependency",
            "no_mujoco_default_dependency",
            "no_pxr_default_dependency",
            "no_mjcf_conversion",
        ],
        "validation_commands": [
            "pytest tests/test_nv01_c_mj01_readiness.py -q",
        ],
        "readiness_boundary": READINESS_BOUNDARY,
    }


def _build_task_payloads(
    artifacts: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    fixture = artifacts["isaac_replay_fixture"]
    frame_bindings = fixture["frame_bindings"]
    task_payloads = {}
    for task_id in artifacts["task_ids"]:
        task_fixture = fixture["task_fixtures"][task_id]
        trajectory_binding = fixture["trajectory_bindings"][task_id]
        common = _common_task_readiness(
            task_id,
            artifacts["task_dirs"][task_id],
            task_fixture["stage_prim"],
            trajectory_binding["trajectory_source_ref"],
            frame_bindings,
            task_fixture["task_config_ref"],
        )
        task_payloads[task_id] = {
            "isaac_runtime_task_validation_input": {
                **common,
                "runtime_target": "Isaac Sim",
                "runtime_status": "blocked_by_missing_isaac_runtime",
                "input_status": "ready_for_isaac_runtime_validation_input_review",
            },
            "mujoco_task_replay_feasibility": {
                **common,
                "runtime_target": "MuJoCo",
                "runtime_status": "blocked_by_missing_mujoco_runtime",
                "model_input_status": "ready_for_mj01_lightweight_replay_input_review",
                "mjcf_conversion_status": "not_converted_to_mjcf",
            },
            "runtime_replay_task_blocking_report": {
                "task_id": task_id,
                "source_task_dir_ref": common["source_task_dir_ref"],
                "stage_task_prim_ref": common["stage_task_prim_ref"],
                "overall_status": "blocked_for_runtime_replay_validation",
                "blocked_by": [
                    "isaac_sim_runtime",
                    "mujoco_runtime",
                    "real_tcp_tool_workpiece_calibration",
                ],
                "missing_runtime_inputs": [
                    "isaac_sim_runtime",
                    "mujoco_runtime",
                ],
                "missing_calibrations": [
                    "tcp_calibration",
                    "tool_frame_calibration",
                    "workpiece_frame_calibration",
                ],
                "readiness_boundary": READINESS_BOUNDARY,
            },
        }
    return task_payloads


def _common_task_readiness(
    task_id: str,
    source_task_dir_ref: str,
    stage_task_prim_ref: str,
    trajectory_ref: str,
    frame_bindings: dict[str, str],
    task_config_ref: str,
) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "source_task_dir_ref": source_task_dir_ref,
        "stage_task_prim_ref": stage_task_prim_ref,
        "trajectory_ref": trajectory_ref,
        "tcp_frame_ref": frame_bindings["tcp_frame"],
        "tool_frame_ref": frame_bindings["tool_frame"],
        "workpiece_frame_ref": frame_bindings["workpiece_frame"],
        "procedure_parameter_refs": {
            "task_replay_config_ref": task_config_ref,
            "procedure_sim_parameter_audit_ref": "procedure_sim_parameter_audit.json",
        },
        "blocked_by": [
            "isaac_sim_runtime",
            "mujoco_runtime",
            "real_tcp_tool_workpiece_calibration",
        ],
        "readiness_boundary": READINESS_BOUNDARY,
    }
