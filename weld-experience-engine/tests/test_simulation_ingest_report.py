from __future__ import annotations

import json
from pathlib import Path

from weldcore.report.simulation_ingest_report import main, run_simulation_ingest_report


FORBIDDEN_POOL_TERMS = (
    "molten_pool",
    "molten pool",
    "weld_pool",
    "weld pool",
    "熔池",
)


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_simulation_ingest_report_writes_runtime_and_docs_outputs(tmp_path: Path) -> None:
    docs_report_dir = tmp_path / "docs-reports"

    evidence = run_simulation_ingest_report(
        outdir=tmp_path / "out",
        docs_report_dir=docs_report_dir,
    )

    assert evidence["summary"]["sample_count"] >= 1
    assert evidence["summary"]["can_import_simulation_dataset"] is True
    assert evidence["sample_summary"]["trajectory_point_count"] > 0
    assert evidence["sample_summary"]["process_signal_count"] > 0

    runtime_dir = tmp_path / "out"
    for filename in [
        "run_record.json",
        "bundle_manifest.json",
        "dataset.json",
        "evidence.md",
    ]:
        assert (runtime_dir / filename).exists()

    assert (docs_report_dir / "simulation_ingest_evidence.md").exists()

    dataset = _read_json(runtime_dir / "dataset.json")
    assert dataset["source_type"] == "simulation"
    assert dataset["schema_version"] == "synthetic-v2-dataset-v0.1"

    markdown = (runtime_dir / "evidence.md").read_text(encoding="utf-8")
    assert "## Run Summary" in markdown
    assert "## Bundle Summary" in markdown
    assert "## Sample Summary" in markdown
    assert "## Input Spec Alignment" in markdown
    assert "## Evidence Binding Summary" in markdown
    assert "## Assumption Fields" in markdown
    assert "## Real-Validation Fields" in markdown
    assert "## Warnings And Errors" in markdown
    assert "## Skill Package Readiness" in markdown
    assert "SimulationOutputBundle" in markdown
    assert "不是 WPS/PQR" in markdown
    assert "不证明真实焊接质量" in markdown
    assert "外部仿真器仍然只是可选 adapter" in markdown
    assert "当前报告使用 simlite/mock bundle 验证平台接入能力" in markdown
    assert "前期调研资料继续作为后续焊接知识嵌入底座" in markdown
    assert "具备后续形成 skill package 的输入基础" in markdown


def test_simulation_ingest_report_runtime_outputs_do_not_include_forbidden_terms(
    tmp_path: Path,
) -> None:
    docs_report_dir = tmp_path / "docs-reports"
    run_simulation_ingest_report(outdir=tmp_path, docs_report_dir=docs_report_dir)

    for filename in [
        "run_record.json",
        "bundle_manifest.json",
        "dataset.json",
        "evidence.md",
    ]:
        text = (tmp_path / filename).read_text(encoding="utf-8").lower()
        assert not any(term in text for term in FORBIDDEN_POOL_TERMS)

    docs_markdown = (docs_report_dir / "simulation_ingest_evidence.md").read_text(
        encoding="utf-8"
    ).lower()
    assert not any(term in docs_markdown for term in FORBIDDEN_POOL_TERMS)


def test_simulation_ingest_report_cli_writes_docs_copy_by_default(tmp_path: Path) -> None:
    outdir = tmp_path / "cli-out"
    docs_report_dir = tmp_path / "cli-docs"

    main(
        [
            "--outdir",
            str(outdir),
            "--docs-report-dir",
            str(docs_report_dir),
        ]
    )

    assert (outdir / "run_record.json").exists()
    assert (outdir / "bundle_manifest.json").exists()
    assert (outdir / "dataset.json").exists()
    assert (outdir / "evidence.md").exists()
    assert (docs_report_dir / "simulation_ingest_evidence.md").exists()


def test_simulation_ingest_report_cli_no_docs_copy(tmp_path: Path) -> None:
    outdir = tmp_path / "cli-out"
    docs_report_dir = tmp_path / "cli-docs"

    main(
        [
            "--outdir",
            str(outdir),
            "--docs-report-dir",
            str(docs_report_dir),
            "--no-docs-copy",
        ]
    )

    assert (outdir / "run_record.json").exists()
    assert (outdir / "bundle_manifest.json").exists()
    assert (outdir / "dataset.json").exists()
    assert (outdir / "evidence.md").exists()
    assert not (docs_report_dir / "simulation_ingest_evidence.md").exists()
