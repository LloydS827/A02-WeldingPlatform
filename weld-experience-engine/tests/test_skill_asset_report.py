import json

from weldcore.skill_asset.asset_report import run_skill_asset_report


def test_skill_asset_report_writes_three_artifacts(tmp_path):
    payload = run_skill_asset_report(tmp_path)

    assert payload["skill_asset"]["domain"] == "welding"
    assert payload["robot_body_asset"]["validation_status"] == "usable_as_robot_body_context"
    assert payload["transfer_assessment"]["status"] == "ready_for_contextual_precheck"
    assert (tmp_path / "skill_asset_report.json").exists()
    assert (tmp_path / "robot_body_asset_report.json").exists()
    assert (tmp_path / "skill_transfer_assessment.json").exists()
    restored = json.loads((tmp_path / "skill_transfer_assessment.json").read_text())
    assert restored["status"] == "ready_for_contextual_precheck"


def test_skill_asset_report_main_prints_json(tmp_path, capsys):
    from weldcore.skill_asset import asset_report

    asset_report.main(["--outdir", str(tmp_path)])

    output = json.loads(capsys.readouterr().out)
    assert output["transfer_assessment"]["status"] == "ready_for_contextual_precheck"
