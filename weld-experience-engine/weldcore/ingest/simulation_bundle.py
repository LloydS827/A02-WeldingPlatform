from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..knowledge.synthetic_input import FORBIDDEN_POOL_TERMS, SyntheticInputFoundation
from ..knowledge.synthetic_manifest import load_synthetic_input_foundation
from ..model import SIMULATION_BUNDLE_SCHEMA_VERSION


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
    else:
        if taxonomy_ref != simulation_input.taxonomy_ref:
            issues.append(
                f"manifest.json: taxonomy_ref mismatch for input_id {input_id}"
            )

    taxonomy_entry = taxonomy_by_ref.get(taxonomy_ref)
    if taxonomy_entry is None:
        issues.append(f"manifest.json: taxonomy_ref {taxonomy_ref} not found")
    elif not taxonomy_entry.ready_for_plan():
        issues.append(
            f"manifest.json: taxonomy_ref {taxonomy_ref} is not ready_for_synthetic_v2_plan"
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
