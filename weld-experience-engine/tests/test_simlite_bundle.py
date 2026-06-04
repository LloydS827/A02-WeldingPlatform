from __future__ import annotations

from pathlib import Path

import pytest

from weldcore.ingest import import_simulation_bundle, validate_simulation_bundle
from weldcore.knowledge.synthetic_manifest import load_synthetic_input_foundation
from weldcore.sim import write_simlite_bundle


def _expected_bundle_id(input_id: str, seed: int, sample_count: int) -> str:
    return f"simlite-{input_id}-{seed}-{sample_count}"


def test_write_simlite_bundle_produces_importable_bundle(tmp_path: Path) -> None:
    foundation = load_synthetic_input_foundation()
    expected_bundle_id = _expected_bundle_id("input-panel-butt-001", 13, 2)

    bundle = write_simlite_bundle(
        tmp_path,
        input_id="input-panel-butt-001",
        sample_count=2,
        seed=13,
        foundation=foundation,
    )

    assert bundle == tmp_path / expected_bundle_id
    assert bundle.is_dir()
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


@pytest.mark.parametrize("sample_count", [0, -1])
def test_write_simlite_bundle_rejects_non_positive_sample_count(
    tmp_path: Path,
    sample_count: int,
) -> None:
    foundation = load_synthetic_input_foundation()

    with pytest.raises(ValueError) as exc_info:
        write_simlite_bundle(
            tmp_path,
            input_id="input-panel-butt-001",
            sample_count=sample_count,
            seed=13,
            foundation=foundation,
        )

    assert "sample_count" in str(exc_info.value)


def test_write_simlite_bundle_uses_distinct_bundle_directories_per_seed(
    tmp_path: Path,
) -> None:
    foundation = load_synthetic_input_foundation()

    first_bundle = write_simlite_bundle(
        tmp_path,
        input_id="input-panel-butt-001",
        sample_count=2,
        seed=13,
        foundation=foundation,
    )
    second_bundle = write_simlite_bundle(
        tmp_path,
        input_id="input-panel-butt-001",
        sample_count=2,
        seed=14,
        foundation=foundation,
    )

    assert first_bundle != second_bundle
    assert first_bundle.parent == tmp_path
    assert second_bundle.parent == tmp_path
    assert "input-panel-butt-001" in first_bundle.name
    assert "13" in first_bundle.name
    assert "2" in first_bundle.name
    assert "input-panel-butt-001" in second_bundle.name
    assert "14" in second_bundle.name
    assert "2" in second_bundle.name

    for bundle in (first_bundle, second_bundle):
        gate = validate_simulation_bundle(bundle, foundation=foundation)
        assert gate.passed is True
        assert gate.issues == []

        result = import_simulation_bundle(bundle, foundation=foundation)
        assert result.gate.passed is True
        assert result.run_record.input_id == "input-panel-butt-001"
        assert result.run_record.simulator.value == "simlite"
        assert len(result.dataset.samples) == 2
