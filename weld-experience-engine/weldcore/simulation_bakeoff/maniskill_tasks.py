from __future__ import annotations

from weldcore.simulation_bakeoff.maniskill_contract import ManiSkillTaskConfig
from weldcore.simulation_bakeoff.model import SimulationTaskSpec
from weldcore.simulation_bakeoff.task_specs import default_simulation_task_specs


def maniskill_task_config_from_spec(task_spec: SimulationTaskSpec) -> ManiSkillTaskConfig:
    return ManiSkillTaskConfig(
        task_id=task_spec.task_id,
        unit_id=task_spec.unit_id,
        task_name=task_spec.name,
        seam_path=task_spec.seam_path,
        tcp_frame=task_spec.tcp_frame,
        orientation_constraint=task_spec.tool_orientation_constraint,
        motion_constraint=task_spec.motion_constraint,
        expected_outputs=task_spec.expected_outputs,
        out_of_scope=task_spec.out_of_scope,
        source_task_spec_id=task_spec.task_id,
    )


def default_maniskill_task_configs() -> tuple[ManiSkillTaskConfig, ...]:
    return tuple(
        maniskill_task_config_from_spec(task_spec)
        for task_spec in default_simulation_task_specs()
    )
