from weldcore.simulation_bakeoff import (
    default_maniskill_task_configs,
    generate_rule_based_demo,
)


def test_rule_based_demo_follows_config_seam_path():
    config = default_maniskill_task_configs()[0]

    demo = generate_rule_based_demo(config)

    assert demo.demo_id == f"demo-{config.task_id}"
    assert demo.task_id == config.task_id
    assert demo.tcp_trajectory == config.seam_path
    assert demo.tool_orientation == config.seam_path
    assert demo.generation_method == "rule_based_seam_path_following"
    assert "not_human_demonstration" in demo.evidence_notes


def test_rule_based_demo_is_generated_for_each_default_task():
    demos = [generate_rule_based_demo(config) for config in default_maniskill_task_configs()]

    assert len(demos) == 2
    assert all(len(demo.tcp_trajectory) >= 2 for demo in demos)
