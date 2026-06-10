# 1000 Requested Samples Next-Batch Plan 设计

日期：2026-06-10

## 1. 背景

项目当前主线是 Physical AI 焊接技能资产底座，不是完整业务系统、最终仿真器选型、真实焊接质量验证或真实机器人执行。当前已经完成：

- `WeldSkillUnit` 到 `SimulationTaskSpec` 的默认任务生成。
- ManiSkill/SAPIEN 小批量 batch 入口。
- Phase 1 accumulation：2 个默认任务族 x 50 samples-per-task，共 100 requested samples。
- Phase 2 sharded accumulation：5 shards x 100 requested samples，共 500 requested samples。
- Phase 2 在真实 `weld-maniskill` 环境中的运行审查：500 requested / 500 completed / 0 failed / 0 skipped。
- 同命令复跑时 5 个 shard 均复用已有 `batch_result.json`。
- `failure_boundary_counts` 为空；completed sample 的 raw artifact、adapter result、experience dataset 和 evidence bundle 字段覆盖率均为 1.0。

因此下一阶段不应再写成“继续 Phase 1 后再进入 Phase 2”。项目已经完成 Phase 2 真实环境审查，下一步应准备 1000 requested samples next-batch plan。

## 2. 已知问题

当前 `SimulationAccumulationReport.next_scale_recommendation` 仍固定输出：

```text
continue_phase_1_then_review_before_phase_2_500_requested_samples
```

这个文案适合 Phase 1 完成后提示进入 Phase 2，但在 Phase 2 真实环境 500 requested samples 已经完成之后，会误导下一步判断。它没有表达：

1. 当前已经具备 Phase 2 sharded scale 证据。
2. 下一批建议是 1000 requested samples，而不是 500 requested samples。
3. 下一批仍应保持 2 个默认任务族，不同时扩大任务复杂度。
4. 若下一批出现 failure boundary，应优先修具体边界，而不是切换仿真器或进入真机路线。

## 3. 目标

本阶段目标是准备 1000 requested samples next-batch plan，并让代码、测试和项目入口文档的默认表述与 Phase 2 之后的真实状态一致。

具体目标：

1. 修正 accumulation report 中偏 Phase 1 的 `next_scale_recommendation` 文案。
2. 明确 1000 requested samples 的推荐组织方式：10 shards x 100 requested samples。
3. 保持当前 2 个默认任务族，继续使用 `samples_per_task=50`，通过 `--shards 10` 扩大总量。
4. 保持 ManiSkill/SAPIEN 为下一批 accumulation 默认入口，但只是在 `ready_to_scale_with_conditions` 的条件边界下继续使用。
5. 若下一批出现 failure boundary，优先修环境、仿真运行、adapter/data contract、dataset/evidence export 等具体边界；不因首次 failure 直接切换仿真器或进入真实机器人路线。
6. 同步更新 README、details 和 HTML 阅读版，避免项目入口与代码报告口径不一致。

## 4. 非目标

本阶段不做：

- 不实际运行 1000 requested samples 的真实 ManiSkill/SAPIEN 批次。
- 不新增第三个默认 `WeldSkillUnit` 或新任务族。
- 不切换 Gazebo/MoveIt、Isaac、ROS 或真实机器人为默认入口。
- 不把 ManiSkill/SAPIEN 写成最终仿真器选型。
- 不把 headless backend probe 写成真实焊接质量验证。
- 不把 `RobotProcessPackageDraft` 或 `RobotFeasibilityResult` 写成真实机器人执行验证。
- 不提交本地 ignored simulation artifacts。

## 5. 方案比较

### 方案 A：直接运行 1000 requested samples

做法是保持现有代码不变，直接执行 `--shards 10 --samples-per-task 50`。

优点：

- 推进最快。
- 可以尽快拿到下一批真实运行结果。

缺点：

- report 仍会输出 Phase 1 后的 recommendation，导致 1000 批次证据与报告结论不一致。
- 下一批如果出现 failure boundary，缺少先修边界而不是切换路线的明确决策口径。

### 方案 B：先修正 recommendation，再准备 1000 next-batch plan

做法是先更新 `next_scale_recommendation`，测试 1000 requested samples shard 组织口径，同步 README/details，再把 1000 真实运行留给下一阶段执行。

优点：

- 与当前“证据边界先行”的项目路线一致。
- 避免把过期 Phase 1 文案带进新批次证据。
- 不同时扩大样本规模和任务复杂度。
- 保持默认工程环境可测试，不要求每个开发环境都具备 ManiSkill/SAPIEN。

缺点：

- 本轮不产出 1000 requested samples 的真实运行结果。

### 方案 C：扩大任务族或切换仿真器

做法是新增默认任务族，或把 Gazebo/MoveIt、Isaac、ROS、真实机器人路线提前切为主线。

优点：

- 看起来覆盖面更广。

缺点：

- 同时扩大任务复杂度和运行规模，难以定位 failure boundary。
- 偏离当前 Phase 2 已验证出的最稳路线。
- 容易把候选仿真器反证工作误写成默认主线。

推荐方案：**方案 B**。

## 6. 核心设计

### 6.1 Report Recommendation

`build_simulation_accumulation_report()` 应输出面向 Phase 2 后下一批的 recommendation，例如：

```text
prepare_next_batch_1000_requested_samples_keep_2_default_task_families_continue_maniskill_sapien_accumulation_entry_fix_failure_boundaries_before_switching_routes
```

该文案应表达四个决策：

- 下一批目标是 1000 requested samples。
- 继续保持 2 个默认任务族。
- 继续使用当前 ManiSkill/SAPIEN accumulation 入口。
- 出现 failure boundary 时先修具体边界，再讨论切换仿真器或真机路线。

为了保持简单，本阶段不引入按状态动态生成 recommendation 的新决策树。原因是现有 report 已经是单一 recommendation 字段，当前最直接的问题是固定文案过期。若后续需要根据 Phase 1、Phase 2、1000 批次状态输出多级建议，可以在 1000 真实运行后再设计。

### 6.2 1000 Requested Samples 组织方式

下一批推荐命令应从 `weld-experience-engine/` 目录执行。`--outdir artifacts/simulation/maniskill-sapien-accumulations` 是相对 `weld-experience-engine/` 的路径，因此真实运行产物应落在：

```text
weld-experience-engine/artifacts/simulation/maniskill-sapien-accumulations/
```

推荐命令：

```bash
cd weld-experience-engine
uv run python -m weldcore.simulation_bakeoff.maniskill_accumulation_pipeline \
  --outdir artifacts/simulation/maniskill-sapien-accumulations \
  --accumulation-id maniskill-sapien-accumulation-next-batch-1000 \
  --shards 10 \
  --samples-per-task 50
```

口径：

- 默认任务族数量：2。
- 每个任务族每个 shard 的 samples-per-task：50。
- 每个 shard requested samples：2 x 50 = 100。
- shard 数：10。
- 总 requested samples：10 x 100 = 1000。

这样可以复用 Phase 2 已验证的 shard 粒度，不改变单 shard 压力，只扩大 shard 数量。

### 6.3 Failure Boundary 策略

下一批出现 failure boundary 时：

1. 先保留 batch/shard 证据，不删除失败样本。
2. 按 `failure_boundary_counts` 判断集中边界。
3. 优先修当前边界，例如：
   - `environment_missing`
   - `simulation_run_failed`
   - `adapter_conversion_failed`
   - `experience_dataset_export_failed`
   - `data_contract_incomplete`
4. completed sample 的关键字段覆盖率仍作为是否可继续扩大/锁定的核心条件。
5. 只有当同一边界被证明不是当前 pipeline 可修复问题，才讨论候选仿真器切换。
6. 真实机器人路线仍不因仿真 batch failure 自动提前。

### 6.4 文档同步

需要同步更新：

- `README.md`
- `README.html`
- `details.md`
- `details.html`

文档应明确：

- 当前下一步是准备或执行 1000 requested samples next-batch。
- 仍保持 2 个默认任务族。
- `next_scale_recommendation` 已从 Phase 1 后建议修正为 Phase 2 后建议。
- 1000 批次命令是可选真实环境运行入口，不是默认测试路径。
- 当前仍不做最终仿真器选型、真实焊接质量验证或真实机器人执行结论。

## 7. 测试策略

本阶段应按 TDD 更新测试：

1. 先新增或修改测试，使其断言 `next_scale_recommendation` 包含：
   - `1000_requested_samples`
   - `2_default_task_families`
   - `maniskill_sapien`
   - `failure_boundaries`
2. 新增 10 shards x 100 requested samples 的 spec/pipeline 轻量测试，确认：
   - `requested_sample_count == 1000`
   - `shard_count == 10`
   - 每个 shard 仍为 100 requested samples
3. 运行聚焦测试：

```bash
cd weld-experience-engine
uv run pytest tests/test_simulation_accumulation_models.py tests/test_maniskill_accumulation_pipeline.py -q
```

4. 最后运行完整默认验证：

```bash
cd weld-experience-engine
uv run pytest -q
```

## 8. 成功标准

本阶段完成后应满足：

- `next_scale_recommendation` 不再建议继续 Phase 1 后进入 Phase 2。
- 代码和测试明确 1000 requested samples next-batch 组织方式。
- README/details 与 HTML 阅读版同步更新。
- 默认测试 `uv run pytest -q` 通过。

## 9. 交付 checklist

代码、测试和文档成功标准满足后，还需要按项目协作要求完成：

- 提交 feature branch。
- 向远端提起 PR。
- PR 合并到远端 main。
- 合并后清理本地 feature worktree/branch。

## 10. 下一阶段建议

本阶段完成后，下一阶段建议在真实 `weld-maniskill` 环境执行 1000 requested samples next-batch：

1. 使用本设计中的 10 shards x 100 requested samples 命令。
2. 首次运行后立即执行同命令复跑，审查 shard 复用。
3. 审查 `failure_boundary_counts` 和 `field_coverage_trend`。
4. 若 1000 requested samples 全 completed，进入更长期持续 accumulation 计划。
5. 若出现 failure boundary，先修具体边界并复跑受影响 shard，再讨论是否扩大任务族。
