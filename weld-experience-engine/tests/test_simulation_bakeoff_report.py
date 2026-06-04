import json
from pathlib import Path

from weldcore.report.simulation_bakeoff_report import main, run_simulation_bakeoff_report


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_simulation_bakeoff_report_writes_runtime_outputs(tmp_path: Path):
    evidence = run_simulation_bakeoff_report(outdir=tmp_path / "out", docs_report_dir=None)

    outdir = tmp_path / "out"
    assert (outdir / "tasks.json").exists()
    assert (outdir / "evidence_bundles.json").exists()
    assert (outdir / "scorecard.json").exists()
    assert (outdir / "report.md").exists()
    assert evidence["scorecard"]["final_simulator_selected"] is False
    assert evidence["rerun_replay"]["attempted"] is True
    assert evidence["rerun_replay"]["status"] in {"logged", "skipped"}
    if evidence["rerun_replay"]["status"] == "logged":
        assert evidence["rerun_replay"]["uri"]
    if evidence["rerun_replay"]["status"] == "skipped":
        assert evidence["rerun_replay"]["skip_reason"]

    tasks = _read_json(outdir / "tasks.json")
    assert {task["task_id"] for task in tasks} == {
        "task-long-straight-horizontal-tracking",
        "task-corner-horizontal-transition",
    }

    markdown = (outdir / "report.md").read_text(encoding="utf-8")
    assert "WeldSkillUnit Simulation Bake-off Evidence" in markdown
    assert "ManiSkill/SAPIEN" in markdown
    assert "Gazebo/MoveIt" in markdown
    assert "不是最终仿真器选择" in markdown
    assert "Rerun" in markdown
    assert "rerun_replay_status" in markdown or "Rerun replay status" in markdown


def test_simulation_bakeoff_report_can_write_docs_copy(tmp_path: Path):
    docs_dir = tmp_path / "docs"

    run_simulation_bakeoff_report(outdir=tmp_path / "out", docs_report_dir=docs_dir)

    assert (docs_dir / "simulation_bakeoff_evidence.md").exists()


def test_simulation_bakeoff_report_cli_no_docs_copy(tmp_path: Path):
    outdir = tmp_path / "cli-out"
    docs_dir = tmp_path / "cli-docs"

    main(["--outdir", str(outdir), "--docs-report-dir", str(docs_dir), "--no-docs-copy"])

    assert (outdir / "report.md").exists()
    assert not (docs_dir / "simulation_bakeoff_evidence.md").exists()
