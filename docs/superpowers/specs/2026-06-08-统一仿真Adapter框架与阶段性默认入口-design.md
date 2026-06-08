# 统一仿真 Adapter 框架与阶段性默认入口设计

日期：2026-06-08

## 1. 背景

项目已经完成从 `WeldSkillUnit` 到 `SimulationTaskSpec`、`SimulatorAdapterResult`、`SimulationEvidenceBundle`、`RobotProcessPackageDraft`、`RobotContextSpec` 和 `RobotFeasibilityResult` 的结构链路。

当前最重要的问题已经从“能不能表达仿真证据”推进为“能不能选出阶段性默认仿真入口，并开始小批量积累数据”。

前一轮讨论已经形成几个关键判断：

- 下一阶段可以推进到仿真入口选择，而不只停留在反证报告。
- 选择不应被写成最终仿真器定型，而是阶段性默认入口。
- ManiSkill/SAPIEN 是第一阶段默认入口主候选。
- simlite 继续作为 L0 稳定基线。
- Gazebo/MoveIt 继续作为机器人规划侧候选和低频对照路线。
- 第一轮数据规模采用 2-3 个 `WeldSkillUnit`，每个约 10 条样本。
- 目标需要提高到统一仿真 adapter 框架，而不是只给 ManiSkill/SAPIEN 做一次性入口。

因此，本阶段设计采用“统一 adapter 框架 + ManiSkill/SAPIEN 阶段性默认入口 + 小批量数据积累”的组合路线。

## 2. 设计目标

本阶段目标是建立一个可逐步扩展的仿真 adapter 框架，并在该框架下把 ManiSkill/SAPIEN 设为第一轮阶段性默认仿真入口。

它要回答：

1. 仿真路线如何统一接入 `SimulationTaskSpec`。
2. 不同路线如何统一输出 `SimulatorAdapterResult` 和 `SimulationEvidenceBundle`。
3. ManiSkill/SAPIEN 是否满足小批量数据积累的最低条件。
4. simlite、ManiSkill/SAPIEN、Gazebo/MoveIt 各自当前角色是什么。
5. 每一轮推进完成后如何判断是否进入下一轮。

本阶段不是最终仿真软件选型，不做真实焊接质量验证，不做正式 WPS/PQR，不做真实机器人执行验证。

## 3. 推荐路线

采用分阶段方案二：

```text
统一仿真 Adapter 契约
-> ManiSkill/SAPIEN 阶段性默认入口
-> 小批量仿真数据积累
-> 批次报告与下一轮入口判断
```

这条路线比“只写反证报告”更能推进项目进度，也比“直接硬切 ManiSkill/SAPIEN”更稳，因为它保留统一接口、失败边界和后续替换能力。

## 4. 总体架构

当前已有链路保持不变：

```text
WeldSkillUnit
-> SimulationTaskSpec
-> SimulatorAdapterResult
-> SimulationEvidenceBundle
-> SkillDataset / experience dataset
-> RobotProcessPackageDraft
```

新增或收束的概念放在 `SimulationTaskSpec` 和 `SimulatorAdapterResult` 之间：

```text
SimulationTaskSpec
-> SimulationAdapterRegistry
-> SimulationAdapterRoute
-> route-specific runner
-> SimulatorAdapterResult
```

第一版不需要重构为复杂插件系统。它应先作为现有 `simulation_bakeoff` 的最小 facade / registry：

- 复用 `run_simlite_reference`。
- 复用 `attempt_maniskill_sapien` 和现有 ManiSkill/SAPIEN spike pipeline。
- 复用 `attempt_gazebo_moveit` 的失败边界表达。
- 统一 route metadata、默认入口、对照入口和可用性状态。

## 5. 核心组件

### 5.1 SimulationAdapterRoute

表达一条仿真路线的最小元信息：

- `route_id`
- `display_name`
- `role`
- `status`
- `runner`
- `default_for_batch`
- `dependency_boundary`
- `evidence_boundary`

建议第一版 route：

| route_id | role | default_for_batch | 当前定位 |
| --- | --- | --- | --- |
| `simlite_reference` | `baseline` | false | L0 稳定基线和测试对照 |
| `maniskill_sapien` | `default_candidate` | true | 第一轮阶段性默认入口 |
| `gazebo_moveit` | `planning_candidate` | false | 机器人规划侧候选和低频反证 |

### 5.2 SimulationAdapterRegistry

职责是列出当前可用路线，并按 route id 调用对应 runner。

第一版 registry 不做动态插件加载，也不做外部配置系统。它只需要提供：

- `default_simulation_adapter_routes()`
- `get_default_batch_route()`
- `run_adapter_route(route_id, task_spec)`
- `run_comparison_routes(task_spec)`

这样后续可以自然扩展到 Isaac、ROS 或其他仿真工具，但当前不为未来路线提前设计复杂机制。

### 5.3 SimulationBatchSpec

表达一次小批量数据积累请求。

建议字段：

- `batch_id`
- `route_id`
- `task_specs`
- `samples_per_task`
- `sample_variation_policy`
- `output_root`
- `comparison_route_ids`
- `stage_boundary`

第一轮默认值：

- route：`maniskill_sapien`
- task：2-3 个 `WeldSkillUnit` 对应的 `SimulationTaskSpec`
- 每个 task：约 10 条样本
- 对照：simlite 必选，Gazebo/MoveIt 可作为失败边界对照
- stage boundary：`simulation_only_not_real_welding_quality`

### 5.4 SimulationBatchResult

表达一次批量运行后的汇总结果。

建议字段：

- `batch_id`
- `route_id`
- `task_count`
- `requested_sample_count`
- `completed_sample_count`
- `failed_sample_count`
- `evidence_bundle_ids`
- `experience_dataset_ids`
- `failure_boundaries`
- `field_coverage`
- `default_entry_decision`
- `next_round_recommendation`

它不替代 `SimulationEvidenceBundle`。它只是批次级索引和判断摘要。

### 5.5 DefaultSimulationEntryDecision

表达阶段性入口选择结论。

建议状态：

- `locked_for_next_batch`
- `locked_with_conditions`
- `fallback_to_simlite`
- `blocked_by_environment`
- `blocked_by_data_contract`

第一轮不产生入口锁定结论，只验证 route facade 和 failure boundary。

第二轮小批量生成完成后，ManiSkill/SAPIEN 最多进入候选状态：

```text
locked_with_conditions
```

第三轮报告完成后，只有当小批量样本成功率、字段覆盖和失败边界都满足最低条件时，才提升为：

```text
locked_for_next_batch
```

## 6. 阶段推进计划

### 第一轮：统一 Adapter Facade

目标：把现有 simlite、ManiSkill/SAPIEN、Gazebo/MoveIt 包进统一 route registry。

验收条件：

- 可以列出三条 route 及其角色。
- 可以通过 route id 运行单个 `SimulationTaskSpec`。
- 每条 route 都输出统一的 `SimulatorAdapterResult`。
- 失败、环境缺失、API 变化都进入 failure boundary。
- 默认测试不依赖本机真实 ManiSkill/SAPIEN 环境。

本轮不要求批量生成 10 条样本。

### 第二轮：ManiSkill/SAPIEN 小批量默认入口

目标：在统一 adapter 框架下，让 ManiSkill/SAPIEN 支持 2-3 个 `WeldSkillUnit`、每个约 10 条样本的小批量生成。

验收条件：

- 有 `SimulationBatchSpec` 和 `SimulationBatchResult`。
- 可以生成批次级 raw artifact、adapter result、experience dataset、`SimulationEvidenceBundle`。
- 每条样本有可追踪的 `batch_id`、`task_id`、`sample_id` 和 route id。
- 失败样本也进入统一结果，不中断整个批次。
- simlite 至少可作为同 task 的 L0 对照。

本轮可以仍然把 Gazebo/MoveIt 作为失败边界对照，不要求真正运行完整规划。

### 第三轮：数据积累前置报告与入口锁定

目标：基于第一批小样本输出可审查报告，判断 ManiSkill/SAPIEN 是否作为下一轮默认入口。

验收条件：

- 报告列出每条 route 的成功/失败情况。
- 报告列出字段覆盖情况。
- 报告区分可积累字段、mock 字段、假设字段、人工补充字段和后续真机验证字段。
- 报告给出 `DefaultSimulationEntryDecision`。
- 如果锁定 ManiSkill/SAPIEN，需要写明锁定条件和回退条件。

本轮之后才能进入更大规模的数据积累。

## 7. 最低锁定条件

ManiSkill/SAPIEN 要成为阶段性默认入口，至少需要满足“数据积累可用条件”：

- 能从现有 `SimulationTaskSpec` 自动生成 ManiSkill/SAPIEN task config。
- 能对 2-3 个默认任务生成小批量样本。
- 能输出 raw artifact。
- 能转成 `SimulatorAdapterResult`。
- 能转成 `SimulationEvidenceBundle`。
- 能形成 experience dataset / `SkillDataset` 兼容输出。
- 失败样本不破坏批次，而是进入 failure boundary。
- 默认测试不依赖本机外部仿真环境。
- 报告能说明哪些字段可积累、哪些字段仍是假设或待验证。

不要求本阶段证明真实机器人可达性、碰撞、焊接质量或正式工艺合规。

## 8. 数据流

第一轮 facade 数据流：

```text
default_simulation_task_specs()
-> SimulationAdapterRegistry
-> selected SimulationAdapterRoute
-> SimulatorAdapterResult
-> build_simulation_evidence_bundle()
```

第二轮批量数据流：

```text
SimulationBatchSpec
-> route registry
-> ManiSkill/SAPIEN batch runner
-> raw artifacts
-> SimulatorAdapterResult[]
-> SimulationEvidenceBundle[]
-> experience dataset exports
-> SimulationBatchResult
```

第三轮报告数据流：

```text
SimulationBatchResult
+ SimulationEvidenceBundle[]
+ route comparison summary
-> default entry decision report
```

## 9. 错误与失败边界

所有外部仿真失败都必须被记录为 evidence，而不是让默认工作流崩掉。

第一版失败边界沿用并扩展现有表达：

- `environment_missing`
- `simulator_api_changed`
- `task_generation_failed`
- `demo_generation_failed`
- `simulation_run_failed`
- `artifact_missing`
- `adapter_conversion_failed`
- `data_contract_incomplete`
- `batch_generation_incomplete`

失败边界不等于项目失败。它是当前仿真选型和数据积累前置判断的一部分。

## 10. 测试策略

第一轮测试：

- registry 能列出三条 route。
- route metadata 正确表达 baseline/default candidate/planning candidate。
- 每条 route 都能通过同一 facade 返回 `SimulatorAdapterResult`。
- 外部环境缺失时返回 failure boundary，而不是抛出未处理异常。

第二轮测试：

- `SimulationBatchSpec` 可以序列化。
- 小批量 runner 可以生成预期数量的样本记录。
- completed 与 failed 样本都进入 `SimulationBatchResult`。
- 每条样本可以追踪到 task、route、batch 和 artifact。
- 默认测试不要求真实 ManiSkill/SAPIEN 安装。

默认 CI 测试只证明数据契约、批次汇总和失败边界行为，不证明真实 ManiSkill/SAPIEN 环境已经可用于数据积累。

真实环境支持的验证应作为可选命令或手动验收路径运行；只有该路径实际完成小批量样本生成后，第三轮报告才可以把 ManiSkill/SAPIEN 写成 `locked_with_conditions` 或 `locked_for_next_batch`。

第三轮测试：

- 报告能读取 batch result 和 evidence bundles。
- 字段覆盖统计稳定。
- `DefaultSimulationEntryDecision` 在成功、部分失败、环境缺失和数据契约不完整时给出不同结论。

完整验证仍保持：

```bash
cd weld-experience-engine
uv run pytest -q
```

## 11. 文档与交付

每一轮完成后都需要同步更新：

- `details.md`
- `details.html`
- 对应 `docs/superpowers/plans/` 实施计划
- 对应 evidence/report 文档

如果 README 中的项目默认主线、验证命令或入口判断发生变化，也要同步更新：

- `README.md`
- `README.html`

每一轮都应独立完成、独立验证、独立合并，不把三轮实现混在一个过大的 PR 里。

## 12. 非目标

本阶段不做：

- 最终仿真器定型。
- 大规模仿真数据平台。
- 完整 ROS/Gazebo/MoveIt 集成。
- Isaac 或更多仿真软件接入。
- 真实机器人控制。
- 真实焊接质量验证。
- 正式 WPS/PQR。
- 专家审核系统完整实现。

## 13. 后续节奏

推荐按以下顺序一轮一轮推进：

1. 写第一轮实施计划：统一 adapter facade / registry。
2. 实施第一轮并合并。
3. 回顾第一轮结果，更新 details。
4. 写第二轮实施计划：ManiSkill/SAPIEN 小批量默认入口。
5. 实施第二轮并合并。
6. 回顾第二轮结果，更新 details。
7. 写第三轮实施计划：数据积累前置报告与入口锁定。
8. 实施第三轮并合并。
9. 再决定是否进入更大规模仿真数据积累。

这种节奏可以保持项目持续前进，也能避免把“统一框架”一次性做成过重的基础设施。
