from __future__ import annotations

import json
from pathlib import Path

import pytest

from weldcore.ingest import import_simulation_bundle
from weldcore.knowledge.synthetic_manifest import load_synthetic_input_foundation
from weldcore.model import SimulationRunStatus, SimulatorName


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_csv(path: Path, header: list[str], rows: list[dict[str, object]]) -> None:
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def _simulation_input_and_taxonomy():
    foundation = load_synthetic_input_foundation()
    simulation_input = next(
        item for item in foundation.simulation_inputs if item.input_id == "input-panel-butt-001"
    )
    taxonomy_entry = next(
        item for item in foundation.task_taxonomy if item.family_id == "panel-butt"
    )
    return simulation_input, taxonomy_entry


def _write_bundle(
    bundle_dir: Path,
    *,
    manifest_overrides: dict[str, object] | None = None,
    trajectory_rows: list[dict[str, object]] | None = None,
    process_rows: list[dict[str, object]] | None = None,
    quality_placeholders: object | None = None,
) -> None:
    simulation_input, taxonomy_entry = _simulation_input_and_taxonomy()
    manifest = {
        "schema_version": "synthetic-v2-bundle-v0.1",
        "source_type": "simulation",
        "bundle_id": "bundle-panel-butt-001",
        "simulation_run_id": "run-panel-butt-001",
        "input_id": simulation_input.input_id,
        "taxonomy_ref": simulation_input.taxonomy_ref,
        "simulator": "simlite",
        "simulator_version": "0.1",
        "adapter_version": "0.1",
        "seed": 7,
        "created_at": "2026-06-03T00:00:00Z",
        "generated_at": "2026-06-03T00:00:00Z",
        "sample_count": 1,
        "artifact_refs": {
            "trajectory": "trajectory.csv",
            "process_signals": "process_signals.csv",
            "evidence_bindings": "evidence_bindings.json",
            "quality_placeholders": "quality_placeholders.json",
        },
        "assumption_summary": ["not WPS/PQR; synthetic-only"],
        "requires_real_validation_later": True,
        "missing_signal_notes": [],
        "generation_boundary": ["not WPS/PQR", "synthetic-only"],
    }
    if manifest_overrides:
        manifest.update(manifest_overrides)

    _write_json(bundle_dir / "manifest.json", manifest)
    _write_csv(
        bundle_dir / "trajectory.csv",
        ["sample_id", "t", "x", "y", "z", "rx", "ry", "rz", "current", "voltage", "force"],
        trajectory_rows
        or [
            {
                "sample_id": "sample-001",
                "t": 0.0,
                "x": 1.0,
                "y": 2.0,
                "z": 3.0,
                "rx": 0.1,
                "ry": 0.2,
                "rz": 0.3,
                "current": 120.0,
                "voltage": 24.0,
                "force": 55.0,
            }
        ],
    )
    _write_csv(
        bundle_dir / "process_signals.csv",
        ["sample_id", "t", "current", "voltage", "wire_feed", "travel_speed"],
        process_rows
        or [
            {
                "sample_id": "sample-001",
                "t": 0.0,
                "current": 120.0,
                "voltage": 24.0,
                "wire_feed": 9.5,
                "travel_speed": 3.1,
            }
        ],
    )
    _write_json(
        bundle_dir / "evidence_bindings.json",
        {
            "input_id": simulation_input.input_id,
            "taxonomy_ref": taxonomy_entry.family_id,
            "bindings": [{"field_path": "geometry_spec.plate_thickness_mm"}],
        },
    )
    _write_json(
        bundle_dir / "quality_placeholders.json",
        quality_placeholders
        if quality_placeholders is not None
        else {
            "quality_label": "simulation_score_placeholder",
            "requires_real_validation_later": False,
        },
    )


def test_valid_bundle_imports_to_skill_dataset(tmp_path: Path) -> None:
    _write_bundle(
        tmp_path,
        manifest_overrides={
            "sample_count": 1,
        },
    )

    result = import_simulation_bundle(tmp_path)

    assert result.gate.passed is True
    assert result.run_record.simulation_run_id == "run-panel-butt-001"
    assert result.run_record.input_id == "input-panel-butt-001"
    assert result.run_record.simulator == SimulatorName.SIMLITE
    assert result.run_record.simulator_version == "0.1"
    assert result.run_record.adapter_version == "0.1"
    assert result.run_record.seed == 7
    assert result.run_record.sample_count == 1
    assert result.run_record.status == SimulationRunStatus.IMPORTED
    assert result.run_record.created_at == "2026-06-03T00:00:00Z"
    assert result.run_record.completed_at == "2026-06-03T00:00:00Z"
    assert result.run_record.output_bundle_uris == [str(tmp_path)]
    assert "not WPS/PQR" in " ".join(result.run_record.boundary_notes)

    dataset = result.dataset
    data = dataset.to_dict()

    assert dataset.source_type.value == "simulation"
    assert dataset.schema_version == "synthetic-v2-dataset-v0.1"
    assert dataset.task == "panel-butt"
    assert len(dataset.samples) == 1
    assert data["samples"][0]["sample_id"] == "sample-001"
    assert data["samples"][0]["trajectory"]["samples"][0]["x"] == 1.0
    assert data["samples"][0]["trajectory"]["samples"][0]["rz"] == 0.3
    assert data["samples"][0]["process_signals"][0]["wire_feed"] == 9.5
    assert data["samples"][0]["weld_condition"]["joint_type"] == "butt"
    assert data["samples"][0]["weld_condition"]["manufacturing_stage"] == (
        _simulation_input_and_taxonomy()[1].manufacturing_stage
    )
    assert data["samples"][0]["metadata"]["input_id"] == "input-panel-butt-001"
    assert data["samples"][0]["metadata"]["taxonomy_ref"] == "panel-butt"
    assert data["samples"][0]["metadata"]["simulation_run_id"] == "run-panel-butt-001"
    assert data["samples"][0]["metadata"]["bundle_id"] == "bundle-panel-butt-001"
    assert data["samples"][0]["metadata"]["artifact_refs"]["trajectory"] == "trajectory.csv"
    assert data["samples"][0]["metadata"]["evidence_bindings"]["taxonomy_ref"] == "panel-butt"
    assert data["samples"][0]["metadata"]["requires_real_validation_later"] is True
    assert data["samples"][0]["metadata"]["validation_status"] == "requires_real_validation_later"
    assert data["samples"][0]["metadata"]["quality_placeholders"]["quality_label"] == "simulation_score_placeholder"
    assert data["samples"][0]["metadata"]["quality_placeholders"]["requires_real_validation_later"] is False
    assert "not WPS/PQR" in json.dumps(data, ensure_ascii=False)


def test_invalid_bundle_raises_value_error(tmp_path: Path) -> None:
    _write_bundle(
        tmp_path,
        manifest_overrides={
            "input_id": "unknown-input",
            "taxonomy_ref": "missing-taxonomy",
        },
    )

    with pytest.raises(ValueError) as exc_info:
        import_simulation_bundle(tmp_path)

    message = str(exc_info.value)
    assert "unknown input_id" in message


def test_process_only_sample_id_is_rejected(tmp_path: Path) -> None:
    _write_bundle(
        tmp_path,
        manifest_overrides={"sample_count": 1},
        process_rows=[
            {
                "sample_id": "sample-999",
                "t": 0.0,
                "current": 120.0,
                "voltage": 24.0,
                "wire_feed": 9.5,
                "travel_speed": 3.1,
            }
        ],
    )

    with pytest.raises(ValueError) as exc_info:
        import_simulation_bundle(tmp_path)

    message = str(exc_info.value)
    assert "sample_id" in message
    assert "process_signals.csv" in message


@pytest.mark.parametrize(
    ("field_name", "field_key", "bad_value"),
    [
        ("trajectory.csv: t", "t", "bad"),
        ("trajectory.csv: x", "x", "bad"),
    ],
)
def test_invalid_required_trajectory_float_raises(
    tmp_path: Path,
    field_name: str,
    field_key: str,
    bad_value: str,
) -> None:
    trajectory_row = {
        "sample_id": "sample-001",
        "t": 0.0,
        "x": 1.0,
        "y": 2.0,
        "z": 3.0,
        "rx": 0.1,
        "ry": 0.2,
        "rz": 0.3,
        "current": 120.0,
        "voltage": 24.0,
        "force": 55.0,
    }
    trajectory_row[field_key] = bad_value
    _write_bundle(
        tmp_path,
        trajectory_rows=[trajectory_row],
        process_rows=[
            {
                "sample_id": "sample-001",
                "t": 0.0,
                "current": 120.0,
                "voltage": 24.0,
                "wire_feed": 9.5,
                "travel_speed": 3.1,
            }
        ],
    )

    with pytest.raises(ValueError) as exc_info:
        import_simulation_bundle(tmp_path)

    assert field_name in str(exc_info.value)


def test_multi_sample_bundle_imports_one_sample_per_distinct_sample_id(
    tmp_path: Path,
) -> None:
    _write_bundle(
        tmp_path,
        manifest_overrides={"sample_count": 2},
        trajectory_rows=[
            {
                "sample_id": "sample-001",
                "t": 0.0,
                "x": 1.0,
                "y": 2.0,
                "z": 3.0,
                "rx": 0.1,
                "ry": 0.2,
                "rz": 0.3,
                "current": 120.0,
                "voltage": 24.0,
                "force": 55.0,
            },
            {
                "sample_id": "sample-001",
                "t": 0.5,
                "x": 1.5,
                "y": 2.5,
                "z": 3.5,
                "rx": 0.15,
                "ry": 0.25,
                "rz": 0.35,
                "current": 121.0,
                "voltage": 24.2,
                "force": 56.0,
            },
            {
                "sample_id": "sample-002",
                "t": 0.0,
                "x": 4.0,
                "y": 5.0,
                "z": 6.0,
                "rx": 0.4,
                "ry": 0.5,
                "rz": 0.6,
                "current": 122.0,
                "voltage": 24.4,
                "force": 57.0,
            },
        ],
        process_rows=[
            {
                "sample_id": "sample-001",
                "t": 0.0,
                "current": 120.0,
                "voltage": 24.0,
                "wire_feed": 9.5,
                "travel_speed": 3.1,
            },
            {
                "sample_id": "sample-001",
                "t": 0.5,
                "current": 121.0,
                "voltage": 24.2,
                "wire_feed": 9.6,
                "travel_speed": 3.2,
            },
            {
                "sample_id": "sample-002",
                "t": 0.0,
                "current": 122.0,
                "voltage": 24.4,
                "wire_feed": 9.7,
                "travel_speed": 3.3,
            },
        ],
    )

    result = import_simulation_bundle(tmp_path)

    assert len(result.dataset.samples) == 2
    assert {sample.sample_id for sample in result.dataset.samples} == {
        "sample-001",
        "sample-002",
    }
    first_sample = next(sample for sample in result.dataset.samples if sample.sample_id == "sample-001")
    assert len(first_sample.trajectory.samples) == 2
    assert first_sample.trajectory.samples[1].x == 1.5
    assert len(first_sample.process_signals) == 2
