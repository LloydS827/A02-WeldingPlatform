from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from weldcore.robot_process import build_robot_context_from_body_asset
from weldcore.simulation_bakeoff import (
    build_simulation_evidence_bundle,
    default_simulation_task_specs,
    run_simlite_reference,
)

from .assessment import build_skill_transfer_assessment
from .asset_report import DEFAULT_URDF_PATH
from .builders import build_manipulation_skill_asset_from_simulation_bundle
from .context import (
    build_contextual_feasibility_result,
    build_default_evidence_writeback_summary,
    build_default_scene_context_asset,
)
from .strategic_alignment import (
    build_a01_b06_skill_asset_mapping,
    build_a02_to_a01_product_validation_handoff,
    build_default_evidence_source_catalog,
    build_default_expert_review_record,
    build_ip_disclosure_support_matrix,
)
from .urdf import build_robot_body_asset_from_urdf


CANONICAL_TASK_ARTIFACTS = (
    "skill_asset_report.json",
    "robot_body_asset_report.json",
    "robot_context_spec.json",
    "scene_context_asset_report.json",
    "skill_transfer_assessment.json",
    "robot_feasibility_result.json",
    "skill_asset_evidence_writeback_summary.json",
    "skill_asset_evidence_source_catalog.json",
    "a01_b06_skill_asset_mapping.json",
    "expert_review_record.json",
    "a02_to_a01_product_validation_handoff.json",
    "ip_disclosure_support_matrix.json",
)
EXTRA_TASK_ARTIFACTS = ("simulation_evidence_bundle.json",)

_NON_EXECUTION_GAPS = (
    "real_tcp_calibration",
    "workpiece_frame_measurement",
    "robot_model_identity",
    "joint_limits_source",
    "full_ik_solver",
    "real_collision_validation",
    "real_robot_execution_log",
    "real_welding_quality_feedback",
)


def run_demo_evidence_pack(
    outdir: str | Path,
    urdf_path: str | Path | None = None,
) -> dict[str, Any]:
    output_dir = Path(outdir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tasks: list[dict[str, Any]] = []
    first_handoff: dict[str, Any] | None = None
    first_ip_support: dict[str, Any] | None = None

    for task_spec in default_simulation_task_specs()[:2]:
        task_dir = output_dir / task_spec.task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        adapter_result = run_simlite_reference(task_spec)
        bundle = build_simulation_evidence_bundle(task_spec, adapter_result)
        skill_asset = build_manipulation_skill_asset_from_simulation_bundle(bundle)
        robot_body_asset = build_robot_body_asset_from_urdf(urdf_path or DEFAULT_URDF_PATH)
        robot_context = build_robot_context_from_body_asset(robot_body_asset)
        scene_context = build_default_scene_context_asset(skill_asset)
        feasibility_result = build_contextual_feasibility_result(
            skill_asset,
            robot_context,
            scene_context,
        )
        evidence_writeback_summary = build_default_evidence_writeback_summary(skill_asset)
        assessment = build_skill_transfer_assessment(
            skill_asset,
            robot_body_asset,
            robot_context=robot_context,
            scene_context=scene_context,
            feasibility_result=feasibility_result,
        )
        evidence_source_catalog = build_default_evidence_source_catalog(skill_asset)
        a01_b06_mapping = build_a01_b06_skill_asset_mapping(skill_asset)
        expert_review_record = build_default_expert_review_record(
            skill_asset,
            robot_context,
            scene_context,
            feasibility_result,
        )
        a02_to_a01_handoff = build_a02_to_a01_product_validation_handoff(skill_asset)
        ip_disclosure_support_matrix = build_ip_disclosure_support_matrix(skill_asset)

        artifacts = {
            "skill_asset_report.json": skill_asset.to_dict(),
            "robot_body_asset_report.json": robot_body_asset.to_dict(),
            "robot_context_spec.json": robot_context.to_dict(),
            "scene_context_asset_report.json": scene_context.to_dict(),
            "skill_transfer_assessment.json": assessment.to_dict(),
            "robot_feasibility_result.json": feasibility_result.to_dict(),
            "skill_asset_evidence_writeback_summary.json": evidence_writeback_summary.to_dict(),
            "skill_asset_evidence_source_catalog.json": [
                entry.to_dict() for entry in evidence_source_catalog
            ],
            "a01_b06_skill_asset_mapping.json": a01_b06_mapping.to_dict(),
            "expert_review_record.json": expert_review_record.to_dict(),
            "a02_to_a01_product_validation_handoff.json": a02_to_a01_handoff.to_dict(),
            "ip_disclosure_support_matrix.json": ip_disclosure_support_matrix.to_dict(),
            "simulation_evidence_bundle.json": bundle.to_dict(),
        }

        for filename in (*CANONICAL_TASK_ARTIFACTS, *EXTRA_TASK_ARTIFACTS):
            _write_json(task_dir / filename, artifacts[filename])

        artifact_refs = {
            filename: f"{task_spec.task_id}/{filename}"
            for filename in (*CANONICAL_TASK_ARTIFACTS, *EXTRA_TASK_ARTIFACTS)
        }
        handoff_data = a02_to_a01_handoff.to_dict()
        ip_support_data = ip_disclosure_support_matrix.to_dict()
        first_handoff = first_handoff or handoff_data
        first_ip_support = first_ip_support or ip_support_data
        tasks.append(
            {
                "task_id": task_spec.task_id,
                "task_name": task_spec.name,
                "skill_asset_id": skill_asset.asset_id,
                "simulation_bundle_id": bundle.bundle_id,
                "transfer_status": assessment.status,
                "expert_review_status": expert_review_record.review_status,
                "feasibility_status": feasibility_result.status,
                "source_type": skill_asset.source_type,
                "artifact_refs": artifact_refs,
                "boundary_reasons": _dedupe(
                    *assessment.evidence_boundary,
                    *feasibility_result.evidence_boundary,
                    *expert_review_record.review_boundary,
                ),
                "why_ready_for_expert_review": [
                    "lightweight feasibility precheck passed",
                    "simulation evidence bundle and canonical skill asset are available",
                    "robot body, robot context, scene context, and expert review record were generated",
                ],
                "why_not_ready_for_robot_execution": _not_execution_reasons(),
            }
        )

    payload = {
        "demo_id": "a02-demo-evidence-pack",
        "generated_artifacts": [],
        "task_count": len(tasks),
        "tasks": tasks,
        "overall_status": "ready_for_expert_review_candidate_pack",
        "readiness_boundary": [
            "ready_for_expert_review",
            "not_ready_for_robot_execution",
            "simulation_only",
            "not_real_welding_quality_validation",
            "not_full_ik_solver",
            "not_real_collision_validation",
        ],
        "field_explanation": {
            "intent": "Intent captures the welding task identity, seam target, and expected operation boundary.",
            "motion": "Motion captures candidate TCP trajectory and tool orientation from simulation evidence.",
            "constraints": "Constraints remain candidate hints until expert review and real workcell validation.",
            "evidence": "Evidence is simulation_only and suitable for review packaging, not direct robot execution.",
        },
        "simulation_evidence_explanation": {
            "SimulationEvidenceBundle": (
                "Per-task bundle containing task_spec, SimLite adapter result, run record, "
                "dataset candidate, rerun status, and bakeoff score."
            ),
            "source_type": "simulation_only",
            "boundary": "Not a real robot log and not real welding quality validation.",
        },
        "a02_to_a01_handoff_summary": _handoff_summary(first_handoff),
        "ip_support_summary": _ip_support_summary(first_ip_support),
        "next_step_recommendation": (
            "Submit the generated pack for welding robotics expert review, then collect real TCP "
            "calibration, workpiece frame measurement, robot identity, execution logs, collision "
            "validation, and welding quality feedback before robot execution."
        ),
    }

    _write_text(output_dir / "demo_summary.md", _render_markdown(payload))
    _write_text(output_dir / "demo_summary.html", _render_html(payload))
    payload["generated_artifacts"] = sorted([*_generated_artifacts(output_dir), "demo_summary.json"])
    _write_json(output_dir / "demo_summary.json", payload)
    return payload


def main(argv: list[str] | None = None) -> dict[str, Any]:
    parser = argparse.ArgumentParser(description="Generate the A02 demo evidence pack.")
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--urdf-path", default=None)
    args = parser.parse_args(argv)

    payload = run_demo_evidence_pack(args.outdir, args.urdf_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


def _not_execution_reasons() -> list[str]:
    explanations = {
        "real_tcp_calibration": "is required before controller execution.",
        "workpiece_frame_measurement": "must be measured on the real workcell.",
        "robot_model_identity": "must be confirmed against the physical robot.",
        "joint_limits_source": "must be validated from vendor, controller, or field evidence.",
        "full_ik_solver": "validation is not included in this lightweight pack.",
        "real_collision_validation": "is still missing.",
        "real_robot_execution_log": "evidence is not connected yet.",
        "real_welding_quality_feedback": "is required before production use.",
    }
    return [f"{gap} {explanations[gap]}" for gap in _NON_EXECUTION_GAPS]


def _handoff_summary(handoff: dict[str, Any] | None) -> dict[str, Any]:
    if handoff is None:
        return {"candidate_outputs": [], "handoff_boundary": []}
    return {
        "candidate_outputs": handoff["candidate_outputs"],
        "handoff_boundary": handoff["handoff_boundary"],
        "required_confirmations": handoff["required_confirmations"],
        "next_step_recommendation": handoff["next_step_recommendation"],
    }


def _ip_support_summary(support: dict[str, Any] | None) -> list[dict[str, Any]]:
    if support is None:
        return []
    return [
        {
            "patent_item_id": item["patent_item_id"],
            "patent_item_name": item["patent_item_name"],
            "supporting_objects": item["supporting_objects"],
            "missing_real_world_evidence": item["missing_real_world_evidence"],
        }
        for item in support["items"]
    ]


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# A02 Demo Evidence Pack",
        "",
        f"Overall status: `{payload['overall_status']}`",
        "",
        "## Boundary",
        "",
        ", ".join(f"`{item}`" for item in payload["readiness_boundary"]),
        "",
        "## A02 -> A01 Handoff",
        "",
        "Candidate outputs: "
        + ", ".join(f"`{item}`" for item in payload["a02_to_a01_handoff_summary"]["candidate_outputs"]),
        "",
        "Handoff boundary: "
        + ", ".join(f"`{item}`" for item in payload["a02_to_a01_handoff_summary"]["handoff_boundary"]),
        "",
        "## Tasks",
        "",
    ]
    for task in payload["tasks"]:
        lines.extend(
            [
                f"### {task['task_id']}",
                "",
                f"- transfer_status: `{task['transfer_status']}`",
                f"- execution_boundary: `{', '.join(task['boundary_reasons'])}`",
                "- why_not_ready_for_robot_execution: "
                + "; ".join(task["why_not_ready_for_robot_execution"]),
                "",
            ]
        )
    return "\n".join(lines)


def _render_html(payload: dict[str, Any]) -> str:
    boundary = ", ".join(html.escape(item) for item in payload["readiness_boundary"])
    task_sections = "\n".join(
        "<section>"
        f"<h2>{html.escape(task['task_id'])}</h2>"
        f"<p>{html.escape('; '.join(task['why_not_ready_for_robot_execution']))}</p>"
        "</section>"
        for task in payload["tasks"]
    )
    ip_items = "\n".join(
        f"<li>{html.escape(item['patent_item_id'])}: {html.escape(item['patent_item_name'])}</li>"
        for item in payload["ip_support_summary"]
    )
    return (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "<head><meta charset=\"utf-8\"><title>A02 Demo Evidence Pack</title></head>\n"
        "<body>\n"
        "<h1>A02 Demo Evidence Pack</h1>\n"
        f"<p>Overall status: {html.escape(payload['overall_status'])}</p>\n"
        f"<p>Boundary: {boundary}</p>\n"
        "<h2>IP Support</h2>\n"
        f"<ul>{ip_items}</ul>\n"
        "<h2>A02 -&gt; A01</h2>\n"
        f"<p>{html.escape(str(payload['a02_to_a01_handoff_summary']))}</p>\n"
        f"{task_sections}\n"
        "</body>\n"
        "</html>\n"
    )


def _generated_artifacts(output_dir: Path) -> list[str]:
    return sorted(
        str(path.relative_to(output_dir))
        for path in output_dir.rglob("*")
        if path.is_file()
    )


def _dedupe(*items: str) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
