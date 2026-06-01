from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from .shipbuilding import ShipbuildingTaskFamily, TaskDisposition


class EvidenceRole(str, Enum):
    PUBLIC_CONSTRAINT = "public_constraint"
    SIMULATION_OUTPUT = "simulation_output"
    ASSUMPTION = "assumption"
    REQUIRES_REAL_VALIDATION_LATER = "requires_real_validation_later"


@dataclass(frozen=True)
class ParameterRange:
    name: str
    unit: str
    min_value: float
    max_value: float
    evidence_role: EvidenceRole
    source_refs: list[str]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_role"] = self.evidence_role.value
        return data


@dataclass(frozen=True)
class SimulationScenarioSpec:
    scenario_id: str
    shipbuilding_task: str
    shipbuilding_context: str
    difficulty: str
    task_disposition: TaskDisposition
    weld_condition: dict[str, Any]
    parameter_ranges: list[ParameterRange]
    motion_templates: list[str]
    quality_placeholders: list[str]
    source_refs: list[str]
    assumptions: list[str]
    evidence_roles: list[EvidenceRole] = field(
        default_factory=lambda: [
            EvidenceRole.PUBLIC_CONSTRAINT,
            EvidenceRole.ASSUMPTION,
            EvidenceRole.REQUIRES_REAL_VALIDATION_LATER,
        ]
    )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["task_disposition"] = self.task_disposition.value
        data["parameter_ranges"] = [item.to_dict() for item in self.parameter_ranges]
        data["evidence_roles"] = [item.value for item in self.evidence_roles]
        return data


@dataclass(frozen=True)
class ScenarioGateResult:
    scenario_id: str
    passed: bool
    issues: list[str]

    @classmethod
    def from_scenario(
        cls,
        scenario: SimulationScenarioSpec,
        require_candidate: bool = False,
    ) -> "ScenarioGateResult":
        issues: list[str] = []
        if not scenario.shipbuilding_context:
            issues.append("missing shipbuilding_context")
        if len(scenario.source_refs) < 2:
            issues.append("requires at least two source refs")
        if require_candidate and scenario.task_disposition != TaskDisposition.CANDIDATE:
            issues.append("scenario must come from a candidate task family")
        if EvidenceRole.PUBLIC_CONSTRAINT not in scenario.evidence_roles:
            issues.append("missing public_constraint evidence role")
        if EvidenceRole.REQUIRES_REAL_VALIDATION_LATER not in scenario.evidence_roles:
            issues.append("missing requires_real_validation_later evidence role")
        text = " ".join(
            [
                scenario.shipbuilding_task,
                scenario.shipbuilding_context,
                *scenario.motion_templates,
                *scenario.quality_placeholders,
                *scenario.assumptions,
            ]
        ).lower()
        if "molten" in text or "weld_pool" in text or "熔池" in text:
            issues.append("molten-pool dependency is out of scope")
        return cls(scenario.scenario_id, not issues, issues)


def _difficulty_label(modeling_difficulty: int) -> str:
    if modeling_difficulty <= 1:
        return "easy"
    if modeling_difficulty <= 3:
        return "medium"
    return "hard"


def scenario_from_task_family(family: ShipbuildingTaskFamily) -> SimulationScenarioSpec:
    return SimulationScenarioSpec(
        scenario_id=f"scenario-{family.family_id}",
        shipbuilding_task=family.name,
        shipbuilding_context=family.shipbuilding_context,
        difficulty=_difficulty_label(family.modeling_difficulty),
        task_disposition=family.disposition,
        weld_condition={
            "family_id": family.family_id,
            "joint_types": [item.value for item in family.joint_types],
            "positions": [item.value for item in family.positions],
            "typical_weld_objects": family.typical_weld_objects,
        },
        parameter_ranges=[
            ParameterRange(
                name="travel_speed",
                unit="mm/s",
                min_value=3.0,
                max_value=8.0,
                evidence_role=EvidenceRole.PUBLIC_CONSTRAINT,
                source_refs=family.source_ids,
            )
        ],
        motion_templates=["straight", "optional_weave"],
        quality_placeholders=["geometry_risk_label", "defect_vocabulary_placeholder"],
        source_refs=family.source_ids,
        assumptions=[
            "Candidate scenario only; public references constrain fields but do not validate welding quality."
        ],
    )
