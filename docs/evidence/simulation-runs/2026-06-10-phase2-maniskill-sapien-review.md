# Phase 2 ManiSkill/SAPIEN 真实环境运行审查

日期：2026-06-10

## 结论

Phase 2 在 `weld-maniskill` conda 环境完成 5 shards x 2 个默认任务族 x 50 samples-per-task，共 500 requested samples 的真实 ManiSkill/SAPIEN headless backend probe。首次运行 500/500 completed，第二次同命令复跑 5 个 shard 均复用已有 `batch_result.json`。

当前判断是 `ready_to_scale_with_conditions`：ManiSkill/SAPIEN 可以作为下一批 accumulation 默认入口继续使用，但这不是最终仿真器选型、真实焊接质量验证或真实机器人执行验证。

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
  --accumulation-id maniskill-sapien-accumulation-phase-2 \
  --shards 5 \
  --samples-per-task 50
```

## 首次运行分布

| 指标 | 结果 |
| --- | --- |
| requested samples | 500 |
| completed samples | 500 |
| failed samples | 0 |
| skipped samples | 0 |
| shard status | 5 x `completed_new_run` |
| report status | `ready_to_scale_with_conditions` |

## 复用运行分布

| 指标 | 结果 |
| --- | --- |
| requested samples | 500 |
| completed samples | 500 |
| failed samples | 0 |
| skipped samples | 0 |
| shard status | 5 x `reused_existing_result` |
| report status | `ready_to_scale_with_conditions` |

## Failure Boundary Counts

`failure_boundary_counts` 为空。本轮没有出现环境缺失、仿真运行失败、adapter 转换失败、dataset 导出失败或 data contract 不完整。

## Field Coverage

5 个 shard 的 completed sample coverage 均为：

| 字段 | 覆盖率 |
| --- | --- |
| `raw_artifact_uri` | 1.0 |
| `adapter_result_uri` | 1.0 |
| `experience_dataset_uri` | 1.0 |
| `evidence_bundle_uri` | 1.0 |
| `failure_artifact_uri` | 0.0 |

`failure_artifact_uri` 为 0.0 是预期结果，因为本轮没有 failed samples。

## Warning 与边界

运行中出现 SAPIEN Vulkan fallback 与 pinocchio 缺失 warning，但没有导致样本失败，也没有进入 failure boundary。

本轮仍只证明 ManiSkill/SAPIEN headless backend probe 和项目数据契约可在 500 requested samples 级别稳定运行；不证明真实焊接质量，不构成 WPS/PQR，不表示真实机器人可执行，也不表示最终仿真器选型完成。

## 下一步

建议下一阶段进入 1000 requested samples 计划准备：保持当前 2 个默认任务族，继续使用 ManiSkill/SAPIEN 作为默认 accumulation 入口；在扩大前先修正 report 中仍偏 Phase 1 的 `next_scale_recommendation` 文案。
