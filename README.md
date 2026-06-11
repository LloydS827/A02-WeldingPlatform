# Physical AI 焊接技能资产底座

## 一句话定义

本仓库支撑 A02「焊接技能大师平台」在 Physical AI for Welding 方向下的研发。当前目标不是先做完整业务系统、真实机器人控制或正式焊接工艺评定，而是把焊接经验、工艺语义、动作轨迹、仿真输出和证据边界沉淀为可学习、可迁移、可审计、后续可接机器人执行验证的技能资产数据结构。

## 文件入口

- [README HTML 阅读版](README.html)
- [项目进展记录 HTML 阅读版](details.html)

`README.md` 是项目入口，面向任何新读者说明项目定位、当前能力、如何运行和边界。

`details.md` 是阶段更新记录，面向项目讨论记录每天或每一轮完成了什么、下一步要做什么、哪些判断发生了变化。

## 当前定位

当前项目已经从早期 POC / MVP / gate / 报告集合，以及随后围绕仿真样本数和 modeled task specs 的扩展工作，进一步收束为以 `ManipulationSkillAsset` 为核心的焊接操作技能资产底座。

现阶段主线是：**先把 welding / manipulation 的动作、意图、约束、证据边界和迁移契约沉淀成 canonical skill asset，再把仿真、真实机器人日志、人工示教和专家标注作为不同证据来源接入这个本体**。样本数、仿真器、URDF 和机器人预检都服务于这个资产本体，而不是反过来成为项目核心。

这意味着当前重点不是直接进入真实机器人执行或真实焊接质量结论，而是先回答：

1. 一个焊接操作技能的可迁移资产结构是什么。
2. 仿真证据如何生成 `ManipulationSkillAsset`，同时保留 `simulation_only` 等边界。
3. 真实协作臂 URDF 应如何作为 `RobotBodyAsset` 参与迁移判断，而不是被误写成技能本体。
4. `ManipulationSkillAsset + RobotBodyAsset` 能否生成 `SkillTransferAssessment`，明确已经通过的最小检查和仍缺失的上下文。
5. 哪些结论来自软件、仿真和资产解析，哪些必须等待 TCP 标定、工件坐标系、场景上下文、IK/collision 和真机验证。
6. 既有 100/500/1000 requested samples、modeled task specs 和 batch 运行结果如何继续作为 skill asset 的证据来源，而不是单独扩张成另一条主线。

## 核心链路

当前核心链路是：

```text
SimulationEvidenceBundle
-> ManipulationSkillAsset

real robot log later
-> ManipulationSkillAsset

human demonstration later
-> ManipulationSkillAsset

ManipulationSkillAsset + RobotBodyAsset(URDF)
-> SkillTransferAssessment
-> RobotContextSpec / SceneContextAsset later
```

这条链路的含义是：

- `ManipulationSkillAsset` 是本阶段的 canonical 技能资产实例，描述技能意图、TCP 轨迹、工具姿态、约束、证据来源、质量边界和迁移契约。
- `SimulationEvidenceBundle` 是当前第一种证据来源，能够从 simlite / adapter 结果构建 `ManipulationSkillAsset`，但仍标记为 `simulation_only`。
- `RobotBodyAsset` 是机器人身体资产上下文，当前由真实上传的 `docs/real-urdf/robot.urdf` 和 33 个 STL mesh 生成，用于说明“这台协作臂身体模型是否可作为迁移上下文”。
- `SkillTransferAssessment` 只回答第一层迁移预检：技能运动是否存在、机器人身体资产是否可用，以及还缺哪些上下文。
- `RobotContextSpec`、`SceneContextAsset`、TCP 标定、工件坐标系、IK、collision 和真机日志是下一层绑定对象。
- `WeldSkillPackage`、`WeldSkillUnit`、`SimulationTaskSpec`、accumulation report 和 modeled task specs 仍保留，它们现在是资产证据、任务来源和历史兼容层。

`ready_for_contextual_precheck` 只表示 `ManipulationSkillAsset + RobotBodyAsset` 具备进入上下文绑定预检的结构条件；`ready_for_robot_execution` 当前仍是保留状态，不应被默认触达。

## 已完成能力

项目当前已经完成以下基础能力：

- 可运行的 `weldcore` 引擎，详见 [weld-experience-engine/README.md](weld-experience-engine/README.md)。
- `ManipulationSkillAsset` canonical 技能资产本体，可从 `SimulationEvidenceBundle` 构建，并保留 source refs、motion、constraints、evidence boundary、quality boundary 和 transfer contract。
- `RobotBodyAsset` 真实机器人身体资产解析：`docs/real-urdf/robot.urdf` 可解析为 7 links、6 revolute joints、33 unique mesh files、66 mesh references，visual/collision mesh 各 33 次引用。
- `SkillTransferAssessment` 可把 `ManipulationSkillAsset + RobotBodyAsset` 判定为 `ready_for_contextual_precheck` 或具体 blocked 状态，并输出 `requires_robot_context_spec`、`requires_tcp_calibration`、`requires_workpiece_frame`、`requires_scene_context_asset` 等后续缺口。
- `weldcore.skill_asset.asset_report` 可输出 `skill_asset_report.json`、`robot_body_asset_report.json` 和 `skill_transfer_assessment.json`。
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

本轮已完成 **canonical manipulation skill asset 本体与真实 URDF RobotBodyAsset 接入层**。

ManiSkill/SAPIEN 小批量默认仿真入口、Phase 1 accumulation 启动层、Phase 2 shard 编排、1000 next-batch 和批量任务建模层仍然有效，但它们现在应被重新解释为 `ManipulationSkillAsset` 的证据来源和压力测试来源。继续扩大 requested samples 之前，优先把“技能资产如何绑定真实机器人身体、TCP、工件坐标系和场景上下文”说清楚。

因此下一阶段的更合理顺序是：

```text
ManipulationSkillAsset
+ RobotBodyAsset(URDF)
-> SkillTransferAssessment
-> RobotContextSpec
-> SceneContextAsset
-> lightweight IK / collision precheck
-> expert review candidate
```

下一阶段要形成的判断包括：

- `RobotContextSpec` 如何表达真实协作臂型号、关节限制、TCP、工具坐标系和控制接口边界。
- `SceneContextAsset` 如何表达焊缝、工件坐标系、夹具/障碍、目标路径和安全边界。
- `SkillTransferAssessment` 如何接入既有 `RobotFeasibilityResult`，把 `ready_for_contextual_precheck` 推进到更具体的 IK/collision/lightweight feasibility 结果。
- 哪些 modeled task specs 和 1000 next-batch 样本应被回填为 `ManipulationSkillAsset` 的证据，而不是继续只作为 batch report。
- 如果下一批出现 failed samples，应先修复具体 failure boundary；如果下一步出现 transfer boundary，应先修 RobotBodyAsset / RobotContextSpec / SceneContextAsset 的具体缺口。

## 如何验证

默认验证路径保持为可安装、可运行、可测试：

```bash
cd weld-experience-engine
uv sync --extra dev --extra viz
uv run pytest -q
```

常用报告命令：

```bash
uv run python -m weldcore.skill_asset.asset_report \
  --outdir artifacts/skill-assets/canonical
uv run python -m weldcore.report.mvp_report
uv run python -m weldcore.report.data_foundation_report
uv run python -m weldcore.report.synthetic_v2_input_report
uv run python -m weldcore.report.simulation_ingest_report
uv run python -m weldcore.report.simulation_bakeoff_report
```

其中 `asset_report` 是当前默认的 canonical skill asset 报告入口，会生成 `ManipulationSkillAsset`、`RobotBodyAsset` 和 `SkillTransferAssessment` 三份 JSON。`simulation_bakeoff_report` 用于生成 `WeldSkillUnit` 仿真 bake-off 证据；它记录 simlite、ManiSkill/SAPIEN 和 Gazebo/MoveIt 候选路线在同一任务契约下的尝试与失败边界，不表示最终仿真器已经选择。

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
│   ├── real-urdf/                      # 真实协作臂 URDF 与 33 个 STL mesh，作为 RobotBodyAsset 输入
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
