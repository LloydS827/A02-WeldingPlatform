# ManiSkill/SAPIEN 小批量默认仿真入口设计

日期：2026-06-09

## 1. 背景

项目已经完成统一仿真 adapter 第一轮 facade / registry：

```text
SimulationTaskSpec
-> SimulationAdapterRoute
-> run_adapter_route()
-> SimulatorAdapterResult
-> SimulationEvidenceBundle
```

当前三条路线已经进入统一 route metadata 和执行入口：

- `simlite_reference`：L0 稳定基线。
- `maniskill_sapien`：阶段性默认入口候选。
- `gazebo_moveit`：机器人规划侧候选和低频反证路线。

下一步需要从“单任务/单次尝试”推进到“小批量仿真数据积累入口”。这一轮不再只证明 adapter 能被调用，而是要让 ManiSkill/SAPIEN route 能围绕少量核心 `WeldSkillUnit` 形成可追踪、可落盘、可审查的小批量运行样本。

## 2. 设计目标

本阶段目标是建立 **ManiSkill/SAPIEN 小批量默认仿真入口**。

它要回答：

1. 如何表达一次小批量仿真请求。
2. 如何把 2 个默认 `WeldSkillUnit` 对应的任务各生成约 10 条运行样本。
3. 每条样本如何追踪 `batch_id`、`task_id`、`sample_id`、`seed`、`variation_policy` 和 route id。
4. 每条完成样本如何落成 raw artifact、`SimulatorAdapterResult`、`SimulationEvidenceBundle` 和 experience dataset export。
5. 失败样本如何进入统一 failure boundary，而不是中断整个批次。
6. 默认 CI 如何验证数据契约和失败边界，同时不要求本机真实 ManiSkill/SAPIEN 环境。

本阶段不是最终仿真器选型，不做入口锁定报告，不做真实机器人执行验证，不做真实焊接质量验证，不替代 WPS/PQR。

## 3. 阶段位置

整体路线分三轮：

```text
第一轮：统一 adapter facade / registry
第二轮：ManiSkill/SAPIEN 小批量默认入口
第三轮：数据积累前置报告与入口锁定
```

当前 spec 覆盖第二轮。

第二轮完成后，项目应具备小批量数据生成入口，但还不能宣称 ManiSkill/SAPIEN 已被锁定为长期默认仿真器。

第三轮应基于第二轮产物，输出字段覆盖、失败边界、可积累字段、mock/假设字段和下一轮入口决策报告。

## 4. 核心口径：运行样本优先

本阶段的“样本”定义为一次可追踪的运行尝试。

每条样本首先代表：

```text
one task
+ one route
+ one seed
+ one variation policy
-> one raw artifact
-> one adapter result
-> one evidence bundle
-> one experience dataset export when completed
```

第一版不要求每条样本都产生复杂真实物理差异，也不要求每条样本都完成真实 ManiSkill/SAPIEN 后端调用。

完成样本必须生成 `experience_dataset.json`。失败或跳过样本不生成 dataset，并把 `experience_dataset_uri` 记为空，同时通过固定的 failure artifact 记录失败边界。

默认样本口径是：

- 能追踪。
- 能落盘。
- 能进入统一 evidence boundary。
- 成功和失败都被记录。
- 可为第三轮报告提供字段覆盖和失败边界证据。

## 5. 样本规模

第一版默认批次规模：

- route：`maniskill_sapien`
- task：2 个默认 `SimulationTaskSpec`
  - `task-long-straight-horizontal-tracking`
  - `task-corner-horizontal-transition`
- 每个 task：10 条运行样本
- 总请求样本数：20

第三个 `WeldSkillUnit` 暂不强行进入第二轮。它可以作为后续扩展对象，避免当前任务契约和扰动策略还不稳定时扩大范围。

## 6. 核心组件

### 6.1 SimulationBatchSpec

表达一次小批量仿真请求。

建议字段：

- `batch_id`
- `route_id`
- `task_specs`
- `samples_per_task`
- `sample_variation_policy`
- `seed_start`
- `output_root`
- `comparison_route_ids`
- `stage_boundary`

第一版默认：

```text
route_id = "maniskill_sapien"
samples_per_task = 10
sample_variation_policy = "deterministic_micro_offset"
comparison_route_ids = ("simlite_reference",)
stage_boundary = "simulation_only_not_real_welding_quality"
```

`comparison_route_ids` 第一版只作为批次 spec 的对照元数据和第三轮报告线索，不在第二轮默认批次中逐样本执行，也不计入 `requested_sample_count`。Gazebo/MoveIt 保留为 route registry 中的规划候选，不进入小批量默认运行。

### 6.2 SimulationSampleRun

表达批次中的单条运行样本。

建议字段：

- `batch_id`
- `sample_id`
- `task_id`
- `route_id`
- `seed`
- `variation_policy`
- `status`
- `raw_artifact_uri`
- `adapter_result_uri`
- `evidence_bundle_uri`
- `experience_dataset_uri`
- `failure_boundary`
- `evidence_notes`

`status` 第一版建议：

- `completed`
- `failed`
- `skipped`

`sample_id` 应可由 batch、task、route 和 seed 稳定生成，例如：

```text
sample-{batch_id}-{route_id}-{task_id}-{seed}
```

### 6.3 SimulationBatchResult

表达一次批次运行的汇总结果。

建议字段：

- `batch_id`
- `route_id`
- `task_count`
- `requested_sample_count`
- `completed_sample_count`
- `failed_sample_count`
- `skipped_sample_count`
- `sample_runs`
- `failure_boundaries`
- `stage_boundary`
- `next_step_hint`

它不替代 `SimulationEvidenceBundle`。它只是批次级索引、统计和下一步提示。

### 6.4 VariationPolicy

第一版只做轻量占位，不做复杂扰动系统。

建议支持：

- `none`
- `deterministic_micro_offset`

`none` 表示不修改任务输入，只改变 seed 和样本标识。

`deterministic_micro_offset` 的第二轮默认验收是元数据占位：每条样本必须记录由 seed 派生的 deterministic offset descriptor，但不要求第一版实际修改 `SimulationTaskSpec` 或 `task_config.json`。如果实现中顺手加入真实 task config 微偏移，也必须保持确定性，并且不得把该偏移解释为真实工艺扰动或质量影响。

## 7. 数据流

主数据流：

```text
SimulationBatchSpec
-> default_simulation_adapter_routes()
-> get_default_batch_route()
-> default_simulation_task_specs()
-> sample plan generation
-> per-sample ManiSkill/SAPIEN runner
-> raw_artifact.json
-> adapter_result.json
-> evidence_bundle.json
-> experience_dataset.json when completed
-> SimulationSampleRun
-> SimulationBatchResult
```

每条样本应尽量复用现有 ManiSkill/SAPIEN pipeline：

```text
SimulationTaskSpec
-> maniskill_task_config_from_spec()
-> generate_rule_based_demo()
-> run_maniskill_lightweight()
-> adapt_maniskill_artifact()
-> build_maniskill_experience_dataset()
-> build_simulation_evidence_bundle()
```

但第二轮需要把当前 `run_maniskill_spike_pipeline()` 从“按 task 输出一次”提升为“按 task x sample 输出多次”的批次入口。

## 8. 输出目录约定

建议默认输出：

```text
artifacts/simulation/maniskill-sapien-batches/
└── {batch_id}/
    ├── batch_spec.json
    ├── batch_result.json
    └── samples/
        └── {sample_id}/
            ├── task_config.json
            ├── demo.json
            ├── raw_artifact.json
            ├── adapter_result.json
            ├── evidence_bundle.json
            ├── experience_dataset.json
            └── failure_artifact.json
```

`experience_dataset.json` 只要求 completed 样本存在。失败或 skipped 样本必须写入 `failure_artifact.json`，并在 `SimulationSampleRun.failure_boundary` 中记录原因。失败样本的 `raw_artifact_uri` 优先指向已生成的 `raw_artifact.json`；如果运行在 raw artifact 前失败，则指向 `failure_artifact.json`，确保路径契约稳定。

## 9. 失败边界

沿用现有 failure boundary，并补充批次级边界：

- `environment_missing`
- `simulator_api_changed`
- `task_generation_failed`
- `demo_generation_failed`
- `simulation_run_failed`
- `artifact_missing`
- `adapter_conversion_failed`
- `data_contract_incomplete`
- `batch_generation_incomplete`
- `sample_generation_failed`
- `experience_dataset_export_failed`

批次失败策略：

- 单条样本失败不终止批次。
- 单个 task 全部失败时，批次仍输出结果，但 `failed_sample_count` 反映失败。
- 如果 batch spec 本身无效，可以整体失败并不生成样本。
- 默认 CI 中外部环境缺失应表现为 failure boundary 或 skipped，不应表现为未处理异常。

## 10. 默认测试与真实环境验证

### 10.1 第二轮 MVP 验收

第二轮默认验收固定为：

- `batch_spec.json` 能表达 2 个默认 task、每个 task 10 条样本，总请求样本数 20。
- `batch_result.json` 汇总 primary route `maniskill_sapien` 的 20 条 requested samples。
- `comparison_route_ids` 不触发 simlite 逐样本运行，不计入 requested / completed / failed / skipped。
- 默认 CI 可以通过 fake 或 lightweight path 验证批次数据契约，不依赖真实 ManiSkill/SAPIEN 环境。
- completed 样本必须有 `raw_artifact.json`、`adapter_result.json`、`evidence_bundle.json` 和 `experience_dataset.json`。
- failed / skipped 样本必须有 `failure_artifact.json`，且 `raw_artifact_uri` 指向已存在的 raw artifact 或 failure artifact。
- 第二轮不生成入口锁定报告；第三轮才允许判断 `locked_with_conditions` 或 `locked_for_next_batch`。

### 10.2 默认测试

默认测试只证明：

- batch spec 可以序列化。
- sample run 可以序列化。
- batch result 可以汇总 completed / failed / skipped。
- 每条样本有稳定 `sample_id`、`seed`、`batch_id`、`task_id` 和 `route_id`。
- 外部环境缺失不会让默认测试失败。
- artifact/evidence/dataset 的路径契约稳定。

默认测试不证明：

- 本机真实 ManiSkill/SAPIEN 后端一定可用。
- 仿真轨迹具有真实焊接物理意义。
- ManiSkill/SAPIEN 已被最终选型。

### 10.3 真实环境验证

真实环境验证应作为可选命令或手动验收：

```bash
uv run python -m weldcore.simulation_bakeoff.maniskill_batch_pipeline --outdir artifacts/simulation/maniskill-sapien-batches
```

只有该路径实际完成小批量运行后，第三轮报告才能把 ManiSkill/SAPIEN 写成 `locked_with_conditions` 或 `locked_for_next_batch`。

## 11. 报告关系

第二轮不做完整入口锁定报告，但应为第三轮准备数据。

第二轮可以输出简单 batch summary：

- batch id
- route id
- task count
- requested sample count
- completed / failed / skipped count
- failure boundaries
- artifact output root

第三轮再基于这些数据输出：

- 字段覆盖报告。
- 可积累字段 / mock 字段 / 假设字段 / 人工补充字段分类。
- ManiSkill/SAPIEN 是否继续作为下一轮默认入口。
- 回退到 simlite 或继续反证的条件。

## 12. 与现有对象关系

`SimulationBatchSpec` 和 `SimulationBatchResult` 是批次层对象。

它们不替代：

- `SimulationTaskSpec`
- `SimulatorAdapterResult`
- `SimulationEvidenceBundle`
- `SkillDataset`
- `RobotProcessPackageDraft`

第二轮应保持机器人侧接口不变。`RobotProcessPackageDraft` 仍然只从单条 evidence bundle 或后续明确聚合入口进入，不在本轮改造成批次级机器人工艺包。

## 13. 文档更新

第二轮完成后应更新：

- `details.md`
- `details.html`
- 对应 evidence/report 文档，如新增批次 summary。

如果 README 中“下一阶段方向”仍停留在第一轮 adapter facade 或过泛化的反证描述，应同步更新：

- `README.md`
- `README.html`

但 README 应保持项目入口定位，不写成每日更新日志。

## 14. 非目标

本阶段不做：

- 最终仿真器定型。
- 数据积累前置报告与入口锁定。
- 大规模仿真数据平台。
- 复杂扰动策略和参数搜索。
- 完整 Gazebo/MoveIt 批量运行。
- 真实机器人控制。
- 真实焊接质量验证。
- 正式 WPS/PQR。
- 专家审核系统完整实现。

## 15. 后续路线

第二轮完成后，建议第三轮进入：

```text
数据积累前置报告与入口锁定
```

第三轮重点不是继续扩大样本量，而是基于第二轮样本回答：

1. ManiSkill/SAPIEN 小批量入口是否稳定。
2. 哪些字段真正可积累。
3. 哪些字段仍是假设、mock 或失败边界。
4. 是否允许 `locked_with_conditions` 或 `locked_for_next_batch`。
5. 下一轮是否进入更大规模数据积累。

只有第三轮报告通过后，才建议进入更大规模仿真数据积累。
