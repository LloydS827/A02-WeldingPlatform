from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ManiSkillAdapterSpec:
    name: str = "maniskill"
    required_dependency: str = "mani_skill"
    mvp_role: str = "optional task environment and demonstration dataset reference adapter"
    runtime_required: bool = False

    def explain_boundary(self) -> str:
        return (
            "ManiSkill is an optional adapter boundary for robotics task and "
            "demonstration conventions; the MVP core models and tests do not "
            "import or require mani_skill at runtime."
        )
