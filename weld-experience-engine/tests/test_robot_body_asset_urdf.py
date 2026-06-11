from pathlib import Path

from weldcore.skill_asset import build_robot_body_asset_from_urdf


ROOT = Path(__file__).resolve().parents[2]
URDF = ROOT / "docs" / "real-urdf" / "robot.urdf"


def test_real_urdf_builds_robot_body_asset():
    asset = build_robot_body_asset_from_urdf(URDF)

    assert asset.robot_model == "generated_robot"
    assert asset.robot_family == "six_axis_collaborative_welding_arm_candidate"
    assert asset.validation_status == "usable_as_robot_body_context"
    assert asset.joint_count == 6
    assert asset.revolute_joint_count == 6
    assert len(asset.link_names) == 7
    assert len(asset.mesh_files) == 33
    assert asset.visual_mesh_count == 33
    assert asset.collision_mesh_count == 33
    assert len(asset.mesh_references) == 66
    assert asset.validation_issues == ()
    assert "uploaded_urdf_asset" in asset.evidence_boundary
    assert "not_real_robot_validated" in asset.evidence_boundary
    assert "not_tcp_calibrated" in asset.evidence_boundary
    assert "not_scene_context" in asset.evidence_boundary
    assert all(limit.lower == -1.57 and limit.upper == 1.57 for limit in asset.joint_limits)


def _write_urdf(tmp_path, text, *, mesh_name="part.stl"):
    root = tmp_path / "robot.urdf"
    mesh_dir = tmp_path / "meshes"
    mesh_dir.mkdir()
    (mesh_dir / mesh_name).write_text("solid placeholder\nendsolid placeholder\n")
    root.write_text(text, encoding="utf-8")
    return root


def test_urdf_blocks_missing_mesh_reference(tmp_path):
    urdf = tmp_path / "robot.urdf"
    urdf.write_text(
        '<robot name="bad"><link name="base"><visual><geometry>'
        '<mesh filename="meshes/missing.stl"/></geometry></visual></link></robot>',
        encoding="utf-8",
    )

    asset = build_robot_body_asset_from_urdf(urdf)

    assert asset.validation_status == "blocked_by_asset_issue"
    assert "missing_mesh:meshes/missing.stl" in asset.validation_issues


def test_urdf_blocks_revolute_joint_without_limit(tmp_path):
    urdf = _write_urdf(
        tmp_path,
        '<robot name="bad">'
        '<link name="a"/><link name="b"/>'
        '<joint name="j1" type="revolute"><parent link="a"/><child link="b"/></joint>'
        "</robot>",
    )

    asset = build_robot_body_asset_from_urdf(urdf)

    assert asset.validation_status == "blocked_by_asset_issue"
    assert "missing_joint_limit:j1" in asset.validation_issues


def test_urdf_blocks_bad_xml(tmp_path):
    urdf = tmp_path / "robot.urdf"
    urdf.write_text("<robot", encoding="utf-8")

    asset = build_robot_body_asset_from_urdf(urdf)

    assert asset.validation_status == "blocked_by_asset_issue"
    assert any(issue.startswith("xml_parse_error:") for issue in asset.validation_issues)


def test_urdf_blocks_missing_urdf_file(tmp_path):
    urdf = tmp_path / "missing.urdf"

    asset = build_robot_body_asset_from_urdf(urdf)

    assert asset.validation_status == "blocked_by_asset_issue"
    assert any(issue.startswith("urdf_read_error:") for issue in asset.validation_issues)


def test_urdf_blocks_invalid_robot_root(tmp_path):
    urdf = _write_urdf(
        tmp_path,
        '<assembly name="not_robot">'
        '<link name="a"/><link name="b"/>'
        '<joint name="j1" type="revolute"><parent link="a"/><child link="b"/>'
        '<limit lower="-1" upper="1" effort="1" velocity="1"/></joint>'
        "</assembly>",
    )

    asset = build_robot_body_asset_from_urdf(urdf)

    assert asset.validation_status == "blocked_by_asset_issue"
    assert "invalid_urdf_root:assembly" in asset.validation_issues


def test_urdf_blocks_invalid_numeric_joint_limit(tmp_path):
    urdf = _write_urdf(
        tmp_path,
        '<robot name="bad_limit">'
        '<link name="a"/><link name="b"/>'
        '<joint name="j1" type="revolute"><parent link="a"/><child link="b"/>'
        '<limit lower="oops" upper="1" effort="1" velocity="1"/></joint>'
        "</robot>",
    )

    asset = build_robot_body_asset_from_urdf(urdf)

    assert asset.validation_status == "blocked_by_asset_issue"
    assert "invalid_joint_limit:j1:lower" in asset.validation_issues


def test_urdf_blocks_fewer_than_six_revolute_joints(tmp_path):
    urdf = _write_urdf(
        tmp_path,
        '<robot name="few">'
        '<link name="a"/><link name="b"/>'
        '<joint name="j1" type="revolute"><parent link="a"/><child link="b"/>'
        '<limit lower="-1" upper="1" effort="1" velocity="1"/></joint>'
        "</robot>",
    )

    asset = build_robot_body_asset_from_urdf(urdf)

    assert asset.validation_status == "blocked_by_asset_issue"
    assert "fewer_than_six_revolute_joints" in asset.validation_issues


def test_urdf_blocks_missing_links(tmp_path):
    urdf = _write_urdf(
        tmp_path,
        '<robot name="no_links">'
        '<joint name="j1" type="revolute"><parent link="a"/><child link="b"/>'
        '<limit lower="-1" upper="1" effort="1" velocity="1"/></joint>'
        "</robot>",
    )

    asset = build_robot_body_asset_from_urdf(urdf)

    assert asset.validation_status == "blocked_by_asset_issue"
    assert "missing_links" in asset.validation_issues


def test_urdf_blocks_missing_visual_or_collision_meshes(tmp_path):
    urdf = tmp_path / "robot.urdf"
    links = "".join(f'<link name="l{i}"/>' for i in range(7))
    joints = "".join(
        f'<joint name="j{i}" type="revolute"><parent link="l{i}"/><child link="l{i + 1}"/>'
        '<limit lower="-1" upper="1" effort="1" velocity="1"/></joint>'
        for i in range(6)
    )
    urdf.write_text(f'<robot name="meshless">{links}{joints}</robot>', encoding="utf-8")

    asset = build_robot_body_asset_from_urdf(urdf)

    assert asset.validation_status == "blocked_by_asset_issue"
    assert "missing_visual_meshes" in asset.validation_issues
    assert "missing_collision_meshes" in asset.validation_issues


def test_urdf_blocks_joint_parent_or_child_not_in_links(tmp_path):
    urdf = _write_urdf(
        tmp_path,
        '<robot name="bad_refs">'
        '<link name="a"/><link name="b"/>'
        '<joint name="j1" type="revolute"><parent link="missing_parent"/><child link="b"/>'
        '<limit lower="-1" upper="1" effort="1" velocity="1"/></joint>'
        '<joint name="j2" type="revolute"><parent link="a"/><child link="missing_child"/>'
        '<limit lower="-1" upper="1" effort="1" velocity="1"/></joint>'
        "</robot>",
    )

    asset = build_robot_body_asset_from_urdf(urdf)

    assert asset.validation_status == "blocked_by_asset_issue"
    assert "joint_parent_missing:j1:missing_parent" in asset.validation_issues
    assert "joint_child_missing:j2:missing_child" in asset.validation_issues
