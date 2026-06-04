import json

from weldcore.skill_unit import WeldSkillUnit, default_weld_skill_units


def test_default_weld_skill_units_cover_core_and_reserved_extension_units():
    units = default_weld_skill_units()
    unit_ids = {unit.unit_id for unit in units}

    assert "long-straight-horizontal-tracking" in unit_ids
    assert "corner-horizontal-transition" in unit_ids
    assert "u-seam-vertical-extension" in unit_ids


def test_weld_skill_unit_serializes_minimal_contract():
    unit = WeldSkillUnit(
        unit_id="long-straight-horizontal-tracking",
        name="长直横焊沿缝跟踪",
        seam_geometry="long_straight",
        welding_position="horizontal",
        motion_skill="tracking",
        robot_constraints=("tcp_path_continuity", "torch_posture_stability"),
        required_sim_outputs=("tcp_trajectory", "tool_orientation", "task_status"),
        evaluation_metrics=("path_continuity", "posture_stability"),
        evidence_requirements=("simulation_boundary", "requires_real_validation_later"),
        out_of_scope=("real_welding_quality", "WPS/PQR"),
    )

    assert unit.to_dict() == {
        "unit_id": "long-straight-horizontal-tracking",
        "name": "长直横焊沿缝跟踪",
        "seam_geometry": "long_straight",
        "welding_position": "horizontal",
        "motion_skill": "tracking",
        "robot_constraints": ["tcp_path_continuity", "torch_posture_stability"],
        "required_sim_outputs": ["tcp_trajectory", "tool_orientation", "task_status"],
        "evaluation_metrics": ["path_continuity", "posture_stability"],
        "evidence_requirements": [
            "simulation_boundary",
            "requires_real_validation_later",
        ],
        "out_of_scope": ["real_welding_quality", "WPS/PQR"],
    }


def test_default_weld_skill_units_exclude_current_forbidden_physics_fields():
    payload = json.dumps(
        [unit.to_dict() for unit in default_weld_skill_units()],
        ensure_ascii=False,
    ).lower()

    assert "molten" not in payload
    assert "weld_pool" not in payload
    assert "thermal" not in payload
    assert "metallurgy" not in payload
    assert "熔池" not in payload
    assert "热过程" not in payload
    assert "冶金" not in payload
