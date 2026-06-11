from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

from .model import RobotBodyAsset, RobotBodyAssetValidationStatus, RobotJointLimit


EVIDENCE_BOUNDARY = (
    "uploaded_urdf_asset",
    "not_real_robot_validated",
    "not_tcp_calibrated",
    "not_scene_context",
)
ROBOT_FAMILY = "six_axis_collaborative_welding_arm_candidate"


def build_robot_body_asset_from_urdf(path: str | Path) -> RobotBodyAsset:
    urdf_path = Path(path)
    try:
        root = ElementTree.parse(urdf_path).getroot()
    except ElementTree.ParseError as exc:
        return _asset(
            source_urdf=str(path),
            validation_issues=(f"xml_parse_error:{exc}",),
        )

    robot_model = root.attrib.get("name", urdf_path.stem)
    link_names = tuple(link.attrib.get("name", "") for link in root.findall("link"))
    joints = root.findall("joint")
    joint_names = tuple(joint.attrib.get("name", "") for joint in joints)
    revolute_joints = [joint for joint in joints if joint.attrib.get("type") == "revolute"]

    visual_meshes = _mesh_filenames(root, "visual")
    collision_meshes = _mesh_filenames(root, "collision")
    mesh_references = visual_meshes + collision_meshes
    mesh_files = tuple(dict.fromkeys(mesh_references))

    validation_issues = []
    for mesh_file in mesh_files:
        if not (urdf_path.parent / mesh_file).exists():
            validation_issues.append(f"missing_mesh:{mesh_file}")

    joint_limits = []
    for joint in revolute_joints:
        joint_name = joint.attrib.get("name", "")
        limit = joint.find("limit")
        if limit is None or "lower" not in limit.attrib or "upper" not in limit.attrib:
            validation_issues.append(f"missing_joint_limit:{joint_name}")
            continue
        joint_limits.append(
            RobotJointLimit(
                joint_name=joint_name,
                lower=float(limit.attrib["lower"]),
                upper=float(limit.attrib["upper"]),
                effort=_optional_float(limit.attrib.get("effort")),
                velocity=_optional_float(limit.attrib.get("velocity")),
            )
        )

    if len(revolute_joints) < 6:
        validation_issues.append("fewer_than_six_revolute_joints")

    return _asset(
        source_urdf=str(path),
        robot_model=robot_model,
        link_names=link_names,
        joint_names=joint_names,
        joint_limits=tuple(joint_limits),
        mesh_files=mesh_files,
        mesh_references=mesh_references,
        joint_count=len(joints),
        revolute_joint_count=len(revolute_joints),
        visual_mesh_count=len(visual_meshes),
        collision_mesh_count=len(collision_meshes),
        validation_issues=tuple(validation_issues),
    )


def _mesh_filenames(root: ElementTree.Element, element_name: str) -> tuple[str, ...]:
    filenames = []
    for element in root.findall(f".//{element_name}"):
        for mesh in element.findall(".//mesh"):
            filename = mesh.attrib.get("filename")
            if filename:
                filenames.append(filename)
    return tuple(filenames)


def _optional_float(value: str | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _asset(
    *,
    source_urdf: str,
    robot_model: str = "unknown",
    link_names: tuple[str, ...] = (),
    joint_names: tuple[str, ...] = (),
    joint_limits: tuple[RobotJointLimit, ...] = (),
    mesh_files: tuple[str, ...] = (),
    mesh_references: tuple[str, ...] = (),
    joint_count: int = 0,
    revolute_joint_count: int = 0,
    visual_mesh_count: int = 0,
    collision_mesh_count: int = 0,
    validation_issues: tuple[str, ...] = (),
) -> RobotBodyAsset:
    validation_status: RobotBodyAssetValidationStatus = "usable_as_robot_body_context"
    if validation_issues:
        validation_status = "blocked_by_asset_issue"

    return RobotBodyAsset(
        robot_id=f"robot-body-{robot_model}",
        robot_model=robot_model,
        robot_family=ROBOT_FAMILY,
        source_urdf=source_urdf,
        link_names=link_names,
        joint_names=joint_names,
        joint_limits=joint_limits,
        mesh_files=mesh_files,
        mesh_references=mesh_references,
        joint_count=joint_count,
        revolute_joint_count=revolute_joint_count,
        visual_mesh_count=visual_mesh_count,
        collision_mesh_count=collision_mesh_count,
        validation_status=validation_status,
        validation_issues=validation_issues,
        evidence_boundary=EVIDENCE_BOUNDARY,
    )
