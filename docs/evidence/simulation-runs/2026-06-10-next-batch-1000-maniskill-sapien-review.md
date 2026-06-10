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

运行中出现 SAPIEN Vulkan fallback 与 pinocchio 缺失 warning；这些 warning 未导致样本失败，也没有进入 failure boundary。

## 运行命令

```bash
conda run -n weld-maniskill python -m weldcore.simulation_bakeoff.maniskill_accumulation_pipeline \
  --outdir artifacts/simulation/maniskill-sapien-accumulations \
  --accumulation-id maniskill-sapien-accumulation-next-batch-1000 \
  --shards 10 \
  --samples-per-task 50
```

首次运行完成后、复用运行前，已读取首次 `accumulation_report.json` 并摘录关键分布；随后同命令复跑覆盖了默认 `accumulation_report.json`，用于验证 shard 复用。

## 首次运行分布

| 指标 | 结果 |
| --- | --- |
| requested samples | 1000 |
| completed samples | 1000 |
| failed samples | 0 |
| skipped samples | 0 |
| shard count | 10 |
| completed shard count | 10 |
| reused shard count | 0 |
| failed shard count | 0 |
| shard status | 10 x `completed_new_run` |
| report status | `ready_to_scale_with_conditions` |

## 复用运行分布

| 指标 | 结果 |
| --- | --- |
| requested samples | 1000 |
| completed samples | 1000 |
| failed samples | 0 |
| skipped samples | 0 |
| shard count | 10 |
| completed shard count | 0 |
| reused shard count | 10 |
| failed shard count | 0 |
| shard status | 10 x `reused_existing_result` |
| report status | `ready_to_scale_with_conditions` |

## Failure Boundary Counts

`failure_boundary_counts` 为空。本轮没有出现环境缺失、仿真运行失败、adapter 转换失败、dataset 导出失败、evidence 导出失败或 data contract 不完整。

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

`dataset_index.json` 汇总同样为 1000 requested / 1000 completed / 0 failed / 0 skipped，`failure_boundaries` 为空；requested sample coverage 与 completed sample coverage 均显示 raw artifact、adapter result、experience dataset 和 evidence bundle 覆盖率为 1.0。

## Recommendation 与边界

本轮 report 的 `next_scale_recommendation` 为：

```text
prepare_next_batch_1000_requested_samples_keep_2_default_task_families_continue_maniskill_sapien_accumulation_entry_fix_failure_boundaries_before_switching_routes
```

这个字段沿用上一阶段的保守建议文本，不表示已经完成最终仿真器选型。结合本轮 1000 requested samples 审查，项目层面的下一步应从“准备 1000 next-batch”转向“持续 accumulation 审查层”。

本轮仍只证明 ManiSkill/SAPIEN headless backend probe 和项目数据契约可在 1000 requested samples 级别稳定运行；不证明真实焊接质量，不构成 WPS/PQR，不表示真实机器人可执行，也不表示最终仿真器选型完成。

## 下一步

建议下一阶段进入持续 accumulation 审查层：

1. 建立跨批次 accumulation ledger，记录 Phase 1、Phase 2、1000 next-batch 的运行元数据、复用状态、failure boundary counts 和 field coverage。
2. 继续保持当前 2 个默认任务族，先观察多批次稳定性，再讨论是否新增第三个默认任务族。
3. 把专家审查对象定义为 `SimulationEvidenceBundle` / experience dataset / `RobotProcessPackageDraft` 的组合，而不是直接进入真机执行。
4. 若未来批次出现 failure boundary，优先修复具体边界并复跑受影响 shard，再讨论仿真器切换或真实机器人路线。
