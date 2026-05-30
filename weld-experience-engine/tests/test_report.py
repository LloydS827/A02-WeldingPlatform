import json

from weldcore.report.generate import run_report


def test_run_report_produces_evidence(tmp_path):
    result = run_report(outdir=str(tmp_path), show_rerun=False)

    assert result["ideal_roundtrip_rms"] < 0.2
    assert {"crescent", "zigzag", "trapezoid"}.issubset(result["classified_ok"].keys())
    assert all(result["classified_ok"].values())
    assert "amp_breakdown_mm" in result
    evidence_text = (tmp_path / "evidence.json").read_text(encoding="utf-8")
    assert "Infinity" not in evidence_text
    assert json.loads(evidence_text)["freq_breakdown_mm"] is None
    assert (tmp_path / "evidence.json").exists()
    assert (tmp_path / "robustness.csv").exists()
    assert (tmp_path / "robustness.png").exists()
    assert (tmp_path / "roundtrip.png").exists()
