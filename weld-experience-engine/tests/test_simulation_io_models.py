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
        taxonomy_ref="panel-butt",
        simulator=SimulatorName.SIMLITE,
        simulator_version="0.1",
        adapter_version="0.1",
        seed=7,
        sample_count=2,
        generated_at="2026-06-03T00:00:00Z",
        assumption_summary=["plate thickness is a simulation assumption"],
        requires_real_validation_later=True,
        missing_signal_notes=[],
        generation_boundary=["not WPS/PQR", "not real quality validation"],
    )

    data = manifest.to_dict()

    assert data["schema_version"] == SIMULATION_BUNDLE_SCHEMA_VERSION
    assert data["source_type"] == "simulation"
    assert data["simulator"] == "simlite"
    assert data["input_id"] == "input-panel-butt-001"
    assert data["sample_count"] == 2
    assert data["requires_real_validation_later"] is True


def test_simulation_run_record_tracks_bundle_paths_and_status():
    record = SimulationRunRecord(
        simulation_run_id="run-panel-butt-001",
        input_ids=["input-panel-butt-001"],
        simulator=SimulatorName.SIMLITE,
        simulator_version="0.1",
        adapter_name="simlite_bundle",
        adapter_version="0.1",
        seed=7,
        started_at="2026-06-03T00:00:00Z",
        finished_at="2026-06-03T00:00:01Z",
        status=SimulationRunStatus.IMPORTED,
        output_bundle_uris=["simulation_ingest_report_out/bundles/bundle-panel-butt-001"],
        sample_count=2,
        warnings=[],
        errors=[],
        boundary_notes=["requires real validation later"],
    )

    data = record.to_dict()

    assert data["status"] == "imported"
    assert data["simulator"] == "simlite"
    assert data["output_bundle_uris"] == [
        "simulation_ingest_report_out/bundles/bundle-panel-butt-001"
    ]
    assert SYNTHETIC_DATASET_SCHEMA_VERSION == "synthetic-v2-dataset-v0.1"
