from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from weldcore.simulation_bakeoff import (
    build_simulation_evidence_bundle,
    default_simulation_task_specs,
    run_simlite_reference,
)
from weldcore.robot_process import build_robot_context_from_body_asset

from .assessment import build_skill_transfer_assessment
from .builders import build_manipulation_skill_asset_from_simulation_bundle
from .context import (
    build_contextual_feasibility_result,
    build_default_evidence_writeback_summary,
    build_default_scene_context_asset,
)
from .urdf import build_robot_body_asset_from_urdf


DEFAULT_URDF_PATH = Path(__file__).resolve().parents[3] / "docs" / "real-urdf" / "robot.urdf"


def run_skill_asset_report(outdir: str | Path, urdf_path: str | Path | None = None) -> dict[str, Any]:
    output_dir = Path(outdir)
    output_dir.mkdir(parents=True, exist_ok=True)

    task_spec = default_simulation_task_specs()[0]
    bundle = build_simulation_evidence_bundle(task_spec, run_simlite_reference(task_spec))
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

    payload = {
        "skill_asset": skill_asset.to_dict(),
        "robot_body_asset": robot_body_asset.to_dict(),
        "robot_context_spec": robot_context.to_dict(),
        "scene_context_asset": scene_context.to_dict(),
        "transfer_assessment": assessment.to_dict(),
        "robot_feasibility_result": feasibility_result.to_dict(),
        "evidence_writeback_summary": evidence_writeback_summary.to_dict(),
    }

    _write_json(output_dir / "skill_asset_report.json", payload["skill_asset"])
    _write_json(output_dir / "robot_body_asset_report.json", payload["robot_body_asset"])
    _write_json(output_dir / "robot_context_spec.json", payload["robot_context_spec"])
    _write_json(output_dir / "scene_context_asset_report.json", payload["scene_context_asset"])
    _write_json(output_dir / "skill_transfer_assessment.json", payload["transfer_assessment"])
    _write_json(output_dir / "robot_feasibility_result.json", payload["robot_feasibility_result"])
    _write_json(
        output_dir / "skill_asset_evidence_writeback_summary.json",
        payload["evidence_writeback_summary"],
    )

    return payload


def main(argv: list[str] | None = None) -> dict[str, Any]:
    parser = argparse.ArgumentParser(description="Generate canonical skill asset reports.")
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--urdf-path", default=None)
    args = parser.parse_args(argv)

    payload = run_skill_asset_report(args.outdir, args.urdf_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
