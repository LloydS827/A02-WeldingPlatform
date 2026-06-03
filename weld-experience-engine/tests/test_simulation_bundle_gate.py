from __future__ import annotations

import csv
import json
from pathlib import Path

from weldcore.ingest import SimulationBundleGateResult, validate_simulation_bundle
from weldcore.knowledge.synthetic_input import FORBIDDEN_POOL_TERMS, SimulationInputSpec
from weldcore.knowledge.synthetic_manifest import load_synthetic_input_foundation
from weldcore.model import SIMULATION_BUNDLE_SCHEMA_VERSION

DEFAULT_INPUT_ID = "input-panel-butt-001"
DEFAULT_TAXONOMY_REF = "panel-butt"
NON_READY_TAXONOMY_REF = "double-bottom-inner-fillet"


def _load_input_spec(
    input_id: str = DEFAULT_INPUT_ID,
    taxonomy_ref: str = DEFAULT_TAXONOMY_REF,
):
    foundation = load_synthetic_input_foundation()
    simulation_input = next(
        item for item in foundation.simulation_inputs if item.input_id == input_id
    )
    taxonomy_entry = next(
        item for item in foundation.task_taxonomy if item.family_id == taxonomy_ref
    )
    return foundation, simulation_input, taxonomy_entry


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_csv(path: Path, header: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def _write_valid_bundle(
    bundle_dir: Path,
    *,
    manifest_overrides: dict[str, object] | None = None,
    trajectory_rows: list[dict[str, object]] | None = None,
    process_rows: list[dict[str, object]] | None = None,
    evidence_bindings: object | None = None,
    quality_placeholders: object | None = None,
    extra_text_files: dict[str, str] | None = None,
    extra_binary_files: dict[str, bytes] | None = None,
) -> tuple[str, str]:
    _, simulation_input, taxonomy_entry = _load_input_spec()
    manifest = {
        "bundle_id": "bundle-panel-butt-001",
        "simulation_run_id": "run-panel-butt-001",
        "schema_version": SIMULATION_BUNDLE_SCHEMA_VERSION,
        "source_type": "simulation",
        "input_id": simulation_input.input_id,
        "taxonomy_ref": simulation_input.taxonomy_ref,
        "simulator": "simlite",
        "simulator_version": "0.1",
        "created_at": "2026-06-03T00:00:00Z",
        "generated_at": "2026-06-03T00:00:00Z",
        "sample_count": 1,
        "artifact_refs": {
            "trajectory": "trajectory.csv",
            "process_signals": "process_signals.csv",
            "evidence_bindings": "evidence_bindings.json",
            "quality_placeholders": "quality_placeholders.json",
        },
        "assumption_summary": ["synthetic-only bundle for gate tests"],
        "missing_signal_notes": "one wire-feed value is not available in the source output",
    }
    if manifest_overrides:
        manifest.update(manifest_overrides)

    trajectory = trajectory_rows or [
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
    ]
    process = process_rows or [
        {
            "sample_id": "sample-001",
            "t": 0.0,
            "current": 120.0,
            "voltage": 24.0,
            "wire_feed": 9.5,
            "travel_speed": 3.1,
        }
    ]
    _write_json(bundle_dir / "manifest.json", manifest)
    _write_csv(
        bundle_dir / "trajectory.csv",
        ["sample_id", "t", "x", "y", "z", "rx", "ry", "rz", "current", "voltage", "force"],
        trajectory,
    )
    _write_csv(
        bundle_dir / "process_signals.csv",
        ["sample_id", "t", "current", "voltage", "wire_feed", "travel_speed"],
        process,
    )
    _write_json(
        bundle_dir / "evidence_bindings.json",
        evidence_bindings
        if evidence_bindings is not None
        else {
            "input_id": simulation_input.input_id,
            "taxonomy_ref": taxonomy_entry.family_id,
            "bindings": [],
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

    for relative_path, text in (extra_text_files or {}).items():
        target = bundle_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    for relative_path, payload in (extra_binary_files or {}).items():
        target = bundle_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)

    return simulation_input.input_id, taxonomy_entry.family_id


def test_valid_single_input_bundle_passes(tmp_path: Path) -> None:
    _write_valid_bundle(tmp_path)

    result = validate_simulation_bundle(tmp_path)

    assert isinstance(result, SimulationBundleGateResult)
    assert result.passed
    assert result.issues == []


def test_valid_single_input_multi_sample_bundle_passes(tmp_path: Path) -> None:
    _write_valid_bundle(
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
                "sample_id": "sample-002",
                "t": 0.2,
                "x": 1.2,
                "y": 2.2,
                "z": 3.2,
                "rx": 0.12,
                "ry": 0.22,
                "rz": 0.32,
                "current": 121.0,
                "voltage": 24.2,
                "force": 56.0,
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
                "sample_id": "sample-002",
                "t": 0.2,
                "current": 121.0,
                "voltage": 24.2,
                "wire_feed": 9.6,
                "travel_speed": 3.2,
            },
        ],
    )

    result = validate_simulation_bundle(tmp_path)

    assert result.passed
    assert result.issues == []


def test_missing_manifest_json_fails(tmp_path: Path) -> None:
    _write_valid_bundle(tmp_path)
    (tmp_path / "manifest.json").unlink()

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("manifest.json" in issue for issue in result.issues)


def test_wrong_schema_version_fails(tmp_path: Path) -> None:
    _write_valid_bundle(tmp_path, manifest_overrides={"schema_version": "wrong"})

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("schema_version" in issue for issue in result.issues)


def test_non_simulation_source_type_fails(tmp_path: Path) -> None:
    _write_valid_bundle(tmp_path, manifest_overrides={"source_type": "imported"})

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("source_type" in issue for issue in result.issues)


def test_missing_required_manifest_field_fails(tmp_path: Path) -> None:
    _write_valid_bundle(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.pop("simulation_run_id")
    _write_json(manifest_path, manifest)

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("simulation_run_id" in issue for issue in result.issues)


def test_missing_other_required_manifest_field_fails(tmp_path: Path) -> None:
    _write_valid_bundle(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.pop("simulator_version")
    _write_json(manifest_path, manifest)

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("simulator_version" in issue for issue in result.issues)


def test_unknown_input_id_fails(tmp_path: Path) -> None:
    _write_valid_bundle(
        tmp_path,
        manifest_overrides={
            "input_id": "missing-input",
            "sample_count": 2,
            "taxonomy_ref": "missing-taxonomy",
        },
    )

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("input_id" in issue and "unknown" in issue for issue in result.issues)
    assert any("sample_count" in issue for issue in result.issues)
    assert any("taxonomy_ref" in issue and "not found" in issue for issue in result.issues)


def test_taxonomy_mismatch_fails(tmp_path: Path) -> None:
    _write_valid_bundle(tmp_path, manifest_overrides={"taxonomy_ref": "wrong-taxonomy"})

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("taxonomy_ref" in issue and "mismatch" in issue for issue in result.issues)


def test_non_ready_taxonomy_fails(tmp_path: Path) -> None:
    foundation = load_synthetic_input_foundation()
    base_input = next(
        item for item in foundation.simulation_inputs if item.input_id == DEFAULT_INPUT_ID
    )
    non_ready_entry = next(
        entry for entry in foundation.task_taxonomy if entry.family_id == NON_READY_TAXONOMY_REF
    )
    custom_input = SimulationInputSpec(
        input_id=base_input.input_id,
        taxonomy_ref=non_ready_entry.family_id,
        procedure_fields=dict(base_input.procedure_fields),
        geometry_spec=dict(base_input.geometry_spec),
        motion_spec=dict(base_input.motion_spec),
        process_spec=dict(base_input.process_spec),
        quality_spec=dict(base_input.quality_spec),
        variant_policy=dict(base_input.variant_policy),
        evidence_bindings=list(base_input.evidence_bindings),
        generation_boundary=list(base_input.generation_boundary),
    )
    custom_foundation = load_synthetic_input_foundation()
    custom_foundation.task_taxonomy = list(foundation.task_taxonomy)
    custom_foundation.simulation_inputs = [custom_input]
    _write_valid_bundle(
        tmp_path,
        manifest_overrides={
            "taxonomy_ref": non_ready_entry.family_id,
        },
    )

    result = validate_simulation_bundle(tmp_path, foundation=custom_foundation)

    assert not result.passed
    assert any("ready_for_synthetic_v2_plan" in issue for issue in result.issues)


def test_input_taxonomy_non_ready_fails_even_when_manifest_points_to_ready_taxonomy(
    tmp_path: Path,
) -> None:
    foundation = load_synthetic_input_foundation()
    base_input = next(
        item for item in foundation.simulation_inputs if item.input_id == DEFAULT_INPUT_ID
    )
    non_ready_entry = next(
        entry for entry in foundation.task_taxonomy if entry.family_id == NON_READY_TAXONOMY_REF
    )
    ready_entry = next(
        entry for entry in foundation.task_taxonomy if entry.family_id == DEFAULT_TAXONOMY_REF
    )
    custom_input = SimulationInputSpec(
        input_id=base_input.input_id,
        taxonomy_ref=non_ready_entry.family_id,
        procedure_fields=dict(base_input.procedure_fields),
        geometry_spec=dict(base_input.geometry_spec),
        motion_spec=dict(base_input.motion_spec),
        process_spec=dict(base_input.process_spec),
        quality_spec=dict(base_input.quality_spec),
        variant_policy=dict(base_input.variant_policy),
        evidence_bindings=list(base_input.evidence_bindings),
        generation_boundary=list(base_input.generation_boundary),
    )
    custom_foundation = load_synthetic_input_foundation()
    custom_foundation.task_taxonomy = list(foundation.task_taxonomy)
    custom_foundation.simulation_inputs = [custom_input]
    _write_valid_bundle(
        tmp_path,
        manifest_overrides={
            "taxonomy_ref": ready_entry.family_id,
        },
    )

    result = validate_simulation_bundle(tmp_path, foundation=custom_foundation)

    assert not result.passed
    assert any("ready_for_synthetic_v2_plan" in issue for issue in result.issues)
    assert any("taxonomy_ref mismatch" in issue for issue in result.issues)


def test_missing_manifest_taxonomy_fails(tmp_path: Path) -> None:
    _write_valid_bundle(
        tmp_path,
        manifest_overrides={"taxonomy_ref": "missing-taxonomy"},
    )

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("taxonomy_ref" in issue and "not found" in issue for issue in result.issues)


def test_missing_trajectory_csv_fails(tmp_path: Path) -> None:
    _write_valid_bundle(tmp_path)
    (tmp_path / "trajectory.csv").unlink()

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("trajectory.csv" in issue for issue in result.issues)


def test_missing_process_signals_csv_fails(tmp_path: Path) -> None:
    _write_valid_bundle(tmp_path)
    (tmp_path / "process_signals.csv").unlink()

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("process_signals.csv" in issue for issue in result.issues)


def test_missing_required_canonical_columns_fail(tmp_path: Path) -> None:
    _write_valid_bundle(
        tmp_path,
    )
    (tmp_path / "trajectory.csv").write_text(
        "sample_id,t,y,z,rx,ry,rz,current,voltage,force\nsample-001,0.0,2.0,3.0,0.1,0.2,0.3,120.0,24.0,55.0\n",
        encoding="utf-8",
    )

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("trajectory.csv" in issue and "x" in issue for issue in result.issues)

    other = tmp_path / "other"
    other.mkdir()
    _write_valid_bundle(other)
    (other / "process_signals.csv").write_text(
        "sample_id,t,current,voltage,travel_speed\nsample-001,0.0,120.0,24.0,3.1\n",
        encoding="utf-8",
    )

    other_result = validate_simulation_bundle(other)

    assert not other_result.passed
    assert any("process_signals.csv" in issue and "wire_feed" in issue for issue in other_result.issues)


def test_blank_trajectory_sample_id_fails(tmp_path: Path) -> None:
    _write_valid_bundle(
        tmp_path,
        manifest_overrides={"sample_count": 1},
        trajectory_rows=[
            {
                "sample_id": "",
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
                "sample_id": "sample-002",
                "t": 0.2,
                "x": 1.2,
                "y": 2.2,
                "z": 3.2,
                "rx": 0.12,
                "ry": 0.22,
                "rz": 0.32,
                "current": 121.0,
                "voltage": 24.2,
                "force": 56.0,
            },
        ],
        process_rows=[
            {
                "sample_id": "sample-002",
                "t": 0.2,
                "current": 121.0,
                "voltage": 24.2,
                "wire_feed": 9.6,
                "travel_speed": 3.2,
            }
        ],
    )

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("sample_id" in issue for issue in result.issues)


def test_blank_process_signal_without_missing_signal_notes_fails(tmp_path: Path) -> None:
    _write_valid_bundle(
        tmp_path,
        manifest_overrides={"missing_signal_notes": ""},
        process_rows=[
            {
                "sample_id": "sample-001",
                "t": 0.0,
                "current": "",
                "voltage": 24.0,
                "wire_feed": 9.5,
                "travel_speed": 3.1,
            }
        ],
    )

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("missing_signal_notes" in issue for issue in result.issues)


def test_blank_process_signal_with_empty_missing_signal_notes_list_fails(
    tmp_path: Path,
) -> None:
    _write_valid_bundle(
        tmp_path,
        manifest_overrides={"missing_signal_notes": []},
        process_rows=[
            {
                "sample_id": "sample-001",
                "t": 0.0,
                "current": "",
                "voltage": 24.0,
                "wire_feed": 9.5,
                "travel_speed": 3.1,
            }
        ],
    )

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("missing_signal_notes" in issue for issue in result.issues)


def test_bad_trajectory_required_numeric_value_fails_at_gate(tmp_path: Path) -> None:
    _write_valid_bundle(
        tmp_path,
        trajectory_rows=[
            {
                "sample_id": "sample-001",
                "t": 0.0,
                "x": "not-a-number",
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

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("trajectory.csv" in issue and "x" in issue for issue in result.issues)


def test_bad_process_required_numeric_value_fails_at_gate(tmp_path: Path) -> None:
    _write_valid_bundle(
        tmp_path,
        process_rows=[
            {
                "sample_id": "sample-001",
                "t": "not-a-number",
                "current": 120.0,
                "voltage": 24.0,
                "wire_feed": 9.5,
                "travel_speed": 3.1,
            }
        ],
    )

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("process_signals.csv" in issue and "t" in issue for issue in result.issues)


def test_bad_optional_process_numeric_value_fails_at_gate(tmp_path: Path) -> None:
    _write_valid_bundle(
        tmp_path,
        process_rows=[
            {
                "sample_id": "sample-001",
                "t": 0.0,
                "current": "not-a-number",
                "voltage": 24.0,
                "wire_feed": 9.5,
                "travel_speed": 3.1,
            }
        ],
    )

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("process_signals.csv" in issue and "current" in issue for issue in result.issues)


def test_artifact_refs_missing_target_file_fails(tmp_path: Path) -> None:
    _write_valid_bundle(
        tmp_path,
        manifest_overrides={
            "artifact_refs": {
                "trajectory": "trajectory.csv",
                "process_signals": "process_signals.csv",
                "evidence_bindings": "missing-evidence.json",
                "quality_placeholders": "quality_placeholders.json",
            }
        },
    )

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("artifact_refs" in issue and "missing-evidence.json" in issue for issue in result.issues)


def test_missing_evidence_bindings_json_fails(tmp_path: Path) -> None:
    _write_valid_bundle(tmp_path)
    (tmp_path / "evidence_bindings.json").unlink()

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("evidence_bindings.json" in issue for issue in result.issues)


def test_missing_quality_placeholders_json_fails(tmp_path: Path) -> None:
    _write_valid_bundle(tmp_path)
    (tmp_path / "quality_placeholders.json").unlink()

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("quality_placeholders.json" in issue for issue in result.issues)


def test_quality_placeholders_without_boundary_reject(tmp_path: Path) -> None:
    _write_valid_bundle(
        tmp_path,
        quality_placeholders={
            "quality_label": "other_placeholder",
            "requires_real_validation_later": False,
        },
    )

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("quality placeholders require boundary" in issue for issue in result.issues)


def test_quality_placeholder_label_is_accepted_even_when_later_validation_is_false(
    tmp_path: Path,
) -> None:
    _write_valid_bundle(
        tmp_path,
        quality_placeholders={
            "quality_label": "simulation_score_placeholder",
            "requires_real_validation_later": False,
        },
    )

    result = validate_simulation_bundle(tmp_path)

    assert result.passed
    assert result.issues == []


def test_forbidden_terms_in_manifest_payload_fail(tmp_path: Path) -> None:
    forbidden_term = FORBIDDEN_POOL_TERMS[0]
    _write_valid_bundle(
        tmp_path,
        manifest_overrides={"generation_boundary": [f"contains {forbidden_term}"]},
    )

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("forbidden" in issue for issue in result.issues)


def test_forbidden_terms_in_quality_payload_fail(tmp_path: Path) -> None:
    forbidden_term = FORBIDDEN_POOL_TERMS[0]
    _write_valid_bundle(
        tmp_path,
        quality_placeholders={
            "quality_label": "other_placeholder",
            "requires_real_validation_later": False,
            "notes": f"contains {forbidden_term}",
        },
    )

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("forbidden" in issue for issue in result.issues)


def test_forbidden_terms_in_artifact_file_fail(tmp_path: Path) -> None:
    _write_valid_bundle(
        tmp_path,
        extra_text_files={"artifacts/scene.usd": f"# {FORBIDDEN_POOL_TERMS[1]} marker"},
    )

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("artifacts/scene.usd" in issue and "forbidden" in issue for issue in result.issues)


def test_non_utf8_artifact_is_skipped_without_crashing(tmp_path: Path) -> None:
    _write_valid_bundle(
        tmp_path,
        extra_binary_files={"artifacts/scene.usd": b"\xff\xfe\xfa\x00\x10\x80"},
    )

    result = validate_simulation_bundle(tmp_path)

    assert result.passed


def test_sample_count_mismatch_vs_distinct_trajectory_sample_ids_fails(tmp_path: Path) -> None:
    _write_valid_bundle(
        tmp_path,
        manifest_overrides={"sample_count": 1},
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
                "sample_id": "sample-002",
                "t": 0.1,
                "x": 1.1,
                "y": 2.1,
                "z": 3.1,
                "rx": 0.11,
                "ry": 0.21,
                "rz": 0.31,
                "current": 121.0,
                "voltage": 24.1,
                "force": 56.0,
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
            }
        ],
    )

    result = validate_simulation_bundle(tmp_path)

    assert not result.passed
    assert any("sample_count" in issue for issue in result.issues)
