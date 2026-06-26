import json

import pytest


EXPECTED_TOP_LEVEL = {
    "nv01_c_mj01_summary.md",
    "nv01_c_mj01_summary.json",
    "isaac_runtime_validation_input_manifest.json",
    "mujoco_lightweight_replay_feasibility_report.json",
    "runtime_replay_blocking_report.json",
    "readiness_reproducibility_manifest.json",
}

EXPECTED_TASK = {
    "isaac_runtime_task_validation_input.json",
    "mujoco_task_replay_feasibility.json",
    "runtime_replay_task_blocking_report.json",
}


def _relative_files(root):
    return sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())


def test_readiness_report_writes_default_artifacts(tmp_path):
    from weldcore.skill_asset.nv01_c_mj01_readiness_report import (
        run_nv01_c_mj01_readiness_report,
    )

    outdir = tmp_path / "readiness"
    summary = run_nv01_c_mj01_readiness_report(outdir=outdir)

    assert summary["report_id"] == "nv01-c-mj01-runtime-replay-readiness-pack"
    assert summary["overall_status"] == "blocked_for_runtime_replay_validation"
    assert summary["source_nv01b"]["source_mode"] == "generated_default"
    assert summary["isaac_status"] == "blocked_by_missing_isaac_runtime"
    assert summary["mujoco_status"] == "blocked_by_missing_mujoco_runtime"
    assert "not_isaac_sim_runtime_validation" in summary["readiness_boundary"]
    assert "not_mujoco_dynamics_validation" in summary["readiness_boundary"]
    assert "not_formal_WPS_PQR" in summary["readiness_boundary"]
    assert "not_ready_for_robot_execution" in summary["readiness_boundary"]
    assert sorted(summary["generated_artifacts"]) == _relative_files(outdir)

    for filename in EXPECTED_TOP_LEVEL:
        assert (outdir / filename).exists()

    for task in summary["tasks"]:
        task_dir = outdir / task["task_output_dir"]
        for filename in EXPECTED_TASK:
            assert (task_dir / filename).exists()

    markdown = (outdir / "nv01_c_mj01_summary.md").read_text(encoding="utf-8")
    assert "不是 Isaac Sim runtime 验证" in markdown
    assert "不是 MuJoCo dynamics validation" in markdown
    assert "不是 policy training 结果" in markdown
    assert "不是正式 WPS/PQR" in markdown
    assert "不是 ready_for_robot_execution" in markdown


def test_readiness_report_explicit_missing_source_fails(tmp_path):
    from weldcore.skill_asset.nv01_c_mj01_readiness import MissingNV01BArtifactError
    from weldcore.skill_asset.nv01_c_mj01_readiness_report import (
        run_nv01_c_mj01_readiness_report,
    )

    with pytest.raises(MissingNV01BArtifactError, match="missing_source_nv01b_dir"):
        run_nv01_c_mj01_readiness_report(
            outdir=tmp_path / "out",
            source_nv01b_dir=tmp_path / "missing",
        )


def test_readiness_report_explicit_source_uses_stable_refs(tmp_path):
    from weldcore.skill_asset.nv01_b_experiment_base_report import (
        run_nv01_b_experiment_base_report,
    )
    from weldcore.skill_asset.nv01_c_mj01_readiness_report import (
        run_nv01_c_mj01_readiness_report,
    )

    source = tmp_path / "source"
    outdir = tmp_path / "out"
    run_nv01_b_experiment_base_report(outdir=source)

    summary = run_nv01_c_mj01_readiness_report(
        outdir=outdir,
        source_nv01b_dir=source,
    )
    manifest = json.loads(
        (outdir / "readiness_reproducibility_manifest.json").read_text(
            encoding="utf-8"
        )
    )

    assert summary["source_nv01b"]["source_mode"] == "external_source_nv01b"
    assert summary["source_nv01b"]["source_nv01b_root_ref"] == "<source-nv01b-dir>"
    assert not any(path.startswith("_source_nv01b/") for path in summary["generated_artifacts"])
    assert manifest["source_nv01b_root_ref"] == "<source-nv01b-dir>"
    assert "--source-nv01b-dir <source-nv01b-dir>" in manifest["command"]

    serialized = json.dumps({"summary": summary, "manifest": manifest}, ensure_ascii=False)
    assert str(source) not in serialized
    assert str(tmp_path) not in serialized


def test_readiness_report_main_prints_json(tmp_path, capsys):
    from weldcore.skill_asset import nv01_c_mj01_readiness_report

    nv01_c_mj01_readiness_report.main(["--outdir", str(tmp_path)])

    output = json.loads(capsys.readouterr().out)
    assert output["overall_status"] == "blocked_for_runtime_replay_validation"
