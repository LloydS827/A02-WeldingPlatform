# Physical AI 焊接技能资产底座

## 一句话定义

本仓库支撑 A02「焊接技能大师平台」在 Physical AI for Welding 方向下的研发。当前目标不是先做完整业务系统、真实机器人控制或正式焊接工艺评定，而是把焊接经验、工艺语义、动作轨迹、仿真输出和证据边界沉淀为可学习、可迁移、可审计、后续可接机器人执行验证的技能资产数据结构。

## 文件入口

- [README HTML 阅读版](README.html)
- [项目进展记录 HTML 阅读版](details.html)

`README.md` 是项目入口，面向任何新读者说明项目定位、当前能力、如何运行和边界。

`details.md` 是阶段更新记录，面向项目讨论记录每天或每一轮完成了什么、下一步要做什么、哪些判断发生了变化。

## 当前定位

当前项目已经从早期 POC / MVP / gate / 报告集合，收束为以 `WeldSkillPackage` 和 `WeldSkillUnit` 为核心的焊接技能资产底座。

现阶段主线是：**把焊接任务从少量默认样例推进到可批量建模、可小批量仿真验证、可继续审查的数据闭环**。当前已经保留 Phase 1 的 100 requested samples 启动入口、Phase 2 sharded scale 入口和 1000 requested samples next-batch 真实环境运行审查结果；在此基础上，本阶段新增批量焊接任务建模层，可从当前 2 个默认任务族生成 8 个 modeled `SimulationTaskSpec`，并输出建模 spec、可喂给 batch spec 的任务列表和 validation report。下一步应先用这些 modeled task specs 跑小批量仿真验证，再决定是否继续扩样本数或扩任务族。

这意味着当前重点不是直接进入真实机器人执行或真实焊接质量结论，而是先回答：

1. 一个焊接技能单元能否稳定生成仿真任务。
2. 不同仿真路线能否按同一输出契约返回结果。
3. 仿真结果能否转成经验数据、证据包和机器人候选草案。
4. 哪些结论来自软件和仿真证据，哪些必须等待专家或真机验证。
5. 仿真样本能否进入 accumulation index 和 accumulation report。
6. 默认任务族能否扩成 modeled task specs，并保持 batch spec、验证报告和专家候选对象可追踪。
7. 500、1000+ requested samples 的规模化仿真应如何分批、复用、强制重跑和审查。

## 核心链路

当前核心链路是：

```text
WeldSkillUnit
-> SimulationTaskSpec
-> simlite / ManiSkill-SAPIEN / Gazebo-MoveIt candidate adapter
-> SimulatorAdapterResult
-> SimulationEvidenceBundle
-> SkillDataset / experience dataset
-> RobotProcessPackageDraft
-> RobotContextSpec + RobotFeasibilityResult
-> ready_for_expert_review 或 blocked_*
```

这条链路的含义是：

- `WeldSkillUnit` 描述可复用、可训练、可评测的焊接动作能力。
- `SimulationTaskSpec` 把技能单元转成仿真任务输入。
- 仿真 adapter 负责尝试运行或明确记录失败边界。
- `SimulationEvidenceBundle` 汇总任务、adapter 结果、转换后的数据和证据状态。
- `SkillDataset` / experience dataset 是技能数据积累的当前承载形态。
- `RobotProcessPackageDraft` 是未来机器人执行候选包草案，不是正式工艺包。
- `RobotContextSpec` 与 `RobotFeasibilityResult` 只做上下文表达和轻量可行性预检，不代表真实机器人已可执行。

`ready_for_expert_review` 只表示这条候选草案具备进入专家审查的结构条件；`ready_for_robot_execution` 当前仍是保留状态，不应被默认触达。

## 已完成能力

项目当前已经完成以下基础能力：

- 可运行的 `weldcore` 引擎，详见 [weld-experience-engine/README.md](weld-experience-engine/README.md)。
- `SkillDataset`、`SkillSample`、`WeldSkillPackage`、迁移评测和 evidence 输出的基础数据结构。
- 经验结构化 POC、技能迁移 MVP、资料底座 gate、`SyntheticSkillDataset v2` 输入规范 gate 和仿真输出接入 gate。
- `WeldSkillUnit` 最小框架，以及长直横焊沿缝跟踪、包角横焊转角过渡等默认技能单元。
- `SimulationTaskSpec`、`SimulatorAdapterResult` 和 `SimulationEvidenceBundle` 最小仿真证据结构。
- simlite/mock bundle 作为 L0 稳定仿真和测试基线。
- ManiSkill/SAPIEN 本机轻量闭环，用于验证外部仿真输出能否接入项目数据结构。
- ManiSkill/SAPIEN 小批量默认仿真入口：`SimulationBatchSpec`、`SimulationSampleRun`、`SimulationBatchResult` 和 2 个默认任务 x 10 条 primary 样本的 batch summary 契约。
- ManiSkill/SAPIEN 仿真数据积累启动层：`SimulationAccumulationBatchSpec`、`SimulationDatasetIndex`、`SimulationAccumulationReport` 和 2 个默认任务 x 50 条 requested samples 的 accumulation report 契约。
- Phase 2 sharded accumulation 入口：`SimulationAccumulationShardSpec`、shard report、已有 `batch_result.json` 默认复用、`--force` 强制重跑，以及 5 shards x 100 requested samples = 500 requested samples 的 CLI 口径。
- accumulation report 可汇总 shard 级 completed / failed / skipped、failure boundary counts、field coverage trend，并在满足保守条件时输出 `locked_for_next_batch_with_conditions`。
- Phase 2 已在 `weld-maniskill` conda 环境完成真实 ManiSkill/SAPIEN 运行审查：首次运行 500 requested / 500 completed / 0 failed / 0 skipped，5 个 shard 均为 `completed_new_run`；同命令复跑 5 个 shard 均为 `reused_existing_result`；`failure_boundary_counts` 为空；completed sample 的 raw artifact、adapter result、experience dataset 和 evidence bundle 字段覆盖率均为 1.0。
- 1000 requested samples next-batch 真实环境运行审查已完成：保持当前 2 个默认任务族，按 10 shards x 100 requested samples 组织；首次运行 1000 requested / 1000 completed / 0 failed / 0 skipped，复用运行 10 个 shard 均为 `reused_existing_result`。
- `failure_boundary_counts` 为空；completed sample 的 raw artifact、adapter result、experience dataset 和 evidence bundle 字段覆盖率均为 1.0。
- `next_scale_recommendation` 已从 Phase 1 后建议修正为 Phase 2 后建议；后续批次若出现 failed samples，先修具体 failure boundary，再讨论切换仿真器或进入真实机器人路线。
- 批量焊接任务建模与验证闭环：新增 `BatchModelingSpec`、`TaskModelingVariation`、`ModeledSimulationTask`、`ModelingValidationReport` 和 `modeling_pipeline` CLI；默认从 2 个 source tasks x 4 variants 生成 8 个 modeled task specs，报告状态为 `ready_for_simulation_batch`，`expert_review_candidate_ratio` 为 1.0。
- modeled task specs 可直接进入 `default_maniskill_batch_spec`，默认兼容口径为 8 个 modeled tasks x 2 samples = 16 requested samples，用于下一轮小批量仿真验证。
- Gazebo/MoveIt 候选路线的统一失败边界记录。
- 从 `SimulationEvidenceBundle` 到 `RobotProcessPackageDraft` 的机器人候选草案转换。
- `RobotContextSpec`、`RobotFeasibilityProbe`、`RobotFeasibilityResult` 和轻量机器人上下文预检接口。
- Rerun 证据回放兼容处理。
- 焊接工艺参数 Excel 表格作为参考资料纳入仓库；它是工程师参数参考，不是当前主流程的主数据源。
- 前期 POC、MVP、gate、白皮书和旧计划材料已归档，避免历史阶段继续占据默认入口。

这些能力说明软件结构、仿真接入和数据证据路径已经有了前半段闭环，但不代表真实焊接质量、正式 WPS/PQR、最终仿真软件选择或真实机器人执行已经完成。

## 下一阶段方向

本轮已完成 **批量焊接任务建模与仿真验证闭环启动层**。

ManiSkill/SAPIEN 小批量默认仿真入口、Phase 1 accumulation 启动层、Phase 2 shard 编排和 1000 next-batch 已经具备软件入口、batch result、dataset index、accumulation report、复用和强制重跑契约。1000 next-batch 在真实 `weld-maniskill` 环境下完成审查后，当前项目判断是 `ready_to_continue_accumulation_with_conditions`；但继续扩大 requested samples 之前，需要先把“任务从哪里来、如何扩、哪些 modeled tasks 值得进入专家审查”说清楚。

因此下一阶段的更合理顺序是：

```text
2 个默认 SimulationTaskSpec
-> BatchModelingSpec
-> 8 个 modeled SimulationTaskSpec
-> modeling_validation_report
-> 小批量 ManiSkill/SAPIEN batch 验证
-> accumulation ledger / 专家候选对象绑定
```

下一阶段要形成的判断包括：

- modeled task specs 能否在小批量 ManiSkill/SAPIEN batch 中稳定完成。
- expert review candidate task ids 如何绑定后续 `SimulationEvidenceBundle`、experience dataset 和 `RobotProcessPackageDraft`。
- 跨批次 accumulation ledger 如何记录 Phase 1、Phase 2、1000 next-batch 和 modeled batch 的运行元数据、复用状态、failure boundary counts 和 field coverage。
- 当前 2 个默认任务族扩成 8 个 modeled tasks 后是否仍保持稳定。
- 何时才适合新增第三个默认任务族。
- 后续批次如果出现 failed samples，应先修复具体 failure boundary，再讨论切换仿真器或进入真实机器人路线。

## 如何验证

默认验证路径保持为可安装、可运行、可测试：

```bash
cd weld-experience-engine
uv sync --extra dev --extra viz
uv run pytest -q
```

常用报告命令：

```bash
uv run python -m weldcore.report.mvp_report
uv run python -m weldcore.report.data_foundation_report
uv run python -m weldcore.report.synthetic_v2_input_report
uv run python -m weldcore.report.simulation_ingest_report
uv run python -m weldcore.report.simulation_bakeoff_report
```

其中 `simulation_bakeoff_report` 用于生成 `WeldSkillUnit` 仿真 bake-off 证据；它记录 simlite、ManiSkill/SAPIEN 和 Gazebo/MoveIt 候选路线在同一任务契约下的尝试与失败边界，不表示最终仿真器已经选择。

可选小批量仿真入口命令：

```bash
uv run python -m weldcore.simulation_bakeoff.maniskill_batch_pipeline \
  --outdir artifacts/simulation/maniskill-sapien-batches
```

该命令生成 2 个默认任务 x 10 条 ManiSkill/SAPIEN primary 样本的 batch spec 和 batch result。若本机缺少真实 ManiSkill/SAPIEN 环境，样本会以 `environment_missing` 等 failure boundary 记录；这不表示真实焊接质量验证、最终仿真器选型或真实机器人执行已经完成。

可选 Phase 1 仿真数据积累入口命令：

```bash
uv run python -m weldcore.simulation_bakeoff.maniskill_accumulation_pipeline \
  --outdir artifacts/simulation/maniskill-sapien-accumulations
```

该命令默认请求 2 个默认任务 x 50 条 ManiSkill/SAPIEN samples，共 100 requested samples，并输出 `accumulation_spec.json`、`dataset_index.json` 和 `accumulation_report.json`。若本机缺少真实 ManiSkill/SAPIEN 环境，报告会进入 `blocked_by_environment`；这属于环境边界和反证记录，不表示项目失败，也不表示最终仿真器已经选型。

可选 Phase 2 shard 仿真数据积累入口命令：

```bash
uv run python -m weldcore.simulation_bakeoff.maniskill_accumulation_pipeline \
  --outdir artifacts/simulation/maniskill-sapien-accumulations \
  --accumulation-id maniskill-sapien-accumulation-phase-2 \
  --shards 5 \
  --samples-per-task 50
```

该命令按 5 个 shard x 100 requested samples 组织 500 requested samples。默认会复用已存在且通过一致性校验的 `batch_result.json`；需要忽略已有 shard 结果并强制重跑时，在同一命令后追加 `--force`。Phase 2 shard 报告用于审查复用状态、failure boundary counts、field coverage trend 和 `locked_for_next_batch_with_conditions`，不表示最终仿真器选型、真实焊接质量验证或真实机器人执行验证已经完成。

可选 1000 requested samples next-batch 命令，从 `weld-experience-engine/` 执行：

```bash
uv run python -m weldcore.simulation_bakeoff.maniskill_accumulation_pipeline \
  --outdir artifacts/simulation/maniskill-sapien-accumulations \
  --accumulation-id maniskill-sapien-accumulation-next-batch-1000 \
  --shards 10 \
  --samples-per-task 50
```

该命令保持当前 2 个默认任务族，按 10 shards x 100 requested samples 组织 1000 requested samples。本轮真实运行审查中，首次运行 1000/1000 completed，复用运行 10 个 shard 均为 `reused_existing_result`，`failure_boundary_counts` 为空。后续需要强制重跑时，在同一命令后追加 `--force`。后续批次若出现 failed samples，应优先修复具体 failure boundary，不直接切换仿真器或进入真实机器人路线；该命令仍不表示最终仿真器选型、真实焊接质量验证或真实机器人执行验证已经完成。

可选批量任务建模入口命令：

```bash
uv run python -m weldcore.simulation_bakeoff.modeling_pipeline \
  --outdir artifacts/simulation/modeling-validation \
  --modeling-batch-id default-batch-modeling-v1 \
  --variants-per-task 4 \
  --batch-samples-per-task 2
```

该命令默认从当前 2 个默认任务族生成 8 个 modeled `SimulationTaskSpec`，输出 `modeling_spec.json`、`modeled_task_specs.json` 和 `modeling_validation_report.json`。报告状态为 `ready_for_simulation_batch` 时，表示这些 modeled task specs 可进入下一轮小批量仿真验证；它仍不表示真实焊接质量验证、正式 WPS/PQR、最终仿真器选型或真实机器人执行验证已经完成。

历史支撑命令仍然保留：

```bash
uv run python -m weldcore.report.generate
uv run python -m weldcore.report.scenario_report
```

这些报告只能用于软件证据、资料证据、仿真接入证据和历史复盘，不能写成真实焊接质量验证、完整外部仿真器集成或正式 WPS/PQR。

## 当前目录结构

```text
.
├── README.md
├── README.html
├── details.md                         # 阶段更新记录和下一步计划
├── details.html
├── docs/
│   ├── strategy/                       # Physical AI 公司战略与项目承接关系
│   ├── architecture/                   # 五层架构、模块边界和 adapter 原则
│   ├── skill-assets/                   # WeldSkillPackage 与 WeldSkillUnit
│   ├── simulation/                     # 仿真路线、simlite 边界和外部 adapter 候选
│   ├── evidence/                       # 资料来源、字段覆盖、证据报告和质量边界
│   ├── archive/                        # POC、MVP、gate、白皮书和旧计划归档
│   └── superpowers/                    # 设计与实施计划记录
└── weld-experience-engine/
    ├── README.md
    ├── pyproject.toml
    ├── tests/
    └── weldcore/
```

## 当前不做事项

- 不把 `stiffened-panel-fillet` 作为默认项目主线；它现在是历史资料 gate 和行业实例。
- 不把 simlite 写成最终仿真器；它只是 L0 稳定基线。
- 不把 ManiSkill/SAPIEN、Gazebo/MoveIt、Isaac、ROS 等候选路线写成已经完成选型。
- 不把候选 adapter 的失败记录写成项目失败；失败边界本身就是当前反证工作的一部分。
- 不把 `RobotProcessPackageDraft` 写成正式机器人工艺包。
- 不把 `RobotFeasibilityResult` 写成真实机器人可达性、碰撞或关节限制验证。
- 不把公开资料、合成数据、仿真输出或报告结论写成真实焊接质量验证。
- 不把资料证据、输入规范、仿真假设或工程师参考表格写成 WPS/PQR。
- 不删除历史成果；历史材料统一保留在归档目录。

## Agent 维护规则

后续推进本项目时，应先判断是否需要同步更新 [details.md](details.md)。

需要更新 `details.md` 的情况包括：

- 项目阶段、范围或默认主线发生变化。
- `WeldSkillPackage`、`WeldSkillUnit`、仿真路线、证据边界或 adapter 边界发生变化。
- 新增或移除重要基础能力、报告命令、验证路径或交付物。
- 下一步计划、风险判断或阶段优先级发生变化。
- 真实焊接质量验证、WPS/PQR、最终仿真器选择等边界判断发生变化。

更新入口文档、阶段说明或路线说明时，必须同步刷新同目录 HTML 阅读版。尤其是根目录 `README.md` 和 `details.md`：Markdown 是维护源，HTML 是面向项目负责人、业务人员、工艺人员和非技术读者的阅读副本。
