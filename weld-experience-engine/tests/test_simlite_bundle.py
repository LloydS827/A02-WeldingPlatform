from __future__ import annotations

from pathlib import Path

from weldcore.ingest import import_simulation_bundle, validate_simulation_bundle
from weldcore.knowledge.synthetic_manifest import load_synthetic_input_foundation
from weldcore.sim import write_simlite_bundle


def test_write_simlite_bundle_produces_importable_bundle(tmp_path: Path) -> None:
    foundation = load_synthetic_input_foundation()

    bundle = write_simlite_bundle(
        tmp_path,
        input_id="input-panel-butt-001",
        sample_count=2,
        seed=13,
        foundation=foundation,
    )

    assert bundle == tmp_path
    assert (bundle / "manifest.json").exists()
    assert (bundle / "trajectory.csv").exists()
    assert (bundle / "process_signals.csv").exists()
    assert (bundle / "evidence_bindings.json").exists()
    assert (bundle / "quality_placeholders.json").exists()

    gate = validate_simulation_bundle(bundle, foundation=foundation)
    assert gate.passed is True
    assert gate.issues == []

    result = import_simulation_bundle(bundle, foundation=foundation)
    assert result.gate.passed is True
    assert result.dataset.schema_version == "synthetic-v2-dataset-v0.1"
    assert len(result.dataset.samples) == 2
    assert result.run_record.input_id == "input-panel-butt-001"
    assert result.run_record.simulator.value == "simlite"

    sample_metadata = result.dataset.samples[0].metadata
    assert sample_metadata["requires_real_validation_later"] is True
    assert "not WPS/PQR" in sample_metadata["generation_boundary"]
    assert "not real welding quality validation" in sample_metadata["generation_boundary"]
