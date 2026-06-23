from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


CANONICAL_NV01B_STATUS = {
    "ready_for_static_openusd_review",
    "blocked_by_openusd_stage_contract_issue",
    "blocked_by_missing_isaac_runtime",
    "not_isaac_sim_runtime_validation",
    "blocked_for_real_isaac_sim_replay",
    "blocked_by_missing_sensor_calibration",
    "blocked_by_missing_real_process_inputs",
    "not_policy_training_result",
    "not_formal_WPS_PQR",
    "not_ready_for_robot_execution",
}

REQUIRED_NV01A_FILES = {
    "summary": "nv01_summary.json",
    "procedure_contract": "weld_procedure_knowledge_contract.json",
    "top_parameter_set": "weld_procedure_parameter_set.json",
    "top_validation_report": "weld_procedure_validation_report.json",
    "mapping_matrix": "procedure_to_nv01_mapping_matrix.json",
    "package": "weld_skill_digital_twin_package.json",
    "openusd_scene_manifest": "openusd_scene_manifest.json",
    "isaac_sim_replay_config": "isaac_sim_replay_config.json",
    "domain_randomization_recipe": "domain_randomization_recipe.json",
    "training_readiness_report": "training_readiness_report.json",
}

TASK_NV01A_FILES = {
    "skill_asset_ref": "skill_asset_ref.json",
    "weld_procedure_parameter_set": "weld_procedure_parameter_set.json",
    "weld_procedure_validation_report": "weld_procedure_validation_report.json",
    "openusd_task_manifest": "openusd_task_manifest.json",
    "isaac_replay_task_config": "isaac_replay_task_config.json",
    "sensor_and_annotation_manifest": "sensor_and_annotation_manifest.json",
    "training_task_readiness": "training_task_readiness.json",
}

READINESS_BOUNDARY = [
    "not_isaac_sim_runtime_validation",
    "not_policy_training_result",
    "not_formal_WPS_PQR",
    "not_ready_for_robot_execution",
]

REQUIRED_METADATA_KEYS = [
    "a02:report_id",
    "a02:procedure_contract_ref",
    "a02:procedure_parameter_set_ref",
    "a02:skill_asset_ref",
    "a02:robot_body_asset_ref",
    "a02:scene_context_asset_ref",
    "a02:readiness_boundary",
    "a02:not_ready_reasons",
    "a02:workpiece_frame",
    "a02:workpiece_geometry_status",
    "a02:seam_path_ref",
    "a02:point_count",
    "a02:path_units",
    "a02:frame_ref",
    "a02:trajectory_ref",
    "a02:trajectory_units",
    "a02:sample_count",
    "a02:tcp_frame_ref",
    "a02:torch_frame_ref",
    "a02:tool_frame_ref",
    "a02:torch_geometry_status",
    "a02:sensor_manifest_ref",
    "a02:sensor_layout_status",
    "a02:required_calibration",
    "a02:safety_boundary_ref",
    "a02:boundary_status",
    "a02:collision_validation_status",
]

REPORT_ID = "nv01-b-openusd-isaac-reproducible-experiment-base"


class MissingNV01AArtifactError(RuntimeError):
    pass


def load_nv01a_artifacts(source_nv01a_dir: str | Path) -> dict[str, Any]:
    root = Path(source_nv01a_dir)
    if not root.exists():
        raise MissingNV01AArtifactError(f"missing_source_nv01a_dir:{root}")

    missing = [
        rel for rel in REQUIRED_NV01A_FILES.values() if not (root / rel).exists()
    ]
    if missing:
        raise MissingNV01AArtifactError(
            "missing_nv01a_artifacts:" + ",".join(sorted(missing))
        )

    artifacts = {
        name: json.loads((root / rel).read_text(encoding="utf-8"))
        for name, rel in REQUIRED_NV01A_FILES.items()
    }
    tasks = artifacts["summary"]["tasks"]
    artifacts["root"] = root
    artifacts["task_ids"] = [task["task_id"] for task in tasks]
    artifacts["task_dirs"] = {
        task["task_id"]: task["task_output_dir"] for task in tasks
    }
    artifacts["task_artifacts"] = {
        task["task_id"]: _load_task_nv01a_artifacts(root / task["task_output_dir"])
        for task in tasks
    }
    return artifacts


def build_nv01_b_experiment_payloads(
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    task_payloads = _build_task_payloads(artifacts)
    stage = author_openusd_stage_usda(artifacts, task_payloads)
    required_prim_paths = _required_prim_paths(task_payloads)
    validation = validate_openusd_stage_text(
        stage,
        required_prim_paths,
        REQUIRED_METADATA_KEYS,
    )
    validation.update(
        {
            "stage_ref": "openusd_stage.usda",
            "required_prim_paths": required_prim_paths,
            "required_metadata_keys": REQUIRED_METADATA_KEYS,
            "canonical_ref_checks": {
                "skill_asset_refs": _present_if(
                    '"a02:skill_asset_ref"' in stage
                    and '"a02:robot_body_asset_ref"' in stage
                    and '"a02:scene_context_asset_ref"' in stage
                )
            },
            "procedure_metadata_checks": {
                "procedure_contract_refs": _present_if(
                    '"a02:procedure_contract_ref"' in stage
                ),
                "procedure_parameter_set_refs": _present_if(
                    '"a02:procedure_parameter_set_ref"' in stage
                ),
            },
            "not_ready_reasons": [
                "blocked_by_missing_isaac_runtime",
                "blocked_for_real_isaac_sim_replay",
                "blocked_by_missing_sensor_calibration",
                "blocked_by_missing_real_process_inputs",
            ],
            "readiness_boundary": READINESS_BOUNDARY,
        }
    )

    audit = _build_procedure_sim_parameter_audit(artifacts)
    sensor = _build_sensor_annotation_manifest()
    blocking = _build_simulation_blocking_report(audit, sensor)
    fixture = _build_isaac_replay_fixture(artifacts, task_payloads)
    reproducibility = _build_experiment_reproducibility_manifest(artifacts)

    return {
        "openusd_stage_usda": stage,
        "openusd_stage_validation_report": validation,
        "isaac_replay_fixture": fixture,
        "procedure_sim_parameter_audit": audit,
        "sensor_annotation_manifest": sensor,
        "simulation_blocking_report": blocking,
        "experiment_reproducibility_manifest": reproducibility,
        "task_payloads": task_payloads,
    }


def author_openusd_stage_usda(
    artifacts: dict[str, Any],
    task_payloads: dict[str, dict[str, Any]],
) -> str:
    first_task_id = artifacts["task_ids"][0]
    first_task = task_payloads[first_task_id]
    lines = [
        "#usda 1.0",
        "(",
        "    customData = {",
        _usd_string("a02:report_id", REPORT_ID, 8),
        _usd_string("a02:procedure_contract_ref", "weld_procedure_knowledge_contract.json", 8),
        _usd_string("a02:procedure_parameter_set_ref", "weld_procedure_parameter_set.json", 8),
        _usd_string("a02:skill_asset_ref", first_task["skill_asset_ref"], 8),
        _usd_string("a02:robot_body_asset_ref", first_task["robot_body_asset_ref"], 8),
        _usd_string("a02:scene_context_asset_ref", first_task["scene_context_asset_ref"], 8),
        _usd_string_array("a02:readiness_boundary", READINESS_BOUNDARY, 8),
        _usd_string_array(
            "a02:not_ready_reasons",
            [
                "blocked_by_missing_isaac_runtime",
                "blocked_for_real_isaac_sim_replay",
                "blocked_by_missing_sensor_calibration",
                "blocked_by_missing_real_process_inputs",
            ],
            8,
        ),
        "    }",
        ")",
        "",
        'def Xform "World"',
        "{",
        "    customData = {",
        _usd_string("a02:readiness_boundary", "not_isaac_sim_runtime_validation", 8),
        "    }",
        '    def Xform "Robot"',
        "    {",
        "        customData = {",
        _usd_string("a02:robot_body_asset_ref", first_task["robot_body_asset_ref"], 12),
        _usd_string("a02:skill_asset_ref", first_task["skill_asset_ref"], 12),
        "        }",
        "    }",
        '    def Xform "Workpiece"',
        "    {",
        "        customData = {",
        _usd_string("a02:workpiece_frame", "workpiece_frame", 12),
        _usd_string("a02:workpiece_geometry_status", "placeholder_from_scene_context", 12),
        _usd_string("a02:scene_context_asset_ref", first_task["scene_context_asset_ref"], 12),
        "        }",
        "    }",
        '    def Xform "WeldTasks"',
        "    {",
    ]
    for task in task_payloads.values():
        lines.extend(_task_usda_lines(task))
    lines.extend(["    }", "}", ""])
    return "\n".join(lines)


def validate_openusd_stage_text(
    stage_text: str,
    required_prim_paths: list[str],
    required_metadata_keys: list[str],
) -> dict[str, Any]:
    present_paths = _extract_xform_paths(stage_text)
    missing_prim_paths = [
        path for path in required_prim_paths if path not in present_paths
    ]
    metadata_checks = {
        key: _present_if(f'"{key}"' in stage_text) for key in required_metadata_keys
    }
    missing_metadata = [
        key for key, status in metadata_checks.items() if status != "present"
    ]
    return {
        "validation_status": (
            "blocked_by_openusd_stage_contract_issue"
            if missing_prim_paths or missing_metadata
            else "ready_for_static_openusd_review"
        ),
        "stage_ref": "openusd_stage.usda",
        "required_prim_paths": required_prim_paths,
        "missing_prim_paths": missing_prim_paths,
        "required_metadata_keys": required_metadata_keys,
        "metadata_checks": metadata_checks,
        "canonical_ref_checks": {},
        "procedure_metadata_checks": {},
        "not_ready_reasons": ["not_isaac_sim_runtime_validation"],
        "readiness_boundary": READINESS_BOUNDARY,
    }


def _load_task_nv01a_artifacts(task_dir: Path) -> dict[str, Any]:
    missing = [
        rel for rel in TASK_NV01A_FILES.values() if not (task_dir / rel).exists()
    ]
    if missing:
        raise MissingNV01AArtifactError(
            "missing_task_nv01a_artifacts:" + ",".join(sorted(missing))
        )
    return {
        name: json.loads((task_dir / rel).read_text(encoding="utf-8"))
        for name, rel in TASK_NV01A_FILES.items()
    }


def _build_task_payloads(
    artifacts: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    task_payloads = {}
    for task_id in artifacts["task_ids"]:
        task_dir = artifacts["task_dirs"][task_id]
        task_artifacts = artifacts["task_artifacts"][task_id]
        manifest = task_artifacts["openusd_task_manifest"]
        canonical_refs = manifest.get("canonical_artifact_refs_by_task", {}).get(
            task_id,
            task_artifacts.get("canonical_artifact_refs", {}),
        )
        if not canonical_refs:
            canonical_refs = artifacts["openusd_scene_manifest"][
                "canonical_artifact_refs_by_task"
            ][task_id]
        task_payloads[task_id] = {
            "task_id": task_id,
            "task_prim": _sanitize_prim_name(task_id),
            "task_dir": task_dir,
            "root_prim": f"/World/WeldTasks/{_sanitize_prim_name(task_id)}",
            "skill_asset_ref": canonical_refs["skill_asset_report.json"],
            "robot_body_asset_ref": canonical_refs["robot_body_asset_report.json"],
            "robot_context_ref": canonical_refs["robot_context_spec.json"],
            "scene_context_asset_ref": canonical_refs["scene_context_asset_report.json"],
            "robot_feasibility_ref": canonical_refs["robot_feasibility_result.json"],
            "procedure_parameter_set_ref": f"{task_dir}/weld_procedure_parameter_set.json",
            "seam_path_ref": canonical_refs["scene_context_asset_report.json"],
            "trajectory_ref": canonical_refs["skill_asset_report.json"],
            "sensor_manifest_ref": "sensor_annotation_manifest.json",
            "safety_boundary_ref": canonical_refs["scene_context_asset_report.json"],
            "parameter_set": task_artifacts["weld_procedure_parameter_set"],
            "isaac_replay_task_config_ref": f"{task_dir}/isaac_replay_task_config.json",
        }
    return task_payloads


def _task_usda_lines(task: dict[str, Any]) -> list[str]:
    return [
        f'        def Xform "{task["task_prim"]}"',
        "        {",
        "            customData = {",
        _usd_string("a02:procedure_parameter_set_ref", task["procedure_parameter_set_ref"], 16),
        _usd_string("a02:skill_asset_ref", task["skill_asset_ref"], 16),
        "            }",
        '            def Xform "SeamPath"',
        "            {",
        "                customData = {",
        _usd_string("a02:seam_path_ref", task["seam_path_ref"], 20),
        _usd_string("a02:point_count", "2", 20),
        _usd_string("a02:path_units", "mm", 20),
        _usd_string("a02:frame_ref", "workpiece_frame", 20),
        "                }",
        "            }",
        '            def Xform "TcpTrajectoryCandidate"',
        "            {",
        "                customData = {",
        _usd_string("a02:trajectory_ref", task["trajectory_ref"], 20),
        _usd_string("a02:trajectory_units", "mm,s", 20),
        _usd_string("a02:sample_count", "2", 20),
        _usd_string("a02:tcp_frame_ref", "tool_tcp_frame", 20),
        "                }",
        "            }",
        '            def Xform "Torch"',
        "            {",
        "                customData = {",
        _usd_string("a02:torch_frame_ref", "torch_frame", 20),
        _usd_string("a02:tool_frame_ref", "tool_frame", 20),
        _usd_string("a02:torch_geometry_status", "placeholder_pending_robot_tool_geometry", 20),
        _usd_string("a02:procedure_parameter_set_ref", task["procedure_parameter_set_ref"], 20),
        "                }",
        "            }",
        '            def Xform "Sensors"',
        "            {",
        "                customData = {",
        _usd_string("a02:sensor_manifest_ref", task["sensor_manifest_ref"], 20),
        _usd_string("a02:sensor_layout_status", "blocked_by_missing_sensor_calibration", 20),
        _usd_string("a02:required_calibration", "sensor_layout_calibration", 20),
        "                }",
        "            }",
        '            def Xform "SafetyBoundary"',
        "            {",
        "                customData = {",
        _usd_string("a02:safety_boundary_ref", task["safety_boundary_ref"], 20),
        _usd_string("a02:boundary_status", "placeholder_from_scene_context", 20),
        _usd_string("a02:collision_validation_status", "not_isaac_sim_runtime_validation", 20),
        "                }",
        "            }",
        "        }",
    ]


def _build_isaac_replay_fixture(
    artifacts: dict[str, Any],
    task_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    first_task = next(iter(task_payloads.values()))
    return {
        "fixture_id": "nv01-b-isaac-replay-fixture",
        "stage_ref": "openusd_stage.usda",
        "runtime_target": "Isaac Sim",
        "runtime_status": "blocked_by_missing_isaac_runtime",
        "robot_asset": first_task["robot_body_asset_ref"],
        "frame_bindings": {
            "world": "/World",
            "workpiece_frame": "/World/Workpiece",
            "tool_frame": "tool_frame",
            "tcp_frame": "tool_tcp_frame",
        },
        "trajectory_bindings": {
            task_id: {
                "stage_prim": f'{task["root_prim"]}/TcpTrajectoryCandidate',
                "trajectory_source_ref": task["trajectory_ref"],
            }
            for task_id, task in task_payloads.items()
        },
        "procedure_parameter_bindings": artifacts["isaac_sim_replay_config"][
            "procedure_parameter_inputs"
        ],
        "task_fixtures": {
            task_id: {
                "task_id": task_id,
                "stage_prim": task["root_prim"],
                "task_config_ref": task["isaac_replay_task_config_ref"],
            }
            for task_id, task in task_payloads.items()
        },
        "blocked_by": [
            "blocked_by_missing_isaac_runtime",
            "blocked_for_real_isaac_sim_replay",
            "blocked_by_missing_sensor_calibration",
            "blocked_by_missing_real_process_inputs",
        ],
        "readiness_boundary": READINESS_BOUNDARY,
    }


def _build_procedure_sim_parameter_audit(
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    contract = artifacts["procedure_contract"]
    parameter_values = artifacts["top_parameter_set"]["values"]
    mappings = {}
    blocking_counts: dict[str, int] = {}
    for field in contract["fields"]:
        field_id = field["field_id"]
        status = parameter_values[field_id]
        blocking_scopes = _blocking_scopes_for_field(field, status)
        for scope in blocking_scopes:
            blocking_counts[scope] = blocking_counts.get(scope, 0) + 1
        mappings[field_id] = {
            "field_id": field_id,
            "display_name": field["display_name"],
            "requirement_level": field["requirement_level"],
            "acquisition_mode": field["acquisition_mode"],
            "a02_target_path": field["a02_target_path"],
            "usd_metadata_path": f"/World/WeldTasks.*.procedure.{field_id}",
            "isaac_replay_parameter": f"procedure_parameter_inputs.{field_id}",
            "domain_randomization_usage": _domain_randomization_usage(field),
            "coverage_status": status["coverage_status"],
            "value_source": status["source"] or "missing_from_nv01a_source",
            "blocks": field["blocks"],
            "blocking_scopes": blocking_scopes,
            "source_ref": "weld_procedure_knowledge_contract.json",
        }
    return {
        "audit_id": "nv01-b-procedure-sim-parameter-audit",
        "contract_version": contract["contract_version"],
        "field_count": contract["field_count"],
        "mappings": mappings,
        "mapped_field_count": len(mappings),
        "blocking_field_count_by_scope": dict(sorted(blocking_counts.items())),
        "source_refs": {
            "procedure_contract": "weld_procedure_knowledge_contract.json",
            "procedure_parameter_set": "weld_procedure_parameter_set.json",
            "domain_randomization_recipe": "domain_randomization_recipe.json",
        },
    }


def _build_sensor_annotation_manifest() -> dict[str, Any]:
    return {
        "manifest_id": "nv01-b-sensor-annotation-manifest",
        "stage_ref": "openusd_stage.usda",
        "sensor_placeholders": [
            "overview_camera_placeholder",
            "torch_camera_placeholder",
        ],
        "annotation_layers": [
            "tcp_pose_trace",
            "weld_seam_annotation",
            "procedure_parameter_overlay",
        ],
        "required_real_calibration": [
            "sensor_layout_calibration",
            "camera_intrinsics_extrinsics",
            "arc_glare_smoke_spatter_calibration",
        ],
        "blocked_by": ["blocked_by_missing_sensor_calibration"],
        "readiness_boundary": READINESS_BOUNDARY,
    }


def _build_simulation_blocking_report(
    audit: dict[str, Any],
    sensor: dict[str, Any],
) -> dict[str, Any]:
    missing_fields_by_scope: dict[str, list[str]] = {}
    for field_id, mapping in audit["mappings"].items():
        for scope in mapping["blocking_scopes"]:
            missing_fields_by_scope.setdefault(scope, []).append(field_id)
    missing_fields_by_scope = {
        scope: sorted(fields) for scope, fields in sorted(missing_fields_by_scope.items())
    }
    scope_status = {
        scope: "blocked_for_real_isaac_sim_replay"
        if scope == "real_isaac_sim_replay"
        else "blocked_by_missing_real_process_inputs"
        for scope in missing_fields_by_scope
    }
    scope_status.update(
        {
            "sensor_simulation": "blocked_by_missing_sensor_calibration",
            "replicator_dataset": "blocked_by_missing_sensor_calibration",
            "policy_training": "not_policy_training_result",
            "wps_pqr_release": "not_formal_WPS_PQR",
        }
    )
    return {
        "report_id": "nv01-b-simulation-blocking-report",
        "overall_status": "blocked_for_real_isaac_sim_replay",
        "scope_status": dict(sorted(scope_status.items())),
        "blocking_items": [
            "blocked_by_missing_isaac_runtime",
            "blocked_by_missing_sensor_calibration",
            "blocked_by_missing_real_process_inputs",
        ],
        "missing_fields_by_scope": missing_fields_by_scope,
        "missing_calibrations": sensor["required_real_calibration"],
        "missing_runtime_inputs": [
            "isaac_sim_runtime",
            "h300_workstation_logs",
            "real_tcp_tool_workpiece_calibration",
        ],
        "next_required_inputs": [
            "real_welding_current_a",
            "real_welding_voltage_v",
            "real_heat_input_inputs",
            "sensor_layout_calibration",
            "expert_review_record",
        ],
        "readiness_boundary": READINESS_BOUNDARY,
    }


def _build_experiment_reproducibility_manifest(
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    return {
        "manifest_id": "nv01-b-experiment-reproducibility-manifest",
        "source_nv01a_root_ref": str(artifacts["root"]),
        "source_nv01a_summary_ref": "nv01_summary.json",
        "generated_artifacts": [
            "openusd_stage.usda",
            "openusd_stage_validation_report.json",
            "isaac_replay_fixture.json",
            "procedure_sim_parameter_audit.json",
            "sensor_annotation_manifest.json",
            "simulation_blocking_report.json",
            "experiment_reproducibility_manifest.json",
        ],
        "command": (
            "uv run python -m weldcore.skill_asset.nv01_b_experiment_base_report "
            "--outdir artifacts/demo/nv01-b-experiment-base"
        ),
        "default_dependency_boundary": [
            "no_isaac_sim_default_dependency",
            "no_openusd_sdk_default_dependency",
            "no_gpu_default_dependency",
        ],
        "source_artifact_refs": {
            name: rel for name, rel in REQUIRED_NV01A_FILES.items()
        },
        "validation_commands": [
            "uv run pytest tests/test_nv01_b_experiment_base.py -q",
        ],
    }


def _blocking_scopes_for_field(
    field: dict[str, Any],
    status: dict[str, Any],
) -> list[str]:
    coverage_status = status["coverage_status"]
    acquisition_mode = field["acquisition_mode"]
    scopes: set[str] = set()
    if (
        coverage_status in {"missing_required", "missing_conditional"}
        and acquisition_mode in {"human_required", "human_confirmed_or_imported"}
    ):
        scopes.add("expert_review")
        if "wps_pqr_release" in field["blocks"]:
            scopes.add("wps_pqr_release")
    if (
        coverage_status in {"missing_required", "missing_conditional"}
        or coverage_status.startswith("blocked_")
    ) and acquisition_mode == "workcell_logged":
        scopes.update(
            {"real_isaac_sim_replay", "sensor_simulation", "expert_review"}
        )
    if coverage_status.startswith("blocked_") and acquisition_mode == "system_computed":
        scopes.update({"policy_training", "wps_pqr_release"})
    return sorted(scopes)


def _domain_randomization_usage(field: dict[str, Any]) -> list[str]:
    if "domain_randomization_recipe" in field["nv01_usage"]:
        return ["domain_randomization_recipe"]
    return []


def _required_prim_paths(task_payloads: dict[str, dict[str, Any]]) -> list[str]:
    paths = ["/World", "/World/Robot", "/World/Workpiece", "/World/WeldTasks"]
    for task in task_payloads.values():
        root = task["root_prim"]
        paths.extend(
            [
                root,
                f"{root}/SeamPath",
                f"{root}/TcpTrajectoryCandidate",
                f"{root}/Torch",
                f"{root}/Sensors",
                f"{root}/SafetyBoundary",
            ]
        )
    return paths


def _extract_xform_paths(stage_text: str) -> set[str]:
    paths: set[str] = set()
    stack: list[str] = []
    pending_name: str | None = None
    in_custom_data = False
    custom_data_depth = 0

    for line in stage_text.splitlines():
        stripped = line.strip()
        if in_custom_data:
            custom_data_depth += stripped.count("{") - stripped.count("}")
            if custom_data_depth <= 0:
                in_custom_data = False
            continue

        if stripped == "}":
            if stack:
                stack.pop()
            continue

        match = re.match(r'def Xform "([^"]+)"', stripped)
        if match:
            name = match.group(1)
            paths.add("/" + "/".join([*stack, name]))
            pending_name = name
            if "{" in stripped:
                stack.append(name)
                pending_name = None
            continue

        if pending_name and stripped == "{":
            stack.append(pending_name)
            pending_name = None
            continue

        if "customData = {" in stripped:
            in_custom_data = True
            custom_data_depth = stripped.count("{") - stripped.count("}")
            if custom_data_depth <= 0:
                in_custom_data = False

    return paths


def _sanitize_prim_name(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9_]", "_", value)
    if not sanitized or sanitized[0].isdigit():
        sanitized = f"task_{sanitized}"
    return sanitized


def _usd_string(key: str, value: Any, indent: int) -> str:
    return f'{" " * indent}string "{_escape_usd(key)}" = "{_escape_usd(str(value))}"'


def _usd_string_array(key: str, values: list[str], indent: int) -> str:
    items = ", ".join(f'"{_escape_usd(value)}"' for value in values)
    return f'{" " * indent}string[] "{_escape_usd(key)}" = [{items}]'


def _escape_usd(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _present_if(condition: bool) -> str:
    return "present" if condition else "missing"
