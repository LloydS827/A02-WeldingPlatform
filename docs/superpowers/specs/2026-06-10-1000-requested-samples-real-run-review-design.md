# 1000 Requested Samples 真实环境运行审查设计

日期：2026-06-10

## 1. 背景

项目当前主线仍是 Physical AI 焊接技能资产底座。上一阶段已经完成 1000 requested samples next-batch plan，并把 `next_scale_recommendation` 从 Phase 1 后建议修正为 Phase 2 后的下一批建议。

当前事实：

- Phase 1：2 个默认任务族 x 50 samples-per-task，共 100 requested samples，作为 accumulation 启动入口保留。
- Phase 2：5 shards x 100 requested samples，共 500 requested samples，已在真实 `weld-maniskill` 环境完成运行审查。
- Phase 2 首次运行结果为 500 requested / 500 completed / 0 failed / 0 skipped。
- Phase 2 同命令复跑时 5 个 shard 均复用已有 `batch_result.json`。
- 1000 next-batch plan 已确定保持当前 2 个默认任务族，按 10 shards x 100 requested samples 组织。

因此本阶段不再停留在“计划 1000 requested samples”，而是把计划推进为真实环境运行审查。

## 2. 目标

本阶段目标是执行并审查 1000 requested samples next-batch：

1. 在真实 `weld-maniskill` conda 环境运行 10 shards x 100 requested samples。
2. 使用同一命令复跑，验证 10 个 shard 是否复用已有 `batch_result.json`。
3. 审查 `requested/completed/failed/skipped` 分布。
4. 审查 `failure_boundary_counts`。
5. 审查 completed sample 的关键字段覆盖率和 `field_coverage_trend`。
6. 形成 tracked 运行审查文档，避免真实运行证据只存在于 ignored artifacts 或终端历史。
7. 同步更新 README、details 和 HTML 阅读版。

## 3. 非目标

本阶段不做：

- 不新增第三个默认 `WeldSkillUnit` 或新任务族。
- 不修改默认 Phase 1 / Phase 2 命令语义。
- 不把 1000 requested samples 的 headless backend probe 写成真实焊接质量验证。
- 不把 ManiSkill/SAPIEN 写成最终仿真器选型。
- 不把运行结果写成真实机器人可执行验证。
- 不提交 `weld-experience-engine/artifacts/simulation/` 下的 raw artifacts、sample artifacts 或 batch artifacts。
- 不因出现 failed samples 直接切换 Gazebo/MoveIt、Isaac、ROS 或真机路线。

## 4. 方案比较

### 方案 A：只执行 1000 首次运行，不复跑

优点是节省时间。缺点是不能验证 shard 复用路径；而复用路径是 Phase 2 后能否持续积累数据的重要工程条件。

### 方案 B：执行 1000 首次运行并同命令复跑

优点是同时验证真实运行和复用行为，可直接回答下一阶段是否具备持续 accumulation 条件。它延续 Phase 2 审查方式，便于对比 500 与 1000 的结果。

缺点是运行时间比只跑一次更长，且会在本地 ignored artifact 目录产生更多文件。

### 方案 C：先新增任务族后再运行 1000

优点是覆盖面更广。缺点是同时扩大样本规模和任务复杂度，若出现 failure boundary 难以判断是规模问题、任务问题还是 adapter/data contract 问题。

推荐方案：**方案 B**。

## 5. 运行设计

运行目录：

```text
weld-experience-engine/
```

真实运行命令：

```bash
conda run -n weld-maniskill python -m weldcore.simulation_bakeoff.maniskill_accumulation_pipeline \
  --outdir artifacts/simulation/maniskill-sapien-accumulations \
  --accumulation-id maniskill-sapien-accumulation-next-batch-1000 \
  --shards 10 \
  --samples-per-task 50
```

同命令复跑仍不加 `--force`，用于验证默认复用行为。

产物位置：

```text
weld-experience-engine/artifacts/simulation/maniskill-sapien-accumulations/maniskill-sapien-accumulation-next-batch-1000/
```

该目录被 `.gitignore` 覆盖，不提交原始 artifacts。tracked 证据只写入：

```text
docs/evidence/simulation-runs/2026-06-10-next-batch-1000-maniskill-sapien-review.md
```

## 6. 审查口径

需要从首次运行和复用运行的 `accumulation_report.json` 审查：

- `requested_sample_count`
- `completed_sample_count`
- `failed_sample_count`
- `skipped_sample_count`
- `status`
- `shard_count`
- `completed_shard_count`
- `reused_shard_count`
- `failed_shard_count`
- 每个 shard report 的 status
- `failure_boundary_counts`
- `field_coverage_trend`
- `next_scale_recommendation`
- `known_limitations`

注意：首次运行和复用运行都会写入同一个 `accumulation_report.json`。因此实施时必须在首次运行完成后、执行复跑前，立即读取首次 `accumulation_report.json`，并把关键分布、shard status、failure boundary counts 和 field coverage 摘录到 tracked 审查文档。可选地把首次报告复制为本地 ignored artifact，例如 `first_run_accumulation_report.json`；但 tracked 证据不能只依赖该 ignored 复制文件。

理想结果：

- 首次运行：1000 requested / 1000 completed / 0 failed / 0 skipped。
- 首次运行：10 个 shard 均为 `completed_new_run`。
- 复用运行：10 个 shard 均为 `reused_existing_result`。
- `failure_boundary_counts` 为空。
- completed sample 的 `raw_artifact_uri`、`adapter_result_uri`、`experience_dataset_uri`、`evidence_bundle_uri` 覆盖率为 1.0。
- `failure_artifact_uri` 覆盖率为 0.0，原因是没有 failed samples。

如果结果与理想结果不同：

1. 不删除失败样本或 failure artifact。
2. 先按 `failure_boundary_counts` 聚类。
3. 若 failure boundary 指向当前项目的 data contract、adapter conversion、dataset/evidence export，可在本分支做最小修复并复跑受影响 shard 或全批次。
4. 若 failure boundary 是环境或外部仿真运行问题，优先记录边界、命令、warning 和复跑结果；除非边界可在当前项目代码内明确修复，否则不扩大为仿真器切换决策。
5. 不把失败直接解释为需要进入真实机器人路线。

## 7. 文档设计

新增运行审查文档：

```text
docs/evidence/simulation-runs/2026-06-10-next-batch-1000-maniskill-sapien-review.md
```

文档应包括：

- 结论。
- 运行环境。
- 精确命令。
- 首次运行分布，且该分布必须在复跑前从首次 `accumulation_report.json` 捕获。
- 复用运行分布。
- failure boundary counts。
- field coverage。
- warning 与边界。
- 是否继续保持 ManiSkill/SAPIEN 为条件性默认 accumulation 入口。
- 下一阶段建议。

同步更新：

- `README.md`
- `details.md`
- `README.html`
- `details.html`

文档口径：

- 若 1000 批次全 completed 且复用成功，写为 `ready_to_continue_accumulation_with_conditions` 一类项目判断；不要写成最终仿真器选型。
- 若出现 failure boundary，写为具体边界和修复优先级；不要写成路线失败。
- 始终保留不代表真实焊接质量验证、不代表 WPS/PQR、不代表真实机器人执行验证的边界。

## 8. 测试与验证

默认软件验证仍使用：

```bash
cd weld-experience-engine
uv run pytest -q
```

真实运行验证使用 `conda run -n weld-maniskill ...`，不要求默认 `uv` 环境内置 ManiSkill/SAPIEN。

本阶段完成前需验证：

- `uv run pytest -q` 通过。
- tracked 运行审查文档存在且包含 1000 首次运行和复用运行事实。
- README/details 与 HTML 阅读版同步。
- git 工作区不包含未跟踪的 `weld-experience-engine/uv.lock`。
- git 工作区不包含将被提交的 raw simulation artifacts。

## 9. 成功标准

本阶段完成后应满足：

- 1000 requested samples next-batch 已在真实 `weld-maniskill` 环境执行过。
- 同命令复跑已验证 shard 复用行为。
- 运行事实已沉淀为 tracked evidence 文档。
- README/details 与 HTML 阅读版已更新。
- 默认测试通过。
- 如果出现 failure boundary，已经按具体边界优先修复或记录阻塞原因，没有切换仿真器或进入真机路线。

## 10. 交付 checklist

代码、文档和验证完成后：

- 提交 feature branch。
- 向远端提起 PR。
- PR 合并到远端 main。
- 合并后清理本地 feature worktree/branch。

## 11. 下一阶段建议

若 1000 requested samples 全 completed 且复用成功，下一阶段建议进入“持续 accumulation 审查层”：

1. 设计跨批次 accumulation ledger，记录 Phase 1、Phase 2、1000 next-batch 的运行元数据。
2. 继续保持 2 个默认任务族，先观察多批次稳定性，再讨论第三个任务族。
3. 把真实专家审查对象定义为 `SimulationEvidenceBundle` / experience dataset / `RobotProcessPackageDraft` 的组合，而不是直接进入真机执行。

若 1000 批次出现 failure boundary，下一阶段优先修复该 boundary 并复跑受影响 shard。
