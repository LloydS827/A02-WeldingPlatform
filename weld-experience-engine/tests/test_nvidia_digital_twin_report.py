from weldcore.skill_asset.demo_report import run_demo_evidence_pack
from weldcore.skill_asset.nvidia_digital_twin import build_nvidia_digital_twin_payloads
from weldcore.skill_asset.procedure_contract import (
    build_weld_procedure_knowledge_contract,
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
    assert "not_ready_for_robot_execution" in package["readiness_boundary"]

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
        assert task_payload["canonical_artifact_refs"] == task["artifact_refs"]
