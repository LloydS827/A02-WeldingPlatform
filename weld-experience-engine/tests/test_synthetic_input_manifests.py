from collections import Counter

from weldcore.knowledge import SyntheticReadiness
from weldcore.knowledge.synthetic_manifest import load_synthetic_input_foundation


def test_synthetic_input_foundation_loads_from_default_docs_manifests():
    from weldcore.knowledge import load_synthetic_input_foundation as exported_loader

    assert exported_loader is load_synthetic_input_foundation

    foundation = load_synthetic_input_foundation()

    assert len(foundation.task_taxonomy) >= 7
    readiness_counts = Counter(entry.readiness for entry in foundation.task_taxonomy)
    assert readiness_counts[SyntheticReadiness.READY_FOR_SYNTHETIC_V2_PLAN] >= 3
    assert readiness_counts[SyntheticReadiness.NEEDS_MORE_SOURCES] >= 1
    assert readiness_counts[SyntheticReadiness.DEFER] >= 3

    result = foundation.validate()
    assert result.passed, result.issues


def test_first_batch_inputs_target_only_ready_taxonomy_families():
    foundation = load_synthetic_input_foundation()

    first_batch_refs = {
        simulation_input.taxonomy_ref
        for simulation_input in foundation.simulation_inputs
    }

    assert first_batch_refs == {
        "stiffened-panel-fillet",
        "panel-butt",
        "micro-panel-web-bulkhead",
    }


def test_procedure_fields_cover_required_groups():
    foundation = load_synthetic_input_foundation()

    groups = {field.field_group for field in foundation.procedure_fields}

    assert {
        "task_joint",
        "geometry_material",
        "process",
        "motion_posture",
        "quality_inspection",
    } <= groups


def test_each_actual_procedure_field_has_evidence_binding():
    foundation = load_synthetic_input_foundation()

    for simulation_input in foundation.simulation_inputs:
        binding_paths = {
            binding.field_path for binding in simulation_input.evidence_bindings
        }

        assert {
            f"procedure_fields.{field_name}"
            for field_name in simulation_input.procedure_fields
        } <= binding_paths
