from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class WeldSkillUnit:
    unit_id: str
    name: str
    seam_geometry: str
    welding_position: str
    motion_skill: str
    robot_constraints: tuple[str, ...] = ()
    required_sim_outputs: tuple[str, ...] = ()
    evaluation_metrics: tuple[str, ...] = ()
    evidence_requirements: tuple[str, ...] = ()
    out_of_scope: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        for key in (
            "robot_constraints",
            "required_sim_outputs",
            "evaluation_metrics",
            "evidence_requirements",
            "out_of_scope",
        ):
            payload[key] = list(payload[key])
        return payload


LONG_STRAIGHT_HORIZONTAL_TRACKING = WeldSkillUnit(
    unit_id="long-straight-horizontal-tracking",
    name="长直横焊沿缝跟踪",
    seam_geometry="long_straight",
    welding_position="horizontal",
    motion_skill="tracking",
    robot_constraints=("tcp_path_continuity", "torch_posture_stability"),
    required_sim_outputs=("tcp_trajectory", "tool_orientation", "task_status"),
    evaluation_metrics=("path_continuity", "posture_stability", "speed_stability"),
    evidence_requirements=("simulation_boundary", "requires_real_validation_later"),
    out_of_scope=("real_welding_quality", "WPS/PQR"),
)

CORNER_HORIZONTAL_TRANSITION = WeldSkillUnit(
    unit_id="corner-horizontal-transition",
    name="包角横焊转角过渡",
    seam_geometry="corner",
    welding_position="horizontal",
    motion_skill="corner_transition",
    robot_constraints=("corner_reachability", "orientation_continuity"),
    required_sim_outputs=("tcp_trajectory", "tool_orientation", "task_status"),
    evaluation_metrics=("corner_continuity", "posture_stability", "stop_start_boundary"),
    evidence_requirements=("simulation_boundary", "requires_real_validation_later"),
    out_of_scope=("real_welding_quality", "WPS/PQR"),
)

U_SEAM_VERTICAL_EXTENSION = WeldSkillUnit(
    unit_id="u-seam-vertical-extension",
    name="U 型缝立焊扩展单元",
    seam_geometry="u_seam",
    welding_position="vertical",
    motion_skill="complex_path_extension",
    robot_constraints=("reachability_extension", "complex_orientation_change"),
    required_sim_outputs=("tcp_trajectory", "tool_orientation", "task_status"),
    evaluation_metrics=("reachability", "path_continuity", "posture_stability"),
    evidence_requirements=("simulation_boundary", "requires_real_validation_later"),
    out_of_scope=("first_batch_implementation", "real_welding_quality", "WPS/PQR"),
)

DEFAULT_WELD_SKILL_UNITS = (
    LONG_STRAIGHT_HORIZONTAL_TRACKING,
    CORNER_HORIZONTAL_TRANSITION,
    U_SEAM_VERTICAL_EXTENSION,
)


def default_weld_skill_units() -> tuple[WeldSkillUnit, ...]:
    return DEFAULT_WELD_SKILL_UNITS
