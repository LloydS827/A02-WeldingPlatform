# A02 机器人技能大师焊接技能资产底座项目进展记录

更新时间：2026-06-22

这份文件用于记录 A02「机器人技能大师能力的焊接技能资产底座」每一阶段完成了什么、下一步准备做什么、哪些判断发生了变化。它不是项目入口说明；项目入口请看 [README.md](README.md)。

## 文件定位

- `README.md`：项目入口，面向任何新读者说明项目定位、核心链路、当前能力、如何运行和边界。
- `details.md`：阶段更新记录，面向项目讨论记录近期更新、当前判断、下一步计划和风险提醒。

本文件应同步维护 [HTML 阅读版](details.html)。更新根目录 `README.md`、本文件或类似面向读者的阶段/路线说明时，也要同步刷新对应 `.html` 阅读副本。

## 当前一句话状态

项目已经按母战略修订为“机器人技能大师能力的焊接技能资产底座”。当前主线以 `ManipulationSkillAsset` 为核心，把仿真、真实机器人日志、人工示教、专家标注和 A01 H300 工站回采数据统一视为技能资产 evidence。默认可运行路径已经能从 `SimulationEvidenceBundle` 构建技能资产，把真实协作臂 URDF 解析为 `RobotBodyAsset`，绑定 nominal `RobotContextSpec` 和默认 `SceneContextAsset`，让 `SkillTransferAssessment` 消费 lightweight `RobotFeasibilityResult` 推进到 `ready_for_expert_review`，并生成 A01/B06 mapping、`ExpertReviewRecord`、A02->A01 handoff 和 IP support matrix。这个状态只表示进入专家审查候选，不表示真实机器人可执行。

## 当前主线判断

现在不适合跳到真实机器人控制或完整 MoveIt/Gazebo 集成，也不应继续只按 requested samples 数量线性扩张。更合理的节奏是先把“技能资产本体是什么、A01/B06 数据如何成为 evidence、专家审查到底审什么、哪些真实上下文缺口阻止迁移验证”做清楚，再继续扩大仿真数据积累。

更合理的主线是：

```text
SimulationEvidenceBundle / real robot log / human demonstration / H300 workcell run
-> ManipulationSkillAsset
+ RobotBodyAsset(URDF)
-> SkillTransferAssessment
-> RobotContextSpec
-> SceneContextAsset
-> RobotFeasibilityResult
-> ExpertReviewRecord
-> A02->A01 product validation handoff / IP evidence support
```

这一段必须先稳定下来。只有当 skill asset 本体、机器人身体资产、场景上下文、输出证据、失败边界、A01/B06 字段映射和专家审查记录都可复跑、可比较、可审查之后，项目才适合继续进入更大规模的持续数据积累或真实机器人迁移验证。

这里的“反证工作”很重要：候选仿真软件不是因为名字先进就自动成为主线，而要通过同一组任务、同一套输出契约和同一份证据报告证明它能接入项目数据结构；不能接入的地方也要明确记录失败原因。

## 近期更新

### 2026-06-22

- 完成 A02 战略口径修订：默认定位从“焊接技能大师平台”收束为“机器人技能大师能力的焊接技能资产底座”。
- 标准化 `ManipulationSkillAsset` evidence source type：canonical skill asset 层使用 `simulation_only`、`human_demo`、`real_robot_log`、`h300_workcell_run` 和 `expert_annotation`；低层仿真 source manifest 仍可保留 `simulation`。
- 新增 A01 H300 工站回采与 B06 Physical AI Package 到 `ManipulationSkillAsset` 的 mapping artifact，覆盖 path points、robot pose、torch pose、manual correction、quality result、trajectory、human correction、quality labels 和 rerun replay ref。
- 新增 `ExpertReviewRecord`，绑定技能资产 ID、机器人上下文、场景上下文、feasibility result、source evidence summary、审查状态、阻塞原因、required real context 和 next actions。
- 新增 A02->A01 product validation handoff，明确 A02 输出的是 skill package candidate、trajectory candidate、torch posture suggestion、process parameter hint 和 failure boundary summary，不是可直接派发的 robot program。
- 新增 IP support matrix，把 P0-02“焊接技能包”、P0-03“焊接轨迹结构化转换”、P0-04“仿真优先焊接技能数据集”映射到 supporting objects、supporting reports 和 missing real-world evidence。
- 扩展 `weldcore.skill_asset.asset_report`，默认从 7 份 JSON 扩展为 12 份 JSON artifact，优先服务 A01 产品验证和 IP 交底准备。
- 更新 README、引擎 README、架构文档和技能包文档，减少平台化表达，明确 `WeldSkillPackage` 是历史兼容 / facade，当前 canonical object 是 `ManipulationSkillAsset`。
- 本轮验证：`uv run pytest -q` 通过 `395 passed`；`asset_report` 已确认写出 12 份 JSON，默认 `transfer_assessment.status=ready_for_expert_review`，`expert_review_record.review_status=pending_expert_review`，`robot_feasibility_result.status=passed`。

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
- 经验数据与 `ManipulationSkillAsset` 之间的跨批次字段追踪还需要进一步收束。
- 专家审查记录结构已经作为 artifact 实现，但尚未接入真实专家结论、审查人、审查时间和闭环动作。
- A01 H300 工站回采和 B06 Physical AI Package 目前是字段合同和报告 artifact，尚未接入真实或脱敏样本。
- 真实 TCP 标定记录、工具坐标系标定记录和工件坐标系测量记录尚未替换当前 nominal context。
- 完整 IK、真实碰撞检测、MoveIt/Gazebo adapter、机器人控制接口和真机日志尚未接入当前 `RobotFeasibilityResult`。
- 真实焊机、机器人、焊材、焊后检测和质量结果尚未接成闭环。
- 当前资料、输入规范、仿真假设和工程师参考表格不能替代正式 WPS/PQR。

## 下一步建议

推荐下一阶段任务是：**用真实或脱敏工站证据替换 nominal context，并运行专家审查闭环**。

目标是在当前 `ready_for_expert_review` 和 `pending_expert_review` 基础上，把“真实上下文证据从哪里来、专家如何审、A02 如何反哺 A01、IP 交底缺哪些真实证据”说清楚：

1. 用真实 TCP calibration record、tool frame calibration 和 workpiece frame measurement records 替换当前 nominal context。
2. 使用 B06 Physical AI Package / A01 H300 真实或脱敏样本作为 `h300_workcell_run`、`real_robot_log` 或 `human_demo` evidence。
3. 运行 `ExpertReviewRecord` 工作流，填入专家结论、阻塞原因、下一步动作和是否允许进入更重 robot adapter 验证。
4. 将 A02 输出回送 A01 产品验证，明确候选轨迹、姿态/参数建议和失败边界如何被 H300 工站消费。
5. 准备 P0-02、P0-03、P0-04 evidence packs，补齐当前 IP support matrix 中列出的 missing real-world evidence。
6. 做一个最小 MoveIt/Gazebo 或等价 robot adapter 反证实验，让更重的 IK / collision 结果填入同一份 `RobotFeasibilityResult`，而不是另建机器人主线。

这一轮仍不应直接进入真实机器人执行或真实焊接质量判断，也不应把结果写成最终仿真器选型。

## 暂缓事项

- 暂缓新增更多任务族或第三个 `WeldSkillUnit` 作为默认积累对象，避免在 scale shard 未稳定前同时扩大任务复杂度。
- 暂缓完整 Gazebo/MoveIt 或 ROS 侧集成，除非它作为候选 adapter 的最小反证实验出现。
- 暂缓专家审核系统化产品录入；下一阶段先运行最小 `ExpertReviewRecord` 工作流和真实标定记录替换，而不是直接建设审核系统。
- 暂缓真实机器人执行结论，当前只做候选草案和审查前置条件。

## 当前可交付物清单

- `README.md`：项目默认入口。
- `details.md`：阶段更新记录和下一步计划。
- `docs/strategy/`：公司级 Physical AI 判断与当前项目承接关系。
- `docs/architecture/`：五层架构、模块边界和 adapter 原则。
- `docs/skill-assets/`：`ManipulationSkillAsset` 主线说明，以及 `WeldSkillPackage` 历史兼容 / facade。
- `docs/simulation/`：仿真路线、simlite 边界、外部 adapter 候选和 ManiSkill/SAPIEN 开发环境说明。
- `docs/evidence/`：资料来源、字段覆盖、证据报告和质量边界。
- `docs/archive/`：POC、MVP、gate、白皮书和旧计划归档。
- `docs/superpowers/specs/`：阶段设计文档。
- `docs/superpowers/plans/`：阶段实施计划。
- `docs/real-urdf/robot.urdf` 与 `docs/real-urdf/meshes/`：真实协作臂 RobotBodyAsset 输入资产。
- `weldcore.skill_asset.asset_report`：canonical skill asset 报告入口，默认生成十二份 JSON，包括 `ManipulationSkillAsset`、`RobotBodyAsset`、`RobotContextSpec`、`SceneContextAsset`、`SkillTransferAssessment`、`RobotFeasibilityResult`、evidence writeback summary、evidence source catalog、A01/B06 mapping、expert review record、A02->A01 handoff 和 IP support matrix。
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

当前分支最近一次完整验证结果为 `395 passed`。

当前 canonical skill asset 报告命令：

```bash
uv run python -m weldcore.skill_asset.asset_report \
  --outdir artifacts/skill-assets/canonical
```

该命令会生成 12 份 JSON：`skill_asset_report.json`、`robot_body_asset_report.json`、`robot_context_spec.json`、`scene_context_asset_report.json`、`skill_transfer_assessment.json`、`robot_feasibility_result.json`、`skill_asset_evidence_writeback_summary.json`、`skill_asset_evidence_source_catalog.json`、`a01_b06_skill_asset_mapping.json`、`expert_review_record.json`、`a02_to_a01_product_validation_handoff.json` 和 `ip_disclosure_support_matrix.json`。当前默认结果中，`robot_body_asset.validation_status` 为 `usable_as_robot_body_context`，`transfer_assessment.status` 为 `ready_for_expert_review`，`expert_review_record.review_status` 为 `pending_expert_review`，`robot_feasibility_result.status` 为 `passed`；它仍然不表示真实机器人可执行。

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
- 不要把 lightweight `RobotFeasibilityResult` 写成完整 IK、真实碰撞检测或真实机器人执行验证。
- 不要把 `ready_for_expert_review` 写成 `ready_for_robot_execution`。
- 不要把工程师参数参考表格写成当前主流程数据源或正式 WPS/PQR。
- 不要删除历史成果；历史材料应继续保留在归档目录中。
