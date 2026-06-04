import json
import subprocess
import sys
from pathlib import Path

import pytest

from weldcore.knowledge.foundation import DataFoundation
from weldcore.report.data_foundation_report import (
    DEFAULT_DOCS_REPORT_DIR,
    run_data_foundation_report,
)


FORBIDDEN_ROUTE_TERMS = (
    "熔池",
    "molten_pool",
    "molten pool",
    "weld_pool",
    "weld pool",
)


def _json_text(path):
    return path.read_text(encoding="utf-8").lower()


ENGINE_ROOT = Path(__file__).resolve().parents[1]


def test_data_foundation_report_returns_summary_and_writes_outputs(tmp_path):
    evidence = run_data_foundation_report(tmp_path)

    assert set(evidence) == {
        "summary",
        "sources",
        "datasets",
        "field_coverage",
        "task_evidence",
    }
    assert evidence["summary"]["source_count"] >= 20
    assert evidence["summary"]["public_source_count"] >= 15
    assert evidence["summary"]["strong_shipbuilding_source_count"] >= 8
    assert evidence["summary"]["public_dataset_count"] >= 6
    assert evidence["summary"]["ready_task_count"] >= 3
    assert len(evidence["sources"]) == evidence["summary"]["source_count"]
    assert len(evidence["datasets"]) == evidence["summary"]["dataset_count"]
    assert len(evidence["field_coverage"]) > 0
    assert len(evidence["task_evidence"]) >= evidence["summary"]["ready_task_count"]

    for filename in [
        "sources.json",
        "datasets.json",
        "field_coverage.csv",
        "task_evidence_map.json",
        "evidence.md",
        "synthetic_skilldataset_v2_plan_input.md",
    ]:
        assert (tmp_path / filename).exists()

    sources = json.loads((tmp_path / "sources.json").read_text(encoding="utf-8"))
    kranendonk = next(
        source
        for source in sources
        if source["source_id"] == "vendor-kranendonk-block-welding-line"
    )
    assert kranendonk["title"]
    assert kranendonk["url"]
    assert kranendonk["shipbuilding_relevance"]
    assert kranendonk["use_boundary"]


def test_data_foundation_report_refreshes_committed_docs_outputs(tmp_path):
    docs_report_dir = tmp_path / "docs-reports"

    run_data_foundation_report(tmp_path / "out", docs_report_dir=docs_report_dir)

    evidence = docs_report_dir / "data_foundation_evidence.md"
    plan_input = docs_report_dir / "synthetic_skilldataset_v2_plan_input.md"
    assert evidence.exists()
    assert plan_input.exists()
    assert "数据集与资料底座证据报告" in evidence.read_text(encoding="utf-8")
    assert "SyntheticSkillDataset v2 规划输入" in plan_input.read_text(encoding="utf-8")


def test_data_foundation_report_blocks_invalid_foundation(tmp_path):
    foundation = DataFoundation(sources=[], datasets=[], task_evidence=[])

    with pytest.raises(ValueError, match="Data foundation gate failed"):
        run_data_foundation_report(tmp_path, foundation=foundation)


def test_data_foundation_report_json_and_csv_outputs_do_not_contain_forbidden_terms(
    tmp_path,
):
    run_data_foundation_report(tmp_path)

    for filename in [
        "sources.json",
        "datasets.json",
        "task_evidence_map.json",
        "field_coverage.csv",
    ]:
        text = _json_text(tmp_path / filename)
        assert not any(term in text for term in FORBIDDEN_ROUTE_TERMS)


def test_data_foundation_report_default_docs_dir_points_to_repo_docs():
    assert DEFAULT_DOCS_REPORT_DIR.name == "reports"
    assert DEFAULT_DOCS_REPORT_DIR.parent.name == "data-foundation"
    assert DEFAULT_DOCS_REPORT_DIR.parent.parent.name == "evidence"
    assert DEFAULT_DOCS_REPORT_DIR.parent.parent.parent.name == "docs"


def test_data_foundation_report_module_entrypoint_refreshes_temp_docs(tmp_path):
    outdir = tmp_path / "cli-out"
    docs_report_dir = tmp_path / "cli-docs"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "weldcore.report.data_foundation_report",
            "--outdir",
            str(outdir),
            "--docs-report-dir",
            str(docs_report_dir),
        ],
        check=True,
        cwd=ENGINE_ROOT,
        text=True,
        capture_output=True,
    )

    assert result.stdout.startswith("=== 数据集与资料底座证据摘要 ===")
    assert (outdir / "sources.json").exists()
    evidence = docs_report_dir / "data_foundation_evidence.md"
    plan_input = docs_report_dir / "synthetic_skilldataset_v2_plan_input.md"
    assert evidence.exists()
    assert plan_input.exists()
    assert "数据集与资料底座证据报告" in evidence.read_text(encoding="utf-8")
    assert "SyntheticSkillDataset v2 规划输入" in plan_input.read_text(encoding="utf-8")
