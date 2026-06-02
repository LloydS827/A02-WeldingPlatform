from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .manifest import DEFAULT_FOUNDATION_ROOT, load_data_foundation
from .synthetic_input import (
    EvidenceBinding,
    SimulationInputSpec,
    SyntheticEvidenceRole,
    SyntheticInputFoundation,
    SyntheticReadiness,
    SyntheticValueStatus,
    TaskTaxonomyEntry,
    WeldProcedureField,
)


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _taxonomy_entry_from_dict(data: dict[str, Any]) -> TaskTaxonomyEntry:
    return TaskTaxonomyEntry(
        family_id=data["family_id"],
        manufacturing_stage=data["manufacturing_stage"],
        weld_object=data["weld_object"],
        joint_type=data["joint_type"],
        weld_position=data["weld_position"],
        groove_geometry=data["groove_geometry"],
        layer_pass=data["layer_pass"],
        access_context=data["access_context"],
        motion_structure=data["motion_structure"],
        readiness=SyntheticReadiness(data["readiness"]),
        modeling_difficulty=data["modeling_difficulty"],
        notes=data["notes"],
    )


def _procedure_field_from_dict(data: dict[str, Any]) -> WeldProcedureField:
    return WeldProcedureField(
        field_name=data["field_name"],
        field_group=data["field_group"],
        required=data["required"],
        description=data["description"],
    )


def _evidence_binding_from_dict(data: dict[str, Any]) -> EvidenceBinding:
    return EvidenceBinding(
        field_path=data["field_path"],
        source_id=data["source_id"],
        evidence_role=SyntheticEvidenceRole(data["evidence_role"]),
        value_status=SyntheticValueStatus(data["value_status"]),
        notes=data.get("notes", ""),
    )


def _simulation_input_from_dict(data: dict[str, Any]) -> SimulationInputSpec:
    return SimulationInputSpec(
        input_id=data["input_id"],
        taxonomy_ref=data["taxonomy_ref"],
        procedure_fields=dict(data["procedure_fields"]),
        geometry_spec=dict(data["geometry_spec"]),
        motion_spec=dict(data["motion_spec"]),
        process_spec=dict(data["process_spec"]),
        quality_spec=dict(data["quality_spec"]),
        variant_policy=dict(data["variant_policy"]),
        evidence_bindings=[
            _evidence_binding_from_dict(item) for item in data["evidence_bindings"]
        ],
        generation_boundary=list(data["generation_boundary"]),
    )


def load_synthetic_input_foundation(
    root: str | Path | None = None,
) -> SyntheticInputFoundation:
    foundation_root = Path(root) if root is not None else DEFAULT_FOUNDATION_ROOT
    manifests_root = foundation_root / "manifests"
    data_foundation = load_data_foundation(foundation_root)

    return SyntheticInputFoundation(
        task_taxonomy=[
            _taxonomy_entry_from_dict(item)
            for item in _load_json(manifests_root / "task_taxonomy.json")
        ],
        procedure_fields=[
            _procedure_field_from_dict(item)
            for item in _load_json(manifests_root / "procedure_fields.json")
        ],
        simulation_inputs=[
            _simulation_input_from_dict(item)
            for item in _load_json(manifests_root / "synthetic_v2_inputs.json")
        ],
        valid_source_ids={source.source_id for source in data_foundation.sources},
    )
