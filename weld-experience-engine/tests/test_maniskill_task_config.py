from weldcore.simulation_bakeoff import (
    default_maniskill_task_configs,
    default_simulation_task_specs,
    maniskill_task_config_from_spec,
)


def test_task_config_maps_default_task_spec_without_losing_boundaries():
    task_spec = default_simulation_task_specs()[0]

    config = maniskill_task_config_from_spec(task_spec)

    assert config.task_id == task_spec.task_id
    assert config.unit_id == task_spec.unit_id
    assert config.source_task_spec_id == task_spec.task_id
    assert config.seam_path == task_spec.seam_path
    assert config.tcp_frame == "torch_tcp"
    assert config.orientation_constraint == task_spec.tool_orientation_constraint
    assert config.motion_constraint == task_spec.motion_constraint
    assert config.expected_outputs == task_spec.expected_outputs
    assert "WPS/PQR" in config.out_of_scope


def test_default_maniskill_task_configs_cover_two_default_units():
    configs = default_maniskill_task_configs()

    assert [config.unit_id for config in configs] == [
        "long-straight-horizontal-tracking",
        "corner-horizontal-transition",
    ]
    assert all(config.task_id.startswith("task-") for config in configs)
