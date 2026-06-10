# 1000 Requested Samples Real Run Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在真实 `weld-maniskill` 环境执行 1000 requested samples next-batch，复跑验证 shard 复用，并把运行事实沉淀为项目证据与入口文档。

**Architecture:** 不修改 accumulation pipeline 核心逻辑；使用已实现的 `maniskill_accumulation_pipeline` CLI 运行 10 shards x 100 requested samples。真实 simulation artifacts 保持 ignored，只提交运行审查 Markdown、README/details 与 HTML 阅读版。

**Tech Stack:** Python CLI、conda `weld-maniskill` 环境、Markdown、简单 HTML 阅读版、pytest、GitHub CLI。

---

## Spec Reference

- Spec: `docs/superpowers/specs/2026-06-10-1000-requested-samples-real-run-review-design.md`
- Worktree: `/Users/lloyd/.config/superpowers/worktrees/A02-焊接技能大师平台/codex-next-batch-1000-run-review`
- Python project root: `/Users/lloyd/.config/superpowers/worktrees/A02-焊接技能大师平台/codex-next-batch-1000-run-review/weld-experience-engine`
- Conda environment: `weld-maniskill`

Critical requirements:

- Run 1000 requested samples in real `weld-maniskill`.
- Rerun the same command without `--force` to verify shard reuse.
- Capture first-run report before rerun overwrites `accumulation_report.json`.
- Do not commit raw simulation artifacts.
- If failures appear, record and prioritize concrete failure boundaries; do not switch simulator or move to real robots.

## File Structure

Create:

- `docs/evidence/simulation-runs/2026-06-10-next-batch-1000-maniskill-sapien-review.md`
  - Tracked review document with run environment, commands, first-run summary, reuse-run summary, field coverage, boundary language, and next-stage recommendation.

Modify:

- `README.md`
  - Update current status from “can execute 1000 next-batch” to “1000 next-batch run review completed” if the run completes; if failures appear, document concrete failure boundaries.
- `details.md`
  - Add 2026-06-10 bullets for 1000 first run, reuse run, field coverage, failure boundaries, and next recommendation.
- `README.html`
  - Refresh from `README.md`.
- `details.html`
  - Refresh from `details.md`.

Do not modify unless a real failure requires a code fix:

- `weld-experience-engine/weldcore/simulation_bakeoff/*.py`
- `weld-experience-engine/tests/*.py`

Do not commit:

- `weld-experience-engine/artifacts/simulation/`
- `weld-experience-engine/uv.lock`
- `weld-experience-engine/weldcore.egg-info/`

---

### Task 1: Preflight And First Real Run

**Files:**
- No tracked file changes expected before the run.
- Ignored artifacts may be created under `weld-experience-engine/artifacts/simulation/`.

- [ ] **Step 1: Verify environment imports**

Run from `weld-experience-engine/`:

```bash
conda run -n weld-maniskill python -c "import mani_skill, sapien, weldcore; print('mani_skill import-ok'); print('sapien import-ok'); print('weldcore import-ok')"
```

Expected:

- Prints all three `import-ok` lines.
- SAPIEN Vulkan fallback or pinocchio warnings are allowed if imports succeed.

- [ ] **Step 2: Confirm `weldcore` points to this worktree**

Run from `weld-experience-engine/`:

```bash
conda run -n weld-maniskill python -c "import pathlib, weldcore; print(pathlib.Path(weldcore.__file__).resolve())"
```

Expected:

- Output path starts with `/Users/lloyd/.config/superpowers/worktrees/A02-焊接技能大师平台/codex-next-batch-1000-run-review/weld-experience-engine/weldcore/`.

If not, run:

```bash
conda run -n weld-maniskill python -m pip install -e .
```

Then repeat the path check.

- [ ] **Step 3: Preflight target artifact directory**

Run from `weld-experience-engine/`:

```bash
test ! -e artifacts/simulation/maniskill-sapien-accumulations/maniskill-sapien-accumulation-next-batch-1000
```

Expected:

- Exit 0: target directory does not exist, so the first run will be a true new run.

If the directory exists:

- Do not delete it silently.
- Inspect it with:

```bash
find artifacts/simulation/maniskill-sapien-accumulations/maniskill-sapien-accumulation-next-batch-1000 -maxdepth 2 -type f | sort | sed -n '1,80p'
```

- Move it aside to an ignored backup path before running:

```bash
mv artifacts/simulation/maniskill-sapien-accumulations/maniskill-sapien-accumulation-next-batch-1000 \
  artifacts/simulation/maniskill-sapien-accumulations/maniskill-sapien-accumulation-next-batch-1000-pre-review-backup-$(date +%Y%m%d%H%M%S)
```

- [ ] **Step 4: Run first 1000 requested samples batch**

Run from `weld-experience-engine/`:

```bash
conda run -n weld-maniskill python -m weldcore.simulation_bakeoff.maniskill_accumulation_pipeline \
  --outdir artifacts/simulation/maniskill-sapien-accumulations \
  --accumulation-id maniskill-sapien-accumulation-next-batch-1000 \
  --shards 10 \
  --samples-per-task 50
```

Expected ideal result:

- `requested_sample_count == 1000`
- `completed_sample_count == 1000`
- `failed_sample_count == 0`
- `skipped_sample_count == 0`
- `status == "ready_to_scale_with_conditions"`
- `completed_shard_count == 10`
- `reused_shard_count == 0`
- all shard reports have `status == "completed_new_run"`

- [ ] **Step 5: Capture first-run report before rerun**

Run from `weld-experience-engine/`:

```bash
python - <<'PY'
import json
from pathlib import Path

path = Path("artifacts/simulation/maniskill-sapien-accumulations/maniskill-sapien-accumulation-next-batch-1000/accumulation_report.json")
report = json.loads(path.read_text(encoding="utf-8"))
summary = {
    "requested_sample_count": report["requested_sample_count"],
    "completed_sample_count": report["completed_sample_count"],
    "failed_sample_count": report["failed_sample_count"],
    "skipped_sample_count": report["skipped_sample_count"],
    "status": report["status"],
    "shard_count": report["shard_count"],
    "completed_shard_count": report["completed_shard_count"],
    "reused_shard_count": report["reused_shard_count"],
    "failed_shard_count": report["failed_shard_count"],
    "shard_statuses": [item["status"] for item in report["shard_reports"]],
    "failure_boundary_counts": report["failure_boundary_counts"],
    "field_coverage_trend": report["field_coverage_trend"],
    "next_scale_recommendation": report["next_scale_recommendation"],
    "known_limitations": report["known_limitations"],
}
print(json.dumps(summary, ensure_ascii=False, indent=2))
Path("artifacts/simulation/maniskill-sapien-accumulations/maniskill-sapien-accumulation-next-batch-1000/first_run_accumulation_report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
PY
```

Expected:

- JSON summary printed.
- `first_run_accumulation_report.json` written as ignored local artifact.
- The printed summary must be copied into the tracked review document in Task 3.

- [ ] **Step 6: Commit nothing**

Do not commit after Task 1. The first-run facts must be combined with reuse-run facts in Task 3.

---

### Task 2: Reuse Rerun And Report Extraction

**Files:**
- No tracked file changes expected before Task 3.

- [ ] **Step 1: Rerun same command without `--force`**

Run from `weld-experience-engine/`:

```bash
conda run -n weld-maniskill python -m weldcore.simulation_bakeoff.maniskill_accumulation_pipeline \
  --outdir artifacts/simulation/maniskill-sapien-accumulations \
  --accumulation-id maniskill-sapien-accumulation-next-batch-1000 \
  --shards 10 \
  --samples-per-task 50
```

Expected ideal result:

- `requested_sample_count == 1000`
- `completed_sample_count == 1000`
- `failed_sample_count == 0`
- `skipped_sample_count == 0`
- `status == "ready_to_scale_with_conditions"`
- `completed_shard_count == 0`
- `reused_shard_count == 10`
- all shard reports have `status == "reused_existing_result"`

- [ ] **Step 2: Extract reuse-run report**

Run from `weld-experience-engine/`:

```bash
python - <<'PY'
import json
from pathlib import Path

path = Path("artifacts/simulation/maniskill-sapien-accumulations/maniskill-sapien-accumulation-next-batch-1000/accumulation_report.json")
report = json.loads(path.read_text(encoding="utf-8"))
summary = {
    "requested_sample_count": report["requested_sample_count"],
    "completed_sample_count": report["completed_sample_count"],
    "failed_sample_count": report["failed_sample_count"],
    "skipped_sample_count": report["skipped_sample_count"],
    "status": report["status"],
    "shard_count": report["shard_count"],
    "completed_shard_count": report["completed_shard_count"],
    "reused_shard_count": report["reused_shard_count"],
    "failed_shard_count": report["failed_shard_count"],
    "shard_statuses": [item["status"] for item in report["shard_reports"]],
    "failure_boundary_counts": report["failure_boundary_counts"],
    "field_coverage_trend": report["field_coverage_trend"],
    "next_scale_recommendation": report["next_scale_recommendation"],
    "known_limitations": report["known_limitations"],
}
print(json.dumps(summary, ensure_ascii=False, indent=2))
PY
```

Expected:

- JSON summary printed.
- The summary must be copied into the tracked review document in Task 3.

- [ ] **Step 3: Inspect dataset index coverage if needed**

Run from `weld-experience-engine/`:

```bash
python - <<'PY'
import json
from pathlib import Path

path = Path("artifacts/simulation/maniskill-sapien-accumulations/maniskill-sapien-accumulation-next-batch-1000/dataset_index.json")
index = json.loads(path.read_text(encoding="utf-8"))
print(json.dumps({
    "requested_sample_count": index["requested_sample_count"],
    "completed_sample_count": index["completed_sample_count"],
    "failed_sample_count": index["failed_sample_count"],
    "skipped_sample_count": index["skipped_sample_count"],
    "failure_boundaries": index["failure_boundaries"],
    "field_coverage_summary": index["field_coverage_summary"],
}, ensure_ascii=False, indent=2))
PY
```

Expected:

- Confirms dataset index counts and coverage.

- [ ] **Step 4: Commit nothing**

Do not commit raw artifacts. Continue to Task 3.

---

### Task 3: Evidence Review Document

**Files:**
- Create: `docs/evidence/simulation-runs/2026-06-10-next-batch-1000-maniskill-sapien-review.md`

- [ ] **Step 1: Write review document**

Create `docs/evidence/simulation-runs/2026-06-10-next-batch-1000-maniskill-sapien-review.md`.

If ideal result holds, use this structure:

```markdown
# 1000 Requested Samples ManiSkill/SAPIEN 真实环境运行审查

日期：2026-06-10

## 结论

1000 requested samples next-batch 已在 `weld-maniskill` conda 环境完成真实 ManiSkill/SAPIEN headless backend probe。首次运行 1000/1000 completed，第二次同命令复跑 10 个 shard 均复用已有 `batch_result.json`。

当前判断是 `ready_to_continue_accumulation_with_conditions`：ManiSkill/SAPIEN 可以继续作为下一阶段 accumulation 默认入口，但这不是最终仿真器选型、真实焊接质量验证或真实机器人执行验证。

## 运行环境

- conda env：`weld-maniskill`
- `mani_skill`：可导入
- `sapien`：可导入
- `weldcore`：当前 worktree editable install
- 默认 `uv` 环境：保持轻量，不内置 ManiSkill/SAPIEN

## 运行命令

```bash
conda run -n weld-maniskill python -m weldcore.simulation_bakeoff.maniskill_accumulation_pipeline \
  --outdir artifacts/simulation/maniskill-sapien-accumulations \
  --accumulation-id maniskill-sapien-accumulation-next-batch-1000 \
  --shards 10 \
  --samples-per-task 50
```

## 首次运行分布

| 指标 | 结果 |
| --- | --- |
| requested samples | 1000 |
| completed samples | 1000 |
| failed samples | 0 |
| skipped samples | 0 |
| shard status | 10 x `completed_new_run` |
| report status | `ready_to_scale_with_conditions` |

## 复用运行分布

| 指标 | 结果 |
| --- | --- |
| requested samples | 1000 |
| completed samples | 1000 |
| failed samples | 0 |
| skipped samples | 0 |
| shard status | 10 x `reused_existing_result` |
| report status | `ready_to_scale_with_conditions` |

## Failure Boundary Counts

`failure_boundary_counts` 为空。

## Field Coverage

10 个 shard 的 completed sample coverage 均为：

| 字段 | 覆盖率 |
| --- | --- |
| `raw_artifact_uri` | 1.0 |
| `adapter_result_uri` | 1.0 |
| `experience_dataset_uri` | 1.0 |
| `evidence_bundle_uri` | 1.0 |
| `failure_artifact_uri` | 0.0 |

`failure_artifact_uri` 为 0.0 是预期结果，因为本轮没有 failed samples。

## Warning 与边界

运行中可能出现 SAPIEN Vulkan fallback 与 pinocchio 缺失 warning；只要没有样本失败或 failure boundary，不把 warning 写成 pipeline failure。

本轮仍只证明 ManiSkill/SAPIEN headless backend probe 和项目数据契约可在 1000 requested samples 级别稳定运行；不证明真实焊接质量，不构成 WPS/PQR，不表示真实机器人可执行，也不表示最终仿真器选型完成。

## 下一步

建议下一阶段进入持续 accumulation 审查层：先建立跨批次 ledger，记录 Phase 1、Phase 2、1000 next-batch 的运行元数据；继续保持当前 2 个默认任务族，观察多批次稳定性后再讨论新增任务族。
```

If failures appear, replace the conclusion and tables with actual observed values, include `failure_boundary_counts`, and write “下一步” as concrete boundary repair.

- [ ] **Step 2: Verify review document**

Run from repository root:

```bash
rg -n "1000 requested|1000/1000|completed_new_run|reused_existing_result|failure_boundary_counts|Field Coverage|最终仿真器|真实焊接质量|真实机器人|WPS/PQR" docs/evidence/simulation-runs/2026-06-10-next-batch-1000-maniskill-sapien-review.md
```

Expected:

- Review document contains run distribution, reuse distribution, field coverage, and boundary language.

- [ ] **Step 3: Commit Task 3**

Run from repository root:

```bash
git add docs/evidence/simulation-runs/2026-06-10-next-batch-1000-maniskill-sapien-review.md
git commit -m "docs: record 1000 sample maniskill run review"
```

---

### Task 4: README And Details Update

**Files:**
- Modify: `README.md`
- Modify: `details.md`

- [ ] **Step 1: Update README**

Update `README.md` so it says:

- 1000 requested samples next-batch has been run in real `weld-maniskill`.
- First run and reuse run distribution.
- `failure_boundary_counts` result.
- completed sample field coverage.
- Current recommendation: continue accumulation review with conditions.
- Next stage: cross-batch accumulation ledger before expanding task families.

Keep:

- Phase 1 command.
- Phase 2 command.
- 1000 command.
- Boundary language: not final simulator selection, not real welding quality validation, not real robot execution validation.

- [ ] **Step 2: Update details**

In `details.md`, add 2026-06-10 bullets:

- 1000 next-batch real run completed.
- First run distribution.
- Reuse run distribution.
- failure boundary counts.
- field coverage.
- current judgment.

Update “下一步建议” to:

- Build cross-batch accumulation ledger or equivalent review layer.
- Keep current 2 default task families until multiple batches are stable.
- If future failures appear, repair concrete boundaries first.

- [ ] **Step 3: Verify Markdown**

Run from repository root:

```bash
rg -n "1000 requested|1000/1000|reused_existing_result|failure_boundary_counts|field coverage|ledger|最终仿真器|真实焊接质量|真实机器人|WPS/PQR" README.md details.md
```

Expected:

- README/details reflect the run as completed if it completed.
- README/details preserve boundaries.

- [ ] **Step 4: Commit Task 4**

Run from repository root:

```bash
git add README.md details.md
git commit -m "docs: update 1000 sample run status"
```

---

### Task 5: HTML Refresh

**Files:**
- Modify: `README.html`
- Modify: `details.html`

- [ ] **Step 1: Refresh HTML from Markdown**

If `pandoc` is available and preserves the current style, use it. If not, use a local one-off Python converter that:

- Reuses the existing `<style>` block.
- Sets title from Markdown H1.
- Keeps the “HTML 阅读版；维护源” link.
- Handles headings, paragraphs, lists, code fences, inline code, bold text, and Markdown links.

Do not commit a converter script.

- [ ] **Step 2: Verify HTML content**

Run from repository root:

```bash
rg -n "1000 requested|1000/1000|reused_existing_result|failure_boundary_counts|field coverage|ledger|最终仿真器|真实焊接质量|真实机器人|WPS/PQR" README.html details.html
```

Expected:

- HTML files contain the same facts and boundary language as Markdown.

- [ ] **Step 3: Commit Task 5**

Run from repository root:

```bash
git add README.html details.html
git commit -m "docs: refresh 1000 sample run html copies"
```

---

### Task 6: Final Verification And Delivery

**Files:**
- No planned file edits.

- [ ] **Step 1: Run full test suite**

Run from `weld-experience-engine/`:

```bash
uv run pytest -q
```

Expected:

- All tests PASS.

- [ ] **Step 2: Check git cleanliness and ignored artifacts**

Run from repository root:

```bash
rm -f weld-experience-engine/uv.lock
git status --short
git check-ignore -v weld-experience-engine/artifacts/simulation/maniskill-sapien-accumulations/maniskill-sapien-accumulation-next-batch-1000/accumulation_report.json
```

Expected:

- No tracked or untracked generated files except ignored artifacts.
- `git check-ignore` confirms simulation artifacts are ignored.

- [ ] **Step 3: Review diff**

Run from repository root:

```bash
git log --oneline --decorate --max-count=10
git diff --stat origin/main..HEAD
```

Expected:

- Diff limited to spec/plan, evidence review, README/details, HTML, and any necessary code/test fixes if failures required them.

- [ ] **Step 4: Push branch**

Run from repository root:

```bash
git push -u origin codex/next-batch-1000-run-review
```

- [ ] **Step 5: Create PR**

Run from repository root:

```bash
gh pr create \
  --title "Review 1000 requested samples ManiSkill run" \
  --body "## Summary
- run and review 1000 requested samples next-batch in weld-maniskill
- record first-run and reuse-run evidence without committing raw artifacts
- update README/details and HTML reading copies

## Verification
- cd weld-experience-engine && uv run pytest -q"
```

- [ ] **Step 6: Merge PR after it is mergeable**

Run from repository root:

```bash
gh pr view --json state,mergeable,isDraft,statusCheckRollup,url
gh pr merge --squash --delete-branch
```

If local worktree branch deletion fails because `main` is checked out elsewhere, verify remote PR merged and clean up manually from original main worktree.

- [ ] **Step 7: Cleanup local worktree and branch**

From original repository root:

```bash
git fetch --prune origin
git pull --ff-only
git worktree remove "/Users/lloyd/.config/superpowers/worktrees/A02-焊接技能大师平台/codex-next-batch-1000-run-review"
git branch -D codex/next-batch-1000-run-review
```

Expected:

- Original `main` is aligned with `origin/main`.
- Feature worktree and local feature branch removed.
