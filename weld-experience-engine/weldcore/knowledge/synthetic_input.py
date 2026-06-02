from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


FORBIDDEN_POOL_TERMS = ("molten_pool", "molten pool", "weld_pool", "weld pool", "熔池")


class SyntheticEvidenceRole(str, Enum):
    FIELD_COVERAGE = "field_coverage"
    TASK_MAPPING = "task_mapping"
    PROCEDURE_REFERENCE = "procedure_reference"
    VOCABULARY = "vocabulary"
    MOTION_TEMPLATE = "motion_template"
    SCHEMA_REFERENCE = "schema_reference"


class SyntheticReadiness(str, Enum):
    READY_FOR_SYNTHETIC_V2_PLAN = "ready_for_synthetic_v2_plan"
    NEEDS_MORE_SOURCES = "needs_more_sources"
    DEFER = "defer"


class SyntheticValueStatus(str, Enum):
    PUBLIC_VOCABULARY = "public_vocabulary"
    PROJECT_DEFINED_PLACEHOLDER = "project_defined_placeholder"
    SIMULATION_ASSUMPTION = "simulation_assumption"
    PUBLIC_REFERENCE_PLUS_SCHEMA = "public_reference_plus_schema"
    PUBLIC_LABEL_VOCABULARY = "public_label_vocabulary"
    SIMULATION_SCORE_PLACEHOLDER = "simulation_score_placeholder"
    REQUIRES_REAL_VALIDATION_LATER = "requires_real_validation_later"
    SCHEMA_ONLY = "schema_only"


class WeldProcedureField(str, Enum):
    WELDING_PROCESS = "welding_process"
    PLATE_THICKNESS_MM = "plate_thickness_mm"
    CURRENT = "current"
    VOLTAGE = "voltage"
    TRAVEL_SPEED = "travel_speed"
    TRAJECTORY = "trajectory"
    TORCH_ANGLE = "torch_angle"
    QUALITY_LABEL = "quality_label"
    DEFECT_LABEL = "defect_label"
    INSPECTION_REFERENCE = "inspection_reference"


REQUIRED_PROCEDURE_FIELDS = tuple(field.value for field in WeldProcedureField)
QUALITY_FIELDS = ("quality_label", "defect_label", "inspection_reference")
QUALITY_BOUNDARY_MARKERS = (
    "public_label_vocabulary",
    "simulation_score_placeholder",
    "requires_real_validation_later",
)


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {_jsonable(key): _jsonable(item) for key, item in value.items()}
    return value


def _field_name(value: Any) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


def _has_forbidden_term(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            _has_forbidden_term(key) or _has_forbidden_term(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_has_forbidden_term(item) for item in value)
    text = str(value).lower()
    return any(term in text for term in FORBIDDEN_POOL_TERMS)


@dataclass(frozen=True)
class EvidenceBinding:
    field_path: str
    source_id: str
    evidence_role: SyntheticEvidenceRole
    value_status: SyntheticValueStatus
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {key: _jsonable(value) for key, value in asdict(self).items()}


@dataclass(frozen=True)
class TaskTaxonomyEntry:
    family_id: str
    manufacturing_stage: str
    weld_object: str
    joint_type: str
    weld_position: str
    readiness: SyntheticReadiness
    groove_geometry: str | None = None
    layer_pass: str | None = None

    def ready_for_plan(self) -> bool:
        return self.readiness == SyntheticReadiness.READY_FOR_SYNTHETIC_V2_PLAN

    def to_dict(self) -> dict[str, Any]:
        return {key: _jsonable(value) for key, value in asdict(self).items()}


@dataclass(frozen=True)
class SyntheticSkillDatasetV2PlanInput:
    first_batch_families: list[str]
    deferred_families: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {key: _jsonable(value) for key, value in asdict(self).items()}


@dataclass(frozen=True)
class SimulationInputSpec:
    input_id: str
    taxonomy_ref: str
    procedure_fields: dict[WeldProcedureField | str, Any]
    geometry_spec: dict[str, Any]
    motion_spec: dict[str, Any]
    process_spec: dict[str, Any]
    quality_spec: dict[str, Any]
    evidence_bindings: list[EvidenceBinding]

    def to_dict(self) -> dict[str, Any]:
        return {key: _jsonable(value) for key, value in asdict(self).items()}


@dataclass(frozen=True)
class SyntheticInputGateResult:
    passed: bool
    issues: list[str]


@dataclass
class SyntheticInputFoundation:
    taxonomy: list[TaskTaxonomyEntry]
    simulation_inputs: list[SimulationInputSpec]
    plan_input: SyntheticSkillDatasetV2PlanInput

    def validate(self, valid_source_ids: set[str] | None = None) -> SyntheticInputGateResult:
        issues: list[str] = []
        taxonomy_by_id = {entry.family_id: entry for entry in self.taxonomy}

        for simulation_input in self.simulation_inputs:
            input_id = simulation_input.input_id
            binding_by_path = {
                binding.field_path: binding for binding in simulation_input.evidence_bindings
            }

            if _has_forbidden_term(simulation_input.to_dict()):
                issues.append(f"{input_id}: forbidden pool-route field is out of scope")

            taxonomy_entry = taxonomy_by_id.get(simulation_input.taxonomy_ref)
            if taxonomy_entry is None:
                issues.append(
                    f"{input_id}: taxonomy_ref {simulation_input.taxonomy_ref} does not exist"
                )
            elif not taxonomy_entry.ready_for_plan():
                issues.append(
                    f"{input_id}: taxonomy_ref {simulation_input.taxonomy_ref} is not ready_for_synthetic_v2_plan"
                )

            if valid_source_ids is not None:
                for binding in simulation_input.evidence_bindings:
                    if binding.source_id not in valid_source_ids:
                        issues.append(
                            f"{input_id}: {binding.field_path} has unknown source_id {binding.source_id}"
                        )

            procedure_fields = {
                _field_name(field): value
                for field, value in simulation_input.procedure_fields.items()
            }
            for field in REQUIRED_PROCEDURE_FIELDS:
                if field not in procedure_fields:
                    issues.append(f"{input_id}: missing procedure_fields.{field}")
            for field in procedure_fields:
                self._require_binding(
                    issues,
                    input_id,
                    binding_by_path,
                    f"procedure_fields.{field}",
                )

            self._require_spec_bindings(
                issues,
                input_id,
                binding_by_path,
                "geometry_spec",
                simulation_input.geometry_spec,
            )
            self._require_spec_bindings(
                issues,
                input_id,
                binding_by_path,
                "motion_spec",
                simulation_input.motion_spec,
            )
            self._require_spec_bindings(
                issues,
                input_id,
                binding_by_path,
                "process_spec",
                simulation_input.process_spec,
            )
            self._require_spec_bindings(
                issues,
                input_id,
                binding_by_path,
                "quality_spec",
                simulation_input.quality_spec,
            )

            self._validate_quality_boundaries(
                issues,
                input_id,
                binding_by_path,
                procedure_fields,
                "procedure_fields",
            )
            self._validate_quality_boundaries(
                issues,
                input_id,
                binding_by_path,
                simulation_input.quality_spec,
                "quality_spec",
            )

        return SyntheticInputGateResult(passed=not issues, issues=issues)

    @staticmethod
    def _require_binding(
        issues: list[str],
        input_id: str,
        binding_by_path: dict[str, EvidenceBinding],
        field_path: str,
    ) -> None:
        if field_path not in binding_by_path:
            issues.append(f"{input_id}: missing evidence binding for {field_path}")

    def _require_spec_bindings(
        self,
        issues: list[str],
        input_id: str,
        binding_by_path: dict[str, EvidenceBinding],
        group_name: str,
        spec: dict[str, Any],
    ) -> None:
        for field in spec:
            self._require_binding(
                issues,
                input_id,
                binding_by_path,
                f"{group_name}.{_field_name(field)}",
            )

    @staticmethod
    def _validate_quality_boundaries(
        issues: list[str],
        input_id: str,
        binding_by_path: dict[str, EvidenceBinding],
        fields: dict[str, Any],
        group_name: str,
    ) -> None:
        for field in QUALITY_FIELDS:
            if field not in fields:
                continue

            field_path = f"{group_name}.{field}"
            binding = binding_by_path.get(field_path)
            value_text = str(fields[field]).lower()
            has_value_boundary = any(
                marker in value_text for marker in QUALITY_BOUNDARY_MARKERS
            )
            has_binding_boundary = (
                binding is not None
                and binding.value_status
                == SyntheticValueStatus.REQUIRES_REAL_VALIDATION_LATER
            )
            if not has_value_boundary and not has_binding_boundary:
                issues.append(
                    f"{input_id}: quality fields require public_label_vocabulary, "
                    f"simulation_score_placeholder, or requires_real_validation_later boundary for {field_path}"
                )
