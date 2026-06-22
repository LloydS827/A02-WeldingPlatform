# A02 Demo Evidence Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 `weldcore.skill_asset.demo_report`，用 2 个默认仿真任务生成可复跑的焊接技能资产可用性证据包，并更新 README/details/HTML 文档。

**Architecture:** 保持 `ManipulationSkillAsset` 和现有 strategic alignment builders 为核心，不新增业务平台或真实数据 connector。`demo_report` 是一个聚合型 CLI：每个任务写出 12 份 canonical artifact 原始文件名，加 1 份额外 `simulation_evidence_bundle.json`，顶层生成 `demo_summary.md/json/html`。`asset_report` 保持单任务 canonical 报告职责。

**Tech Stack:** Python dataclasses/typed dict style payloads, existing `weldcore.skill_asset` builders, existing `weldcore.simulation_bakeoff` simlite reference, pytest, Markdown/HTML generated docs.

---

## File Map

- Create `weld-experience-engine/weldcore/skill_asset/demo_report.py`
  - CLI and library entry point for the demo evidence pack.
  - Builds per-task evidence chain by reusing existing builders.
  - Writes JSON artifacts, `demo_summary.json`, `demo_summary.md`, `demo_summary.html`.
- Create `weld-experience-engine/tests/test_skill_asset_demo_report.py`
  - TDD coverage for file set, summary schema, readiness boundaries, CLI output.
- Modify `README.md`
  - Add demo evidence pack command, artifact list, and boundary.
- Modify `details.md`
  - Add 2026-06-22 stage update for Demo Evidence Pack and next-stage recommendation.
- Modify `weld-experience-engine/README.md`
  - Add engine-level demo command and explain relationship to `asset_report`.
- Modify `docs/architecture/module-boundaries.md`
  - Fix outdated core-object statement: `ManipulationSkillAsset` is canonical; `WeldSkillPackage` is historical compatibility/facade.
- Modify `README.html`, `details.html`
  - Regenerate from Markdown using the repo's current lightweight renderer.

Canonical per-task artifact filenames must be exactly:

```text
skill_asset_report.json
robot_body_asset_report.json
robot_context_spec.json
scene_context_asset_report.json
skill_transfer_assessment.json
robot_feasibility_result.json
skill_asset_evidence_writeback_summary.json
skill_asset_evidence_source_catalog.json
a01_b06_skill_asset_mapping.json
expert_review_record.json
a02_to_a01_product_validation_handoff.json
ip_disclosure_support_matrix.json
```

Additional demo source artifact:

```text
simulation_evidence_bundle.json
```

---

### Task 1: Demo Report Tests

**Files:**
- Create: `weld-experience-engine/tests/test_skill_asset_demo_report.py`

- [ ] **Step 1: Write failing tests for full artifact set and summary schema**

Create `weld-experience-engine/tests/test_skill_asset_demo_report.py`:

```python
import json

from weldcore.skill_asset.demo_report import (
    CANONICAL_TASK_ARTIFACTS,
    EXTRA_TASK_ARTIFACTS,
    run_demo_evidence_pack,
)


REQUIRED_NOT_EXECUTION_GAPS = {
    "real_tcp_calibration",
    "workpiece_frame_measurement",
    "robot_model_identity",
    "joint_limits_source",
    "full_ik_solver",
    "real_collision_validation",
    "real_robot_execution_log",
    "real_welding_quality_feedback",
}


def test_demo_evidence_pack_writes_summary_and_per_task_artifacts(tmp_path):
    payload = run_demo_evidence_pack(tmp_path)

    assert payload["demo_id"] == "a02-demo-evidence-pack"
    assert payload["overall_status"] == "ready_for_expert_review_candidate_pack"
    assert payload["task_count"] == 2
    assert "ready_for_expert_review" in payload["readiness_boundary"]
    assert "not_ready_for_robot_execution" in payload["readiness_boundary"]
    assert "simulation_only" in payload["readiness_boundary"]

    for filename in ("demo_summary.md", "demo_summary.json", "demo_summary.html"):
        assert (tmp_path / filename).exists()
        assert filename in payload["generated_artifacts"]

    expected_task_files = set(CANONICAL_TASK_ARTIFACTS) | set(EXTRA_TASK_ARTIFACTS)
    for task in payload["tasks"]:
        task_dir = tmp_path / task["task_id"]
        assert task_dir.exists()
        assert set(task["artifact_refs"]) == expected_task_files
        for filename in expected_task_files:
            rel_path = f"{task['task_id']}/{filename}"
            assert task["artifact_refs"][filename] == rel_path
            assert rel_path in payload["generated_artifacts"]
            assert (tmp_path / rel_path).exists()
        assert task["transfer_status"] == "ready_for_expert_review"
        assert task["expert_review_status"] == "pending_expert_review"
        assert task["feasibility_status"] == "passed"
        assert task["source_type"] == "simulation_only"
        assert "not_ready_for_robot_execution" in task["boundary_reasons"]
        gap_text = " ".join(task["why_not_ready_for_robot_execution"])
        assert all(gap in gap_text for gap in REQUIRED_NOT_EXECUTION_GAPS)

    generated_files = sorted(
        str(path.relative_to(tmp_path))
        for path in tmp_path.rglob("*")
        if path.is_file()
    )
    assert sorted(payload["generated_artifacts"]) == generated_files


def test_demo_summary_explains_a01_and_ip_support(tmp_path):
    payload = run_demo_evidence_pack(tmp_path)

    assert "intent" in payload["field_explanation"]
    assert "motion" in payload["field_explanation"]
    assert "SimulationEvidenceBundle" in payload["simulation_evidence_explanation"]
    assert "trajectory_candidate" in payload["a02_to_a01_handoff_summary"]["candidate_outputs"]
    assert "not_ready_for_robot_execution" in payload["a02_to_a01_handoff_summary"]["handoff_boundary"]
    assert {item["patent_item_id"] for item in payload["ip_support_summary"]} == {
        "P0-02",
        "P0-03",
        "P0-04",
    }

    md = (tmp_path / "demo_summary.md").read_text(encoding="utf-8")
    html = (tmp_path / "demo_summary.html").read_text(encoding="utf-8")
    assert "ready_for_expert_review" in md
    assert "not_ready_for_robot_execution" in md
    assert "real_tcp_calibration" in md
    assert "real_welding_quality_feedback" in md
    assert "A02 -> A01" in md
    assert "P0-02" in html
    assert "workpiece_frame_measurement" in html
    assert "real_robot_execution_log" in html

    restored = json.loads((tmp_path / "demo_summary.json").read_text(encoding="utf-8"))
    assert restored == payload
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_skill_asset_demo_report.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'weldcore.skill_asset.demo_report'`.

- [ ] **Step 3: Commit failing tests**

```bash
git add weld-experience-engine/tests/test_skill_asset_demo_report.py
git commit -m "test: specify skill asset demo evidence pack"
```

---

### Task 2: Demo Report Implementation

**Files:**
- Create: `weld-experience-engine/weldcore/skill_asset/demo_report.py`
- Test: `weld-experience-engine/tests/test_skill_asset_demo_report.py`

- [ ] **Step 1: Implement `demo_report.py` with existing builders**

Create `weld-experience-engine/weldcore/skill_asset/demo_report.py`.

Implementation requirements:

- Define `CANONICAL_TASK_ARTIFACTS` with the exact 12 filenames from the spec.
- Define `EXTRA_TASK_ARTIFACTS = ("simulation_evidence_bundle.json",)`.
- Use `default_simulation_task_specs()` without adding tasks.
- For each task:
  - `run_simlite_reference(task_spec)`
  - `build_simulation_evidence_bundle(...)`
  - `build_manipulation_skill_asset_from_simulation_bundle(...)`
  - `build_robot_body_asset_from_urdf(...)`
  - `build_robot_context_from_body_asset(...)`
  - `build_default_scene_context_asset(...)`
  - `build_contextual_feasibility_result(...)`
  - `build_default_evidence_writeback_summary(...)`
  - `build_skill_transfer_assessment(...)`
  - strategic alignment builders.
- Write the 12 canonical artifacts with original names.
- Write `simulation_evidence_bundle.json` as an extra demo source artifact.
- Build `demo_summary.json` with the schema in the spec.
- Render `demo_summary.md` and `demo_summary.html`.

Minimal structure:

```python
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from weldcore.robot_process import build_robot_context_from_body_asset
from weldcore.simulation_bakeoff import (
    build_simulation_evidence_bundle,
    default_simulation_task_specs,
    run_simlite_reference,
)

from .assessment import build_skill_transfer_assessment
from .builders import build_manipulation_skill_asset_from_simulation_bundle
from .context import (
    build_contextual_feasibility_result,
    build_default_evidence_writeback_summary,
    build_default_scene_context_asset,
)
from .strategic_alignment import (
    build_a01_b06_skill_asset_mapping,
    build_a02_to_a01_product_validation_handoff,
    build_default_evidence_source_catalog,
    build_default_expert_review_record,
    build_ip_disclosure_support_matrix,
)
from .urdf import build_robot_body_asset_from_urdf


DEFAULT_URDF_PATH = Path(__file__).resolve().parents[3] / "docs" / "real-urdf" / "robot.urdf"
CANONICAL_TASK_ARTIFACTS = (...)
EXTRA_TASK_ARTIFACTS = ("simulation_evidence_bundle.json",)


def run_demo_evidence_pack(outdir: str | Path, urdf_path: str | Path | None = None) -> dict[str, Any]:
    ...


def main(argv: list[str] | None = None) -> dict[str, Any]:
    ...
```

Do not add the module to `__all__` unless needed by tests; tests import the module directly.

- [ ] **Step 2: Run demo report tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_skill_asset_demo_report.py -q
```

Expected: PASS.

- [ ] **Step 3: Run affected report tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_skill_asset_demo_report.py tests/test_skill_asset_report.py tests/test_strategic_skill_asset_alignment.py -q
```

Expected: PASS.

- [ ] **Step 4: Run demo command manually**

Run:

```bash
cd weld-experience-engine
rm -rf artifacts/demo/skill-asset-evidence
uv run python -m weldcore.skill_asset.demo_report --outdir artifacts/demo/skill-asset-evidence >/tmp/a02-demo-evidence-pack.json
```

Expected:

- Command exits 0.
- `artifacts/demo/skill-asset-evidence/demo_summary.md/json/html` exist.
- Two task directories exist.
- Each task directory has 13 JSON files: 12 canonical + `simulation_evidence_bundle.json`.

- [ ] **Step 5: Remove generated demo artifacts from git status if untracked**

Run:

```bash
git status --short
```

Expected: `artifacts/demo/skill-asset-evidence` is either ignored or untracked. Do not commit generated demo output unless already tracked by project convention.

- [ ] **Step 6: Commit implementation**

```bash
git add weld-experience-engine/weldcore/skill_asset/demo_report.py
git commit -m "feat: add skill asset demo evidence pack"
```

---

### Task 3: Documentation Updates

**Files:**
- Modify: `README.md`
- Modify: `details.md`
- Modify: `weld-experience-engine/README.md`
- Modify: `docs/architecture/module-boundaries.md`
- Modify: `README.html`
- Modify: `details.html`

- [ ] **Step 1: Update README and engine README**

In `README.md`, add a new section after “默认技能资产报告” named “默认 demo evidence pack” with:

```bash
cd weld-experience-engine
uv run python -m weldcore.skill_asset.demo_report \
  --outdir artifacts/demo/skill-asset-evidence
```

Explain:

- It runs 2 default simulation tasks.
- Each task outputs 12 canonical artifact JSON plus `simulation_evidence_bundle.json`.
- Top-level outputs are `demo_summary.md/json/html`.
- It is `ready_for_expert_review` evidence, not `ready_for_robot_execution`.

In `weld-experience-engine/README.md`, add the same command and clarify that `asset_report` is single-task canonical output while `demo_report` is multi-task explanatory evidence pack.

- [ ] **Step 2: Update details.md**

In `details.md`, add a new 2026-06-22 bullet group above the existing same-date entries or as a new subsection:

- Added A02 Demo Evidence Pack.
- Default command and output directory.
- Two default tasks.
- Explanation report for non-R&D readers.
- Boundary remains not robot executable.
- Next stage should use real or desensitized calibration/workcell evidence.

Also update “当前一句话状态”, “已完成能力”, “尚未完成”, “下一步建议”, and “当前可交付物清单” only where directly necessary.

- [ ] **Step 3: Update architecture module boundary**

In `docs/architecture/module-boundaries.md`, replace:

```markdown
`WeldSkillPackage` 是项目核心对象。
```

with:

```markdown
`ManipulationSkillAsset` 是当前 canonical 技能资产本体。`WeldSkillPackage` 保留为历史兼容 / facade，不再作为默认主线核心对象。
```

Update the table row for `weldcore.transfer` if needed, but do not rewrite unrelated architecture docs.

- [ ] **Step 4: Regenerate root HTML reading copies**

Run from repository root:

```bash
python - <<'PY'
from __future__ import annotations

import html
import re
from pathlib import Path

STYLE_RE = re.compile(r"<style>(.*?)</style>", re.S)
STYLE = STYLE_RE.search(Path("README.html").read_text()).group(1)


def inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', escaped)
    return escaped


def markdown_body(markdown: str) -> str:
    lines = markdown.splitlines()
    out: list[str] = []
    paragraph: list[str] = []
    list_open = False
    ordered_open = False
    code_open = False
    code_lines: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            out.append(f"    <p>{inline(' '.join(paragraph))}</p>")
            paragraph = []

    def close_lists() -> None:
        nonlocal list_open, ordered_open
        if list_open:
            out.append("    </ul>")
            list_open = False
        if ordered_open:
            out.append("    </ol>")
            ordered_open = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_paragraph()
            close_lists()
            if code_open:
                out.append(f"    <pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
                code_lines = []
                code_open = False
            else:
                code_open = True
            continue
        if code_open:
            code_lines.append(line)
            continue
        if not stripped:
            flush_paragraph()
            close_lists()
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            close_lists()
            out.append(f"    <h1>{inline(stripped[2:])}</h1>")
        elif stripped.startswith("## "):
            flush_paragraph()
            close_lists()
            out.append(f"    <h2>{inline(stripped[3:])}</h2>")
        elif stripped.startswith("### "):
            flush_paragraph()
            close_lists()
            out.append(f"    <h3>{inline(stripped[4:])}</h3>")
        elif stripped.startswith("- "):
            flush_paragraph()
            if ordered_open:
                out.append("    </ol>")
                ordered_open = False
            if not list_open:
                out.append("    <ul>")
                list_open = True
            out.append(f"      <li>{inline(stripped[2:])}</li>")
        elif re.match(r"^\d+\. ", stripped):
            flush_paragraph()
            if list_open:
                out.append("    </ul>")
                list_open = False
            if not ordered_open:
                out.append("    <ol>")
                ordered_open = True
            out.append(f"      <li>{inline(re.sub(r'^\d+\. ', '', stripped))}</li>")
        else:
            paragraph.append(stripped)
    flush_paragraph()
    close_lists()
    return "\n".join(out)


def render(source: str, target: str, title: str) -> None:
    body = markdown_body(Path(source).read_text())
    Path(target).write_text(
        f"""<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{html.escape(title)}</title>
  <style>{STYLE}</style>
</head>
<body>
  <main>
    <div class=\"meta\">HTML 阅读版；维护源：<a href=\"{source}\">{source}</a></div>
{body}
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )


render("README.md", "README.html", "A02 机器人技能大师焊接技能资产底座")
render("details.md", "details.html", "A02 项目进展记录")
PY
```

- [ ] **Step 5: Run documentation checks**

Run:

```bash
rg -n "demo_report|skill-asset-evidence|Demo Evidence Pack|ready_for_expert_review|not_ready_for_robot_execution|ManipulationSkillAsset|WeldSkillPackage" README.md details.md weld-experience-engine/README.md docs/architecture/module-boundaries.md README.html details.html
```

Expected:

- Demo command appears in README, details, engine README, README.html, details.html.
- Architecture doc says `ManipulationSkillAsset` is canonical and `WeldSkillPackage` is historical compatibility/facade.
- Boundaries still mention `not_ready_for_robot_execution`.

- [ ] **Step 6: Commit docs**

```bash
git add README.md details.md weld-experience-engine/README.md docs/architecture/module-boundaries.md README.html details.html
git commit -m "docs: document A02 demo evidence pack"
```

---

### Task 4: Final Verification

**Files:**
- Read: all changed files

- [ ] **Step 1: Run targeted tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_skill_asset_demo_report.py tests/test_skill_asset_report.py tests/test_strategic_skill_asset_alignment.py -q
```

Expected: PASS.

- [ ] **Step 2: Run full test suite**

Run:

```bash
cd weld-experience-engine
uv run pytest -q
```

Expected: PASS.

- [ ] **Step 3: Run demo command once**

Run:

```bash
cd weld-experience-engine
rm -rf artifacts/demo/skill-asset-evidence
uv run python -m weldcore.skill_asset.demo_report --outdir artifacts/demo/skill-asset-evidence >/tmp/a02-demo-evidence-pack-final.json
```

Expected: command exits 0 and writes top-level summary plus two task directories.

- [ ] **Step 4: Inspect final git status**

Run:

```bash
git status --short --branch
```

Expected: only intended source/doc changes are tracked or staged; generated artifacts are not committed.

- [ ] **Step 5: Commit verification-only fixes if needed**

If final verification requires small fixes, commit them with a focused message:

```bash
git add <changed-files>
git commit -m "fix: stabilize A02 demo evidence pack"
```

If no fixes are needed, do not create an empty commit.

---

### Task 5: PR, Merge, and Cleanup

**Files:**
- No source edits expected.

- [ ] **Step 1: Push branch**

Run:

```bash
git push -u origin codex/a02-demo-evidence-pack
```

Expected: push succeeds.

- [ ] **Step 2: Create PR**

Use `gh` if available:

```bash
gh pr create --title "Add A02 demo evidence pack" --body "$(cat <<'EOF'
## Summary
- add a reusable `weldcore.skill_asset.demo_report` evidence pack command
- generate two simulation-backed task evidence chains plus explanatory markdown/json/html summaries
- document the demo entrypoint and refresh project status docs

## Verification
- `uv run pytest tests/test_skill_asset_demo_report.py tests/test_skill_asset_report.py tests/test_strategic_skill_asset_alignment.py -q`
- `uv run pytest -q`
- `uv run python -m weldcore.skill_asset.demo_report --outdir artifacts/demo/skill-asset-evidence`
EOF
)"
```

Expected: PR URL returned.

- [ ] **Step 3: Merge PR remotely**

If checks pass and repository permissions allow:

```bash
gh pr merge --merge --delete-branch
```

Expected: PR merged and remote branch deleted.

If merge is blocked by checks or permissions, report the blocker instead of forcing.

- [ ] **Step 4: Clean local branch and worktree**

From the main repository root, after merge:

```bash
git fetch origin
git switch main
git pull --ff-only origin main
git worktree remove .worktrees/a02-demo-evidence-pack
git branch -d codex/a02-demo-evidence-pack
```

Expected: local worktree removed and local branch deleted.

- [ ] **Step 5: Mark goal complete with final summary**

Summarize:

- Project context learned.
- Spec and plan locations.
- Implemented demo evidence pack.
- Verification results.
- PR URL and merge status.
- Next-stage recommendation: real/desensitized calibration and H300 evidence replacement, expert review closure, heavier robot adapter counter-evidence.
