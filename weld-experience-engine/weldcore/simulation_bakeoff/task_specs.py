from __future__ import annotations

from weldcore.simulation_bakeoff.model import SimulationPathPoint, SimulationTaskSpec
from weldcore.skill_unit import CORNER_HORIZONTAL_TRANSITION, LONG_STRAIGHT_HORIZONTAL_TRACKING


def _metrics_with_path_continuity(metrics: tuple[str, ...]) -> tuple[str, ...]:
    if "path_continuity" in metrics:
        return metrics
    return ("path_continuity", *metrics)


def _robot_constraints(unit_constraints: tuple[str, ...]) -> tuple[str, ...]:
    return ("ik_reachability", "collision_check", *unit_constraints)


LONG_STRAIGHT_HORIZONTAL_PATH = (
    SimulationPathPoint(t=0.0, x=0.00, y=0.0, z=0.12, rx=0.0, ry=90.0, rz=0.0),
    SimulationPathPoint(t=0.25, x=0.15, y=0.0, z=0.12, rx=0.0, ry=90.0, rz=0.0),
    SimulationPathPoint(t=0.5, x=0.30, y=0.0, z=0.12, rx=0.0, ry=90.0, rz=0.0),
    SimulationPathPoint(t=0.75, x=0.45, y=0.0, z=0.12, rx=0.0, ry=90.0, rz=0.0),
    SimulationPathPoint(t=1.0, x=0.60, y=0.0, z=0.12, rx=0.0, ry=90.0, rz=0.0),
)

CORNER_HORIZONTAL_PATH = (
    SimulationPathPoint(t=0.0, x=0.00, y=0.00, z=0.12, rx=0.0, ry=90.0, rz=0.0),
    SimulationPathPoint(t=0.2, x=0.12, y=0.00, z=0.12, rx=0.0, ry=90.0, rz=0.0),
    SimulationPathPoint(t=0.45, x=0.24, y=0.00, z=0.12, rx=0.0, ry=90.0, rz=15.0),
    SimulationPathPoint(t=0.7, x=0.24, y=0.12, z=0.12, rx=0.0, ry=90.0, rz=60.0),
    SimulationPathPoint(t=1.0, x=0.24, y=0.24, z=0.12, rx=0.0, ry=90.0, rz=90.0),
)

DEFAULT_SIMULATION_TASK_SPECS = (
    SimulationTaskSpec(
        task_id=f"task-{LONG_STRAIGHT_HORIZONTAL_TRACKING.unit_id}",
        unit_id=LONG_STRAIGHT_HORIZONTAL_TRACKING.unit_id,
        name=LONG_STRAIGHT_HORIZONTAL_TRACKING.name,
        seam_path=LONG_STRAIGHT_HORIZONTAL_PATH,
        tcp_frame="torch_tcp",
        tool_orientation_constraint=("keep_torch_posture_stable",),
        motion_constraint=("constant_tracking_speed", "continuous_tcp_motion"),
        robot_constraint=_robot_constraints(LONG_STRAIGHT_HORIZONTAL_TRACKING.robot_constraints),
        expected_outputs=LONG_STRAIGHT_HORIZONTAL_TRACKING.required_sim_outputs,
        evaluation_metrics=_metrics_with_path_continuity(
            LONG_STRAIGHT_HORIZONTAL_TRACKING.evaluation_metrics
        ),
        out_of_scope=LONG_STRAIGHT_HORIZONTAL_TRACKING.out_of_scope,
    ),
    SimulationTaskSpec(
        task_id=f"task-{CORNER_HORIZONTAL_TRANSITION.unit_id}",
        unit_id=CORNER_HORIZONTAL_TRANSITION.unit_id,
        name=CORNER_HORIZONTAL_TRANSITION.name,
        seam_path=CORNER_HORIZONTAL_PATH,
        tcp_frame="torch_tcp",
        tool_orientation_constraint=("maintain_orientation_through_corner",),
        motion_constraint=("continuous_corner_transition", "bounded_stop_start"),
        robot_constraint=_robot_constraints(CORNER_HORIZONTAL_TRANSITION.robot_constraints),
        expected_outputs=CORNER_HORIZONTAL_TRANSITION.required_sim_outputs,
        evaluation_metrics=_metrics_with_path_continuity(
            CORNER_HORIZONTAL_TRANSITION.evaluation_metrics
        ),
        out_of_scope=CORNER_HORIZONTAL_TRANSITION.out_of_scope,
    ),
)


def default_simulation_task_specs() -> tuple[SimulationTaskSpec, ...]:
    return DEFAULT_SIMULATION_TASK_SPECS
