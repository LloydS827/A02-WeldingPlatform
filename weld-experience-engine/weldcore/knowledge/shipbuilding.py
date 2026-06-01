from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from .sources import PublicWeldKnowledgeBase, UsableFor


class WeldJointType(str, Enum):
    BUTT = "butt"
    FILLET = "fillet"
    TEE = "tee"
    LAP = "lap"
    GROOVE = "groove"
    COMPLEX = "complex"


class WeldPosition(str, Enum):
    FLAT = "flat"
    HORIZONTAL = "horizontal"
    VERTICAL_UP = "vertical_up"
    OVERHEAD = "overhead"
    MULTI_POSITION = "multi_position"


class TaskDisposition(str, Enum):
    CANDIDATE = "candidate"
    PROBE = "probe"
    DEFER = "defer"


@dataclass(frozen=True)
class ShipbuildingTaskFamily:
    family_id: str
    name: str
    shipbuilding_context: str
    typical_weld_objects: list[str]
    joint_types: list[WeldJointType]
    positions: list[WeldPosition]
    modeling_difficulty: int
    required_fields: list[str]
    assumption_fields: list[str]
    source_ids: list[str]
    disposition: TaskDisposition
    notes: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["joint_types"] = [item.value for item in self.joint_types]
        data["positions"] = [item.value for item in self.positions]
        data["disposition"] = self.disposition.value
        return data


@dataclass(frozen=True)
class TaskGateResult:
    family_id: str
    passed: bool
    issues: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TaskPriorityScore:
    family_id: str
    score: int
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_task_family_support(
    family: ShipbuildingTaskFamily,
    kb: PublicWeldKnowledgeBase,
) -> TaskGateResult:
    issues: list[str] = []
    sources_by_id = kb.by_id()
    referenced_sources = []

    if not family.shipbuilding_context:
        issues.append("missing shipbuilding_context")

    for source_id in family.source_ids:
        source = sources_by_id.get(source_id)
        if source is None:
            issues.append(f"unknown source: {source_id}")
        else:
            referenced_sources.append(source)

    if len(referenced_sources) < 2:
        issues.append("requires at least two known sources")

    if referenced_sources and not any(
        UsableFor.SCENARIO_SELECTION in source.usable_for for source in referenced_sources
    ):
        issues.append("requires at least one scenario_selection source")

    covered_fields = {field for source in referenced_sources for field in source.covered_fields}
    declared_assumptions = set(family.assumption_fields)
    for field in family.required_fields:
        if field not in covered_fields and field not in declared_assumptions:
            issues.append(f"unsupported required field: {field}")

    text = " ".join(
        [
            family.family_id,
            family.name,
            family.shipbuilding_context,
            *family.required_fields,
            *family.assumption_fields,
            family.notes,
        ]
    ).lower()
    if "molten" in text or "weld_pool" in text or "熔池" in text:
        issues.append("molten-pool dependency is out of scope")

    return TaskGateResult(family.family_id, not issues, issues)


def score_task_family(
    family: ShipbuildingTaskFamily,
    kb: PublicWeldKnowledgeBase,
) -> TaskPriorityScore:
    support = validate_task_family_support(family, kb)
    score = 0
    reasons: list[str] = []
    if support.passed:
        score += 5
        reasons.append("kb support gate passed")
    else:
        reasons.extend(support.issues)
    if family.disposition == TaskDisposition.CANDIDATE:
        score += 3
        reasons.append("candidate disposition")
    elif family.disposition == TaskDisposition.PROBE:
        score += 1
        reasons.append("probe disposition")
    score += max(0, 4 - family.modeling_difficulty)
    reasons.append(f"modeling_difficulty={family.modeling_difficulty}")
    return TaskPriorityScore(family.family_id, score, reasons)


def rank_task_families(
    families: list[ShipbuildingTaskFamily],
    kb: PublicWeldKnowledgeBase,
) -> list[ShipbuildingTaskFamily]:
    return sorted(
        families,
        key=lambda family: (
            -score_task_family(family, kb).score,
            family.modeling_difficulty,
            family.family_id,
        ),
    )


def select_first_batch_candidates(
    families: list[ShipbuildingTaskFamily],
    kb: PublicWeldKnowledgeBase,
    limit: int = 3,
) -> list[ShipbuildingTaskFamily]:
    return [
        family
        for family in rank_task_families(families, kb)
        if family.disposition == TaskDisposition.CANDIDATE
        and validate_task_family_support(family, kb).passed
    ][:limit]
