from __future__ import annotations

from weldcore.simulation_bakeoff.maniskill_contract import (
    ManiSkillTaskConfig,
    RuleBasedDemo,
)


def generate_rule_based_demo(config: ManiSkillTaskConfig) -> RuleBasedDemo:
    return RuleBasedDemo(
        demo_id=f"demo-{config.task_id}",
        task_id=config.task_id,
        tcp_trajectory=config.seam_path,
        tool_orientation=config.seam_path,
        generation_method="rule_based_seam_path_following",
        evidence_notes=(
            "not_human_demonstration",
            "not_robot_execution_validation",
        ),
    )
