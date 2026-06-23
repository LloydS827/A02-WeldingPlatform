import json

import pytest

from weldcore.skill_asset.demo_report import run_demo_evidence_pack
from weldcore.skill_asset.nvidia_digital_twin import (
    MissingCanonicalArtifactError,
    build_nvidia_digital_twin_payloads,
    load_demo_pack,
    load_task_artifacts,
)
from weldcore.skill_asset.procedure_contract import (
    build_weld_procedure_knowledge_contract,
)


EXPECTED_TOP_LEVEL_ARTIFACTS = {
    "nv01_summary.md",
    "nv01_summary.json",
    "weld_procedure_knowledge_contract.json",
    "weld_procedure_parameter_set.json",
    "weld_procedure_validation_report.json",
    "procedure_to_nv01_mapping_matrix.json",
    "weld_skill_digital_twin_package.json",
    "openusd_scene_manifest.json",
    "isaac_sim_replay_config.json",
    "domain_randomization_recipe.json",
    "training_readiness_report.json",
    "nvidia_stack_alignment_matrix.json",
}

EXPECTED_TASK_ARTIFACTS = {
    "skill_asset_ref.json",
    "weld_procedure_parameter_set.json",
    "weld_procedure_validation_report.json",
    "openusd_task_manifest.json",
    "isaac_replay_task_config.json",
    "sensor_and_annotation_manifest.json",
    "training_task_readiness.json",
}


def _relative_files(root):
    return sorted(
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file()
    )


def test_nvidia_payloads_bind_procedure_contract_to_canonical_demo(tmp_path):
    source_dir = tmp_path / "source"
    demo = run_demo_evidence_pack(source_dir)
    contract = build_weld_procedure_knowledge_contract()

    payloads = build_nvidia_digital_twin_payloads(source_dir, demo, contract)

    assert set(payloads) == {
        "weld_procedure_parameter_set",
        "weld_procedure_validation_report",
        "procedure_to_nv01_mapping_matrix",
        "weld_skill_digital_twin_package",
        "openusd_scene_manifest",
        "isaac_sim_replay_config",
        "domain_randomization_recipe",
        "training_readiness_report",
        "nvidia_stack_alignment_matrix",
        "task_payloads",
    }

    package = payloads["weld_skill_digital_twin_package"]
    assert package["overall_status"] == "ready_for_simulation_replay_package_design"
    assert package["task_count"] == 2
    assert package["procedure_contract_ref"] == "weld_procedure_knowledge_contract.json"
    assert package["source_demo_pack_ref"] == "demo_summary.json"
    assert "not_ready_for_robot_execution" in package["readiness_boundary"]

    matrix = payloads["procedure_to_nv01_mapping_matrix"]
    assert matrix["procedure_contract_ref"] == "weld_procedure_knowledge_contract.json"
    assert matrix["canonical_artifact_refs_by_task"] == {
        task["task_id"]: task["artifact_refs"] for task in demo["tasks"]
    }

    openusd = payloads["openusd_scene_manifest"]
    assert openusd["root_prim"] == "/World"
    assert "procedure_parameter_bindings" in openusd
    assert openusd["missing_usd_authoring_inputs"]

    isaac = payloads["isaac_sim_replay_config"]
    assert "blocked_by_missing_isaac_runtime" in isaac["not_ready_reasons"]
    assert "procedure_parameter_inputs" in isaac

    recipe = payloads["domain_randomization_recipe"]
    randomization_by_name = {
        item["name"]: item for item in recipe["randomization_items"]
    }
    assert {
        "groove_gap_variation",
        "travel_speed_window",
        "arc_glare_smoke_spatter",
    } <= set(randomization_by_name)
    assert randomization_by_name["groove_gap_variation"][
        "linked_procedure_fields"
    ] == ["root_gap_mm", "groove_angle_deg"]
    assert randomization_by_name["travel_speed_window"][
        "linked_procedure_fields"
    ] == ["travel_speed_mm_per_min"]

    training = payloads["training_readiness_report"]
    assert training["design_review_status"] == "ready_for_training_design_review"
    assert training["training_status"] == "not_ready_for_policy_training"
    assert training["procedure_contract_gates"]
    assert "blocked_by_missing_isaac_runtime" in training["blocked_by"]

    alignment = payloads["nvidia_stack_alignment_matrix"]
    assert "WeldProcedureKnowledgeContract" in alignment["a02_object_mappings"]
    assert "RobotBodyAsset" in alignment["a02_object_mappings"]

    assert set(payloads["task_payloads"]) == {
        task["task_id"] for task in demo["tasks"]
    }
    for task in demo["tasks"]:
        task_payload = payloads["task_payloads"][task["task_id"]]
        assert "weld_procedure_parameter_set" in task_payload
        assert "weld_procedure_validation_report" in task_payload
        assert "openusd_task_manifest" in task_payload
        assert "isaac_replay_task_config" in task_payload
        assert "sensor_and_annotation_manifest" in task_payload
        assert "training_task_readiness" in task_payload
        assert task_payload["canonical_artifact_refs"] == task["artifact_refs"]


def test_load_demo_pack_reads_summary_json(tmp_path):
    demo = run_demo_evidence_pack(tmp_path)

    loaded = load_demo_pack(tmp_path)

    assert loaded == demo


def test_load_task_artifacts_returns_all_referenced_artifacts(tmp_path):
    demo = run_demo_evidence_pack(tmp_path)
    task = demo["tasks"][0]

    artifacts = load_task_artifacts(tmp_path, task)

    assert set(artifacts) == set(task["artifact_refs"])


def test_load_task_artifacts_raises_for_missing_referenced_artifact(tmp_path):
    demo = run_demo_evidence_pack(tmp_path)
    task = demo["tasks"][0]
    missing_ref = task["artifact_refs"]["skill_asset_report.json"]
    (tmp_path / missing_ref).unlink()

    with pytest.raises(MissingCanonicalArtifactError, match="missing_canonical_artifacts"):
        load_task_artifacts(tmp_path, task)


def test_nvidia_report_writes_top_level_and_per_task_artifacts(tmp_path):
    from weldcore.skill_asset.nvidia_digital_twin_report import (
        run_nvidia_digital_twin_report,
    )

    outdir = tmp_path / "nv01"

    summary = run_nvidia_digital_twin_report(outdir=outdir)

    assert summary["report_id"] == "k01-nv01-a-procedure-constrained-manifest-evidence-pack"
    assert summary["task_count"] == 2
    assert summary["overall_status"] == "ready_for_simulation_replay_package_design"
    assert "ready_for_procedure_contract_review" in summary["readiness_states"]
    assert "not_ready_for_policy_training" in summary["readiness_states"]
    assert "not_formal_WPS_PQR" in summary["readiness_boundary"]
    assert sorted(summary["generated_artifacts"]) == _relative_files(outdir)

    for filename in EXPECTED_TOP_LEVEL_ARTIFACTS:
        assert (outdir / filename).exists()

    for task in summary["tasks"]:
        task_dir = outdir / task["task_output_dir"]
        for filename in EXPECTED_TASK_ARTIFACTS:
            assert (task_dir / filename).exists()

    markdown = (outdir / "nv01_summary.md").read_text(encoding="utf-8")
    assert "不是正式 WPS/PQR" in markdown
    assert "不是 ready_for_robot_execution" in markdown
    assert "不是 Isaac Sim runtime 验证" in markdown
    assert "不是 policy training 结果" in markdown

    restored = json.loads((outdir / "nv01_summary.json").read_text(encoding="utf-8"))
    assert restored == summary


def test_nvidia_report_generated_artifacts_exclude_preexisting_files(tmp_path):
    from weldcore.skill_asset.nvidia_digital_twin_report import (
        run_nvidia_digital_twin_report,
    )

    outdir = tmp_path / "nv01"
    outdir.mkdir()
    (outdir / "user_note.txt").write_text("do not claim this as generated\n")

    summary = run_nvidia_digital_twin_report(outdir=outdir)

    assert "user_note.txt" not in summary["generated_artifacts"]
    assert sorted(summary["generated_artifacts"]) == [
        filename for filename in _relative_files(outdir) if filename != "user_note.txt"
    ]


def test_nvidia_report_generated_artifacts_exclude_preexisting_source_files(tmp_path):
    from weldcore.skill_asset.nvidia_digital_twin_report import (
        run_nvidia_digital_twin_report,
    )

    outdir = tmp_path / "nv01"
    source_dir = outdir / "_source_demo_evidence"
    source_dir.mkdir(parents=True)
    user_note = source_dir / "user_note.txt"
    user_note.write_text("keep this user file\n")

    summary = run_nvidia_digital_twin_report(outdir=outdir)

    assert user_note.exists()
    assert "_source_demo_evidence/user_note.txt" not in summary["generated_artifacts"]


def test_nvidia_report_artifacts_keep_boundaries_and_refs(tmp_path):
    from weldcore.skill_asset.nvidia_digital_twin_report import (
        run_nvidia_digital_twin_report,
    )

    outdir = tmp_path / "nv01"

    summary = run_nvidia_digital_twin_report(outdir=outdir)

    package = json.loads(
        (outdir / "weld_skill_digital_twin_package.json").read_text(encoding="utf-8")
    )
    assert package["source_demo_pack_root_ref"] == "_source_demo_evidence"
    assert "source_demo_ref" not in package
    assert package["source_demo_pack_ref"] == "_source_demo_evidence/demo_summary.json"
    assert package["procedure_contract_ref"] == "weld_procedure_knowledge_contract.json"
    assert (
        outdir / package["source_demo_pack_ref"]
    ).exists()
    assert "not_ready_for_robot_execution" in package["readiness_boundary"]
    assert "not_formal_WPS_PQR" in package["readiness_boundary"]

    validation = json.loads(
        (outdir / "weld_procedure_validation_report.json").read_text(encoding="utf-8")
    )
    assert validation["ready_for_simulation_replay_package_design"] is True
    assert validation["ready_for_expert_review"] is False
    assert (
        "blocked_by_missing_human_required_fields"
        in validation["not_ready_reasons"]
    )

    isaac = json.loads(
        (outdir / "isaac_sim_replay_config.json").read_text(encoding="utf-8")
    )
    assert "blocked_by_missing_isaac_runtime" in isaac["not_ready_reasons"]
    assert "ready_for_simulation_replay" not in summary["readiness_states"]

    for task in summary["tasks"]:
        task_dir = outdir / task["task_id"].replace("/", "_")
        for filename in (
            "openusd_task_manifest.json",
            "isaac_replay_task_config.json",
            "sensor_and_annotation_manifest.json",
            "training_task_readiness.json",
        ):
            task_artifact = json.loads(
                (task_dir / filename).read_text(encoding="utf-8")
            )
            assert task_artifact["canonical_artifact_root_ref"] == (
                "_source_demo_evidence"
            )

    markdown = (outdir / "nv01_summary.md").read_text(encoding="utf-8")
    assert "不是正式 WPS/PQR" in markdown
    assert "不是 ready_for_robot_execution" in markdown
    assert "Isaac Sim runtime" in markdown


def test_nvidia_report_main_prints_json(tmp_path, capsys):
    from weldcore.skill_asset import nvidia_digital_twin_report

    nvidia_digital_twin_report.main(["--outdir", str(tmp_path)])

    output = json.loads(capsys.readouterr().out)
    assert output["overall_status"] == "ready_for_simulation_replay_package_design"


def test_existing_source_demo_with_missing_canonical_artifact_fails(tmp_path):
    from weldcore.skill_asset.nvidia_digital_twin_report import (
        run_nvidia_digital_twin_report,
    )

    source_dir = tmp_path / "source"
    demo = run_demo_evidence_pack(source_dir)
    first_task = demo["tasks"][0]
    (source_dir / first_task["artifact_refs"]["skill_asset_report.json"]).unlink()

    with pytest.raises(MissingCanonicalArtifactError, match="missing_canonical_artifacts"):
        run_nvidia_digital_twin_report(
            source_demo_dir=source_dir,
            outdir=tmp_path / "nv01",
        )


def test_missing_explicit_source_demo_dir_generates_default_source(tmp_path):
    from weldcore.skill_asset.nvidia_digital_twin_report import (
        run_nvidia_digital_twin_report,
    )

    missing_source_dir = tmp_path / "missing-source"

    summary = run_nvidia_digital_twin_report(
        source_demo_dir=missing_source_dir,
        outdir=tmp_path / "nv01",
    )

    assert summary["source_demo"]["source_demo_mode"] == (
        "generated_default_for_missing_requested_source"
    )
    assert summary["source_demo"]["requested_source_demo_dir"] == str(missing_source_dir)
    assert "_source_demo_evidence/demo_summary.json" in summary["generated_artifacts"]
