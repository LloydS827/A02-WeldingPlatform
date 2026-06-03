from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from collections import defaultdict
from pathlib import Path
from typing import Any

from ..knowledge.synthetic_input import FORBIDDEN_POOL_TERMS, SyntheticInputFoundation
from ..knowledge.synthetic_manifest import load_synthetic_input_foundation
from ..model import (
    SIMULATION_BUNDLE_SCHEMA_VERSION,
    SYNTHETIC_DATASET_SCHEMA_VERSION,
    ProcessSignal,
    QualityObservation,
    SimulationRunRecord,
    SimulationRunStatus,
    SimulatorName,
    SkillDataset,
    SkillSample,
    SourceType,
    WeldCondition,
)
from ..model.trajectory import Trajectory, TrajectorySample


TRAJECTORY_REQUIRED_COLUMNS = (
    "sample_id",
    "t",
    "x",
    "y",
    "z",
    "rx",
    "ry",
    "rz",
    "current",
    "voltage",
    "force",
)
PROCESS_REQUIRED_COLUMNS = (
    "sample_id",
    "t",
    "current",
    "voltage",
    "wire_feed",
    "travel_speed",
)
@dataclass(frozen=True)
class SimulationBundleGateResult:
    passed: bool
    issues: list[str]


@dataclass(frozen=True)
class SimulationBundleImportResult:
    gate: SimulationBundleGateResult
    run_record: SimulationRunRecord
    dataset: SkillDataset


def validate_simulation_bundle(
    bundle_dir: str | Path,
    foundation: SyntheticInputFoundation | None = None,
) -> SimulationBundleGateResult:
    bundle_path = Path(bundle_dir)
    issues: list[str] = []
    synthetic_foundation = foundation or load_synthetic_input_foundation()
    simulation_inputs_by_id = {
        simulation_input.input_id: simulation_input
        for simulation_input in synthetic_foundation.simulation_inputs
    }
    taxonomy_by_ref = {
        entry.family_id: entry for entry in synthetic_foundation.task_taxonomy
    }

    manifest_path = bundle_path / "manifest.json"
    trajectory_path = bundle_path / "trajectory.csv"
    process_path = bundle_path / "process_signals.csv"
    evidence_path = bundle_path / "evidence_bindings.json"
    quality_path = bundle_path / "quality_placeholders.json"

    manifest = _load_json(manifest_path, issues, "manifest.json")
    trajectory_rows = _load_csv_rows(
        trajectory_path, issues, "trajectory.csv", TRAJECTORY_REQUIRED_COLUMNS
    )
    process_rows = _load_csv_rows(
        process_path, issues, "process_signals.csv", PROCESS_REQUIRED_COLUMNS
    )
    _load_json(evidence_path, issues, "evidence_bindings.json")
    quality_placeholders = _load_json(
        quality_path, issues, "quality_placeholders.json"
    )

    _scan_bundle_for_forbidden_terms(bundle_path, issues)

    if manifest is not None:
        _validate_manifest(
            manifest,
            trajectory_rows,
            issues,
            simulation_inputs_by_id,
            taxonomy_by_ref,
        )
        _validate_process_signal_notes(manifest, process_rows, issues)

    if quality_placeholders is not None:
        _validate_quality_placeholders(quality_placeholders, issues)

    return SimulationBundleGateResult(passed=not issues, issues=issues)


def import_simulation_bundle(
    bundle_dir: str | Path,
    foundation: SyntheticInputFoundation | None = None,
) -> SimulationBundleImportResult:
    bundle_path = Path(bundle_dir)
    gate = validate_simulation_bundle(bundle_path, foundation=foundation)
    if not gate.passed:
        raise ValueError(
            "simulation bundle gate failed: " + "; ".join(gate.issues)
        )

    synthetic_foundation = foundation or load_synthetic_input_foundation()
    manifest = _read_json_file(bundle_path / "manifest.json")
    trajectory_rows = _read_csv_rows(bundle_path / "trajectory.csv")
    process_rows = _read_csv_rows(bundle_path / "process_signals.csv")
    evidence_bindings = _read_json_file(bundle_path / "evidence_bindings.json")
    quality_placeholders = _read_json_file(bundle_path / "quality_placeholders.json")

    simulation_input = _simulation_input_by_id(
        synthetic_foundation, manifest["input_id"]
    )
    taxonomy_entry = _taxonomy_entry_by_ref(
        synthetic_foundation, manifest["taxonomy_ref"]
    )

    bundle_id = str(manifest.get("bundle_id") or bundle_path.name)
    simulation_run_id = str(manifest.get("simulation_run_id", ""))
    simulator = _simulation_name_from_manifest(manifest.get("simulator"))
    created_at = str(manifest.get("created_at") or manifest.get("generated_at") or "")
    completed_at = str(
        manifest.get("completed_at")
        or manifest.get("generated_at")
        or manifest.get("created_at")
        or ""
    )
    boundary_notes = _normalize_string_list(
        manifest.get("generation_boundary") or manifest.get("boundary_notes") or []
    )
    dataset = _build_skill_dataset(
        bundle_id=bundle_id,
        manifest=manifest,
        simulation_input=simulation_input,
        taxonomy_entry=taxonomy_entry,
        trajectory_rows=trajectory_rows,
        process_rows=process_rows,
        evidence_bindings=evidence_bindings,
        quality_placeholders=quality_placeholders,
    )
    run_record = SimulationRunRecord(
        simulation_run_id=simulation_run_id,
        input_id=str(manifest.get("input_id", "")),
        simulator=simulator,
        status=SimulationRunStatus.IMPORTED,
        created_at=created_at,
        completed_at=completed_at,
        output_bundle_uris=[str(bundle_path)],
        warnings=[],
        errors=[],
        boundary_notes=boundary_notes,
    )
    return SimulationBundleImportResult(gate=gate, run_record=run_record, dataset=dataset)


def _load_json(path: Path, issues: list[str], label: str) -> Any | None:
    if not path.exists():
        issues.append(f"missing required file: {label}")
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except UnicodeDecodeError:
        issues.append(f"{label}: could not decode as utf-8")
    except json.JSONDecodeError as exc:
        issues.append(f"{label}: invalid json ({exc.msg})")
    except OSError as exc:
        issues.append(f"{label}: could not read ({exc.strerror or exc.__class__.__name__})")
    return None


def _load_csv_rows(
    path: Path,
    issues: list[str],
    label: str,
    required_columns: tuple[str, ...],
) -> list[dict[str, str]] | None:
    if not path.exists():
        issues.append(f"missing required file: {label}")
        return None
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames or []
            missing = [column for column in required_columns if column not in fieldnames]
            if missing:
                issues.append(f"{label}: missing required columns {', '.join(missing)}")
            return list(reader)
    except UnicodeDecodeError:
        issues.append(f"{label}: could not decode as utf-8")
    except csv.Error as exc:
        issues.append(f"{label}: invalid csv ({exc})")
    except OSError as exc:
        issues.append(f"{label}: could not read ({exc.strerror or exc.__class__.__name__})")
    return None


def _validate_manifest(
    manifest: Any,
    trajectory_rows: list[dict[str, str]] | None,
    issues: list[str],
    simulation_inputs_by_id: dict[str, Any],
    taxonomy_by_ref: dict[str, Any],
) -> None:
    if not isinstance(manifest, dict):
        issues.append("manifest.json: expected json object")
        return

    if manifest.get("schema_version") != SIMULATION_BUNDLE_SCHEMA_VERSION:
        issues.append("manifest.json: schema_version mismatch")

    if manifest.get("source_type") != "simulation":
        issues.append("manifest.json: source_type must be simulation")

    input_id = manifest.get("input_id")
    taxonomy_ref = manifest.get("taxonomy_ref")
    simulation_input = simulation_inputs_by_id.get(input_id)
    if simulation_input is None:
        issues.append(f"manifest.json: unknown input_id {input_id}")
        _validate_taxonomy_ref(
            issues,
            taxonomy_by_ref,
            taxonomy_ref,
            "manifest.json",
        )
    else:
        if taxonomy_ref != simulation_input.taxonomy_ref:
            issues.append(
                f"manifest.json: taxonomy_ref mismatch for input_id {input_id}"
            )
        _validate_taxonomy_ref(
            issues,
            taxonomy_by_ref,
            simulation_input.taxonomy_ref,
            f"input_id {input_id}",
        )
        if taxonomy_ref != simulation_input.taxonomy_ref:
            _validate_taxonomy_ref(
                issues,
                taxonomy_by_ref,
                taxonomy_ref,
                "manifest.json",
            )

    if trajectory_rows is not None:
        sample_ids: set[str] = set()
        for row in trajectory_rows:
            sample_id = row.get("sample_id", "")
            if _is_blank(sample_id):
                issues.append("trajectory.csv: blank sample_id")
                continue
            sample_ids.add(str(sample_id).strip())
        sample_count = manifest.get("sample_count")
        if sample_count != len(sample_ids):
            issues.append("manifest.json: sample_count mismatch with trajectory.csv")


def _validate_taxonomy_ref(
    issues: list[str],
    taxonomy_by_ref: dict[str, Any],
    taxonomy_ref: Any,
    scope: str,
) -> None:
    taxonomy_entry = taxonomy_by_ref.get(taxonomy_ref)
    if taxonomy_entry is None:
        issues.append(f"{scope}: taxonomy_ref {taxonomy_ref} not found")
    elif not taxonomy_entry.ready_for_plan():
        issues.append(
            f"{scope}: taxonomy_ref {taxonomy_ref} is not ready_for_synthetic_v2_plan"
        )


def _validate_process_signal_notes(
    manifest: dict[str, Any],
    process_rows: list[dict[str, str]] | None,
    issues: list[str],
) -> None:
    if process_rows is None:
        return

    missing_note_required = False
    for row in process_rows:
        for field_name in ("current", "voltage", "wire_feed", "travel_speed"):
            value = row.get(field_name, "")
            if _is_blank(value):
                missing_note_required = True
                break
        if missing_note_required:
            break

    if missing_note_required and _is_blank(manifest.get("missing_signal_notes")):
        issues.append(
            "process_signals.csv: blank signal values require missing_signal_notes"
        )


def _validate_quality_placeholders(
    quality_placeholders: Any,
    issues: list[str],
) -> None:
    if not isinstance(quality_placeholders, dict):
        issues.append("quality_placeholders.json: expected json object")
        return

    requires_real_validation_later = quality_placeholders.get(
        "requires_real_validation_later"
    )
    quality_label = quality_placeholders.get("quality_label")
    if not (
        requires_real_validation_later is True
        or quality_label == "simulation_score_placeholder"
    ):
        issues.append(
            "quality_placeholders.json: quality placeholders require boundary"
        )


def _scan_bundle_for_forbidden_terms(bundle_path: Path, issues: list[str]) -> None:
    for path in bundle_path.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError:
            continue
        lowered = text.lower()
        matches = [term for term in FORBIDDEN_POOL_TERMS if term in lowered]
        if matches:
            issues.append(
                f"{path.relative_to(bundle_path)}: forbidden term(s) detected: {', '.join(matches)}"
            )


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    return False


def _read_json_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _simulation_input_by_id(
    foundation: SyntheticInputFoundation,
    input_id: str,
):
    for simulation_input in foundation.simulation_inputs:
        if simulation_input.input_id == input_id:
            return simulation_input
    raise KeyError(input_id)


def _taxonomy_entry_by_ref(foundation: SyntheticInputFoundation, taxonomy_ref: str):
    for taxonomy_entry in foundation.task_taxonomy:
        if taxonomy_entry.family_id == taxonomy_ref:
            return taxonomy_entry
    raise KeyError(taxonomy_ref)


def _simulation_name_from_manifest(value: Any) -> SimulatorName:
    if value is None:
        return SimulatorName.OTHER
    try:
        return SimulatorName(str(value))
    except ValueError:
        return SimulatorName.OTHER


def _normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_optional_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _trajectory_from_rows(rows: list[dict[str, str]]) -> Trajectory:
    samples = [
        TrajectorySample(
            t=_coerce_float(row.get("t")),
            x=_coerce_float(row.get("x")),
            y=_coerce_float(row.get("y")),
            z=_coerce_float(row.get("z")),
            rx=_coerce_float(row.get("rx")),
            ry=_coerce_float(row.get("ry")),
            rz=_coerce_float(row.get("rz")),
            current=_coerce_optional_float(row.get("current")),
            voltage=_coerce_optional_float(row.get("voltage")),
            force=_coerce_optional_float(row.get("force")),
        )
        for row in sorted(rows, key=lambda item: _coerce_float(item.get("t")))
    ]
    return Trajectory(samples=samples)


def _process_signals_from_rows(rows: list[dict[str, str]]) -> list[ProcessSignal]:
    return [
        ProcessSignal(
            t=_coerce_float(row.get("t")),
            current=_coerce_optional_float(row.get("current")),
            voltage=_coerce_optional_float(row.get("voltage")),
            wire_feed=_coerce_optional_float(row.get("wire_feed")),
            travel_speed=_coerce_optional_float(row.get("travel_speed")),
        )
        for row in sorted(rows, key=lambda item: _coerce_float(item.get("t")))
    ]


def _build_skill_dataset(
    *,
    bundle_id: str,
    manifest: dict[str, Any],
    simulation_input: Any,
    taxonomy_entry: Any,
    trajectory_rows: list[dict[str, str]],
    process_rows: list[dict[str, str]],
    evidence_bindings: Any,
    quality_placeholders: Any,
) -> SkillDataset:
    trajectory_rows_by_sample_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    process_rows_by_sample_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    sample_id_order: list[str] = []

    for row in trajectory_rows:
        sample_id = str(row.get("sample_id", "")).strip()
        if sample_id not in trajectory_rows_by_sample_id:
            sample_id_order.append(sample_id)
        trajectory_rows_by_sample_id[sample_id].append(row)

    for row in process_rows:
        sample_id = str(row.get("sample_id", "")).strip()
        process_rows_by_sample_id[sample_id].append(row)
        if sample_id not in trajectory_rows_by_sample_id and sample_id not in sample_id_order:
            sample_id_order.append(sample_id)

    samples = [
        _build_skill_sample(
            sample_id=sample_id,
            bundle_id=bundle_id,
            manifest=manifest,
            simulation_input=simulation_input,
            taxonomy_entry=taxonomy_entry,
            trajectory_rows=trajectory_rows_by_sample_id.get(sample_id, []),
            process_rows=process_rows_by_sample_id.get(sample_id, []),
            evidence_bindings=evidence_bindings,
            quality_placeholders=quality_placeholders,
        )
        for sample_id in sample_id_order
        if sample_id
    ]
    return SkillDataset(
        dataset_id=f"{bundle_id}-dataset",
        source_type=SourceType.SIMULATION,
        task=str(manifest.get("taxonomy_ref", "")),
        samples=samples,
        schema_version=SYNTHETIC_DATASET_SCHEMA_VERSION,
        license_and_rights="synthetic simulation data; requires real validation later",
    )


def _build_skill_sample(
    *,
    sample_id: str,
    bundle_id: str,
    manifest: dict[str, Any],
    simulation_input: Any,
    taxonomy_entry: Any,
    trajectory_rows: list[dict[str, str]],
    process_rows: list[dict[str, str]],
    evidence_bindings: Any,
    quality_placeholders: Any,
) -> SkillSample:
    trajectory = _trajectory_from_rows(trajectory_rows)
    process_signals = _process_signals_from_rows(process_rows)
    plate_thickness_mm = _coerce_float(
        simulation_input.geometry_spec.get("plate_thickness_mm"), default=0.0
    )
    groove_width_mm = _coerce_float(
        simulation_input.geometry_spec.get("groove_width_mm"), default=0.0
    )
    length_mm = _trajectory_length_mm(trajectory)
    material = simulation_input.procedure_fields.get("base_material", "unknown")
    if not isinstance(material, str) or not material.strip():
        material = "unknown"
    requires_real_validation_later = _requires_real_validation_later(
        manifest, quality_placeholders
    )
    return SkillSample(
        sample_id=sample_id,
        weld_condition=WeldCondition(
            weld_type=str(manifest.get("taxonomy_ref", "")),
            joint_type=str(taxonomy_entry.joint_type),
            plate_thickness_mm=plate_thickness_mm,
            groove_width_mm=groove_width_mm,
            length_mm=length_mm,
            position=str(getattr(taxonomy_entry, "weld_position", "")),
            material=material,
            manufacturing_stage=str(taxonomy_entry.manufacturing_stage),
            weld_object=str(taxonomy_entry.weld_object),
            groove_geometry=str(taxonomy_entry.groove_geometry),
            layer_pass=str(taxonomy_entry.layer_pass),
            access_context=str(taxonomy_entry.access_context),
            motion_structure=str(taxonomy_entry.motion_structure),
        ),
        trajectory=trajectory,
        process_signals=process_signals,
        quality_observation=QualityObservation(
            status="requires_real_validation_later",
            notes="synthetic quality placeholder only",
        ),
        metadata={
            "input_id": str(manifest.get("input_id", "")),
            "taxonomy_ref": str(manifest.get("taxonomy_ref", "")),
            "simulation_run_id": str(manifest.get("simulation_run_id", "")),
            "bundle_id": bundle_id,
            "assumption_summary": _normalize_string_list(
                manifest.get("assumption_summary") or []
            ),
            "artifact_refs": dict(manifest.get("artifact_refs") or {})
            if isinstance(manifest.get("artifact_refs"), dict)
            else {},
            "evidence_bindings": evidence_bindings,
            "requires_real_validation_later": requires_real_validation_later,
            "generation_boundary": _normalize_string_list(
                manifest.get("generation_boundary")
                or manifest.get("boundary_notes")
                or []
            ),
            "boundary_notes": _normalize_string_list(
                manifest.get("generation_boundary")
                or manifest.get("boundary_notes")
                or []
            ),
            "validation_status": "requires_real_validation_later",
        },
    )


def _trajectory_length_mm(trajectory: Trajectory) -> float:
    if len(trajectory.samples) == 0:
        return 0.0
    xs = [sample.x for sample in trajectory.samples]
    return max(xs) - min(xs)


def _requires_real_validation_later(
    manifest: dict[str, Any],
    quality_placeholders: Any,
) -> bool:
    if (
        isinstance(quality_placeholders, dict)
        and "requires_real_validation_later" in quality_placeholders
    ):
        return bool(quality_placeholders["requires_real_validation_later"])
    if isinstance(manifest.get("requires_real_validation_later"), bool):
        return bool(manifest["requires_real_validation_later"])
    return True
