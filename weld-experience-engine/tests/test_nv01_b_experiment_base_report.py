import json

import pytest


EXPECTED_TOP_LEVEL = {
    "nv01_b_summary.md",
    "nv01_b_summary.json",
    "openusd_stage.usda",
    "openusd_stage_validation_report.json",
    "isaac_replay_fixture.json",
    "procedure_sim_parameter_audit.json",
    "sensor_annotation_manifest.json",
    "simulation_blocking_report.json",
    "experiment_reproducibility_manifest.json",
}

EXPECTED_TASK = {
    "openusd_task_stage_fragment.usda",
    "isaac_replay_task_fixture.json",
    "procedure_sim_parameter_audit.json",
    "sensor_annotation_manifest.json",
    "simulation_blocking_report.json",
}


def _relative_files(root):
    return sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())


def test_nv01_b_report_writes_default_artifacts(tmp_path):
    from weldcore.skill_asset.nv01_b_experiment_base_report import (
        run_nv01_b_experiment_base_report,
    )

    outdir = tmp_path / "nv01b"
    summary = run_nv01_b_experiment_base_report(outdir=outdir)

    assert summary["report_id"] == "nv01-b-openusd-isaac-reproducible-experiment-base"
    assert summary["overall_status"] == "blocked_for_real_isaac_sim_replay"
    assert summary["openusd_authoring_status"] == "ready_for_static_openusd_review"
    assert summary["source_nv01a"]["source_mode"] == "generated_default"
    assert "not_isaac_sim_runtime_validation" in summary["readiness_boundary"]
    assert "not_formal_WPS_PQR" in summary["readiness_boundary"]
    assert sorted(summary["generated_artifacts"]) == _relative_files(outdir)

    for filename in EXPECTED_TOP_LEVEL:
        assert (outdir / filename).exists()

    for task in summary["tasks"]:
        task_dir = outdir / task["task_output_dir"]
        for filename in EXPECTED_TASK:
            assert (task_dir / filename).exists()

    stage = (outdir / "openusd_stage.usda").read_text(encoding="utf-8")
    assert "#usda 1.0" in stage
    assert 'def Xform "World"' in stage

    markdown = (outdir / "nv01_b_summary.md").read_text(encoding="utf-8")
    assert "不是 Isaac Sim runtime 验证" in markdown
    assert "不是 policy training 结果" in markdown
    assert "不是正式 WPS/PQR" in markdown
    assert "不是 ready_for_robot_execution" in markdown


def test_nv01_b_report_explicit_missing_source_fails(tmp_path):
    from weldcore.skill_asset.nv01_b_experiment_base import MissingNV01AArtifactError
    from weldcore.skill_asset.nv01_b_experiment_base_report import (
        run_nv01_b_experiment_base_report,
    )

    with pytest.raises(MissingNV01AArtifactError, match="missing_source_nv01a_dir"):
        run_nv01_b_experiment_base_report(
            outdir=tmp_path / "out",
            source_nv01a_dir=tmp_path / "missing",
        )


def test_nv01_b_report_explicit_incomplete_source_fails(tmp_path):
    from weldcore.skill_asset.nvidia_digital_twin_report import (
        run_nvidia_digital_twin_report,
    )
    from weldcore.skill_asset.nv01_b_experiment_base import MissingNV01AArtifactError
    from weldcore.skill_asset.nv01_b_experiment_base_report import (
        run_nv01_b_experiment_base_report,
    )

    source = tmp_path / "source"
    run_nvidia_digital_twin_report(outdir=source)
    (source / "isaac_sim_replay_config.json").unlink()

    with pytest.raises(MissingNV01AArtifactError, match="isaac_sim_replay_config.json"):
        run_nv01_b_experiment_base_report(
            outdir=tmp_path / "out",
            source_nv01a_dir=source,
        )


def test_nv01_b_report_excludes_preexisting_user_files(tmp_path):
    from weldcore.skill_asset.nv01_b_experiment_base_report import (
        run_nv01_b_experiment_base_report,
    )

    outdir = tmp_path / "nv01b"
    outdir.mkdir()
    (outdir / "user_note.txt").write_text("keep\n", encoding="utf-8")

    summary = run_nv01_b_experiment_base_report(outdir=outdir)

    assert "user_note.txt" not in summary["generated_artifacts"]
    assert sorted(summary["generated_artifacts"]) == [
        path for path in _relative_files(outdir) if path != "user_note.txt"
    ]


def test_nv01_b_report_main_prints_json(tmp_path, capsys):
    from weldcore.skill_asset import nv01_b_experiment_base_report

    nv01_b_experiment_base_report.main(["--outdir", str(tmp_path)])

    output = json.loads(capsys.readouterr().out)
    assert output["overall_status"] == "blocked_for_real_isaac_sim_replay"
