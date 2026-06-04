from weldcore.model import (
    SIMULATION_BUNDLE_SCHEMA_VERSION,
    SYNTHETIC_DATASET_SCHEMA_VERSION,
    SimulationBundleManifest,
    SimulationRunRecord,
    SimulationRunStatus,
    SimulatorName,
)


def test_simulation_bundle_manifest_serializes_contract_fields():
    manifest = SimulationBundleManifest(
        bundle_id="bundle-panel-butt-001",
        simulation_run_id="run-panel-butt-001",
        input_id="input-panel-butt-001",
        simulator=SimulatorName.SIMLITE,
        simulator_version="0.1",
        adapter_version="0.1",
        seed=7,
        created_at="2026-06-03T00:00:00Z",
        generated_at="2026-06-03T00:00:00Z",
        sample_count=2,
        taxonomy_ref="panel-butt",
        artifact_refs={"trajectory": "trajectory.csv"},
        assumption_summary=["plate thickness is a simulation assumption"],
        requires_real_validation_later=True,
        missing_signal_notes=["wire_feed missing for one source row"],
        generation_boundary=["not WPS/PQR"],
        validation_status="pending_gate",
    )

    data = manifest.to_dict()

    assert set(data) == {
        "bundle_id",
        "simulation_run_id",
        "input_id",
        "source_type",
        "schema_version",
        "simulator",
        "simulator_version",
        "adapter_version",
        "seed",
        "created_at",
        "generated_at",
        "sample_count",
        "taxonomy_ref",
        "artifact_refs",
        "assumption_summary",
        "requires_real_validation_later",
        "missing_signal_notes",
        "generation_boundary",
        "validation_status",
    }
    assert data["schema_version"] == SIMULATION_BUNDLE_SCHEMA_VERSION
    assert data["source_type"] == "simulation"
    assert data["simulator"] == "simlite"
    assert data["input_id"] == "input-panel-butt-001"
    assert data["sample_count"] == 2
    assert data["adapter_version"] == "0.1"
    assert data["seed"] == 7
    assert data["artifact_refs"] == {"trajectory": "trajectory.csv"}
    assert data["requires_real_validation_later"] is True
    assert data["missing_signal_notes"] == ["wire_feed missing for one source row"]
    assert data["generation_boundary"] == ["not WPS/PQR"]
    assert data["validation_status"] == "pending_gate"


def test_simulation_run_record_tracks_bundle_paths_and_status():
    record = SimulationRunRecord(
        simulation_run_id="run-panel-butt-001",
        input_id="input-panel-butt-001",
        simulator=SimulatorName.SIMLITE,
        simulator_version="0.1",
        adapter_version="0.1",
        seed=7,
        sample_count=2,
        status=SimulationRunStatus.IMPORTED,
        created_at="2026-06-03T00:00:00Z",
        completed_at="2026-06-03T00:00:01Z",
        output_bundle_uris=["simulation_ingest_report_out/bundles/bundle-panel-butt-001"],
        warnings=["missing optional recording"],
        errors=["gate warning promoted for review"],
        boundary_notes=["requires real validation later"],
    )

    data = record.to_dict()

    assert set(data) == {
        "simulation_run_id",
        "input_id",
        "simulator",
        "simulator_version",
        "adapter_version",
        "seed",
        "sample_count",
        "status",
        "created_at",
        "completed_at",
        "output_bundle_uris",
        "warnings",
        "errors",
        "boundary_notes",
    }
    assert data["status"] == "imported"
    assert data["simulator"] == "simlite"
    assert data["simulator_version"] == "0.1"
    assert data["adapter_version"] == "0.1"
    assert data["seed"] == 7
    assert data["sample_count"] == 2
    assert data["output_bundle_uris"] == [
        "simulation_ingest_report_out/bundles/bundle-panel-butt-001"
    ]
    assert data["warnings"] == ["missing optional recording"]
    assert data["errors"] == ["gate warning promoted for review"]
    assert data["boundary_notes"] == ["requires real validation later"]
    assert SYNTHETIC_DATASET_SCHEMA_VERSION == "synthetic-v2-dataset-v0.1"
