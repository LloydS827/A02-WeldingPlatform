from weldcore.knowledge import (
    EvidenceBinding,
    SimulationInputSpec,
    SyntheticEvidenceRole,
    SyntheticInputFoundation,
    SyntheticReadiness,
    SyntheticSkillDatasetV2PlanInput,
    SyntheticValueStatus,
    TaskTaxonomyEntry,
    WeldProcedureField,
)


VALID_SOURCE_ID = "project-260522-shipbuilding-welding-brain-plan"


def procedure_field_catalog() -> list[WeldProcedureField]:
    return [
        WeldProcedureField("joint_type", "task_joint", required=True),
        WeldProcedureField("welding_process", "process", required=True),
        WeldProcedureField("plate_thickness_mm", "geometry", required=True),
        WeldProcedureField("current", "process", required=True),
        WeldProcedureField("voltage", "process", required=True),
        WeldProcedureField("travel_speed", "process", required=True),
        WeldProcedureField("trajectory", "motion", required=True),
        WeldProcedureField("torch_angle", "motion", required=True),
        WeldProcedureField("quality_label", "quality", required=True),
        WeldProcedureField("defect_label", "quality", required=True),
        WeldProcedureField("inspection_reference", "quality", required=True),
        WeldProcedureField(
            "wire_feed",
            "process",
            required=False,
            description="Optional later WPS/PQR extension.",
        ),
    ]


def ready_taxonomy(family_id: str = "panel-butt") -> TaskTaxonomyEntry:
    return TaskTaxonomyEntry(
        family_id=family_id,
        manufacturing_stage="panel_line",
        weld_object="panel",
        joint_type="butt",
        weld_position="flat",
        groove_geometry="single_v_placeholder",
        layer_pass="single_pass",
        access_context="open_panel",
        motion_structure="single_seam",
        readiness=SyntheticReadiness.READY_FOR_SYNTHETIC_V2_PLAN,
        modeling_difficulty="easy",
        notes="Ready.",
    )


def plan_input() -> SyntheticSkillDatasetV2PlanInput:
    return SyntheticSkillDatasetV2PlanInput(
        plan_id="synthetic-v2-plan-input-001",
        first_batch_input_ids=["synthetic-v2-panel-butt-001"],
        deferred_family_ids=["double-bottom-internal-fillet"],
        notes=["First batch uses ready task families only."],
    )


def binding(
    field_path: str,
    source_id: str = VALID_SOURCE_ID,
    evidence_role: SyntheticEvidenceRole = SyntheticEvidenceRole.PROJECT_INTERNAL,
    value_status: SyntheticValueStatus = SyntheticValueStatus.ASSUMED,
) -> EvidenceBinding:
    return EvidenceBinding(
        field_path=field_path,
        source_id=source_id,
        evidence_role=evidence_role,
        value_status=value_status,
        notes="test binding",
    )


def valid_input(**overrides) -> SimulationInputSpec:
    evidence_bindings = [
        binding("procedure_fields.joint_type"),
        binding("procedure_fields.welding_process", evidence_role=SyntheticEvidenceRole.PUBLIC_PROCESS_REFERENCE),
        binding("procedure_fields.plate_thickness_mm"),
        binding("procedure_fields.current", evidence_role=SyntheticEvidenceRole.PUBLIC_DATASET_SCHEMA),
        binding("procedure_fields.voltage", evidence_role=SyntheticEvidenceRole.PUBLIC_DATASET_SCHEMA),
        binding("procedure_fields.travel_speed", evidence_role=SyntheticEvidenceRole.PUBLIC_DATASET_SCHEMA),
        binding("procedure_fields.trajectory", evidence_role=SyntheticEvidenceRole.SIMULATION_OUTPUT, value_status=SyntheticValueStatus.GENERATED),
        binding("procedure_fields.torch_angle"),
        binding("procedure_fields.quality_label", value_status=SyntheticValueStatus.REQUIRES_REAL_VALIDATION_LATER),
        binding("procedure_fields.defect_label", value_status=SyntheticValueStatus.REQUIRES_REAL_VALIDATION_LATER),
        binding("procedure_fields.inspection_reference", value_status=SyntheticValueStatus.REQUIRES_REAL_VALIDATION_LATER),
        binding("geometry_spec.groove_geometry"),
        binding("geometry_spec.plate_thickness_mm"),
        binding("motion_spec.motion_template", evidence_role=SyntheticEvidenceRole.SHIPBUILDING_CASE),
        binding("motion_spec.trajectory", evidence_role=SyntheticEvidenceRole.SIMULATION_OUTPUT, value_status=SyntheticValueStatus.GENERATED),
        binding("motion_spec.torch_angle"),
        binding("process_spec.current", evidence_role=SyntheticEvidenceRole.PUBLIC_DATASET_SCHEMA),
        binding("process_spec.voltage", evidence_role=SyntheticEvidenceRole.PUBLIC_DATASET_SCHEMA),
        binding("process_spec.travel_speed", evidence_role=SyntheticEvidenceRole.PUBLIC_DATASET_SCHEMA),
        binding("quality_spec.quality_label", value_status=SyntheticValueStatus.REQUIRES_REAL_VALIDATION_LATER),
        binding("quality_spec.defect_label", value_status=SyntheticValueStatus.REQUIRES_REAL_VALIDATION_LATER),
        binding("quality_spec.inspection_reference", value_status=SyntheticValueStatus.REQUIRES_REAL_VALIDATION_LATER),
        binding("quality_spec.requires_real_validation_later", evidence_role=SyntheticEvidenceRole.REQUIRES_REAL_VALIDATION_LATER, value_status=SyntheticValueStatus.REQUIRES_REAL_VALIDATION_LATER),
    ]
    spec = SimulationInputSpec(
        input_id="synthetic-v2-panel-butt-001",
        taxonomy_ref="panel-butt",
        procedure_fields={
            "joint_type": "butt",
            "welding_process": "GMAW",
            "plate_thickness_mm": 8.0,
            "current": 180,
            "voltage": 24,
            "travel_speed": 6.0,
            "trajectory": "single_straight_seam",
            "torch_angle": "work_angle_placeholder",
            "quality_label": "public_label_vocabulary: acceptable_placeholder",
            "defect_label": "public_label_vocabulary: none_placeholder",
            "inspection_reference": "requires_real_validation_later: visual_placeholder",
        },
        geometry_spec={
            "groove_geometry": "single_v_placeholder",
            "plate_thickness_mm": 8.0,
        },
        motion_spec={
            "motion_template": "single_straight_seam",
            "trajectory": "line_segment_placeholder",
            "torch_angle": "work_angle_placeholder",
        },
        process_spec={
            "current": 180,
            "voltage": 24,
            "travel_speed": 6.0,
        },
        quality_spec={
            "quality_label": "public_label_vocabulary: acceptable_placeholder",
            "defect_label": "public_label_vocabulary: none_placeholder",
            "inspection_reference": "requires_real_validation_later: visual_placeholder",
            "requires_real_validation_later": True,
        },
        variant_policy={"count": 3, "mode": "bounded_assumption"},
        evidence_bindings=evidence_bindings,
        generation_boundary=["not a WPS/PQR", "requires real validation later"],
    )
    return SimulationInputSpec(**{**spec.__dict__, **overrides})


def foundation_with(
    *inputs: SimulationInputSpec,
    taxonomy: TaskTaxonomyEntry | None = None,
    fields: list[WeldProcedureField] | None = None,
    valid_source_ids: set[str] | None = None,
) -> SyntheticInputFoundation:
    return SyntheticInputFoundation(
        task_taxonomy=[taxonomy or ready_taxonomy()],
        procedure_fields=fields or procedure_field_catalog(),
        simulation_inputs=list(inputs),
        valid_source_ids=valid_source_ids,
    )


def test_public_api_accepts_plan_shape_and_serializes_enums():
    assert SyntheticEvidenceRole("public_process_reference") == SyntheticEvidenceRole.PUBLIC_PROCESS_REFERENCE
    assert SyntheticValueStatus("constrained") == SyntheticValueStatus.CONSTRAINED

    taxonomy = ready_taxonomy()
    plan = plan_input()

    assert WeldProcedureField("joint_type", "task_joint", required=True).to_dict() == {
        "field_name": "joint_type",
        "field_group": "task_joint",
        "required": True,
        "description": "",
    }
    assert taxonomy.to_dict()["readiness"] == "ready_for_synthetic_v2_plan"
    assert taxonomy.to_dict()["access_context"] == "open_panel"
    assert plan.to_dict() == {
        "plan_id": "synthetic-v2-plan-input-001",
        "first_batch_input_ids": ["synthetic-v2-panel-butt-001"],
        "deferred_family_ids": ["double-bottom-internal-fillet"],
        "notes": ["First batch uses ready task families only."],
    }


def test_complete_simulation_input_passes_foundation_validation_with_owned_source_ids():
    result = foundation_with(
        valid_input(),
        valid_source_ids={VALID_SOURCE_ID},
    ).validate()

    assert result.passed
    assert result.issues == []


def test_deferred_task_input_is_rejected():
    deferred_taxonomy = TaskTaxonomyEntry(
        family_id="double-bottom-internal-fillet",
        manufacturing_stage="block_assembly",
        weld_object="double_bottom",
        joint_type="fillet",
        weld_position="overhead",
        groove_geometry="tee_placeholder",
        layer_pass="multi_pass",
        access_context="confined_block",
        motion_structure="multi_short_seams",
        readiness=SyntheticReadiness.DEFER,
        modeling_difficulty="hard",
        notes="Deferred.",
    )

    result = foundation_with(
        valid_input(taxonomy_ref="double-bottom-internal-fillet"),
        taxonomy=deferred_taxonomy,
    ).validate()

    assert not result.passed
    assert any("not ready_for_synthetic_v2_plan" in issue for issue in result.issues)


def test_forbidden_pool_route_field_is_rejected():
    spec = valid_input(geometry_spec={"groove_geometry": "none", "molten_pool": "camera_placeholder"})

    result = foundation_with(spec).validate()

    assert not result.passed
    assert any("forbidden pool-route" in issue for issue in result.issues)


def test_missing_required_procedure_field_is_rejected_from_catalog():
    spec = valid_input(
        procedure_fields={
            key: value
            for key, value in valid_input().procedure_fields.items()
            if key != "joint_type"
        }
    )

    result = foundation_with(spec).validate()

    assert not result.passed
    assert any("procedure_fields.joint_type" in issue for issue in result.issues)


def test_required_procedure_field_without_binding_is_rejected():
    spec = valid_input(
        evidence_bindings=[
            item for item in valid_input().evidence_bindings if item.field_path != "procedure_fields.joint_type"
        ],
    )

    result = foundation_with(spec).validate()

    assert not result.passed
    assert any("procedure_fields.joint_type" in issue for issue in result.issues)


def test_optional_procedure_field_is_not_required():
    fields = [
        WeldProcedureField("joint_type", "task_joint", required=True),
        WeldProcedureField("wire_feed", "process", required=False),
    ]
    spec = valid_input(
        procedure_fields={"joint_type": "butt"},
        evidence_bindings=[binding("procedure_fields.joint_type")],
        geometry_spec={},
        motion_spec={},
        process_spec={},
        quality_spec={},
    )

    result = foundation_with(spec, fields=fields).validate()

    assert result.passed


def test_present_optional_procedure_field_without_binding_is_rejected():
    spec = valid_input(
        procedure_fields={
            **valid_input().procedure_fields,
            "wire_feed": 5.2,
        },
    )

    result = foundation_with(spec).validate()

    assert not result.passed
    assert any("procedure_fields.wire_feed" in issue for issue in result.issues)


def test_missing_geometry_business_field_evidence_binding_is_rejected():
    spec = valid_input(
        geometry_spec={
            "groove_geometry": "single_v_placeholder",
            "plate_thickness_mm": 8.0,
            "root_gap_mm": 2.0,
        }
    )

    result = foundation_with(spec).validate()

    assert not result.passed
    assert any("geometry_spec.root_gap_mm" in issue for issue in result.issues)


def test_unknown_evidence_source_id_is_rejected():
    spec = valid_input(
        evidence_bindings=[
            *valid_input().evidence_bindings,
            binding("process_spec.current", "unknown-source"),
        ]
    )

    result = foundation_with(spec, valid_source_ids={VALID_SOURCE_ID}).validate()

    assert not result.passed
    assert any("unknown source_id unknown-source" in issue for issue in result.issues)


def test_quality_field_without_boundary_is_rejected():
    spec = valid_input(
        quality_spec={
            "quality_label": "acceptable",
            "defect_label": "none",
            "inspection_reference": "visual",
            "requires_real_validation_later": True,
        },
        evidence_bindings=[
            binding(path, value_status=SyntheticValueStatus.ASSUMED)
            for path in [
                "procedure_fields.joint_type",
                "procedure_fields.welding_process",
                "procedure_fields.plate_thickness_mm",
                "procedure_fields.current",
                "procedure_fields.voltage",
                "procedure_fields.travel_speed",
                "procedure_fields.trajectory",
                "procedure_fields.torch_angle",
                "procedure_fields.quality_label",
                "procedure_fields.defect_label",
                "procedure_fields.inspection_reference",
                "geometry_spec.groove_geometry",
                "geometry_spec.plate_thickness_mm",
                "motion_spec.motion_template",
                "motion_spec.trajectory",
                "motion_spec.torch_angle",
                "process_spec.current",
                "process_spec.voltage",
                "process_spec.travel_speed",
                "quality_spec.quality_label",
                "quality_spec.defect_label",
                "quality_spec.inspection_reference",
                "quality_spec.requires_real_validation_later",
            ]
        ],
    )

    result = foundation_with(spec).validate()

    assert not result.passed
    assert any("quality fields require" in issue for issue in result.issues)


def test_procedure_quality_fields_without_boundary_are_rejected():
    quality_procedure_paths = {
        "procedure_fields.quality_label",
        "procedure_fields.defect_label",
        "procedure_fields.inspection_reference",
    }
    base_input = valid_input()
    spec = valid_input(
        procedure_fields={
            **base_input.procedure_fields,
            "quality_label": "acceptable",
            "defect_label": "none",
            "inspection_reference": "visual",
        },
        evidence_bindings=[
            EvidenceBinding(
                field_path=item.field_path,
                source_id=item.source_id,
                evidence_role=item.evidence_role,
                value_status=(
                    SyntheticValueStatus.ASSUMED
                    if item.field_path in quality_procedure_paths
                    else item.value_status
                ),
                notes=item.notes,
            )
            for item in base_input.evidence_bindings
        ],
    )

    result = foundation_with(spec).validate()

    assert not result.passed
    assert any("procedure_fields.quality_label" in issue for issue in result.issues)


def test_unbound_geometry_field_issue_contains_specific_field_path():
    spec = valid_input(
        evidence_bindings=[
            item for item in valid_input().evidence_bindings if item.field_path != "geometry_spec.plate_thickness_mm"
        ],
    )

    result = foundation_with(spec).validate()

    assert not result.passed
    assert any("geometry_spec.plate_thickness_mm" in issue for issue in result.issues)


def test_mixed_quality_fields_report_unbound_defect_label():
    spec = valid_input(
        evidence_bindings=[
            item for item in valid_input().evidence_bindings if item.field_path != "quality_spec.defect_label"
        ],
    )

    result = foundation_with(spec).validate()

    assert not result.passed
    assert any("quality_spec.defect_label" in issue for issue in result.issues)
