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


def ready_taxonomy(family_id: str = "panel-butt") -> TaskTaxonomyEntry:
    return TaskTaxonomyEntry(
        family_id=family_id,
        manufacturing_stage="panel_line",
        weld_object="panel",
        joint_type="butt",
        weld_position="flat",
        readiness=SyntheticReadiness.READY_FOR_SYNTHETIC_V2_PLAN,
    )


def binding(
    field_path: str,
    source_id: str = "project-260522-shipbuilding-welding-brain-plan",
    value_status: SyntheticValueStatus = SyntheticValueStatus.SIMULATION_ASSUMPTION,
) -> EvidenceBinding:
    return EvidenceBinding(
        field_path=field_path,
        source_id=source_id,
        evidence_role=SyntheticEvidenceRole.FIELD_COVERAGE,
        value_status=value_status,
        notes="test binding",
    )


def valid_input(**overrides) -> SimulationInputSpec:
    evidence_bindings = [
        binding("procedure_fields.welding_process"),
        binding("procedure_fields.plate_thickness_mm"),
        binding("procedure_fields.current"),
        binding("procedure_fields.voltage"),
        binding("procedure_fields.travel_speed"),
        binding("procedure_fields.trajectory"),
        binding("procedure_fields.torch_angle"),
        binding("procedure_fields.quality_label", value_status=SyntheticValueStatus.PUBLIC_LABEL_VOCABULARY),
        binding("procedure_fields.defect_label", value_status=SyntheticValueStatus.PUBLIC_LABEL_VOCABULARY),
        binding("procedure_fields.inspection_reference", value_status=SyntheticValueStatus.PUBLIC_LABEL_VOCABULARY),
        binding("geometry_spec.groove_geometry"),
        binding("geometry_spec.plate_thickness_mm"),
        binding("motion_spec.motion_template"),
        binding("motion_spec.trajectory"),
        binding("motion_spec.torch_angle"),
        binding("process_spec.current"),
        binding("process_spec.voltage"),
        binding("process_spec.travel_speed"),
        binding("quality_spec.quality_label", value_status=SyntheticValueStatus.PUBLIC_LABEL_VOCABULARY),
        binding("quality_spec.defect_label", value_status=SyntheticValueStatus.PUBLIC_LABEL_VOCABULARY),
        binding("quality_spec.inspection_reference", value_status=SyntheticValueStatus.PUBLIC_LABEL_VOCABULARY),
        binding("quality_spec.requires_real_validation_later", value_status=SyntheticValueStatus.REQUIRES_REAL_VALIDATION_LATER),
    ]
    spec = SimulationInputSpec(
        input_id="synthetic-v2-panel-butt-001",
        taxonomy_ref="panel-butt",
        procedure_fields={
            WeldProcedureField.WELDING_PROCESS: "GMAW",
            WeldProcedureField.PLATE_THICKNESS_MM: 8.0,
            WeldProcedureField.CURRENT: 180,
            WeldProcedureField.VOLTAGE: 24,
            WeldProcedureField.TRAVEL_SPEED: 6.0,
            WeldProcedureField.TRAJECTORY: "single_straight_seam",
            WeldProcedureField.TORCH_ANGLE: "work_angle_placeholder",
            WeldProcedureField.QUALITY_LABEL: "public_label_vocabulary: acceptable_placeholder",
            WeldProcedureField.DEFECT_LABEL: "public_label_vocabulary: none_placeholder",
            WeldProcedureField.INSPECTION_REFERENCE: "requires_real_validation_later: visual_placeholder",
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
        evidence_bindings=evidence_bindings,
    )
    return SimulationInputSpec(**{**spec.__dict__, **overrides})


def foundation_with(*inputs: SimulationInputSpec, taxonomy: TaskTaxonomyEntry | None = None) -> SyntheticInputFoundation:
    return SyntheticInputFoundation(
        taxonomy=[taxonomy or ready_taxonomy()],
        simulation_inputs=list(inputs),
        plan_input=SyntheticSkillDatasetV2PlanInput(
            first_batch_families=["panel-butt"],
            deferred_families=["double-bottom-internal-fillet"],
        ),
    )


def test_task_taxonomy_entry_serializes_readiness_as_string():
    row = ready_taxonomy().to_dict()

    assert row["readiness"] == "ready_for_synthetic_v2_plan"


def test_plan_input_to_dict_records_first_batch_and_deferred_families():
    plan = SyntheticSkillDatasetV2PlanInput(
        first_batch_families=["stiffened-panel-fillet", "panel-butt"],
        deferred_families=["double-bottom-internal-fillet"],
    )

    assert plan.to_dict() == {
        "first_batch_families": ["stiffened-panel-fillet", "panel-butt"],
        "deferred_families": ["double-bottom-internal-fillet"],
    }


def test_complete_simulation_input_passes_foundation_validation():
    result = foundation_with(valid_input()).validate(
        valid_source_ids={"project-260522-shipbuilding-welding-brain-plan"}
    )

    assert result.passed
    assert result.issues == []


def test_deferred_task_input_is_rejected():
    deferred_taxonomy = TaskTaxonomyEntry(
        family_id="double-bottom-internal-fillet",
        manufacturing_stage="block_assembly",
        weld_object="double_bottom",
        joint_type="fillet",
        weld_position="overhead",
        readiness=SyntheticReadiness.DEFER,
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
    spec = valid_input(evidence_bindings=[*valid_input().evidence_bindings, binding("process_spec.current", "unknown-source")])

    result = foundation_with(spec).validate(valid_source_ids={"project-260522-shipbuilding-welding-brain-plan"})

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
            binding(path)
            for path in [
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


def test_unbound_geometry_field_issue_contains_specific_field_path():
    spec = valid_input(
        geometry_spec={
            "groove_geometry": "single_v_placeholder",
            "plate_thickness_mm": 8.0,
        },
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
