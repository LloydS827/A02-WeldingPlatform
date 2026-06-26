import json


EXPECTED_TOP_LEVEL = {
    "mj01_a_summary.md",
    "mj01_a_summary.json",
    "mj01_mujoco_runtime_probe_report.json",
    "mj01_mujoco_model_input_resolution_report.json",
    "mj01_mujoco_probe_report.json",
    "nv01_c0_isaac_remote_preflight_report.json",
    "mj01_a_reproducibility_manifest.json",
}

EXPECTED_TASK = {
    "mj01_task_trajectory_dry_run_input.json",
    "nv01_c0_task_isaac_remote_preflight_input.json",
}


def _relative_files(root):
    return sorted(
        str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()
    )


def _patch_missing_mujoco(monkeypatch):
    import importlib

    original_import_module = importlib.import_module

    def fake_import_module(name, package=None):
        if name == "mujoco":
            raise ModuleNotFoundError(name)
        return original_import_module(name, package)

    monkeypatch.setattr("importlib.import_module", fake_import_module)


def _assert_no_absolute_path_leaks(outdir, *paths):
    serialized_outputs = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in outdir.rglob("*")
        if path.is_file()
    )
    for path in paths:
        assert str(path) not in serialized_outputs


def _managed_report_text(outdir):
    return "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in outdir.rglob("*")
        if path.is_file()
        and "_source_readiness" not in path.relative_to(outdir).parts
    )


def test_report_writes_default_artifacts_without_mujoco(tmp_path, monkeypatch):
    from weldcore.skill_asset.mj01_mujoco_probe_report import (
        run_mj01_mujoco_probe_report,
    )

    _patch_missing_mujoco(monkeypatch)
    outdir = tmp_path / "out"

    summary = run_mj01_mujoco_probe_report(outdir=outdir)

    assert summary["report_id"] == "mj01-a-local-mujoco-probe-nv01-c0-preflight"
    assert summary["overall_status"] == "blocked_for_runtime_probe_or_preflight"
    assert summary["source_readiness"]["source_mode"] == "generated_default"
    assert summary["source_readiness"]["source_readiness_root_ref"] == (
        "_source_readiness"
    )
    assert summary["mujoco_runtime_status"] == "skipped_by_missing_mujoco_runtime"
    assert summary["mujoco_probe_status"] == "skipped_by_missing_mujoco_runtime"
    assert summary["isaac_remote_preflight_status"] == (
        "blocked_by_missing_remote_isaac_runtime"
    )
    assert "not_mujoco_dynamics_validation" in summary["readiness_boundary"]
    assert "not_isaac_sim_runtime_validation" in summary["readiness_boundary"]
    assert "not_policy_training_result" in summary["readiness_boundary"]
    assert "not_formal_WPS_PQR" in summary["readiness_boundary"]
    assert "not_ready_for_robot_execution" in summary["readiness_boundary"]
    assert (outdir / "_source_readiness").is_dir()
    assert sorted(summary["generated_artifacts"]) == _relative_files(outdir)
    assert _source_urdf_from_default_output(outdir).startswith("/")

    for filename in EXPECTED_TOP_LEVEL:
        assert (outdir / filename).exists()

    for task in summary["tasks"]:
        task_dir = outdir / task["task_output_dir"]
        for filename in EXPECTED_TASK:
            assert (task_dir / filename).exists()

    runtime = json.loads(
        (outdir / "mj01_mujoco_runtime_probe_report.json").read_text(
            encoding="utf-8"
        )
    )
    model = json.loads(
        (outdir / "mj01_mujoco_model_input_resolution_report.json").read_text(
            encoding="utf-8"
        )
    )
    probe = json.loads(
        (outdir / "mj01_mujoco_probe_report.json").read_text(encoding="utf-8")
    )
    isaac = json.loads(
        (outdir / "nv01_c0_isaac_remote_preflight_report.json").read_text(
            encoding="utf-8"
        )
    )
    manifest = json.loads(
        (outdir / "mj01_a_reproducibility_manifest.json").read_text(
            encoding="utf-8"
        )
    )

    assert runtime["report_id"] == "mj01-a-mujoco-runtime-probe"
    assert runtime["runtime_probe_status"] == "skipped_by_missing_mujoco_runtime"
    assert model["report_id"] == "mj01-a-mujoco-model-input-resolution"
    assert model["source_readiness_ref"] == "nv01_c_mj01_summary.json"
    assert model["source_urdf_ref"] == "robot_body_asset_report.source_urdf"
    assert probe["report_id"] == "mj01-a-mujoco-probe"
    assert probe["trajectory_dry_run_status"] == "dry_run_inputs_prepared"
    assert isaac["report_id"] == "nv01-c0-isaac-remote-preflight"
    assert isaac["runtime_location"] == "remote_or_server_required"
    assert manifest["report_cli_status"] == "implemented"
    assert "mj01_mujoco_probe_report.py" in manifest["builder"]

    markdown = (outdir / "mj01_a_summary.md").read_text(encoding="utf-8")
    assert "不是 MuJoCo 动力学验证" in markdown
    assert "不是 Isaac runtime 验证" in markdown
    assert "不是策略训练" in markdown
    assert "不是正式 WPS/PQR" in markdown
    assert "不可直接机器人执行" in markdown

    source_urdf = _source_urdf_from_default_output(outdir)
    _assert_no_absolute_path_leaks(outdir, tmp_path)
    serialized_outputs = _managed_report_text(outdir)
    if source_urdf.startswith("/"):
        assert source_urdf not in serialized_outputs
    assert "/Users/" not in serialized_outputs


def test_report_reuses_source_readiness_dir_with_stable_refs(tmp_path, monkeypatch):
    from weldcore.skill_asset.mj01_mujoco_probe_report import (
        run_mj01_mujoco_probe_report,
    )
    from weldcore.skill_asset.nv01_c_mj01_readiness_report import (
        run_nv01_c_mj01_readiness_report,
    )

    _patch_missing_mujoco(monkeypatch)
    source_readiness = tmp_path / "source_readiness"
    outdir = tmp_path / "out"
    run_nv01_c_mj01_readiness_report(outdir=source_readiness)
    source_before = {
        str(path.relative_to(source_readiness)): path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
        for path in source_readiness.rglob("*")
        if path.is_file()
    }

    summary = run_mj01_mujoco_probe_report(
        outdir=outdir,
        source_readiness_dir=source_readiness,
    )
    manifest = json.loads(
        (outdir / "mj01_a_reproducibility_manifest.json").read_text(
            encoding="utf-8"
        )
    )

    assert summary["source_readiness"]["source_mode"] == "external_source_readiness"
    assert summary["source_readiness"]["source_readiness_root_ref"] == (
        "<source-readiness-dir>"
    )
    assert not any(
        path.startswith("_source_readiness/")
        for path in summary["generated_artifacts"]
    )
    assert manifest["source_readiness_root_ref"] == "<source-readiness-dir>"
    assert "--source-readiness-dir <source-readiness-dir>" in manifest["command"]
    assert not (outdir / "_source_readiness").exists()

    for task in summary["tasks"]:
        for filename in EXPECTED_TASK:
            assert (outdir / task["task_output_dir"] / filename).exists()
        break

    source_urdf = _source_urdf_from_readiness(source_readiness)
    _assert_no_absolute_path_leaks(outdir, tmp_path, source_readiness)
    assert source_urdf not in "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in outdir.rglob("*")
        if path.is_file()
    )
    source_after = {
        str(path.relative_to(source_readiness)): path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
        for path in source_readiness.rglob("*")
        if path.is_file()
    }
    assert source_after == source_before


def test_report_main_prints_json(tmp_path, capsys, monkeypatch):
    from weldcore.skill_asset import mj01_mujoco_probe_report

    _patch_missing_mujoco(monkeypatch)

    mj01_mujoco_probe_report.main(["--outdir", str(tmp_path)])

    output = json.loads(capsys.readouterr().out)
    assert output["mujoco_runtime_status"] == "skipped_by_missing_mujoco_runtime"


def _source_urdf_from_default_output(outdir):
    return _source_urdf_from_readiness(outdir / "_source_readiness")


def _source_urdf_from_readiness(source_readiness):
    feasibility = json.loads(
        (
            source_readiness / "mujoco_lightweight_replay_feasibility_report.json"
        ).read_text(encoding="utf-8")
    )
    report = json.loads(
        (
            source_readiness
            / "_source_nv01b"
            / "_source_nv01a"
            / "_source_demo_evidence"
            / feasibility["urdf_ref"]
        ).read_text(encoding="utf-8")
    )
    return report["source_urdf"]
