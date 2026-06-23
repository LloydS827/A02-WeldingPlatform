# A02 机器人技能大师焊接技能资产底座项目进展记录

更新时间：2026-06-23

这份文件用于记录 A02「机器人技能大师能力的焊接技能资产底座」每一阶段完成了什么、下一步准备做什么、哪些判断发生了变化。它不是项目入口说明；项目入口请看 [README.md](README.md)。

## 文件定位

- `README.md`：项目入口，面向任何新读者说明项目定位、核心链路、当前能力、如何运行和边界。
- `details.md`：阶段更新记录，面向项目讨论记录近期更新、当前判断、下一步计划和风险提醒。

本文件应同步维护 [HTML 阅读版](details.html)。更新根目录 `README.md`、本文件或类似面向读者的阶段/路线说明时，也要同步刷新对应 `.html` 阅读副本。

## 当前一句话状态

项目已经按母战略修订为“机器人技能大师能力的焊接技能资产底座”。当前主线以 `ManipulationSkillAsset` 为核心，把仿真、真实机器人日志、人工示教、专家标注和 A01 H300 工站回采数据统一视为技能资产 evidence。默认可运行路径已经能从 `SimulationEvidenceBundle` 构建技能资产，把真实协作臂 URDF 解析为 `RobotBodyAsset`，绑定 nominal `RobotContextSpec` 和默认 `SceneContextAsset`，让 `SkillTransferAssessment` 消费 lightweight `RobotFeasibilityResult` 推进到 `ready_for_expert_review`，并生成 A01/B06 mapping、`ExpertReviewRecord`、A02->A01 handoff、IP support matrix 和 2 个默认仿真任务的 demo evidence pack。基于 NVIDIA 技术框架调研和焊接工艺参数 Excel，下一阶段路线调整为 K01 + NV01：以 Excel 字段表形成焊接工艺知识合同，以 OpenUSD / Isaac Sim / Isaac Lab 作为未来真实仿真训练闭环主底座。这个状态只表示进入专家审查候选、工艺知识合同设计、数字孪生包设计和训练准备合同阶段，不表示真实机器人可执行。

## 当前主线判断

现在不适合跳到真实机器人控制，也不应继续把 ManiSkill/SAPIEN、Gazebo/MoveIt、Isaac 等作为长期平行候选反复 bake-off。更合理的节奏是承认重底座不应重复造轮子：OpenUSD 负责未来世界模型交换，Isaac Sim 负责未来真实仿真、传感器和合成数据，Isaac Lab 负责后续训练闭环；A02 负责把焊接工艺字段合同、技能资产、证据链、专家审查和 A01/IP handoff 编译成这些重底座能消费的数字孪生包。

更合理的下一阶段目标主线是：

```text
SimulationEvidenceBundle / real robot log / human demonstration / H300 workcell run
-> WeldProcedureKnowledgeContract / WeldProcedureParameterSet
-> ManipulationSkillAsset
+ RobotBodyAsset(URDF)
-> RobotContextSpec
-> SceneContextAsset
-> RobotFeasibilityResult
-> SkillTransferAssessment
-> ExpertReviewRecord
-> A02->A01 product validation handoff / IP evidence support
-> future OpenUSD / Isaac Sim / Isaac Lab digital twin and training package
```

这一段必须先稳定下来。只有当 procedure knowledge contract、skill asset 本体、机器人身体资产、场景上下文、输出证据、失败边界、A01/B06 字段映射、专家审查记录和 OpenUSD/Isaac-oriented manifest 都可复跑、可比较、可审查之后，项目才适合继续进入 Isaac Sim runtime、Replicator 合成数据、Isaac Lab 训练环境或真实机器人迁移验证。

这里的“反证工作”仍然重要，但口径发生变化：OpenUSD/Isaac 被提升为未来主底座，其他工具不再作为同等默认主线候选，而是作为历史支撑、轻量测试、对照 adapter 或失败边界反证来源。OpenUSD/Isaac 自身也不能凭品牌直接越过 evidence gate，必须通过 A02 的 canonical schema、manifest、review record 和 readiness report 证明可接入。

## 近期更新

### 2026-06-23

- 结合 `docs/Nvidia技术框架调研.md` 完成 NVIDIA-native 路线判断：A02 未来真实仿真训练闭环的重底座优先选用 OpenUSD / Isaac Sim / Isaac Lab，而不是继续长期平行比较多个通用仿真训练框架。
- 新增 NV01 设计：`NV01 NVIDIA-Native Weld Skill Digital Twin Foundation`，把下一阶段目标定义为生成 `WeldSkillDigitalTwinPackage`、`openusd_scene_manifest`、`isaac_sim_replay_config`、`domain_randomization_recipe`、`training_readiness_report` 和 `nvidia_stack_alignment_matrix`。
- 明确 OpenUSD 是主交换层，Isaac Sim 是默认目标仿真运行时，Isaac Lab 是训练闭环目标层；Cosmos 后置用于长尾视觉增强和世界模型扩展，不进入当前默认路径。
- 明确 A02 不重复造通用物理引擎、机器人仿真器、3D 场景标准或训练框架；A02 继续掌握 `ManipulationSkillAsset`、工艺知识、证据治理、专家审查、A02->A01 handoff 和 IP support。
- 同步修订 README、仿真路线和模块边界，避免继续把 ManiSkill/SAPIEN、Gazebo/MoveIt、Isaac 等写成同等长期候选。
- 当前仍不引入 Isaac Sim 默认依赖，不写真实 USD stage，不训练 Isaac Lab 策略，不接 Cosmos，不宣称真实机器人可执行。
- 进一步修订 NV01：保留原有 NVIDIA-native 数字孪生包方向，同时加入 K01 焊接工艺知识合同前置层。`docs/焊接工艺数据库主要参数表.xlsx` 的 47 个字段、8 个类别、21 个必填、12 个条件必填和 14 个补充字段将成为下一阶段字段合同源。
- 明确 K01 字段需要按必要性和来源双轴分类：必填、条件必填、补充；人必须填写/确认、系统计算、仿真推导、工站回采、资料库引用。

### 2026-06-22

- 完成 A02 战略口径修订：默认定位从“焊接技能大师平台”收束为“机器人技能大师能力的焊接技能资产底座”。
- 标准化 `ManipulationSkillAsset` evidence source type：canonical skill asset 层使用 `simulation_only`、`human_demo`、`real_robot_log`、`h300_workcell_run` 和 `expert_annotation`；低层仿真 source manifest 仍可保留 `simulation`。
- 新增 A01 H300 工站回采与 B06 Physical AI Package 到 `ManipulationSkillAsset` 的 mapping artifact，覆盖 path points、robot pose、torch pose、manual correction、quality result、trajectory、human correction、quality labels 和 rerun replay ref。
- 新增 `ExpertReviewRecord`，绑定技能资产 ID、机器人上下文、场景上下文、feasibility result、source evidence summary、审查状态、阻塞原因、required real context 和 next actions。
- 新增 A02->A01 product validation handoff，明确 A02 输出的是 skill package candidate、trajectory candidate、torch posture suggestion、process parameter hint 和 failure boundary summary，不是可直接派发的 robot program。
- 新增 IP support matrix，把 P0-02“焊接技能包”、P0-03“焊接轨迹结构化转换”、P0-04“仿真优先焊接技能数据集”映射到 supporting objects、supporting reports 和 missing real-world evidence。
- 扩展 `weldcore.skill_asset.asset_report`，默认从 7 份 JSON 扩展为 12 份 JSON artifact，优先服务 A01 产品验证和 IP 交底准备。
- 新增 `weldcore.skill_asset.demo_report`，默认运行 2 个仿真任务；每个任务输出 12 份 canonical artifact 原始文件名和 `simulation_evidence_bundle.json`，顶层输出 `demo_summary.md/json/html`，用于形成解释型 demo evidence pack。
- 更新 README、引擎 README、架构文档和技能包文档，减少平台化表达，明确 `WeldSkillPackage` 是历史兼容 / facade，当前 canonical object 是 `ManipulationSkillAsset`。
- 本轮验证：`uv run pytest -q` 通过 `398 passed`；`asset_report` 已确认写出 12 份 JSON；`demo_report` 已确认写出 2 个默认任务的 evidence pack。默认 `transfer_assessment.status=ready_for_expert_review`，`expert_review_record.review_status=pending_expert_review`，`robot_feasibility_result.status=passed`，demo pack 顶层状态为 `ready_for_expert_review_candidate_pack`。

### 2026-06-16

- 完成 contextual lightweight transfer precheck 设计和实现，把 `RobotContextSpec`、`SceneContextAsset`、`RobotFeasibilityResult` 接回 `ManipulationSkillAsset` 主线。
- 新增 `SceneContextAsset`，表达工件坐标系、焊缝路径、安全边界、夹具/障碍占位、场景验证状态和 evidence boundary；缺少 workpiece frame 或 seam path 的场景会阻止进入轻量预检。
- 新增 `build_robot_context_from_body_asset`，把真实 URDF `RobotBodyAsset` 绑定为 `RobotContextSpec`，记录机器人型号、base frame、nominal TCP、工具坐标系、关节限制来源、workspace hint 和 `not_tcp_calibrated`、`not_vendor_validated`、`not_ready_for_robot_execution` 等边界。
- 新增 `build_contextual_feasibility_result`，对缺失 robot context、scene context、TCP 轨迹、工具姿态、关节限制来源、路径连续性、URDF body issue、workspace hint 半径和 z 边界做 lightweight reachability / collision-assumed / joint-limit / path continuity / orientation 预检。
- 扩展 `build_skill_transfer_assessment`：旧版 `ManipulationSkillAsset + RobotBodyAsset` 两输入路径仍保持 `ready_for_contextual_precheck`；显式传入 `RobotContextSpec + SceneContextAsset + RobotFeasibilityResult` 时，默认路径推进到 `ready_for_expert_review`，失败时输出具体 missing / incomplete / failed 状态。
- 扩展 `weldcore.skill_asset.asset_report`，默认输出 `skill_asset_report.json`、`robot_body_asset_report.json`、`robot_context_spec.json`、`scene_context_asset_report.json`、`skill_transfer_assessment.json`、`robot_feasibility_result.json` 和 `skill_asset_evidence_writeback_summary.json` 七份 JSON。
- 新增 `SkillAssetEvidenceWritebackSummary`，把 8 个 modeled task specs 和 1000 next-batch samples 记录为 `ManipulationSkillAsset` evidence candidates，而不是继续把扩样本数作为孤立主线。
- 本轮验证：`uv run pytest -q` 通过 `390 passed`；`asset_report` 可写出 7 份 JSON，默认 `transfer_assessment.status=ready_for_expert_review`，`robot_feasibility_result.status=passed`。
- 当前边界仍然明确：不是完整 IK solver，不是真实 collision validation，不是真实机器人执行，不是 WPS/PQR，也不是真实焊接质量验证。

### 2026-06-11

- 完成 canonical manipulation skill asset 本体设计和实现，明确项目核心不再是单纯扩大 requested samples，而是把 welding / manipulation 动作保存为可迁移、可验证、可审计的 `ManipulationSkillAsset`。
- 新增 `ManipulationSkillAsset`、`SkillAssetEvidence`、`SkillTransferContract` 和 `SkillTransferAssessment`，可表达技能意图、TCP 轨迹、工具姿态、约束、证据边界、质量边界和迁移契约。
- 新增 `build_manipulation_skill_asset_from_simulation_bundle`，可从当前 `SimulationEvidenceBundle` 生成 canonical skill asset，并保留 `simulation_only`、`not_real_welding_quality_validation`、`not_WPS_PQR`、`not_ready_for_robot_execution` 等边界。
- 将用户上传的真实协作臂仿真资产纳入 `docs/real-urdf/`，并作为 `RobotBodyAsset` 接入系统。当前 `robot.urdf` 解析结果为 7 links、6 revolute joints、33 unique mesh files、66 mesh references，visual/collision mesh 各 33 次引用。
- 新增 `build_robot_body_asset_from_urdf`，覆盖 missing mesh、missing joint limit、bad XML、missing URDF file、invalid root、invalid numeric joint limit 和少于 6 个 revolute joints 等资产边界。
- 新增 `build_skill_transfer_assessment`，第一版只接收 `ManipulationSkillAsset + RobotBodyAsset`，可输出 `ready_for_contextual_precheck`、`blocked_by_missing_skill_motion` 或 `blocked_by_robot_body_asset_issue`。
- `ready_for_contextual_precheck` 默认只表示技能运动存在且机器人身体资产可用；仍会列出 `requires_robot_context_spec`、`requires_tcp_calibration`、`requires_workpiece_frame` 和 `requires_scene_context_asset`，不表示真实机器人可执行。
- 新增 `weldcore.skill_asset.asset_report` CLI，可输出 `skill_asset_report.json`、`robot_body_asset_report.json` 和 `skill_transfer_assessment.json`。
- 本轮继续保留 `WeldSkillPackage` / `package_from_sample` 旧 facade，避免破坏既有技能包和迁移评测入口。
- 完成批量焊接任务建模与仿真验证闭环设计和实施计划，并通过 review。
- 新增 `BatchModelingSpec`、`TaskModelingVariation`、`ModeledSimulationTask`、`ModelingValidationReport` 和 `ModelingCoverageSummary`。
- 新增 `build_modeled_simulation_tasks`，默认从 2 个 source tasks x 4 variants 生成 8 个 modeled `SimulationTaskSpec`。
- 新增 `build_modeling_validation_report`，验证 source 覆盖、modeled task id 一致性、path geometry 变化、输出字段、评价指标、out-of-scope 边界和禁用真实焊接质量术语。
- 建模报告包含 `expert_review_candidate_task_ids` 和 `expert_review_candidate_ratio`；完整默认路径下状态为 `ready_for_simulation_batch`，候选比例为 1.0。
- 建模报告会阻止不完整批次：如果只传入部分 modeled tasks，会进入 `blocked_by_modeling_issue`，避免缺 7/8 任务时仍显示 ready。
- 新增 `modeled_task_specs` 和 `simulation_task_specs_from_modeling_payload`，保证 `modeled_task_specs.json` 可恢复成 `SimulationTaskSpec` 并进入 `default_maniskill_batch_spec`。
- 新增 `weldcore.simulation_bakeoff.modeling_pipeline` CLI，输出 `modeling_spec.json`、`modeled_task_specs.json` 和 `modeling_validation_report.json`。
- 当前默认兼容口径为 8 个 modeled tasks x 2 samples = 16 requested samples，用于下一阶段小批量 ManiSkill/SAPIEN 验证。
- 当时阶段仍不做最终仿真器选型、真实焊接质量验证、正式 WPS/PQR 或真实机器人执行结论。

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
- 当时阶段仍不做最终仿真器选型、真实焊接质量验证或真实机器人执行结论。
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
- `ManipulationSkillAsset` canonical 技能资产本体。
- 从 `SimulationEvidenceBundle` 到 `ManipulationSkillAsset` 的构建器。
- 真实 URDF 到 `RobotBodyAsset` 的解析与验证，当前资产为 7 links、6 revolute joints、33 unique mesh files、66 mesh references。
- `RobotBodyAsset -> RobotContextSpec` 绑定构建器，可从真实 URDF 机器人身体资产生成 nominal 机器人上下文，并保留 TCP 未标定、vendor 未验证和不可执行边界。
- `SceneContextAsset`，可表达工件坐标系、焊缝路径、安全边界、夹具/障碍占位和场景证据边界。
- `RobotFeasibilityResult` 已接入 `SkillTransferAssessment` 主线，可做 lightweight reachability、collision-assumed、joint-limit source、path continuity 和 orientation 结构预检。
- `SkillTransferAssessment` 可输出 `ready_for_contextual_precheck`、`ready_for_lightweight_feasibility_precheck`、`ready_for_expert_review` 和具体 blocked 状态。
- `SkillAssetEvidenceWritebackSummary` 可把 modeled task specs 和 1000 next-batch 样本记录为 skill asset evidence candidates。
- `EvidenceSourceCatalogEntry`，可标准化记录 `simulation_only`、`human_demo`、`real_robot_log`、`h300_workcell_run` 和 `expert_annotation`。
- `A01B06SkillAssetMapping`，可把 A01 H300 工站回采和 B06 Physical AI Package 字段映射到 `ManipulationSkillAsset`。
- `ExpertReviewRecord`，可绑定技能资产、机器人上下文、场景上下文、预检结果和人工审查边界。
- `A02ToA01ProductValidationHandoff`，可表达 A02 反哺 A01 产品验证的候选输出和失败边界。
- `IPDisclosureSupportMatrix`，可把 P0-02、P0-03、P0-04 关联到支撑对象、报告和缺失真实证据。
- `weldcore.skill_asset.asset_report`，可生成 skill asset、robot body asset、robot context spec、scene context asset、transfer assessment、robot feasibility result、evidence writeback summary、evidence source catalog、A01/B06 mapping、expert review record、A02->A01 handoff 和 IP support matrix 十二份 JSON。
- `weldcore.skill_asset.demo_report`，可生成 2 个默认仿真任务的解释型 demo evidence pack；每个任务保留 12 份 canonical artifact 原始文件名和 `simulation_evidence_bundle.json`，顶层生成 `demo_summary.md/json/html`。
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

这些能力仍属于软件结构、仿真接入和证据管理能力，不代表真实焊接质量验证、Isaac Sim runtime 验证、Isaac Lab 训练闭环或真实机器人执行验证。

## 尚未完成

- OpenUSD / Isaac Sim / Isaac Lab 已被确定为未来真实仿真训练闭环主底座方向，但 NV01 数字孪生包合同尚未实现。
- K01 焊接工艺知识合同尚未实现；Excel 字段尚未生成 `WeldProcedureKnowledgeContract`、`WeldProcedureParameterSet`、`WeldProcedureValidationReport` 或 `ProcedureToNV01MappingMatrix`。
- OpenUSD scene manifest、Isaac Sim replay config、domain randomization recipe、training readiness report 和 NVIDIA stack alignment matrix 尚未生成。
- Isaac Sim runtime 尚未接入，尚未完成 robot import、stage authoring、TCP trajectory replay、传感器仿真、Replicator 合成数据或真实 collision validation。
- Isaac Lab training environment 尚未设计和运行，尚未定义可执行 observation/action/reward/termination/curriculum。
- Cosmos、Nucleus、Isaac ROS、Jetson/边缘推理尚未接入，且不应进入 NV01 默认范围。
- 规模化持续积累仿真数据的默认入口已完成 500 requested samples 和 1000 requested samples 级真实环境审查，但 modeled task specs 的小批量 ManiSkill/SAPIEN 验证尚未完成。
- 跨批次 accumulation ledger 尚未建立。
- 候选仿真软件面对 modeled task specs 的稳定性、可复跑性、输出字段覆盖率和失败边界仍需在下一批继续反证。
- 经验数据与 `ManipulationSkillAsset` 之间的跨批次字段追踪还需要进一步收束。
- 专家审查记录结构已经作为 artifact 实现，但尚未接入真实专家结论、审查人、审查时间和闭环动作。
- demo evidence pack 已能进入 `ready_for_expert_review` evidence 讨论，但仍缺真实专家审查结论、真实执行日志和真实焊接质量反馈。
- A01 H300 工站回采和 B06 Physical AI Package 目前是字段合同和报告 artifact，尚未接入真实或脱敏样本。
- 真实 TCP 标定记录、工具坐标系标定记录和工件坐标系测量记录尚未替换当前 nominal context。
- 完整 IK、真实碰撞检测、MoveIt/Gazebo adapter、机器人控制接口和真机日志尚未接入当前 `RobotFeasibilityResult`。
- 真实焊机、机器人、焊材、焊后检测和质量结果尚未接成闭环。
- 当前资料、输入规范、仿真假设和工程师参考表格不能替代正式 WPS/PQR。

## 下一步建议

推荐下一阶段任务调整为：**K01 + NV01 Weld Procedure Knowledge Contract and NVIDIA-Native Digital Twin Foundation**。

目标是在当前 Demo Evidence Pack 和焊接工艺参数 Excel 基础上，把 A02 的工艺知识字段、技能资产证据链编译为未来 OpenUSD / Isaac Sim / Isaac Lab 能消费的焊接技能数字孪生与训练准备包：

1. 生成 `WeldProcedureKnowledgeContract`，把 Excel 47 个字段转成字段合同。
2. 生成 `WeldProcedureParameterSet`，表达每个 demo task 当前已有、缺失、可计算、可推导和需要人确认的工艺字段。
3. 生成 `WeldProcedureValidationReport`，明确必填、条件必填、补充字段覆盖和阻塞状态。
4. 生成 `ProcedureToNV01MappingMatrix`，把工艺字段映射到 `ManipulationSkillAsset`、OpenUSD process metadata、Isaac replay、domain randomization、training readiness 和 expert gate。
5. 生成 `WeldSkillDigitalTwinPackage`，绑定 demo evidence pack、procedure contract、canonical artifact、任务清单、readiness boundary 和 NVIDIA stack target。
6. 生成 `openusd_scene_manifest`，明确未来 USD stage 的 root prim、robot/workpiece/weld task/sensor/safety prim、坐标系、语义标签、procedure metadata 和 evidence binding。
7. 生成 `isaac_sim_replay_config`，描述 Isaac Sim robot import、trajectory replay、工艺参数输入、sensor simulation、Replicator dataset、validation checks 和 missing runtime boundary。
8. 生成 `domain_randomization_recipe`，把坡口、间隙、工装偏置、反光、烟尘、弧光、TCP 偏差、传感器外参、工艺参数窗口等焊接有效扰动结构化，并追溯到 K01 字段。
9. 生成 `training_readiness_report`，面向 Isaac Lab 说明 observation、action、reward、termination、curriculum、dataset、procedure gate、evaluation 和 expert gate。
10. 生成 `nvidia_stack_alignment_matrix`，把 `WeldProcedureKnowledgeContract`、`RobotBodyAsset`、`RobotContextSpec`、`SceneContextAsset`、`ManipulationSkillAsset`、`RobotFeasibilityResult` 和 `ExpertReviewRecord` 映射到 OpenUSD/Isaac/Isaac Lab 层。
11. 保留真实 TCP/tool/workpiece/sensor 标定、A01 H300 回采、B06 Physical AI Package、工艺人员确认、专家审查结论和真实焊接质量反馈作为 K01 + NV01 之后的真实闭环输入。

这一轮仍不应直接进入真实机器人执行或真实焊接质量判断，也不应把 Excel/K01 输出写成正式 WPS/PQR，或把 `ready_for_simulation_replay_package_design` 写成已经完成 Isaac Sim runtime 验证。

## 暂缓事项

- 暂缓新增更多任务族或第三个 `WeldSkillUnit` 作为默认积累对象，避免在 scale shard 未稳定前同时扩大任务复杂度。
- 暂缓完整 Gazebo/MoveIt 侧集成；它们后续只作为对照 adapter 或反证来源，不再优先于 OpenUSD/Isaac 主底座。
- 暂缓 Isaac Sim 默认依赖、OpenUSD SDK 强依赖、Isaac Lab 训练、Cosmos 接入、Nucleus 服务化、Isaac ROS/Jetson 部署。
- 暂缓完整工艺数据库、录入 UI、权限系统和 WPS/PQR 审批系统；本阶段只做字段合同和缺口报告。
- 暂缓专家审核系统化产品录入；下一阶段先运行最小 `ExpertReviewRecord` 工作流和真实标定记录替换，而不是直接建设审核系统。
- 暂缓真实机器人执行结论，当前只做候选草案和审查前置条件。

## 当前可交付物清单

- `README.md`：项目默认入口。
- `details.md`：阶段更新记录和下一步计划。
- `docs/strategy/`：公司级 Physical AI 判断与当前项目承接关系。
- `docs/architecture/`：五层架构、模块边界和 adapter 原则。
- `docs/skill-assets/`：`ManipulationSkillAsset` 主线说明，以及 `WeldSkillPackage` 历史兼容 / facade。
- `docs/simulation/`：仿真路线、simlite 边界、外部 adapter 候选和 ManiSkill/SAPIEN 开发环境说明。
- `docs/Nvidia技术框架调研.md`：NVIDIA OpenUSD / Omniverse / Isaac Sim / Isaac Lab / Cosmos 技术框架调研资料，是 NV01 路线调整的重要输入。
- `docs/evidence/`：资料来源、字段覆盖、证据报告和质量边界。
- `docs/archive/`：POC、MVP、gate、白皮书和旧计划归档。
- `docs/superpowers/specs/`：阶段设计文档。
- `docs/superpowers/plans/`：阶段实施计划。
- `docs/real-urdf/robot.urdf` 与 `docs/real-urdf/meshes/`：真实协作臂 RobotBodyAsset 输入资产。
- `weldcore.skill_asset.asset_report`：canonical skill asset 报告入口，默认生成十二份 JSON，包括 `ManipulationSkillAsset`、`RobotBodyAsset`、`RobotContextSpec`、`SceneContextAsset`、`SkillTransferAssessment`、`RobotFeasibilityResult`、evidence writeback summary、evidence source catalog、A01/B06 mapping、expert review record、A02->A01 handoff 和 IP support matrix。
- `weldcore.skill_asset.demo_report`：默认 demo evidence pack 入口，生成 2 个仿真任务的 per-task canonical artifacts、`simulation_evidence_bundle.json` 和顶层 `demo_summary.md/json/html`。
- `weldcore.simulation_bakeoff.maniskill_accumulation_pipeline`：100 requested samples 口径的仿真数据积累入口。
- `weldcore.simulation_bakeoff.maniskill_accumulation_pipeline --shards 5 --samples-per-task 50`：5 shards x 100 requested samples，共 500 requested samples 的 Phase 2 shard 积累入口。
- `weldcore.simulation_bakeoff.maniskill_accumulation_pipeline --shards 10 --samples-per-task 50`：10 shards x 100 requested samples，共 1000 requested samples 的 next-batch 积累入口。
- `weldcore.simulation_bakeoff.modeling_pipeline`：批量焊接任务建模入口，默认生成 8 个 modeled task specs 和 validation report。
- `docs/evidence/simulation-runs/2026-06-10-next-batch-1000-maniskill-sapien-review.md`：1000 requested samples 真实环境运行审查记录。
- `docs/焊接工艺数据库主要参数表.xlsx`：K01 焊接工艺知识合同源，不是正式 WPS/PQR。
- `weld-experience-engine/`：可运行的焊接技能资产引擎、测试和报告命令。

## 最近一次验证方式

进入 `weld-experience-engine` 后运行：

```bash
uv sync --extra dev --extra viz
uv run pytest -q
```

当前分支最近一次完整验证结果为 `395 passed`。

当前 canonical skill asset 报告命令：

```bash
uv run python -m weldcore.skill_asset.asset_report \
  --outdir artifacts/skill-assets/canonical
```

该命令会生成 12 份 JSON：`skill_asset_report.json`、`robot_body_asset_report.json`、`robot_context_spec.json`、`scene_context_asset_report.json`、`skill_transfer_assessment.json`、`robot_feasibility_result.json`、`skill_asset_evidence_writeback_summary.json`、`skill_asset_evidence_source_catalog.json`、`a01_b06_skill_asset_mapping.json`、`expert_review_record.json`、`a02_to_a01_product_validation_handoff.json` 和 `ip_disclosure_support_matrix.json`。当前默认结果中，`robot_body_asset.validation_status` 为 `usable_as_robot_body_context`，`transfer_assessment.status` 为 `ready_for_expert_review`，`expert_review_record.review_status` 为 `pending_expert_review`，`robot_feasibility_result.status` 为 `passed`；它仍然不表示真实机器人可执行。

当前默认 demo evidence pack 命令：

```bash
cd weld-experience-engine
uv run python -m weldcore.skill_asset.demo_report \
  --outdir artifacts/demo/skill-asset-evidence
```

该命令运行 2 个默认仿真任务；每个任务输出 12 份 canonical artifact 原始文件名和 `simulation_evidence_bundle.json`，顶层输出 `demo_summary.md`、`demo_summary.json` 和 `demo_summary.html`。默认状态是 `ready_for_expert_review` evidence / `ready_for_expert_review_candidate_pack`，并保留 `not_ready_for_robot_execution`、`simulation_only`、`not_full_ik_solver`、`not_real_collision_validation` 和 `not_real_welding_quality_validation` 边界。

可选小批量入口命令：

```bash
uv run python -m weldcore.simulation_bakeoff.maniskill_batch_pipeline \
  --outdir artifacts/simulation/maniskill-sapien-batches
```

该命令在缺少真实 ManiSkill/SAPIEN 环境时会输出 `environment_missing` failure boundary；这属于历史对照 adapter 的反证边界，不表示 OpenUSD/Isaac 主底座已经完成 runtime 验证。

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

该命令按 5 个 shard x 100 requested samples 组织 500 requested samples。默认复用已存在且通过一致性校验的 `batch_result.json`；需要忽略已有结果并强制重跑时追加 `--force`。输出中的 shard reports、`failure_boundary_counts`、`field_coverage_trend` 和 `locked_for_next_batch_with_conditions` 用于历史对照 adapter 的数据积累判断，但不代表 Isaac Sim runtime 验证、真实焊接质量验证或真实机器人执行验证已经完成。

可选 1000 requested samples next-batch 命令：

```bash
uv run python -m weldcore.simulation_bakeoff.maniskill_accumulation_pipeline \
  --outdir artifacts/simulation/maniskill-sapien-accumulations \
  --accumulation-id maniskill-sapien-accumulation-next-batch-1000 \
  --shards 10 \
  --samples-per-task 50
```

该命令按 10 个 shard x 100 requested samples 组织 1000 requested samples。本轮真实运行审查中，首次运行 1000/1000 completed，复用运行 10 个 shard 均为 `reused_existing_result`，`failure_boundary_counts` 为空。后续批次若出现 failed samples，应优先修复具体 failure boundary；该命令仍不表示 Isaac Sim runtime 验证、真实焊接质量验证或真实机器人执行验证已经完成。

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
- 不要把历史候选或对照 adapter 写成与 OpenUSD/Isaac 同等优先的长期主线。
- 不要把 adapter 失败边界写成项目失败；它是当前反证工作的一部分。
- 不要把 simlite 写成最终仿真器。
- 不要把 Rerun 写成仿真器、机器人控制总线或生产数据库。
- 不要把 `RobotProcessPackageDraft` 写成正式机器人工艺包。
- 不要把 lightweight `RobotFeasibilityResult` 写成完整 IK、真实碰撞检测或真实机器人执行验证。
- 不要把 `ready_for_expert_review` 写成 `ready_for_robot_execution`。
- 不要把 Excel/K01 字段合同、参数集、系统计算结果或仿真推导结果写成正式 WPS/PQR。
- 不要删除历史成果；历史材料应继续保留在归档目录中。
