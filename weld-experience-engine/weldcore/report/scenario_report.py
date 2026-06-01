from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from ..knowledge.scenario import ScenarioGateResult, scenario_from_task_family
from ..knowledge.seeds import load_seed_knowledge_base, load_seed_task_families
from ..knowledge.shipbuilding import (
    rank_task_families,
    score_task_family,
    select_first_batch_candidates,
    validate_task_family_support,
)


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_scenario_report(
    outdir: str | Path = "scenario_report_out",
    knowledge_base=None,
    task_families=None,
) -> dict[str, Any]:
    outpath = Path(outdir)
    outpath.mkdir(parents=True, exist_ok=True)

    kb = knowledge_base or load_seed_knowledge_base()
    families = task_families or load_seed_task_families()

    kb_issues = kb.validation_issues()
    if kb_issues:
        raise ValueError("Knowledge base gate failed: " + "; ".join(kb_issues))

    family_gate_results = [validate_task_family_support(family, kb) for family in families]
    task_gate_failures = [result for result in family_gate_results if not result.passed]
    if task_gate_failures:
        message = "; ".join(
            f"{result.family_id}: {', '.join(result.issues)}" for result in task_gate_failures
        )
        raise ValueError("Task family gate failed: " + message)

    ranked = rank_task_families(families, kb)
    selected = select_first_batch_candidates(families, kb, limit=3)
    scenarios = [scenario_from_task_family(family) for family in selected]
    scenario_gates = [
        ScenarioGateResult.from_scenario(scenario, require_candidate=True)
        for scenario in scenarios
    ]
    failed_scenarios = [gate for gate in scenario_gates if not gate.passed]
    if failed_scenarios:
        message = "; ".join(
            f"{gate.scenario_id}: {', '.join(gate.issues)}" for gate in failed_scenarios
        )
        raise ValueError("Scenario gate failed: " + message)

    coverage = kb.field_coverage()
    evidence = {
        "sources": kb.to_dict(),
        "field_coverage": coverage.to_dict(),
        "task_families": [family.to_dict() for family in ranked],
        "task_scores": [score_task_family(family, kb).to_dict() for family in ranked],
        "task_gates": [result.to_dict() for result in family_gate_results],
        "scenarios": [scenario.to_dict() for scenario in scenarios],
        "scenario_gates": [gate.__dict__ for gate in scenario_gates],
    }

    _write_json(outpath / "sources.json", evidence["sources"])
    _write_json(outpath / "task_families.json", evidence["task_families"])
    _write_json(outpath / "scenarios.json", evidence["scenarios"])

    with (outpath / "field_coverage.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["source_count", "covered_fields", "missing_fields"])
        writer.writerow(
            [
                coverage.source_count,
                ";".join(coverage.covered_fields),
                ";".join(coverage.missing_fields),
            ]
        )

    lines = [
        "# 仿真优先船舶焊接场景证据报告",
        "",
        "## 边界",
        "",
        "- 本报告用于选择仿真场景和字段约束，不等于真实焊接质量验证。",
        "- 公开资料是 public_constraint，不是 validation。",
        "- 熔池图像、熔池形态、熔池控制和焊中闭环不纳入本阶段。",
        "",
        "## 第一批候选场景",
        "",
    ]
    for scenario in scenarios:
        lines.extend(
            [
                f"### {scenario.scenario_id}",
                "",
                f"- 船舶任务：{scenario.shipbuilding_task}",
                f"- 船舶制造环节：{scenario.shipbuilding_context}",
                f"- 难度：{scenario.difficulty}",
                f"- 来源：{', '.join(scenario.source_refs)}",
                f"- 证据角色：{', '.join(role.value for role in scenario.evidence_roles)}",
                "",
            ]
        )
    (outpath / "evidence.md").write_text("\n".join(lines), encoding="utf-8")

    try:
        _write_priority_plot(outpath / "task_priority.png", ranked, kb)
    except Exception:
        pass

    print("=== 仿真优先船舶焊接场景证据摘要 ===")
    print(f"公开来源: {len(kb.sources)}")
    print(f"候选场景: {len(scenarios)}")
    print(f"报告目录: {outpath}")
    return evidence


def _write_priority_plot(path: Path, families, kb) -> None:
    import matplotlib.pyplot as plt

    scores = [score_task_family(family, kb).score for family in families]
    labels = [family.family_id for family in families]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.barh(labels, scores)
    ax.invert_yaxis()
    ax.set_xlabel("priority score")
    ax.set_title("Shipbuilding welding task family priority")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    run_scenario_report()
