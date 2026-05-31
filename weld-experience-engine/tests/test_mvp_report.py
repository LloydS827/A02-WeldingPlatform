import json

from weldcore.report.mvp_report import run_mvp_report


def test_mvp_report_writes_skill_transfer_evidence(tmp_path):
    result = run_mvp_report(tmp_path)

    expected = {
        "evidence.json",
        "metrics.csv",
        "transfer_summary.png",
        "ip_notes.md",
    }
    assert expected.issubset({path.name for path in tmp_path.iterdir()})
    assert result["experiment"]["decision"] in {"pass", "review", "fail"}

    evidence = json.loads((tmp_path / "evidence.json").read_text(encoding="utf-8"))
    assert evidence["dataset"]["source_type"] == "simulation"
    assert evidence["skill_package"]["package_id"] == "pkg-straight-flat-001"
    assert evidence["rerun_boundary"]["runtime_required"] is False

    metrics = (tmp_path / "metrics.csv").read_text(encoding="utf-8")
    assert "trajectory_rms_mm" in metrics

    ip_notes = (tmp_path / "ip_notes.md").read_text(encoding="utf-8")
    assert "专利" in ip_notes
    assert "论文" in ip_notes
