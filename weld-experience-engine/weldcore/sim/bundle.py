from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from ..knowledge.synthetic_input import SyntheticInputFoundation
from ..knowledge.synthetic_manifest import load_synthetic_input_foundation
from ..model import SIMULATION_BUNDLE_SCHEMA_VERSION

DEFAULT_GENERATED_AT = "2026-06-03T00:00:00Z"
DEFAULT_SIMULATOR_VERSION = "0.1"
DEFAULT_ADAPTER_VERSION = "0.1"


def write_simlite_bundle(
    outdir: str | Path,
    input_id: str,
    sample_count: int = 1,
    seed: int = 7,
    foundation: SyntheticInputFoundation | None = None,
) -> Path:
    bundle_dir = Path(outdir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    synthetic_foundation = foundation or load_synthetic_input_foundation()
    simulation_input = _simulation_input_by_id(synthetic_foundation, input_id)
    taxonomy_ref = simulation_input.taxonomy_ref

    manifest = {
        "bundle_id": f"simlite-{input_id}-{seed}-{sample_count}",
        "simulation_run_id": f"run-{input_id}-{seed}-{sample_count}",
        "input_id": simulation_input.input_id,
        "taxonomy_ref": taxonomy_ref,
        "simulator": "simlite",
        "simulator_version": DEFAULT_SIMULATOR_VERSION,
        "adapter_version": DEFAULT_ADAPTER_VERSION,
        "seed": seed,
        "sample_count": sample_count,
        "generated_at": DEFAULT_GENERATED_AT,
        "created_at": DEFAULT_GENERATED_AT,
        "source_type": "simulation",
        "schema_version": SIMULATION_BUNDLE_SCHEMA_VERSION,
        "assumption_summary": [
            "synthetic simulation bundle for gate and import tests",
            "placeholder process values only",
        ],
        "requires_real_validation_later": True,
        "missing_signal_notes": [],
        "generation_boundary": [
            *list(simulation_input.generation_boundary),
            "not WPS/PQR",
            "not real welding quality validation",
        ],
        "artifact_refs": {
            "trajectory": "trajectory.csv",
            "process_signals": "process_signals.csv",
            "evidence_bindings": "evidence_bindings.json",
            "quality_placeholders": "quality_placeholders.json",
        },
    }

    trajectory_rows, process_rows = _build_sample_rows(sample_count, seed)
    _write_json(bundle_dir / "manifest.json", manifest)
    _write_csv(
        bundle_dir / "trajectory.csv",
        ["sample_id", "t", "x", "y", "z", "rx", "ry", "rz", "current", "voltage", "force"],
        trajectory_rows,
    )
    _write_csv(
        bundle_dir / "process_signals.csv",
        ["sample_id", "t", "current", "voltage", "wire_feed", "travel_speed"],
        process_rows,
    )
    _write_json(
        bundle_dir / "evidence_bindings.json",
        [binding.to_dict() for binding in simulation_input.evidence_bindings],
    )
    _write_json(
        bundle_dir / "quality_placeholders.json",
        {
            "quality_label": "simulation_score_placeholder",
            "requires_real_validation_later": True,
        },
    )
    return bundle_dir


def _simulation_input_by_id(
    foundation: SyntheticInputFoundation,
    input_id: str,
):
    for simulation_input in foundation.simulation_inputs:
        if simulation_input.input_id == input_id:
            return simulation_input
    raise KeyError(input_id)


def _build_sample_rows(
    sample_count: int,
    seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    trajectory_rows: list[dict[str, Any]] = []
    process_rows: list[dict[str, Any]] = []

    for sample_index in range(sample_count):
        sample_id = f"sample-{sample_index + 1:03d}"
        seed_offset = seed * 0.01 + sample_index * 0.25
        for step in range(5):
            t = round(sample_index * 10.0 + step * 0.25, 3)
            x = round(seed_offset + sample_index * 12.0 + step * 2.5, 3)
            y = round(1.5 + sample_index * 0.4 + step * 0.05, 3)
            z = round(2.5 + sample_index * 0.2 + step * 0.03, 3)
            rx = round(0.1 + sample_index * 0.01 + step * 0.005, 3)
            ry = round(0.2 + sample_index * 0.01 + step * 0.005, 3)
            rz = round(0.3 + sample_index * 0.01 + step * 0.005, 3)
            current = round(180.0 + sample_index * 1.5 + step * 0.75 + seed_offset, 3)
            voltage = round(24.0 + sample_index * 0.2 + step * 0.05, 3)
            wire_feed = round(6.0 + sample_index * 0.1 + step * 0.03, 3)
            travel_speed = round(5.0 + sample_index * 0.12 + step * 0.02, 3)
            force = round(55.0 + sample_index * 0.5 + step * 0.2, 3)

            trajectory_rows.append(
                {
                    "sample_id": sample_id,
                    "t": t,
                    "x": x,
                    "y": y,
                    "z": z,
                    "rx": rx,
                    "ry": ry,
                    "rz": rz,
                    "current": current,
                    "voltage": voltage,
                    "force": force,
                }
            )
            process_rows.append(
                {
                    "sample_id": sample_id,
                    "t": t,
                    "current": current,
                    "voltage": voltage,
                    "wire_feed": wire_feed,
                    "travel_speed": travel_speed,
                }
            )

    return trajectory_rows, process_rows


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_csv(path: Path, header: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)
