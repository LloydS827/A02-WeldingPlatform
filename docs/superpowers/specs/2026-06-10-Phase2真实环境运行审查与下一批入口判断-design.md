# Phase 2 真实环境运行审查与下一批入口判断设计

日期：2026-06-10

## 1. 背景

项目当前已经具备 ManiSkill/SAPIEN Phase 2 sharded accumulation 入口：

```text
WeldSkillUnit
-> SimulationTaskSpec
-> ManiSkill/SAPIEN shard batch
-> raw artifact / adapter result
-> experience dataset / SimulationEvidenceBundle
-> SimulationDatasetIndex
-> SimulationAccumulationReport
```

上一阶段已经实现 5 shards x 100 requested samples = 500 requested samples 的 CLI、shard 复用、`--force` 强制重跑、`failure_boundary_counts`、`field_coverage_trend` 和 `locked_for_next_batch_with_conditions` 状态判断。

本阶段不再重复建设 shard 编排能力，而是按既定 Phase 2 入口在真实 `weld-maniskill` conda 环境中运行，并把审查结果沉淀为项目级证据和下一步路线判断。

## 2. 已观察事实

本轮在 `weld-maniskill` conda 环境中确认：

- `mani_skill` 可导入。
- `sapien` 可导入。
- 当前 worktree 的 `weldcore` 已以 editable 方式安装到该环境。
- 默认 `uv` 开发环境仍不包含 ManiSkill/SAPIEN；这符合项目约定，即默认工程环境保持轻量，真实仿真依赖放在独立 conda 环境。

已执行 Phase 2 命令：

```bash
conda run -n weld-maniskill python -m weldcore.simulation_bakeoff.maniskill_accumulation_pipeline \
  --outdir artifacts/simulation/maniskill-sapien-accumulations \
  --accumulation-id maniskill-sapien-accumulation-phase-2 \
  --shards 5 \
  --samples-per-task 50
```

首次运行结果：

- requested samples：500
- completed samples：500
- failed samples：0
- skipped samples：0
- shard 状态：5 个 `completed_new_run`
- `failure_boundary_counts`：空
- completed 样本关键字段覆盖率：
  - `raw_artifact_uri`：1.0
  - `adapter_result_uri`：1.0
  - `experience_dataset_uri`：1.0
  - `evidence_bundle_uri`：1.0
  - `failure_artifact_uri`：0.0
- report 状态：`ready_to_scale_with_conditions`

随后使用同一命令复跑，默认复用已有 shard result：

- requested samples：500
- completed samples：500
- failed samples：0
- skipped samples：0
- shard 状态：5 个 `reused_existing_result`
- `failure_boundary_counts`：空
- report 状态：`ready_to_scale_with_conditions`

运行中出现 SAPIEN Vulkan fallback 与 pinocchio 缺失 warning，但没有导致样本失败，也没有进入 adapter/data contract failure boundary。

## 3. 设计目标

本阶段目标是把 Phase 2 真实环境运行从“命令已经跑过”转成“项目可审查证据与下一步决策”。

需要回答：

1. 500 requested samples 的 completed / failed / skipped 分布是否支持继续放大。
2. shard 复用行为是否可解释。
3. failure boundary counts 是否集中在环境、仿真运行、adapter/data contract，或为空。
4. completed samples 的关键字段覆盖是否稳定。
5. 当前结果应进入 `ready_to_scale_with_conditions`、`locked_for_next_batch_with_conditions`，还是阻塞修复。
6. README 和 details 是否准确反映本阶段判断。

## 4. 备选方案

### 方案 A：只保留终端运行结果，不更新文档

优点是改动最小。缺点是运行证据只存在于本地 ignored artifacts 和终端历史中，后续项目讨论无法追踪为什么允许或不允许进入下一批。

### 方案 B：新增 Phase 2 运行审查文档，并同步 README/details

优点是把事实证据、边界判断和下一步计划沉淀到项目资料中，同时不改核心代码、不扩大实现面。它符合当前项目“证据边界先行”的节奏。

缺点是不会把 21MB ignored artifacts 纳入 git；如需复核原始样本，需要在本机 artifact 目录查看或重新运行命令。

### 方案 C：在本轮继续扩到 1000+ requested samples 或新增任务族

优点是推进更快。缺点是 500 级审查刚完成，立刻扩大任务复杂度容易掩盖当前需要确认的事实：默认入口是否稳定、字段覆盖是否一致、失败边界是否可解释。

推荐方案：**方案 B**。

## 5. 核心设计

新增一份 tracked 审查文档：

```text
docs/evidence/simulation-runs/2026-06-10-phase2-maniskill-sapien-review.md
```

文档记录：

- 运行环境。
- 精确命令。
- 首次新运行结果。
- 第二次复用结果。
- completed / failed / skipped / reused 分布。
- `failure_boundary_counts`。
- `field_coverage_trend`。
- 当前状态判断。
- 保守边界。
- 下一阶段建议。

同步更新：

- `README.md`
- `README.html`
- `details.md`
- `details.html`

文档口径：

- ManiSkill/SAPIEN 可以进入下一批 accumulation 默认入口，但只是在当前 headless backend probe 和数据契约层面的 `ready_to_scale_with_conditions`。
- 由于没有 failed samples，本轮不需要触达 `locked_for_next_batch_with_conditions`；该状态保留给“存在少量允许 failure boundary，但 completed 数据契约稳定”的情形。
- 本轮不代表最终仿真器选型。
- 本轮不代表真实焊接质量验证。
- 本轮不代表真实机器人执行验证。

## 6. 不做事项

- 不修改 shard accumulation 核心代码。
- 不提交 ignored raw artifacts、sample artifacts 或 21MB 仿真输出目录。
- 不新增第三个默认 `WeldSkillUnit`。
- 不扩到 1000+ requested samples。
- 不切换 Gazebo/MoveIt、Isaac 或 ROS 为默认入口。
- 不把 ManiSkill/SAPIEN 写成最终仿真器。
- 不把 headless `Empty-v1` backend probe 写成真实工艺仿真或真实焊接质量验证。

## 7. 成功标准

本阶段完成后应满足：

- Phase 2 已在真实 `weld-maniskill` 环境下运行过 500 requested samples。
- 首次运行和复用运行的分布被记录。
- failure boundary counts 和 field coverage trend 被明确审查。
- README/details 与 HTML 阅读版同步更新。
- 默认验证 `uv run pytest -q` 通过。
- 变更通过 PR 合并，合并后清理本地分支。

## 8. 下一阶段建议

如果本阶段验证继续成立，下一阶段建议进入 **下一批默认入口锁定后的 1000 requested samples 计划**：

1. 继续使用 ManiSkill/SAPIEN 作为下一批 accumulation 默认入口。
2. 保持当前 2 个默认任务族，不急于新增任务族。
3. 将下一批规模提高到 10 shards x 100 requested samples 或等价的 1000 requested samples。
4. 在 1000 级运行前先修正文档中仍指向 Phase 1 的 `next_scale_recommendation` 文案，使 report 对 Phase 2 完成后的下一步表达更准确。
5. 若下一批出现 failure boundary，优先修环境、仿真运行、adapter/data contract 边界，而不是切换仿真器或上真机。
