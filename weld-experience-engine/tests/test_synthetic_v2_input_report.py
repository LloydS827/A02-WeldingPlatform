import csv
import inspect
import json
from pathlib import Path

import pytest

from weldcore.knowledge import SyntheticInputFoundation
from weldcore.report.synthetic_v2_input_report import (
    DEFAULT_DOCS_REPORT_DIR,
    run_synthetic_v2_input_report,
)


FORBIDDEN_POOL_TERMS = (
    "molten_pool",
    "molten pool",
    "weld_pool",
    "weld pool",
    "熔池",
)


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_synthetic_v2_input_report_returns_summary_and_writes_outputs(tmp_path):
    evidence = run_synthetic_v2_input_report(outdir=tmp_path, docs_report_dir=None)

    assert set(evidence) == {
        "summary",
        "task_taxonomy",
        "procedure_fields",
        "simulation_inputs",
    }
    assert evidence["summary"]["ready_task_count"] >= 3
    assert evidence["summary"]["simulation_input_count"] == 3

    for filename in [
        "task_taxonomy.json",
        "procedure_fields.json",
        "simulation_inputs.json",
        "evidence_bindings.csv",
        "evidence.md",
    ]:
        assert (tmp_path / filename).exists()

    taxonomy = _read_json(tmp_path / "task_taxonomy.json")
    procedure_fields = _read_json(tmp_path / "procedure_fields.json")
    simulation_inputs = _read_json(tmp_path / "simulation_inputs.json")
    assert len(taxonomy) >= evidence["summary"]["ready_task_count"]
    assert len(procedure_fields) > 0
    assert len(simulation_inputs) == 3

    with (tmp_path / "evidence_bindings.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert set(rows[0]) >= {
        "input_id",
        "taxonomy_ref",
        "field_path",
        "source_id",
        "evidence_role",
        "value_status",
        "notes",
    }


def test_synthetic_v2_input_report_markdown_states_boundaries(tmp_path):
    run_synthetic_v2_input_report(outdir=tmp_path, docs_report_dir=None)

    markdown = (tmp_path / "evidence.md").read_text(encoding="utf-8")

    assert "不是 WPS/PQR" in markdown
    assert "不证明真实焊接质量" in markdown
    assert "SyntheticSkillDataset v2" in markdown
    assert "python -m weldcore.report.synthetic_v2_input_report" in markdown
    assert "首批仿真输入：3" in markdown


def test_synthetic_v2_input_report_json_and_csv_outputs_do_not_contain_forbidden_pool_terms(
    tmp_path,
):
    run_synthetic_v2_input_report(outdir=tmp_path, docs_report_dir=None)

    for filename in [
        "task_taxonomy.json",
        "procedure_fields.json",
        "simulation_inputs.json",
        "evidence_bindings.csv",
    ]:
        text = (tmp_path / filename).read_text(encoding="utf-8").lower()
        assert not any(term in text for term in FORBIDDEN_POOL_TERMS)


def test_synthetic_v2_input_report_refreshes_docs_copy(tmp_path):
    docs_report_dir = tmp_path / "docs-reports"

    run_synthetic_v2_input_report(
        outdir=tmp_path / "out",
        docs_report_dir=docs_report_dir,
    )

    evidence = docs_report_dir / "synthetic_v2_input_evidence.md"
    assert evidence.exists()
    assert "SyntheticSkillDataset v2" in evidence.read_text(encoding="utf-8")


def test_synthetic_v2_input_report_blocks_invalid_foundation(tmp_path):
    foundation = SyntheticInputFoundation(
        task_taxonomy=[],
        procedure_fields=[],
        simulation_inputs=[],
    )

    with pytest.raises(ValueError, match="Synthetic v2 input gate failed"):
        run_synthetic_v2_input_report(
            outdir=tmp_path,
            foundation=foundation,
            docs_report_dir=None,
        )


def test_synthetic_v2_input_report_default_docs_dir_points_to_repo_docs():
    assert DEFAULT_DOCS_REPORT_DIR.name == "reports"
    assert DEFAULT_DOCS_REPORT_DIR.parent.name == "data-foundation"
    assert DEFAULT_DOCS_REPORT_DIR.parent.parent.name == "evidence"
    assert DEFAULT_DOCS_REPORT_DIR.parent.parent.parent.name == "docs"


def test_synthetic_v2_input_report_programmatic_default_skips_docs_copy():
    signature = inspect.signature(run_synthetic_v2_input_report)

    assert signature.parameters["docs_report_dir"].default is None
