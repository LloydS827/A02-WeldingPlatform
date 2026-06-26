from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any


READINESS_BOUNDARY = [
    "not_mujoco_dynamics_validation",
    "not_isaac_sim_runtime_validation",
    "not_policy_training_result",
    "not_formal_WPS_PQR",
    "not_ready_for_robot_execution",
]

CANONICAL_MJ01A_NV01C0_STATUS = {
    "skipped_by_missing_mujoco_runtime",
    "available",
    "blocked_by_mujoco_import_error",
    "blocked_by_missing_mujoco_runtime",
    "passed_minimal_mjcf_sanity_probe",
    "blocked_by_mujoco_model_load_error",
    "blocked_by_missing_robot_body_asset_source_urdf",
    "blocked_by_missing_remote_isaac_runtime",
    "blocked_for_runtime_probe_or_preflight",
    "dry_run_inputs_prepared",
    "implemented",
    "imported",
    "import_error",
    "loaded_real_urdf_with_mujoco",
    "missing",
    "not_converted_to_mjcf",
    "not_installed_locally_by_design",
    "ready_for_mj01_lightweight_replay_input_review",
    "resolved_from_robot_body_asset_report",
    *READINESS_BOUNDARY,
}

REQUIRED_READINESS_FILES = {
    "summary": "nv01_c_mj01_summary.json",
    "mujoco_feasibility": "mujoco_lightweight_replay_feasibility_report.json",
    "isaac_manifest": "isaac_runtime_validation_input_manifest.json",
    "blocking": "runtime_replay_blocking_report.json",
    "reproducibility": "readiness_reproducibility_manifest.json",
}

REQUIRED_TASK_FILES = {
    "mujoco_task_replay_feasibility": "mujoco_task_replay_feasibility.json",
    "isaac_runtime_task_validation_input": "isaac_runtime_task_validation_input.json",
}

INSTALL_HINT = "uv sync --extra dev --extra viz --extra mujoco"
MINIMAL_MJCF = """
<mujoco model="mj01_minimal_probe">
  <worldbody>
    <body name="probe_body">
      <geom type="sphere" size="0.01"/>
    </body>
  </worldbody>
</mujoco>
"""


class MissingReadinessArtifactError(RuntimeError):
    pass


def load_readiness_artifacts(source_readiness_dir: str | Path) -> dict[str, Any]:
    root = Path(source_readiness_dir)
    if not root.exists():
        raise MissingReadinessArtifactError(f"missing_source_readiness_dir:{root}")

    missing = [
        relative_path
        for relative_path in REQUIRED_READINESS_FILES.values()
        if not (root / relative_path).exists()
    ]
    if missing:
        raise MissingReadinessArtifactError(
            "missing_readiness_artifacts:" + ",".join(sorted(missing))
        )

    artifacts: dict[str, Any] = {
        name: _read_json(root / relative_path)
        for name, relative_path in REQUIRED_READINESS_FILES.items()
    }
    tasks = artifacts["summary"]["tasks"]
    task_dirs = {task["task_id"]: task["task_output_dir"] for task in tasks}

    artifacts["source_readiness_dir"] = root
    artifacts["task_ids"] = [task["task_id"] for task in tasks]
    artifacts["task_dirs"] = task_dirs
    artifacts["task_artifacts"] = _load_task_artifacts(root, task_dirs)

    report_ref = artifacts["mujoco_feasibility"].get("urdf_ref")
    report_path = _resolve_robot_body_asset_report(root, report_ref)
    artifacts["robot_body_asset_report_ref"] = report_ref
    artifacts["_robot_body_asset_report_path"] = report_path
    artifacts["robot_body_asset_report"] = _load_robot_body_asset_report(report_path)
    artifacts["_source_urdf_path"] = _resolve_source_urdf_path(
        artifacts["robot_body_asset_report"]
    )
    return artifacts


def probe_mujoco_runtime() -> dict[str, Any]:
    base = {
        "report_id": "mj01-a-mujoco-runtime-probe",
        "runtime_target": "MuJoCo",
        "mujoco_version": None,
        "install_hint": INSTALL_HINT,
        "optional_dependency_extra": "mujoco",
        "readiness_boundary": READINESS_BOUNDARY,
    }
    try:
        mujoco = importlib.import_module("mujoco")
    except ModuleNotFoundError as exc:
        if exc.name not in {None, "mujoco"}:
            return {
                **base,
                "runtime_probe_status": "blocked_by_mujoco_import_error",
                "mujoco_python_import_status": "import_error",
                "import_error": str(exc),
                "blocked_by": ["mujoco_import_error"],
            }
        return {
            **base,
            "runtime_probe_status": "skipped_by_missing_mujoco_runtime",
            "mujoco_python_import_status": "missing",
            "blocked_by": ["mujoco_runtime"],
        }
    except Exception as exc:
        return {
            **base,
            "runtime_probe_status": "blocked_by_mujoco_import_error",
            "mujoco_python_import_status": "import_error",
            "import_error": str(exc),
            "blocked_by": ["mujoco_import_error"],
        }

    return {
        **base,
        "runtime_probe_status": "available",
        "mujoco_python_import_status": "imported",
        "mujoco_version": getattr(mujoco, "__version__", None),
        "blocked_by": [],
    }


def build_mj01_a_nv01_c0_payloads(artifacts: dict[str, Any]) -> dict[str, Any]:
    runtime = probe_mujoco_runtime()
    model = _build_model_input_resolution_report(artifacts)
    probe = _build_mujoco_probe_report(artifacts, runtime, model)
    return {
        "mujoco_runtime_probe_report": runtime,
        "mujoco_model_input_resolution_report": model,
        "mujoco_probe_report": probe,
        "isaac_remote_preflight_report": _build_isaac_remote_preflight_report(
            artifacts
        ),
        "reproducibility_manifest": _build_reproducibility_manifest(artifacts),
        "task_payloads": _build_task_payloads(artifacts),
    }


def _load_task_artifacts(
    root: Path,
    task_dirs: dict[str, str],
) -> dict[str, dict[str, Any]]:
    task_artifacts = {}
    for task_id, task_dir_ref in task_dirs.items():
        task_dir = root / task_dir_ref
        missing = [
            f"{task_dir_ref}/{relative_path}"
            for relative_path in REQUIRED_TASK_FILES.values()
            if not (task_dir / relative_path).exists()
        ]
        if missing:
            raise MissingReadinessArtifactError(
                "missing_readiness_task_artifacts:" + ",".join(sorted(missing))
            )
        task_artifacts[task_id] = {
            name: _read_json(task_dir / relative_path)
            for name, relative_path in REQUIRED_TASK_FILES.items()
        }
    return task_artifacts


def _resolve_robot_body_asset_report(root: Path, report_ref: str | None) -> Path | None:
    if not report_ref:
        return None
    candidates = [
        root / "_source_nv01b" / "_source_nv01a" / "_source_demo_evidence" / report_ref,
        root / report_ref,
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _load_robot_body_asset_report(report_path: Path | None) -> dict[str, Any]:
    if report_path is None:
        return {
            "report_status": "blocked_by_missing_robot_body_asset_report",
            "source_urdf": None,
            "link_names": [],
            "joint_names": [],
            "mesh_references": [],
        }
    return _read_json(report_path)


def _resolve_source_urdf_path(robot_body_asset_report: dict[str, Any]) -> Path | None:
    source_urdf = robot_body_asset_report.get("source_urdf")
    if not source_urdf:
        return None
    path = Path(source_urdf)
    if path.exists():
        return path
    return None


def _build_model_input_resolution_report(artifacts: dict[str, Any]) -> dict[str, Any]:
    robot = artifacts["robot_body_asset_report"]
    source_urdf_path = artifacts.get("_source_urdf_path")
    source_urdf_ref = (
        "robot_body_asset_report.source_urdf" if robot.get("source_urdf") else None
    )
    source_urdf_status = (
        "resolved_from_robot_body_asset_report"
        if source_urdf_path is not None
        else "blocked_by_missing_robot_body_asset_source_urdf"
    )
    blocked_by = []
    if source_urdf_path is None:
        blocked_by.append("robot_body_asset_source_urdf")

    return {
        "report_id": "mj01-a-mujoco-model-input-resolution",
        "source_readiness_ref": REQUIRED_READINESS_FILES["summary"],
        "source_mujoco_feasibility_ref": REQUIRED_READINESS_FILES[
            "mujoco_feasibility"
        ],
        "robot_body_asset_report_ref": _stable_ref(
            artifacts.get("robot_body_asset_report_ref")
        ),
        "source_urdf_status": source_urdf_status,
        "source_urdf_ref": source_urdf_ref,
        "link_count": len(robot.get("link_names", [])),
        "joint_count": len(robot.get("joint_names", [])),
        "mesh_reference_count": len(robot.get("mesh_references", [])),
        "frame_binding_inputs": artifacts["mujoco_feasibility"].get(
            "frame_binding_inputs",
            {},
        ),
        "trajectory_replay_inputs": artifacts["mujoco_feasibility"].get(
            "trajectory_replay_inputs",
            {},
        ),
        "blocked_by": blocked_by,
        "readiness_boundary": READINESS_BOUNDARY,
    }


def _build_mujoco_probe_report(
    artifacts: dict[str, Any],
    runtime: dict[str, Any],
    model: dict[str, Any],
) -> dict[str, Any]:
    runtime_status = runtime["runtime_probe_status"]
    task_reports = artifacts["mujoco_feasibility"].get("task_reports", {})
    if runtime_status != "available":
        return {
            "report_id": "mj01-a-mujoco-probe",
            "runtime_probe_status": runtime_status,
            "minimal_mjcf_probe_status": runtime_status,
            "real_urdf_load_status": runtime_status,
            "real_urdf_load_error": None,
            "model_load_diagnostics": {
                "runtime_probe_status": runtime_status,
                "source_urdf_status": model["source_urdf_status"],
            },
            "model_load_blocking_items": sorted(
                {*runtime.get("blocked_by", []), *model.get("blocked_by", [])}
            ),
            "real_urdf_load_next_step": "install_mujoco_runtime_and_retry_probe",
            "trajectory_dry_run_status": "dry_run_inputs_prepared",
            "task_reports": task_reports,
            "blocked_by": sorted(
                {*runtime.get("blocked_by", []), *model.get("blocked_by", [])}
            ),
            "readiness_boundary": READINESS_BOUNDARY,
        }

    mujoco = importlib.import_module("mujoco")
    minimal_status, minimal_diagnostics = _run_minimal_mjcf_probe(mujoco)
    real_status, real_error, real_diagnostics = _run_real_urdf_load_probe(
        artifacts,
        mujoco,
    )
    blocking_items = _model_load_blocking_items(
        real_status,
        model,
        minimal_diagnostics,
        real_diagnostics,
    )
    return {
        "report_id": "mj01-a-mujoco-probe",
        "runtime_probe_status": runtime_status,
        "minimal_mjcf_probe_status": minimal_status,
        "real_urdf_load_status": real_status,
        "real_urdf_load_error": real_error,
        "model_load_diagnostics": {
            "minimal_mjcf": minimal_diagnostics,
            **real_diagnostics,
        },
        "model_load_blocking_items": blocking_items,
        "real_urdf_load_next_step": _real_urdf_next_step(real_status, model),
        "trajectory_dry_run_status": "dry_run_inputs_prepared",
        "task_reports": task_reports,
        "blocked_by": blocking_items,
        "readiness_boundary": READINESS_BOUNDARY,
    }


def _run_minimal_mjcf_probe(mujoco: Any) -> tuple[str, dict[str, Any]]:
    try:
        mujoco.MjModel.from_xml_string(MINIMAL_MJCF)
    except Exception as exc:
        return (
            "blocked_by_mujoco_model_load_error",
            {
                "status": "blocked_by_mujoco_model_load_error",
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )
    return (
        "passed_minimal_mjcf_sanity_probe",
        {"status": "passed_minimal_mjcf_sanity_probe"},
    )


def _run_real_urdf_load_probe(
    artifacts: dict[str, Any],
    mujoco: Any,
) -> tuple[str, str | None, dict[str, Any]]:
    source_urdf_path = artifacts.get("_source_urdf_path")
    if source_urdf_path is None:
        return (
            "blocked_by_missing_robot_body_asset_source_urdf",
            None,
            {
                "status": "blocked_by_missing_robot_body_asset_source_urdf",
                "source_urdf_ref": "robot_body_asset_report.source_urdf",
            },
        )

    try:
        mujoco.MjModel.from_xml_path(str(source_urdf_path))
    except Exception as exc:
        error = _sanitize_text(str(exc), artifacts)
        return (
            "blocked_by_mujoco_model_load_error",
            error,
            {
                "status": "blocked_by_mujoco_model_load_error",
                "error_type": type(exc).__name__,
                "error": error,
                "source_urdf_ref": "robot_body_asset_report.source_urdf",
            },
        )

    return (
        "loaded_real_urdf_with_mujoco",
        None,
        {
            "status": "loaded_real_urdf_with_mujoco",
            "source_urdf_ref": "robot_body_asset_report.source_urdf",
        },
    )


def _model_load_blocking_items(
    real_status: str,
    model: dict[str, Any],
    minimal_diagnostics: dict[str, Any],
    real_diagnostics: dict[str, Any],
) -> list[str]:
    items = set(model.get("blocked_by", []))
    if minimal_diagnostics["status"] == "blocked_by_mujoco_model_load_error":
        items.add("minimal_mjcf_model_load")
    if real_status == "blocked_by_mujoco_model_load_error":
        items.add("real_urdf_mujoco_model_load")
    if real_status == "blocked_by_missing_robot_body_asset_source_urdf":
        items.add("robot_body_asset_source_urdf")
    if real_diagnostics.get("status") != "loaded_real_urdf_with_mujoco":
        items.add("mjcf_conversion_or_urdf_compatibility")
    return sorted(items)


def _real_urdf_next_step(real_status: str, model: dict[str, Any]) -> str:
    if real_status == "loaded_real_urdf_with_mujoco":
        return "prepare_trajectory_replay_runner"
    if model.get("mesh_reference_count", 0) > 0:
        return "repair_mesh_paths_before_mujoco_load"
    return "prepare_minimal_mjcf_adapter"


def _build_isaac_remote_preflight_report(artifacts: dict[str, Any]) -> dict[str, Any]:
    isaac = artifacts["isaac_manifest"]
    return {
        "report_id": "nv01-c0-isaac-remote-preflight",
        "runtime_target": "Isaac Sim",
        "runtime_location": "remote_or_server_required",
        "local_runtime_status": "not_installed_locally_by_design",
        "remote_runtime_status": "blocked_by_missing_remote_isaac_runtime",
        "source_stage_ref": isaac.get("source_stage_ref", "openusd_stage.usda"),
        "source_replay_fixture_ref": isaac.get(
            "source_replay_fixture_ref",
            "isaac_replay_fixture.json",
        ),
        "required_prim_paths": isaac.get("required_prim_paths", []),
        "frame_bindings": isaac.get("frame_bindings", {}),
        "trajectory_bindings": isaac.get("trajectory_bindings", {}),
        "sensor_placeholders": isaac.get("sensor_placeholders", []),
        "expected_remote_outputs": [
            "nv01_c0_isaac_stage_import_report.json",
            "nv01_c0_isaac_replay_fixture_report.json",
            "nv01_c0_isaac_runtime_blocking_report.json",
        ],
        "expected_isaac_sim_version": "to_be_selected_on_remote_runtime",
        "required_gpu_driver": "nvidia_driver_required_on_remote_runtime",
        "remote_launch_method": "headless_or_workstation_server_runner",
        "remote_stage_path_policy": "copy_openusd_stage_usda_to_remote_workspace",
        "remote_fixture_path_policy": (
            "copy_isaac_runtime_validation_input_manifest_and_replay_fixture_to_remote_workspace"
        ),
        "expected_runtime_report_schema": [
            "stage_import_status",
            "fixture_load_status",
            "required_prim_path_status",
            "frame_binding_status",
            "trajectory_binding_status",
            "sensor_placeholder_status",
            "runtime_errors",
            "blocking_items",
            "readiness_boundary",
        ],
        "blocked_by": ["remote_isaac_runtime"],
        "readiness_boundary": READINESS_BOUNDARY,
    }


def _build_reproducibility_manifest(artifacts: dict[str, Any]) -> dict[str, Any]:
    return {
        "manifest_id": "mj01-a-nv01-c0-builder-reproducibility-manifest",
        "source_readiness_ref": REQUIRED_READINESS_FILES["summary"],
        "source_mujoco_feasibility_ref": REQUIRED_READINESS_FILES[
            "mujoco_feasibility"
        ],
        "source_isaac_manifest_ref": REQUIRED_READINESS_FILES["isaac_manifest"],
        "builder": "weldcore.skill_asset.mj01_mujoco_probe",
        "generated_payloads": [
            "mujoco_runtime_probe_report",
            "mujoco_model_input_resolution_report",
            "mujoco_probe_report",
            "isaac_remote_preflight_report",
            "reproducibility_manifest",
            "task_payloads",
        ],
        "runtime_dependencies": ["optional:mujoco"],
        "default_dependency_boundary": [
            "no_mujoco_default_dependency",
            "no_isaac_sim_local_dependency",
            "no_urdf_to_mjcf_conversion",
        ],
        "readiness_boundary": READINESS_BOUNDARY,
    }


def _build_task_payloads(artifacts: dict[str, Any]) -> dict[str, dict[str, Any]]:
    task_payloads = {}
    for task_id, task_artifact in artifacts["task_artifacts"].items():
        mujoco_task = task_artifact["mujoco_task_replay_feasibility"]
        isaac_task = task_artifact["isaac_runtime_task_validation_input"]
        task_payloads[task_id] = {
            "mj01_task_trajectory_dry_run_input": {
                "task_id": task_id,
                "runtime_target": "MuJoCo",
                "trajectory_ref": mujoco_task.get("trajectory_ref"),
                "source_task_dir_ref": mujoco_task.get("source_task_dir_ref"),
                "frame_refs": {
                    "tcp_frame_ref": mujoco_task.get("tcp_frame_ref"),
                    "tool_frame_ref": mujoco_task.get("tool_frame_ref"),
                    "workpiece_frame_ref": mujoco_task.get("workpiece_frame_ref"),
                },
                "dry_run_status": "dry_run_inputs_prepared",
                "blocked_by": mujoco_task.get("blocked_by", []),
                "readiness_boundary": READINESS_BOUNDARY,
            },
            "nv01_c0_task_isaac_remote_preflight_input": {
                "task_id": task_id,
                "runtime_target": "Isaac Sim",
                "runtime_location": "remote_or_server_required",
                "source_task_dir_ref": isaac_task.get("source_task_dir_ref"),
                "stage_task_prim_ref": isaac_task.get("stage_task_prim_ref"),
                "trajectory_ref": isaac_task.get("trajectory_ref"),
                "remote_runtime_status": "blocked_by_missing_remote_isaac_runtime",
                "blocked_by": ["remote_isaac_runtime"],
                "readiness_boundary": READINESS_BOUNDARY,
            },
        }
    return task_payloads


def _stable_ref(value: Any) -> str | None:
    if value is None:
        return None
    return str(value).replace("\\", "/")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sanitize_text(text: str, artifacts: dict[str, Any]) -> str:
    replacements = [
        (artifacts.get("source_readiness_dir"), "<source-readiness-dir>"),
        (artifacts.get("_source_urdf_path"), "<robot-body-source-urdf>"),
        (artifacts.get("_robot_body_asset_report_path"), "<robot-body-asset-report>"),
        (
            artifacts["robot_body_asset_report"].get("source_urdf"),
            "<robot-body-source-urdf>",
        ),
    ]
    sanitized = text
    for original, replacement in replacements:
        if original:
            sanitized = sanitized.replace(str(original), replacement)
    return sanitized
