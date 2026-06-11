# 焊接技能大师平台项目进展记录

更新时间：2026-06-11

这份文件用于记录 A02「焊接技能大师平台」每一阶段完成了什么、下一步准备做什么、哪些判断发生了变化。它不是项目入口说明；项目入口请看 [README.md](README.md)。

## 文件定位

- `README.md`：项目入口，面向任何新读者说明项目定位、核心链路、当前能力、如何运行和边界。
- `details.md`：阶段更新记录，面向项目讨论记录近期更新、当前判断、下一步计划和风险提醒。

本文件应同步维护 [HTML 阅读版](details.html)。更新根目录 `README.md`、本文件或类似面向读者的阶段/路线说明时，也要同步刷新对应 `.html` 阅读副本。

## 当前一句话状态

项目已经完成从 `WeldSkillUnit`、轻量仿真证据、经验数据到机器人候选草案前置接口的结构链路，并完成统一仿真 adapter 第一轮 facade / registry、ManiSkill/SAPIEN 小批量默认仿真入口、仿真数据积累启动层、Phase 2 sharded accumulation 入口、1000 requested samples next-batch 真实环境运行审查，以及批量焊接任务建模与验证闭环启动层。当前既保留 100/500/1000 requested samples 的运行审查口径，也已能从当前 2 个默认任务族生成 8 个 modeled `SimulationTaskSpec`，输出 `modeling_validation_report` 并进入下一轮小批量仿真验证准备状态。

## 当前主线判断

现在不适合跳到真实机器人控制或完整 MoveIt/Gazebo 集成，也不应继续只按 requested samples 数量线性扩张。更合理的节奏是先把“批量任务从哪里来、如何验证、如何进入专家候选对象”做清楚，再继续扩大仿真数据积累。

更合理的主线是：

```text
WeldSkillUnit
-> SimulationTaskSpec
-> BatchModelingSpec / modeled SimulationTaskSpec
-> modeling_validation_report
-> candidate simulator adapter
-> SimulatorAdapterResult
-> SimulationEvidenceBundle
-> SkillDataset / experience dataset
-> RobotProcessPackageDraft
```

这一段必须先稳定下来。只有当仿真任务契约、批量建模、输出证据、失败边界和数据转换都可复跑、可比较、可审查之后，项目才适合继续进入更大规模的持续数据积累。

这里的“反证工作”很重要：候选仿真软件不是因为名字先进就自动成为主线，而要通过同一组任务、同一套输出契约和同一份证据报告证明它能接入项目数据结构；不能接入的地方也要明确记录失败原因。

## 近期更新

### 2026-06-11

- 完成批量焊接任务建模与仿真验证闭环设计和实施计划，并通过 review。
- 新增 `BatchModelingSpec`、`TaskModelingVariation`、`ModeledSimulationTask`、`ModelingValidationReport` 和 `ModelingCoverageSummary`。
- 新增 `build_modeled_simulation_tasks`，默认从 2 个 source tasks x 4 variants 生成 8 个 modeled `SimulationTaskSpec`。
- 新增 `build_modeling_validation_report`，验证 source 覆盖、modeled task id 一致性、path geometry 变化、输出字段、评价指标、out-of-scope 边界和禁用真实焊接质量术语。
- 建模报告包含 `expert_review_candidate_task_ids` 和 `expert_review_candidate_ratio`；完整默认路径下状态为 `ready_for_simulation_batch`，候选比例为 1.0。
- 建模报告会阻止不完整批次：如果只传入部分 modeled tasks，会进入 `blocked_by_modeling_issue`，避免缺 7/8 任务时仍显示 ready。
- 新增 `modeled_task_specs` 和 `simulation_task_specs_from_modeling_payload`，保证 `modeled_task_specs.json` 可恢复成 `SimulationTaskSpec` 并进入 `default_maniskill_batch_spec`。
- 新增 `weldcore.simulation_bakeoff.modeling_pipeline` CLI，输出 `modeling_spec.json`、`modeled_task_specs.json` 和 `modeling_validation_report.json`。
- 当前默认兼容口径为 8 个 modeled tasks x 2 samples = 16 requested samples，用于下一阶段小批量 ManiSkill/SAPIEN 验证。
- 当前仍不做最终仿真器选型、真实焊接质量验证、正式 WPS/PQR 或真实机器人执行结论。

### 2026-06-10

- 完成仿真数据积累启动层设计与实施计划，并通过 review。
- 新增 `SimulationAccumulationBatchSpec`、`SimulationDatasetIndexItem`、`SimulationFieldCoverageSummary`、`SimulationDatasetIndex` 和 `SimulationAccumulationReport`。
- 新增 `build_simulation_dataset_index` 和 `build_simulation_accumulation_report`，可从 `SimulationBatchResult` 汇总 dataset index、字段覆盖和 accumulation 状态。
- `SimulationSampleRun` 增加 `failure_artifact_uri`，避免 raw artifact 已存在时无法准确追踪真实 failure artifact。
- `run_maniskill_batch_pipeline` 支持 `samples_per_task` 和 `seed_start` 参数；默认仍保持 2 个任务 x 10 samples。
- 新增 `run_maniskill_accumulation_pipeline` 和 CLI，默认请求 2 个任务 x 50 samples，共 100 requested samples。
- accumulation 输出包含 `accumulation_spec.json`、`dataset_index.json` 和 `accumulation_report.json`。
- accumulation report 可区分 `accumulating_completed_samples`、`accumulating_with_failures`、`blocked_by_environment`、`blocked_by_pipeline_failure` 和 `ready_to_scale_with_conditions`；其中 `ready_to_scale_with_conditions` 表示 500 requested samples 全 completed 且无 failure boundary 的理想通过状态。
- 完成 sharded accumulation 设计和实现，新增 `SimulationAccumulationShardSpec`、shard report、shard plan 迭代和 shard 结果一致性校验。
- 新增 Phase 2 CLI：`--shards 5 --samples-per-task 50` 可组织 5 个 shard x 100 requested samples，共 500 requested samples。
- shard 运行默认复用已存在且可解析、可校验的 `batch_result.json`，避免每次从零重跑。
- 新增 `--force`，用于忽略已有 `batch_result.json` 并强制重跑 shard。
- accumulation report 新增 shard 级 completed / failed / skipped 汇总、`failure_boundary_counts` 和 `field_coverage_trend`，用于观察 failure boundary counts 与字段覆盖趋势。
- `locked_for_next_batch_with_conditions` 保留给“存在少量允许 failure boundary，但 completed 数据契约稳定”的情况，用于允许 ManiSkill/SAPIEN 作为下一批 accumulation 默认入口继续使用。
- Phase 2 已在真实 `weld-maniskill` 环境完成运行审查。
- 首次运行：500 requested / 500 completed / 0 failed / 0 skipped；5 个 shard 均为 `completed_new_run`。
- 复用运行：同命令复跑 5 个 shard 均为 `reused_existing_result`。
- `failure_boundary_counts` 为空。
- completed sample 的 raw artifact、adapter result、experience dataset 和 evidence bundle 关键字段覆盖率稳定为 1.0；failure artifact 覆盖率为 0.0 是因为本轮没有 failed samples。
- 本轮没有 failed samples，所以状态保持 `ready_to_scale_with_conditions`，不需要触达 `locked_for_next_batch_with_conditions`。
- 完成 1000 requested samples next-batch plan，推荐按 10 shards x 100 requested samples 组织。
- 1000 next-batch 继续保持当前 2 个默认任务族，避免在扩大样本数时同时扩大任务复杂度。
- report 中 `next_scale_recommendation` 已从 Phase 1 后建议修正为 Phase 2 后的 1000 next-batch 建议。
- 下一批若出现 failed samples，采用 failure boundary 策略：优先修环境、仿真运行、adapter/data contract、dataset/evidence export 等具体边界，再讨论切换仿真器或移动到真实机器人路线。
- 当前仍不做最终仿真器选型、真实焊接质量验证或真实机器人执行结论。
- 完成 1000 requested samples next-batch 真实环境运行审查。
- 首次运行：1000 requested / 1000 completed / 0 failed / 0 skipped；10 个 shard 均为 `completed_new_run`。
- 复用运行：同命令复跑 10 个 shard 均为 `reused_existing_result`。
- `failure_boundary_counts` 为空。
- completed sample 的 raw artifact、adapter result、experience dataset 和 evidence bundle 关键字段覆盖率稳定为 1.0；failure artifact 覆盖率为 0.0 是因为本轮没有 failed samples。
- 当前项目判断为 `ready_to_continue_accumulation_with_conditions`，下一轮建议进入跨批次 accumulation ledger / 持续审查层。

### 2026-06-09

- 确认第二轮主线为 ManiSkill/SAPIEN 小批量默认仿真入口。
- 样本口径采用“运行样本优先”：每条样本代表一次可追踪运行尝试，携带 `seed`、`variation_policy`、证据路径和失败边界。
- 新增 `SimulationBatchSpec`、`SimulationSamplePlan`、`SimulationSampleRun` 和 `SimulationBatchResult`，默认表达 2 个任务 x 10 条 ManiSkill/SAPIEN primary 样本。
- 新增 `run_maniskill_batch_pipeline` 和 CLI，可输出 `batch_spec.json`、`batch_result.json` 以及每条样本的 raw artifact、adapter result、evidence bundle、experience dataset 或 failure artifact。
- `comparison_route_ids=("simlite_reference",)` 当前只作为对照元数据，不触发 simlite 逐样本运行，也不计入 requested / completed / failed / skipped。
- 对 task generation、demo generation、runner exception、artifact write、adapter conversion、dataset export 和 evidence export 建立样本级失败边界，单条样本失败不会中断整个 batch。
- completed 样本的 raw artifact、adapter result、experience dataset 和 evidence bundle 已按 `sample_id` 做内部身份收束，避免后续数据积累时出现同一 task 下多条样本 ID 混淆。
- 第二轮只做小批量入口和 batch summary，不做最终仿真器定型或入口锁定报告。
- 第三轮已经转向仿真数据积累启动层，目标是直接开始积累并建立后续规模化批次结构。

### 2026-06-08

- 完成统一仿真 adapter 第一轮 facade / registry：simlite、ManiSkill/SAPIEN、Gazebo/MoveIt 已进入同一 route 元数据和执行入口。
- `simulation_bakeoff` 已改为消费统一 route registry，scorecard 和 evidence generation 使用同一轮 registry 快照。
- ManiSkill/SAPIEN 仍是阶段性默认入口候选，不是最终仿真器定型。
- 本轮不做小批量样本生成和入口锁定报告；下一轮将围绕 ManiSkill/SAPIEN 小批量默认入口推进。

### 2026-06-07

- 完成机器人上下文与可执行性预检接口，并通过 PR #9 合并。
- 新增 `RobotContextSpec`、`RobotFeasibilityProbe`、`RobotFeasibilityResult`。
- 新增轻量机器人上下文预检函数，用于表达缺少机器人型号、TCP、坐标系、可达性、碰撞和关节限制等上下文时的阻塞原因。
- `RobotProcessPackageDraft` 可以在上下文和预检结果足够时推进到 `ready_for_expert_review`。
- `ready_for_robot_execution` 仍然保留，不作为当前可触达状态。
- 修复 Rerun 新版时间 API 兼容问题。
- 合并后主分支验证通过，最近一次完整测试为 `252 passed`。

### 2026-06-06

- 完成从 `SimulationEvidenceBundle` 到 `RobotProcessPackageDraft` 的最小决策接口，并通过 PR #8 合并。
- 明确机器人候选草案只回答“这条仿真经验能否形成未来可审查候选包”，不输出真实机器人执行结论。
- 明确字段来源、缺失字段、专家审查项、真机验证项和 evidence boundary。
- 将工程师整理的焊接工艺参数 Excel 表格纳入仓库，作为参考资料，不作为当前仿真主流程的主数据源。

### 2026-06-05

- 完成 ManiSkill/SAPIEN 本机轻量仿真闭环。
- 建立 `SimulationTaskSpec` 到 ManiSkill/SAPIEN task config 的转换。
- 通过 raw artifact、adapter result 和 `SimulationEvidenceBundle` 验证外部仿真输出可以进入项目数据结构。
- 保留 Gazebo/MoveIt 候选路线的失败边界记录，避免把环境不可用混同为数据结构失败。

### 2026-06-04

- 完成项目级重构，把默认入口从 POC / MVP / gate / 报告集合收束为 Physical AI 焊接技能资产底座。
- 建立 `WeldSkillUnit` 最小框架。
- 建立仿真路线准备、仿真 bake-off 和 Rerun 证据边界说明。
- 将前期 POC、MVP、gate、白皮书和旧计划归档为历史证据。

## 已完成能力

- 可运行的 `weldcore` 引擎。
- `SkillDataset`、`SkillSample`、`WeldSkillPackage` 和迁移评测基础结构。
- `WeldSkillUnit` 最小技能单元表达。
- `SimulationTaskSpec`、`SimulatorAdapterResult`、`SimulationEvidenceBundle` 仿真证据结构。
- simlite L0 稳定仿真和测试基线。
- ManiSkill/SAPIEN 轻量 adapter 试跑路径。
- Gazebo/MoveIt 候选路线失败边界记录。
- 从仿真证据到机器人候选草案的转换。
- 机器人上下文和轻量可执行性预检接口。
- 统一仿真 adapter facade / registry。
- ManiSkill/SAPIEN 小批量默认仿真入口和 batch summary 契约。
- 仿真数据积累启动层、dataset index 和 accumulation report 契约。
- Phase 2 sharded accumulation、已有 batch result 复用、`--force` 强制重跑、failure boundary counts、field coverage trend 和 `locked_for_next_batch_with_conditions` 判断。
- 批量焊接任务建模与验证闭环，默认 2 个 source tasks x 4 variants = 8 个 modeled task specs。
- 报告命令和历史证据归档。

这些能力仍属于软件结构、仿真接入和证据管理能力，不代表真实焊接质量验证、最终仿真器选型或真实机器人执行验证。

## 尚未完成

- 最终仿真软件选型尚未完成。
- 规模化持续积累仿真数据的默认入口已完成 500 requested samples 和 1000 requested samples 级真实环境审查，但 modeled task specs 的小批量 ManiSkill/SAPIEN 验证尚未完成。
- 跨批次 accumulation ledger 尚未建立。
- 候选仿真软件面对 modeled task specs 的稳定性、可复跑性、输出字段覆盖率和失败边界仍需在下一批继续反证。
- 经验数据与技能资产之间的字段追踪还需要进一步收束。
- 专家审查记录结构尚未作为主线对象实现。
- 真实焊机、机器人、焊材、焊后检测和质量结果尚未接成闭环。
- 当前资料、输入规范、仿真假设和工程师参考表格不能替代正式 WPS/PQR。

## 下一步建议

推荐下一阶段任务是：**使用 modeled task specs 做小批量 ManiSkill/SAPIEN 仿真验证**。

目标是在 2 个默认任务族已能生成 8 个 modeled task specs 之后，把建模层真正接到仿真运行层：

1. 使用 `modeled_task_specs.json` 恢复出的 8 个 `SimulationTaskSpec` 组织小批量 batch，建议先按 2-5 samples/task 运行 16-40 requested samples。
2. 记录 modeled batch 的 requested/completed/failed/skipped、failure boundary counts、raw artifact、adapter result、experience dataset 和 `SimulationEvidenceBundle` 覆盖情况。
3. 把 `expert_review_candidate_task_ids` 绑定到后续 `SimulationEvidenceBundle`、experience dataset 和 `RobotProcessPackageDraft`，明确专家到底审查哪些对象。
4. 将跨批次 accumulation ledger 作为支撑层，记录 Phase 1、Phase 2、1000 next-batch 和 modeled batch 的运行事实。
5. 继续保持当前 2 个默认任务族，先观察 modeled task 稳定性，再讨论是否新增第三个默认任务族。
6. 后续批次如果出现 failed samples，先修复具体 failure boundary，再讨论切换仿真器或移动到真实机器人路线。

这一轮仍不应直接进入真实机器人执行或真实焊接质量判断，也不应把结果写成最终仿真器选型。

## 暂缓事项

- 暂缓新增更多任务族或第三个 `WeldSkillUnit` 作为默认积累对象，避免在 scale shard 未稳定前同时扩大任务复杂度。
- 暂缓完整 Gazebo/MoveIt 或 ROS 侧集成，除非它作为候选 adapter 的最小反证实验出现。
- 暂缓专家审核系统化录入，因为当前还需要先用 modeled batch 稳定“审核什么对象”。
- 暂缓真实机器人执行结论，当前只做候选草案和审查前置条件。

## 当前可交付物清单

- `README.md`：项目默认入口。
- `details.md`：阶段更新记录和下一步计划。
- `docs/strategy/`：公司级 Physical AI 判断与当前项目承接关系。
- `docs/architecture/`：五层架构、模块边界和 adapter 原则。
- `docs/skill-assets/`：`WeldSkillPackage` 与 `WeldSkillUnit`。
- `docs/simulation/`：仿真路线、simlite 边界、外部 adapter 候选和 ManiSkill/SAPIEN 开发环境说明。
- `docs/evidence/`：资料来源、字段覆盖、证据报告和质量边界。
- `docs/archive/`：POC、MVP、gate、白皮书和旧计划归档。
- `docs/superpowers/specs/`：阶段设计文档。
- `docs/superpowers/plans/`：阶段实施计划。
- `weldcore.simulation_bakeoff.maniskill_accumulation_pipeline`：100 requested samples 口径的仿真数据积累入口。
- `weldcore.simulation_bakeoff.maniskill_accumulation_pipeline --shards 5 --samples-per-task 50`：5 shards x 100 requested samples，共 500 requested samples 的 Phase 2 shard 积累入口。
- `weldcore.simulation_bakeoff.maniskill_accumulation_pipeline --shards 10 --samples-per-task 50`：10 shards x 100 requested samples，共 1000 requested samples 的 next-batch 积累入口。
- `weldcore.simulation_bakeoff.modeling_pipeline`：批量焊接任务建模入口，默认生成 8 个 modeled task specs 和 validation report。
- `docs/evidence/simulation-runs/2026-06-10-next-batch-1000-maniskill-sapien-review.md`：1000 requested samples 真实环境运行审查记录。
- `docs/焊接工艺数据库主要参数表.xlsx`：工程师参数参考表格。
- `weld-experience-engine/`：可运行的焊接技能资产引擎、测试和报告命令。

## 最近一次验证方式

进入 `weld-experience-engine` 后运行：

```bash
uv sync --extra dev --extra viz
uv run pytest -q
```

当前分支最近一次完整验证结果为 `341 passed`。

可选小批量入口命令：

```bash
uv run python -m weldcore.simulation_bakeoff.maniskill_batch_pipeline \
  --outdir artifacts/simulation/maniskill-sapien-batches
```

该命令在缺少真实 ManiSkill/SAPIEN 环境时会输出 `environment_missing` failure boundary；这属于当前反证边界，不表示仿真入口失败，也不表示最终仿真器已经选型。

可选 Phase 1 仿真数据积累入口命令：

```bash
uv run python -m weldcore.simulation_bakeoff.maniskill_accumulation_pipeline \
  --outdir artifacts/simulation/maniskill-sapien-accumulations
```

该命令默认请求 2 个默认任务 x 50 samples，共 100 requested samples，并输出 `accumulation_spec.json`、`dataset_index.json` 和 `accumulation_report.json`。缺少真实 ManiSkill/SAPIEN 环境时，状态会进入 `blocked_by_environment`；这属于环境边界和反证记录。

可选 Phase 2 shard 仿真数据积累入口命令：

```bash
uv run python -m weldcore.simulation_bakeoff.maniskill_accumulation_pipeline \
  --outdir artifacts/simulation/maniskill-sapien-accumulations \
  --accumulation-id maniskill-sapien-accumulation-phase-2 \
  --shards 5 \
  --samples-per-task 50
```

该命令按 5 个 shard x 100 requested samples 组织 500 requested samples。默认复用已存在且通过一致性校验的 `batch_result.json`；需要忽略已有结果并强制重跑时追加 `--force`。输出中的 shard reports、`failure_boundary_counts`、`field_coverage_trend` 和 `locked_for_next_batch_with_conditions` 用于下一批入口判断，但不代表最终仿真器选型、真实焊接质量验证或真实机器人执行验证已经完成。

可选 1000 requested samples next-batch 命令：

```bash
uv run python -m weldcore.simulation_bakeoff.maniskill_accumulation_pipeline \
  --outdir artifacts/simulation/maniskill-sapien-accumulations \
  --accumulation-id maniskill-sapien-accumulation-next-batch-1000 \
  --shards 10 \
  --samples-per-task 50
```

该命令按 10 个 shard x 100 requested samples 组织 1000 requested samples。本轮真实运行审查中，首次运行 1000/1000 completed，复用运行 10 个 shard 均为 `reused_existing_result`，`failure_boundary_counts` 为空。后续批次若出现 failed samples，应优先修复具体 failure boundary，不直接切换仿真器或进入真实机器人路线；该命令仍不表示最终仿真器选型、真实焊接质量验证或真实机器人执行验证已经完成。

可选批量任务建模入口命令：

```bash
uv run python -m weldcore.simulation_bakeoff.modeling_pipeline \
  --outdir artifacts/simulation/modeling-validation \
  --modeling-batch-id default-batch-modeling-v1 \
  --variants-per-task 4 \
  --batch-samples-per-task 2
```

该命令默认从当前 2 个默认任务族生成 8 个 modeled `SimulationTaskSpec`，输出 `modeling_spec.json`、`modeled_task_specs.json` 和 `modeling_validation_report.json`。`modeled_task_specs.json` 可恢复为 `SimulationTaskSpec` 并进入 `default_maniskill_batch_spec`，用于下一阶段小批量 ManiSkill/SAPIEN 验证。

报告命令可按需运行，用来生成当前证据或历史支撑材料；它们不是默认研发主线本身。

## 风险提醒

- 不要把当前仿真结果写成真实焊接质量验证。
- 不要把候选仿真软件写成已经完成选型。
- 不要把 adapter 失败边界写成项目失败；它是当前反证工作的一部分。
- 不要把 simlite 写成最终仿真器。
- 不要把 Rerun 写成仿真器、机器人控制总线或生产数据库。
- 不要把 `RobotProcessPackageDraft` 写成正式机器人工艺包。
- 不要把 `RobotFeasibilityResult` 写成真实机器人执行验证。
- 不要把工程师参数参考表格写成当前主流程数据源或正式 WPS/PQR。
- 不要删除历史成果；历史材料应继续保留在归档目录中。
