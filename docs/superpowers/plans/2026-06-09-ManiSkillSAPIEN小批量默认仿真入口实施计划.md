# ManiSkill/SAPIEN 小批量默认仿真入口 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 ManiSkill/SAPIEN 小批量默认仿真入口，让 2 个默认 `SimulationTaskSpec` 各生成 10 条可追踪运行样本，并稳定输出 batch spec、batch result、样本 artifact、evidence 和 completed 样本 dataset。

**Architecture:** 保持现有单次 `run_maniskill_spike_pipeline()` 不变，新增批次层对象和 `maniskill_batch_pipeline`。批次入口复用现有 `maniskill_task_config_from_spec()`、`generate_rule_based_demo()`、`run_maniskill_lightweight()`、`adapt_maniskill_artifact()`、`build_maniskill_experience_dataset()` 和 `build_simulation_evidence_bundle()`，只在外层增加 sample planning、稳定落盘、失败 artifact 与汇总。

**Tech Stack:** Python dataclasses, existing `weldcore.simulation_bakeoff` modules, pytest, `uv run pytest`.

---

## Scope Boundaries

本计划只实现第二轮小批量默认入口：

- 默认 primary route 是 `maniskill_sapien`。
- 默认 2 个 task，每个 task 10 条样本，总 `requested_sample_count = 20`。
- `comparison_route_ids=("simlite_reference",)` 只作为元数据和第三轮报告线索，不执行、不计数。
- `deterministic_micro_offset` 第二轮只要求记录 seed 派生的 metadata descriptor，不要求修改真实 task config。
- completed 样本必须有 `raw_artifact.json`、`adapter_result.json`、`evidence_bundle.json`、`experience_dataset.json`。
- failed / skipped 样本必须有 `failure_artifact.json`；`raw_artifact_uri` 必须指向已存在的 `raw_artifact.json` 或 `failure_artifact.json`。
- 默认 CI 不依赖真实 ManiSkill/SAPIEN 环境。
- 不做最终仿真器定型、入口锁定报告、真实机器人执行、真实焊接质量验证或 WPS/PQR。

## File Structure

- Create: `weld-experience-engine/weldcore/simulation_bakeoff/batch.py`
  - `SimulationBatchSpec`、`SimulationSampleRun`、`SimulationBatchResult`
  - `SimulationSamplePlan`
  - `default_maniskill_batch_spec()`
  - `iter_batch_sample_plans()`
  - `summarize_sample_runs()`
  - stable `sample_id` and deterministic offset descriptor helpers
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/maniskill_batch_pipeline.py`
  - `run_maniskill_batch_pipeline()`
  - CLI `main()`
  - per-sample artifact writing and failure artifact rules
- Modify: `weld-experience-engine/weldcore/simulation_bakeoff/maniskill_contract.py`
  - Extend `FailureBoundary` with batch-level boundaries used by the spec.
- Modify: `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py`
  - Export new batch models, helpers, and pipeline entry.
- Create: `weld-experience-engine/tests/test_simulation_batch_models.py`
  - Batch model serialization, sample planning, count aggregation, comparison route metadata tests.
- Create: `weld-experience-engine/tests/test_maniskill_batch_pipeline.py`
  - End-to-end batch pipeline tests for completed samples and structured failures.
- Modify: `README.md`, `README.html`, `details.md`, `details.html`
  - After implementation, update current status and verification notes.

## Task 1: Batch Models And Sample Planning

**Files:**
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/batch.py`
- Create: `weld-experience-engine/tests/test_simulation_batch_models.py`
- Modify: `weld-experience-engine/weldcore/simulation_bakeoff/maniskill_contract.py`
- Modify: `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py`

- [ ] **Step 1: Write failing tests for default batch spec and sample planning**

Create `weld-experience-engine/tests/test_simulation_batch_models.py`.

Required tests:

```python
from weldcore.simulation_bakeoff import (
    SimulationBatchSpec,
    SimulationBatchResult,
    SimulationSamplePlan,
    SimulationSampleRun,
    default_maniskill_batch_spec,
    iter_batch_sample_plans,
    summarize_sample_runs,
)


def test_default_batch_spec_requests_twenty_primary_samples():
    spec = default_maniskill_batch_spec(
        batch_id="batch-test",
        output_root="artifacts/simulation/maniskill-sapien-batches",
    )

    samples = tuple(iter_batch_sample_plans(spec))

    assert isinstance(spec, SimulationBatchSpec)
    assert spec.route_id == "maniskill_sapien"
    assert spec.samples_per_task == 10
    assert spec.sample_variation_policy == "deterministic_micro_offset"
    assert spec.comparison_route_ids == ("simlite_reference",)
    assert len(spec.task_specs) == 2
    assert len(samples) == 20
    assert isinstance(samples[0], SimulationSamplePlan)
    assert {sample.route_id for sample in samples} == {"maniskill_sapien"}
    assert samples[0].sample_id == (
        "sample-batch-test-maniskill_sapien-"
        f"{spec.task_specs[0].task_id}-0"
    )
```

```python
def test_sample_plans_record_seed_and_variation_descriptor():
    spec = default_maniskill_batch_spec(batch_id="batch-test", seed_start=100)

    samples = tuple(iter_batch_sample_plans(spec))

    assert samples[0].seed == 100
    assert samples[1].seed == 101
    assert samples[0].variation_policy == "deterministic_micro_offset"
    assert samples[0].variation_descriptor["policy"] == "deterministic_micro_offset"
    assert samples[0].variation_descriptor["seed"] == 100
    assert "not_real_welding_process_variation" in samples[0].evidence_notes
```

```python
def test_batch_result_summarizes_completed_failed_and_skipped_samples():
    runs = (
        SimulationSampleRun(
            batch_id="batch-test",
            sample_id="sample-1",
            task_id="task-a",
            route_id="maniskill_sapien",
            seed=1,
            variation_policy="deterministic_micro_offset",
            variation_descriptor={"policy": "deterministic_micro_offset", "seed": 1},
            status="completed",
            raw_artifact_uri="samples/sample-1/raw_artifact.json",
            adapter_result_uri="samples/sample-1/adapter_result.json",
            evidence_bundle_uri="samples/sample-1/evidence_bundle.json",
            experience_dataset_uri="samples/sample-1/experience_dataset.json",
            failure_boundary=(),
            evidence_notes=("simulation_only_not_real_welding_quality",),
        ),
        SimulationSampleRun(
            batch_id="batch-test",
            sample_id="sample-2",
            task_id="task-a",
            route_id="maniskill_sapien",
            seed=2,
            variation_policy="deterministic_micro_offset",
            variation_descriptor={"policy": "deterministic_micro_offset", "seed": 2},
            status="failed",
            raw_artifact_uri="samples/sample-2/failure_artifact.json",
            adapter_result_uri=None,
            evidence_bundle_uri=None,
            experience_dataset_uri=None,
            failure_boundary=("task_generation_failed",),
            evidence_notes=("simulation_only_not_real_welding_quality",),
        ),
        SimulationSampleRun(
            batch_id="batch-test",
            sample_id="sample-3",
            task_id="task-a",
            route_id="maniskill_sapien",
            seed=3,
            variation_policy="deterministic_micro_offset",
            variation_descriptor={"policy": "deterministic_micro_offset", "seed": 3},
            status="skipped",
            raw_artifact_uri="samples/sample-3/failure_artifact.json",
            adapter_result_uri=None,
            evidence_bundle_uri=None,
            experience_dataset_uri=None,
            failure_boundary=("batch_generation_incomplete",),
            evidence_notes=("simulation_only_not_real_welding_quality",),
        ),
    )

    result = summarize_sample_runs(
        batch_id="batch-test",
        route_id="maniskill_sapien",
        task_count=1,
        requested_sample_count=3,
        sample_runs=runs,
    )

    assert isinstance(result, SimulationBatchResult)
    assert result.completed_sample_count == 1
    assert result.failed_sample_count == 1
    assert result.skipped_sample_count == 1
    assert result.failure_boundaries == (
        "task_generation_failed",
        "batch_generation_incomplete",
    )
    payload = result.to_dict()
    assert payload["sample_runs"][0]["status"] == "completed"
    assert payload["sample_runs"][2]["raw_artifact_uri"].endswith(
        "failure_artifact.json"
    )
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_simulation_batch_models.py
```

Expected: FAIL because `SimulationBatchSpec`, `SimulationSamplePlan`, `SimulationSampleRun`, `SimulationBatchResult`, `default_maniskill_batch_spec`, `iter_batch_sample_plans`, and `summarize_sample_runs` do not exist yet.

- [ ] **Step 3: Implement batch models and helpers**

Create `weld-experience-engine/weldcore/simulation_bakeoff/batch.py`.

Implementation requirements:

- Use frozen dataclasses and `to_dict()` methods consistent with `model.py`.
- Use `Literal` types for:
  - `VariationPolicy = Literal["none", "deterministic_micro_offset"]`
  - `SampleRunStatus = Literal["completed", "failed", "skipped"]`
- Add `variation_descriptor: dict[str, Any]` to `SimulationSampleRun`.
- Add `SimulationSamplePlan` as the pre-execution sample plan object. It should contain `batch_id`, `sample_id`, `task_id`, `route_id`, `seed`, `variation_policy`, `variation_descriptor`, and `evidence_notes`. It must not contain final `status` or artifact URI fields.
- `SimulationBatchSpec` fields:
  - `batch_id: str`
  - `route_id: str`
  - `task_specs: tuple[SimulationTaskSpec, ...]`
  - `samples_per_task: int`
  - `sample_variation_policy: VariationPolicy`
  - `seed_start: int`
  - `output_root: str`
  - `comparison_route_ids: tuple[str, ...]`
  - `stage_boundary: str`
- `SimulationSampleRun` fields:
  - `batch_id`, `sample_id`, `task_id`, `route_id`, `seed`, `variation_policy`, `variation_descriptor`
  - `status`
  - `raw_artifact_uri: str`
  - `adapter_result_uri: str | None`
  - `evidence_bundle_uri: str | None`
  - `experience_dataset_uri: str | None`
  - `failure_boundary: tuple[str, ...]`
  - `evidence_notes: tuple[str, ...]`
- `SimulationBatchResult` fields:
  - `batch_id`, `route_id`, `task_count`, `requested_sample_count`
  - `completed_sample_count`, `failed_sample_count`, `skipped_sample_count`
  - `sample_runs: tuple[SimulationSampleRun, ...]`
  - `failure_boundaries: tuple[str, ...]`
  - `stage_boundary: str`
  - `next_step_hint: str`
- `default_maniskill_batch_spec()` should default to:
  - `batch_id="maniskill-sapien-default-batch"`
  - `route_id="maniskill_sapien"`
  - `task_specs=default_simulation_task_specs()`
  - `samples_per_task=10`
  - `sample_variation_policy="deterministic_micro_offset"`
  - `seed_start=0`
  - `output_root="artifacts/simulation/maniskill-sapien-batches"`
  - `comparison_route_ids=("simlite_reference",)`
  - `stage_boundary="simulation_only_not_real_welding_quality"`
- `iter_batch_sample_plans(spec)` returns `SimulationSamplePlan` objects with:
  - deterministic sample ids: `sample-{batch_id}-{route_id}-{task_id}-{seed}`
  - evidence notes include `"simulation_only_not_real_welding_quality"`, `"not_final_simulator_selection"`, `"not_real_welding_process_variation"`
- `comparison_route_ids` must not create sample plans.
- `summarize_sample_runs()` must count statuses and collect unique failure boundaries in first-seen order.
- `skipped` is a supported final `SimulationSampleRun.status` for future explicit skip decisions. The default batch pipeline in Task 2 should not emit skipped sample runs; it should either complete or fail each requested primary sample. If a future caller emits skipped runs, the same failure artifact URI contract applies.

Modify `weld-experience-engine/weldcore/simulation_bakeoff/maniskill_contract.py`:

- Extend `FailureBoundary` with:
  - `"data_contract_incomplete"`
  - `"batch_generation_incomplete"`
  - `"sample_generation_failed"`
  - `"experience_dataset_export_failed"`

Modify `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py`:

- Export new classes and helpers.

- [ ] **Step 4: Run model tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_simulation_batch_models.py
```

Expected: PASS.

- [ ] **Step 5: Run nearby existing tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_simulation_bakeoff_models.py tests/test_simulation_adapter_routes.py tests/test_maniskill_pipeline.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add weld-experience-engine/weldcore/simulation_bakeoff/batch.py \
  weld-experience-engine/weldcore/simulation_bakeoff/maniskill_contract.py \
  weld-experience-engine/weldcore/simulation_bakeoff/__init__.py \
  weld-experience-engine/tests/test_simulation_batch_models.py
git commit -m "feat: add simulation batch models"
```

## Task 2: ManiSkill Batch Pipeline And CLI

**Files:**
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/maniskill_batch_pipeline.py`
- Create: `weld-experience-engine/tests/test_maniskill_batch_pipeline.py`
- Modify: `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py`

- [ ] **Step 1: Write failing completed-batch pipeline test**

Create `weld-experience-engine/tests/test_maniskill_batch_pipeline.py`.

Required completed test:

```python
import json

from weldcore.simulation_bakeoff import run_maniskill_batch_pipeline


def _mock_completed_backend(monkeypatch):
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._maniskill_backend_available",
        lambda: True,
    )
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._run_backend",
        lambda config, demo: {
            "status": "completed",
            "task_state": {"attempted": True, "backend_invoked": True},
            "metrics": {"task_contract_outputs_ready": 1.0, "path_continuity": 1.0},
        },
    )


def test_batch_pipeline_writes_twenty_completed_primary_samples(tmp_path, monkeypatch):
    _mock_completed_backend(monkeypatch)

    result = run_maniskill_batch_pipeline(
        outdir=tmp_path,
        batch_id="batch-test",
    )

    assert result["batch_id"] == "batch-test"
    assert result["route_id"] == "maniskill_sapien"
    assert result["task_count"] == 2
    assert result["requested_sample_count"] == 20
    assert result["completed_sample_count"] == 20
    assert result["failed_sample_count"] == 0
    assert result["skipped_sample_count"] == 0
    assert result["failure_boundaries"] == []

    batch_dir = tmp_path / "batch-test"
    assert (batch_dir / "batch_spec.json").exists()
    assert (batch_dir / "batch_result.json").exists()
    assert json.loads((batch_dir / "batch_result.json").read_text()) == result

    assert len(result["sample_runs"]) == 20
    for sample in result["sample_runs"]:
        sample_dir = batch_dir / "samples" / sample["sample_id"]
        assert sample["status"] == "completed"
        assert sample["experience_dataset_uri"].endswith("experience_dataset.json")
        assert (sample_dir / "task_config.json").exists()
        assert (sample_dir / "demo.json").exists()
        assert (sample_dir / "raw_artifact.json").exists()
        assert (sample_dir / "adapter_result.json").exists()
        assert (sample_dir / "evidence_bundle.json").exists()
        assert (sample_dir / "experience_dataset.json").exists()
        assert not (sample_dir / "failure_artifact.json").exists()
```

- [ ] **Step 2: Write failing structured-failure pipeline tests**

Add tests:

```python
def test_batch_pipeline_records_environment_missing_as_twenty_failed_samples(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._maniskill_backend_available",
        lambda: False,
    )

    result = run_maniskill_batch_pipeline(
        outdir=tmp_path,
        batch_id="batch-test",
    )

    assert result["requested_sample_count"] == 20
    assert result["completed_sample_count"] == 0
    assert result["failed_sample_count"] == 20
    assert result["failure_boundaries"] == ["environment_missing"]

    batch_dir = tmp_path / "batch-test"
    for sample in result["sample_runs"]:
        sample_dir = batch_dir / "samples" / sample["sample_id"]
        assert sample["status"] == "failed"
        assert sample["experience_dataset_uri"] is None
        assert sample["failure_boundary"] == ["environment_missing"]
        assert sample["raw_artifact_uri"].endswith("raw_artifact.json")
        assert (sample_dir / "raw_artifact.json").exists()
        assert (sample_dir / "failure_artifact.json").exists()
```

```python
def test_batch_pipeline_uses_failure_artifact_uri_when_task_generation_fails(
    tmp_path,
    monkeypatch,
):
    def fail_task_generation(task_spec):
        raise ValueError("bad task")

    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_batch_pipeline."
        "maniskill_task_config_from_spec",
        fail_task_generation,
    )

    result = run_maniskill_batch_pipeline(
        outdir=tmp_path,
        batch_id="batch-test",
    )

    assert result["failed_sample_count"] == 20
    assert result["failure_boundaries"] == ["task_generation_failed"]

    batch_dir = tmp_path / "batch-test"
    for sample in result["sample_runs"]:
        sample_dir = batch_dir / "samples" / sample["sample_id"]
        assert sample["raw_artifact_uri"].endswith("failure_artifact.json")
        assert (sample_dir / "failure_artifact.json").exists()
        assert not (sample_dir / "raw_artifact.json").exists()
```

Also add a focused assertion in one of the tests:

```python
def test_batch_pipeline_keeps_comparison_routes_as_metadata_only(tmp_path, monkeypatch):
    _mock_completed_backend(monkeypatch)

    def fail_if_simlite_runs(*args, **kwargs):
        raise AssertionError("simlite comparison route should not run in batch pipeline")

    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.routes.run_simlite_reference",
        fail_if_simlite_runs,
    )

    result = run_maniskill_batch_pipeline(outdir=tmp_path, batch_id="batch-test")
    spec = json.loads((tmp_path / "batch-test" / "batch_spec.json").read_text())

    assert spec["comparison_route_ids"] == ["simlite_reference"]
    assert result["requested_sample_count"] == 20
    assert {sample["route_id"] for sample in result["sample_runs"]} == {
        "maniskill_sapien"
    }
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_maniskill_batch_pipeline.py
```

Expected: FAIL because `run_maniskill_batch_pipeline` and `maniskill_batch_pipeline.py` do not exist.

- [ ] **Step 4: Implement batch pipeline**

Create `weld-experience-engine/weldcore/simulation_bakeoff/maniskill_batch_pipeline.py`.

Implementation requirements:

- Public function:

```python
def run_maniskill_batch_pipeline(
    outdir: str | Path = "artifacts/simulation/maniskill-sapien-batches",
    batch_id: str = "maniskill-sapien-default-batch",
) -> dict[str, Any]:
    ...
```

- It creates a `SimulationBatchSpec` with `output_root=str(outdir)` and writes:
  - `{outdir}/{batch_id}/batch_spec.json`
  - `{outdir}/{batch_id}/batch_result.json`
- It creates sample directories under:
  - `{outdir}/{batch_id}/samples/{sample_id}/`
- It iterates only primary `maniskill_sapien` sample plans from `iter_batch_sample_plans(spec)`.
- The default pipeline must emit one final `SimulationSampleRun` for every requested primary sample. In this second-round implementation, those final runs should be `completed` or `failed`; `skipped` remains a supported model status but is not produced by the default batch pipeline.
- For each sample:
  - write `task_config.json` after task config generation succeeds
  - write `demo.json` after demo generation succeeds
  - write `raw_artifact.json` after lightweight run returns
  - if artifact status is `"completed"`:
    - write `adapter_result.json`
    - write `experience_dataset.json`
    - write `evidence_bundle.json`
    - sample status is `"completed"`
    - failure boundary is empty
  - if artifact status is `"failed"`:
    - write `failure_artifact.json`
    - sample status is `"failed"`
    - failure boundary mirrors artifact failure boundary
    - `experience_dataset_uri` is `None`
    - `raw_artifact_uri` points to `raw_artifact.json`
  - if task config generation, demo generation, adapter conversion, dataset export, or evidence export fails:
    - write `failure_artifact.json`
    - sample status is `"failed"`
    - failure boundary uses the matching boundary from the spec
    - `raw_artifact_uri` points to existing `raw_artifact.json` if it exists; otherwise `failure_artifact.json`
    - do not raise for per-sample failures
- Batch spec invalidity may raise, but normal per-sample failures must not stop the batch.
- Return `SimulationBatchResult.to_dict()`.

Failure artifact guidance:

- Reuse `RawManiSkillArtifact` for `failure_artifact.json`.
- Use run id `maniskill-{sample_id}`.
- Include sample metadata in `task_state`, at minimum:
  - `batch_id`
  - `sample_id`
  - `seed`
  - `variation_policy`
  - `variation_descriptor`
  - `task_status="failed"`
- Include evidence notes:
  - `"simulation_only_not_real_welding_quality"`
  - `"not_final_simulator_selection"`

When writing completed raw artifacts, it is acceptable to preserve the existing `run_id` from `run_maniskill_lightweight`; do not mutate existing dataclasses unless needed.

- [ ] **Step 5: Add CLI**

In `maniskill_batch_pipeline.py`, add:

```python
def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--outdir",
        default="artifacts/simulation/maniskill-sapien-batches",
    )
    parser.add_argument("--batch-id", default="maniskill-sapien-default-batch")
    args = parser.parse_args(argv)
    result = run_maniskill_batch_pipeline(args.outdir, batch_id=args.batch_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

Add the usual `if __name__ == "__main__": main()`.

- [ ] **Step 6: Export pipeline entry**

Modify `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py`:

- Export `run_maniskill_batch_pipeline`.

- [ ] **Step 7: Run batch pipeline tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_maniskill_batch_pipeline.py
```

Expected: PASS.

- [ ] **Step 8: Run related regression tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q \
  tests/test_simulation_batch_models.py \
  tests/test_maniskill_batch_pipeline.py \
  tests/test_maniskill_pipeline.py \
  tests/test_simulation_bakeoff_maniskill_adapter.py \
  tests/test_maniskill_runner.py
```

Expected: PASS.

- [ ] **Step 9: Commit**

Run:

```bash
git add weld-experience-engine/weldcore/simulation_bakeoff/maniskill_batch_pipeline.py \
  weld-experience-engine/weldcore/simulation_bakeoff/__init__.py \
  weld-experience-engine/tests/test_maniskill_batch_pipeline.py
git commit -m "feat: add maniskill batch pipeline"
```

## Task 3: Documentation, Verification, And Integration Polish

**Files:**
- Modify: `README.md`
- Modify: `README.html`
- Modify: `details.md`
- Modify: `details.html`
- Modify if needed: `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py`
- Modify if needed: `weld-experience-engine/tests/test_maniskill_batch_pipeline.py`

- [ ] **Step 1: Run focused command check for CLI**

Run the default CI-safe failure path:

```bash
cd weld-experience-engine
uv run python -m weldcore.simulation_bakeoff.maniskill_batch_pipeline \
  --outdir /tmp/maniskill-sapien-batches \
  --batch-id batch-doc-check
```

Expected:

- Command exits 0.
- JSON prints `requested_sample_count` as 20.
- If ManiSkill/SAPIEN is not installed, JSON prints `failed_sample_count` as 20 and `failure_boundaries` includes `environment_missing`.
- `/tmp/maniskill-sapien-batches/batch-doc-check/batch_spec.json` exists.
- `/tmp/maniskill-sapien-batches/batch-doc-check/batch_result.json` exists.

- [ ] **Step 2: Update README**

Modify `README.md` and `README.html`.

Required changes:

- In “已完成能力”, add that the project now has a ManiSkill/SAPIEN 小批量默认仿真入口.
- In “下一阶段方向”, change from “下一阶段应优先做 ManiSkill/SAPIEN 小批量默认仿真入口” to a completed/next boundary:
  - current completed: 小批量入口已具备软件入口和 batch result 契约
  - next: 基于小批量结果做数据积累前置报告与入口锁定
- In “如何验证”, add the optional/manual command:

```bash
uv run python -m weldcore.simulation_bakeoff.maniskill_batch_pipeline \
  --outdir artifacts/simulation/maniskill-sapien-batches
```

State clearly:

- This command is a simulation batch entry, not final simulator selection.
- Default test path still does not prove real welding quality or real robot execution.

- [ ] **Step 3: Update details**

Modify `details.md` and `details.html`.

Required changes:

- Add a 2026-06-09 update entry or extend the existing one:
  - implemented `SimulationBatchSpec` / `SimulationSampleRun` / `SimulationBatchResult`
  - added `run_maniskill_batch_pipeline`
  - default batch is 2 tasks x 10 primary samples
  - comparison route remains metadata only
  - failure samples write `failure_artifact.json`
- Update “当前一句话状态” from “正在进入设计” to “已完成软件入口”.
- Update “下一步建议” to say the next stage is “数据积累前置报告与入口锁定”.

- [ ] **Step 4: Run full verification**

Run:

```bash
cd weld-experience-engine
uv run pytest -q
```

Expected: all tests pass.

If `uv run` creates `weld-experience-engine/uv.lock` and it is untracked, remove it before committing unless the user explicitly asks to keep it.

- [ ] **Step 5: Check git cleanliness and staged diff**

Run:

```bash
git status --short
git diff --check
```

Expected:

- Only intended implementation/docs files are modified.
- No whitespace errors.
- No generated artifacts under `artifacts/` or `/tmp` are staged.
- No untracked `weld-experience-engine/uv.lock` remains.

- [ ] **Step 6: Commit**

Run:

```bash
git add README.md README.html details.md details.html
git commit -m "docs: record maniskill batch entry"
```

If Task 3 requires tiny export/test polish beyond docs, include those exact files in the same commit and mention why in the commit body.

## Final Verification

After all tasks are complete:

- Run:

```bash
cd weld-experience-engine
uv run pytest -q
```

- Run:

```bash
git log --oneline -5
git status --short --branch
```

- Confirm:
  - branch is `codex/maniskill-batch-entry`
  - working tree is clean
  - tests pass
  - plan/spec/doc commits are present
  - no generated artifacts are tracked

## Final Review Gate

After implementation tasks finish, dispatch:

1. Spec compliance reviewer for the whole implementation against:
   - `docs/superpowers/specs/2026-06-09-ManiSkillSAPIEN小批量默认仿真入口-design.md`
   - this plan
2. Code quality reviewer for changed Python and tests.

Do not merge or push until both final reviews are approved and verification output is confirmed.
