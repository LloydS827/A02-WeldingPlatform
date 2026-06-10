# 1000 Requested Samples Next-Batch Plan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修正 Phase 2 后的 accumulation report 下一批建议，并把 1000 requested samples next-batch 计划同步到测试和项目入口文档。

**Architecture:** 保持现有 ManiSkill/SAPIEN accumulation pipeline 结构，不新增仿真器、不新增默认任务族。最小代码改动集中在 `SimulationAccumulationReport.next_scale_recommendation` 的规模感知文案与轻量 shard 口径测试；文档同步说明 10 shards x 100 requested samples 的下一批计划。

**Tech Stack:** Python dataclasses、pytest、Markdown、现有简单 HTML 阅读版、git/GitHub CLI。

---

## Spec Reference

- Spec: `docs/superpowers/specs/2026-06-10-1000-requested-samples-next-batch-plan-design.md`
- Worktree: `/Users/lloyd/.config/superpowers/worktrees/A02-焊接技能大师平台/codex-next-batch-1000-plan`
- Python project root for commands: `/Users/lloyd/.config/superpowers/worktrees/A02-焊接技能大师平台/codex-next-batch-1000-plan/weld-experience-engine`

Key decisions:

- Next batch recommendation: 1000 requested samples.
- Organization: 10 shards x 100 requested samples.
- Task families: keep current 2 default task families.
- Samples per task: keep `samples_per_task=50`.
- Route: continue current ManiSkill/SAPIEN accumulation entry under conditions.
- Failure policy: if the next batch produces failure boundaries, fix concrete boundaries before switching simulator or moving to real robots.

## File Structure

Modify:

- `weld-experience-engine/weldcore/simulation_bakeoff/accumulation.py`
  - Replace outdated Phase 1-to-Phase 2 recommendation text.
- `weld-experience-engine/tests/test_simulation_accumulation_models.py`
  - Add/adjust tests for recommendation wording and 10-shard next-batch spec organization.
- `weld-experience-engine/tests/test_maniskill_accumulation_pipeline.py`
  - Add a lightweight mocked pipeline test for 10 shards x 100 requested samples.
- `README.md`
  - Update next-stage language and add 1000 requested samples optional command.
- `details.md`
  - Record this stage and next-batch plan.
- `README.html`
  - Refresh from `README.md`.
- `details.html`
  - Refresh from `details.md`.

Do not modify:

- Real ManiSkill/SAPIEN runner behavior.
- Default Phase 1 command behavior.
- Default Phase 2 5-shard command behavior.
- Gazebo/MoveIt, Isaac, ROS, robot execution modules.
- Ignored simulation artifact directories.

---

### Task 1: Report Recommendation And Scale Tests

**Files:**
- Modify: `weld-experience-engine/tests/test_simulation_accumulation_models.py`
- Modify: `weld-experience-engine/weldcore/simulation_bakeoff/accumulation.py`

- [ ] **Step 1: Write failing Phase 2 recommendation test**

In `weld-experience-engine/tests/test_simulation_accumulation_models.py`, keep `test_accumulation_report_uses_index_status_and_next_scale_fields` focused on a small Phase 1-scale report and add a new Phase 2-scale recommendation test:

```python
def test_phase_two_ready_report_recommends_one_thousand_sample_next_batch():
    spec = default_maniskill_sharded_accumulation_spec()
    shard = iter_accumulation_shard_specs(spec)[0]
    shard = dataclasses.replace(shard, requested_sample_count=500)
    batch_result = _shard_batch_result(
        shard,
        (
            _shard_sample_run(
                shard.batch_id,
                f"sample-{seed}",
                "completed",
                seed,
            )
            for seed in range(500)
        ),
    )
    index = _index_from_batch_results((batch_result,))

    report = build_simulation_accumulation_report(
        dataset_index=index,
        dataset_index_uri="dataset_index.json",
    )

    assert "1000_requested_samples" in report.next_scale_recommendation
    assert "2_default_task_families" in report.next_scale_recommendation
    assert "maniskill_sapien" in report.next_scale_recommendation
    assert "failure_boundaries" in report.next_scale_recommendation
    assert "phase_1" not in report.next_scale_recommendation
```

Keep the small-report test conservative:

```python
    assert "phase_2_500_requested_samples" in report.next_scale_recommendation
    assert "1000_requested_samples" not in report.next_scale_recommendation
```

- [ ] **Step 2: Run focused test and verify RED**

Run from `weld-experience-engine/`:

```bash
uv run pytest tests/test_simulation_accumulation_models.py::test_phase_two_ready_report_recommends_one_thousand_sample_next_batch -q
```

Expected: FAIL because the current recommendation is `continue_phase_1_then_review_before_phase_2_500_requested_samples`.

- [ ] **Step 3: Write failing next-batch shard organization test**

In `weld-experience-engine/tests/test_simulation_accumulation_models.py`, add:

```python
def test_next_batch_sharded_accumulation_spec_can_request_one_thousand_samples():
    spec = default_maniskill_sharded_accumulation_spec(
        accumulation_id="acc-next-batch-1000",
        output_root="artifacts/simulation/maniskill-sapien-accumulations",
        shard_count=10,
        samples_per_task=50,
    )

    shards = tuple(iter_accumulation_shard_specs(spec))

    assert spec.shard_count == 10
    assert spec.samples_per_task == 50
    assert len(spec.task_specs) == 2
    assert spec.target_requested_sample_count == 1000
    assert [shard.requested_sample_count for shard in shards] == [100] * 10
    assert [shard.seed_start for shard in shards] == [
        0,
        100,
        200,
        300,
        400,
        500,
        600,
        700,
        800,
        900,
    ]
```

- [ ] **Step 4: Run new shard test**

Run from `weld-experience-engine/`:

```bash
uv run pytest tests/test_simulation_accumulation_models.py::test_next_batch_sharded_accumulation_spec_can_request_one_thousand_samples -q
```

Expected: PASS if existing sharded spec already supports arbitrary `shard_count`; if it fails, implement the minimum fix in `accumulation.py` without changing Phase 2 defaults.

- [ ] **Step 5: Implement minimal scale-aware recommendation fix**

In `weld-experience-engine/weldcore/simulation_bakeoff/accumulation.py`, add a small helper near `_readiness_for_next_scale()`:

```python
def _next_scale_recommendation(
    dataset_index: SimulationDatasetIndex,
    status: AccumulationStatus,
) -> str:
    if (
        dataset_index.requested_sample_count >= 500
        and status
        in {"ready_to_scale_with_conditions", "locked_for_next_batch_with_conditions"}
    ):
        return (
            "prepare_next_batch_1000_requested_samples_keep_"
            "2_default_task_families_continue_maniskill_sapien_"
            "accumulation_entry_fix_failure_boundaries_before_"
            "switching_routes"
        )
    return (
        "continue_phase_1_then_review_before_"
        "phase_2_500_requested_samples"
    )
```

Then set:

```python
next_scale_recommendation=_next_scale_recommendation(dataset_index, status),
```

Do not add a broader recommendation engine or config layer.

- [ ] **Step 6: Verify focused model tests pass**

Run from `weld-experience-engine/`:

```bash
uv run pytest tests/test_simulation_accumulation_models.py::test_accumulation_report_uses_index_status_and_next_scale_fields tests/test_simulation_accumulation_models.py::test_phase_two_ready_report_recommends_one_thousand_sample_next_batch tests/test_simulation_accumulation_models.py::test_next_batch_sharded_accumulation_spec_can_request_one_thousand_samples -q
```

Expected: both tests PASS.

- [ ] **Step 7: Commit Task 1**

Run from the repository root:

```bash
git add weld-experience-engine/weldcore/simulation_bakeoff/accumulation.py weld-experience-engine/tests/test_simulation_accumulation_models.py
git commit -m "fix: update next batch recommendation"
```

---

### Task 2: Pipeline Next-Batch Smoke Test

**Files:**
- Modify: `weld-experience-engine/tests/test_maniskill_accumulation_pipeline.py`

- [ ] **Step 1: Write pipeline smoke test**

In `weld-experience-engine/tests/test_maniskill_accumulation_pipeline.py`, add a test near `test_accumulation_pipeline_runs_phase_two_shards`:

```python
def test_accumulation_pipeline_can_plan_next_batch_one_thousand_samples(
    tmp_path,
    monkeypatch,
):
    _mock_completed_backend(monkeypatch)

    result = run_maniskill_accumulation_pipeline(
        outdir=tmp_path,
        accumulation_id="acc-next-batch-1000",
        shards=10,
        samples_per_task=50,
    )

    acc_dir = tmp_path / "acc-next-batch-1000"
    assert result["requested_sample_count"] == 1000
    assert result["completed_sample_count"] == 1000
    assert result["status"] == "ready_to_scale_with_conditions"
    assert result["shard_count"] == 10
    assert len(result["shard_reports"]) == 10
    assert result["next_scale_recommendation"].startswith(
        "prepare_next_batch_1000_requested_samples"
    )

    index = json.loads((acc_dir / "dataset_index.json").read_text(encoding="utf-8"))
    assert len(index["index_items"]) == 1000
    assert len(index["batch_ids"]) == 10
```

- [ ] **Step 2: Run new pipeline test**

Run from `weld-experience-engine/`:

```bash
uv run pytest tests/test_maniskill_accumulation_pipeline.py::test_accumulation_pipeline_can_plan_next_batch_one_thousand_samples -q
```

Expected: PASS if Task 1 recommendation fix is complete. If it fails due to the old recommendation, verify Task 1 was applied. If it fails due to shard behavior, fix only the minimal shard-count path.

- [ ] **Step 3: Run related accumulation tests**

Run from `weld-experience-engine/`:

```bash
uv run pytest tests/test_simulation_accumulation_models.py tests/test_maniskill_accumulation_pipeline.py -q
```

Expected: all tests in both files PASS.

- [ ] **Step 4: Commit Task 2**

Run from repository root:

```bash
git add weld-experience-engine/tests/test_maniskill_accumulation_pipeline.py
git commit -m "test: cover 1000 sample next batch"
```

---

### Task 3: README And Details Update

**Files:**
- Modify: `README.md`
- Modify: `details.md`

- [ ] **Step 1: Update `README.md` next-stage text**

Edit `README.md` so the next-stage section says:

- The next stage is to prepare/execute 1000 requested samples next-batch.
- The recommended organization is 10 shards x 100 requested samples.
- The current 2 default task families remain the default scope.
- The report `next_scale_recommendation` has been updated away from Phase 1 wording.
- Failure boundary policy: fix concrete boundaries before switching simulator or moving to real robots.

Add an optional command after the Phase 2 command:

```bash
uv run python -m weldcore.simulation_bakeoff.maniskill_accumulation_pipeline \
  --outdir artifacts/simulation/maniskill-sapien-accumulations \
  --accumulation-id maniskill-sapien-accumulation-next-batch-1000 \
  --shards 10 \
  --samples-per-task 50
```

Keep the command under language saying it must be run from `weld-experience-engine/`, and keep boundary language: not final simulator selection, not real welding quality validation, not robot execution validation.

- [ ] **Step 2: Update `details.md` stage record**

In `details.md`, add bullets to the 2026-06-10 section:

- Added 1000 requested samples next-batch plan.
- Recommendation is 10 shards x 100 requested samples.
- Kept current 2 default task families.
- Updated report `next_scale_recommendation` away from Phase 1 wording.
- If next batch shows failure boundaries, fix concrete boundaries first.

Update “下一步建议” so it points to executing the 1000 requested samples next-batch in `weld-maniskill`, then rerunning the same command to verify shard reuse.

- [ ] **Step 3: Verify Markdown content**

Run from repository root:

```bash
rg -n "1000 requested|10 shards|2 个默认任务族|next_scale_recommendation|failure boundary|最终仿真器|真实焊接质量|真实机器人" README.md details.md
```

Expected:

- Both Markdown files mention 1000 requested samples.
- Both preserve boundary language.
- Text no longer presents fixing `next_scale_recommendation` as future work; it should be described as completed or part of this stage.

- [ ] **Step 4: Commit Task 3**

Run from repository root:

```bash
git add README.md details.md
git commit -m "docs: describe 1000 sample next batch"
```

---

### Task 4: HTML Refresh

**Files:**
- Modify: `README.html`
- Modify: `details.html`

- [ ] **Step 1: Inspect current HTML style**

Run from repository root:

```bash
sed -n '1,80p' README.html
sed -n '1,80p' details.html
```

Use the existing simple reading-copy style. Do not hand-maintain independent content.

- [ ] **Step 2: Refresh HTML from Markdown**

If `pandoc` is installed and output is compatible, use it. Otherwise run a local one-off conversion command from shell. The converter may be temporary and must not be committed.

The HTML must reflect the Markdown content for:

- 1000 requested samples.
- 10 shards x 100 requested samples.
- 2 default task families.
- `next_scale_recommendation`.
- boundary language.

- [ ] **Step 3: Verify HTML content**

Run from repository root:

```bash
rg -n "1000 requested|10 shards|2 个默认任务族|next_scale_recommendation|failure boundary|最终仿真器|真实焊接质量|真实机器人" README.html details.html
```

Expected:

- HTML files contain the same new facts and boundary language as Markdown.

- [ ] **Step 4: Commit Task 4**

Run from repository root:

```bash
git add README.html details.html
git commit -m "docs: refresh next batch html copies"
```

---

### Task 5: Final Verification And Delivery Prep

**Files:**
- No new code files expected.
- May modify docs only if verification reveals a mismatch.

- [ ] **Step 1: Run full test suite**

Run from `weld-experience-engine/`:

```bash
uv run pytest -q
```

Expected: all tests PASS.

- [ ] **Step 2: Verify no generated lock/artifact files are staged**

Run from repository root:

```bash
git status --short
```

Expected:

- Clean working tree.
- No `weld-experience-engine/uv.lock`.
- No `weld-experience-engine/artifacts/`.

- [ ] **Step 3: Review final diff summary**

Run from repository root:

```bash
git log --oneline --decorate --max-count=8
git diff --stat origin/main..HEAD
```

Expected:

- Commits include spec, report/test changes, docs, HTML.
- Diff is limited to the files listed in this plan.

- [ ] **Step 4: Push branch**

Run from repository root:

```bash
git push -u origin codex/next-batch-1000-plan
```

- [ ] **Step 5: Open PR**

Run from repository root:

```bash
gh pr create \
  --title "Prepare 1000 requested samples next batch" \
  --body "## Summary
- update accumulation report recommendation for the Phase 2 -> 1000 requested samples next batch
- cover 10 shards x 100 requested samples with tests
- update README/details and HTML reading copies

## Verification
- cd weld-experience-engine && uv run pytest -q"
```

- [ ] **Step 6: Merge PR after checks pass**

Run from repository root:

```bash
gh pr merge --squash --delete-branch
```

If repository policy requires merge commits instead of squash, use the policy-compatible option.

- [ ] **Step 7: Clean local worktree after merge**

From the original repository root, run:

```bash
git fetch origin
git checkout main
git pull --ff-only
git worktree remove "/Users/lloyd/.config/superpowers/worktrees/A02-焊接技能大师平台/codex-next-batch-1000-plan"
git branch -D codex/next-batch-1000-plan
```

Expected: feature worktree removed and local main up to date.
