# A02 机器人技能大师战略对齐修订设计

日期：2026-06-22

## 1. 背景

公司母战略已经将长期能力收束为 MAS：M 是机器人技能大师，A 是时空智能，S 是多主体协同。A02 对应 M，但它不应被继续讲成一个独立平台概念，而应被定位为公司机器人技能大师能力下的 **焊接技能资产底座**。

当前 A02 已经完成从早期 POC、MVP、样本扩张、gate 报告到 `ManipulationSkillAsset` 本体的收束，并且已经具备：

- `SimulationEvidenceBundle -> ManipulationSkillAsset`。
- `RobotBodyAsset -> RobotContextSpec`。
- `SceneContextAsset`。
- lightweight `RobotFeasibilityResult`。
- `SkillTransferAssessment -> ready_for_expert_review`。
- 七份默认 `asset_report` JSON。

方向是正确的，但默认文档和最小接口还需要继续修正：

1. 减少“焊接技能大师平台”的平台化表达。
2. 把仿真样本、URDF、robot precheck 明确写成技能资产 evidence，而不是项目主线本身。
3. 增加 A01 工站回采数据和 B06 Physical AI Package 到 `ManipulationSkillAsset` 的映射。
4. 建立专家审查记录结构，使 `ready_for_expert_review` 后面有可审查对象。
5. 明确 A02 对 A01 和 IP 的输出，而不是只在仓库内自洽。

## 2. 设计目标

本轮目标是做一次 **小而完整的战略对齐修订**：

1. 将项目入口改为“机器人技能大师能力的焊接技能资产底座”。
2. 将当前主链路重写为：

   ```text
   SimulationEvidenceBundle
   / real_robot_log
   / human_demo
   / h300_workcell_run
   / B06 Physical AI Package
   -> ManipulationSkillAsset
   -> SkillTransferAssessment
   -> RobotContextSpec + SceneContextAsset + RobotFeasibilityResult
   -> ExpertReviewRecord
   -> expert review candidate
   ```

3. 标准化 `ManipulationSkillAsset` evidence source 类型，至少包括：
   - `simulation_only`
   - `human_demo`
   - `real_robot_log`
   - `h300_workcell_run`
   - `expert_annotation`
4. 定义 A01/H300 工站回采数据到 skill asset evidence 的映射表。
5. 定义 B06 Physical AI Package 到 skill asset evidence 的映射表。
6. 建立最小 `ExpertReviewRecord`，绑定技能资产、机器人上下文、场景上下文、预检结果、审查结论、阻塞原因和下一步动作。
7. 扩展默认 `asset_report`，让它优先服务 A01 产品验证和 P0-02/P0-03/P0-04 IP 交底。
8. 更新 README、details、引擎 README 和 HTML 阅读副本。

## 3. 非目标

本轮不做以下事情：

- 不实现 A01 真实工站生产 connector。
- 不实现 B06 Physical AI Package 完整 parser 或跨仓库运行依赖。
- 不实现真实 TCP 标定、工件坐标系测量或真实 robot controller 接口。
- 不把 `ready_for_expert_review` 写成 `ready_for_robot_execution`。
- 不把 lightweight feasibility 写成完整 IK、真实 collision 或 MoveIt/Gazebo 验证。
- 不把 A02 扩成完整业务平台、审核系统或工站产品。
- 不删除历史 POC、MVP、gate、simulation accumulation 成果；只把它们放到 evidence / 历史索引口径。

## 4. 方案比较

### 方案 A：只改 README

优点：最快，风险最低。  
缺点：A01/B06/IP 映射仍然只是文字承诺，代码层默认报告无法证明项目已对齐新战略。

### 方案 B：大规模改造成工站/数据平台

优点：看起来覆盖 A01、B06、A02 所有接口。  
缺点：越界，容易把 A02 做成平台或生产 connector，破坏“技能资产底座”的边界，也会与 A01/B06 责任重叠。

### 方案 C：战略入口重排 + 最小接口对象承接

优点：既修正文档主叙事，又让默认报告出现 A01/B06/evidence/expert review 的结构证据；范围足够小，不进入生产 connector 或真实执行。  
缺点：仍然只是 contract / mapping / review record 的第一版，不等于真实工站数据已接入。

本轮采用方案 C。

## 5. 核心对象调整

### 5.1 Evidence Source

`SkillAssetSourceType` 调整为新战略口径：

```text
simulation_only
human_demo
real_robot_log
h300_workcell_run
expert_annotation
```

默认 simlite 生成的 skill asset 应使用 `source_type = simulation_only`。历史 `simulation` 口径只保留在低层仿真 bundle 或旧 facade 中，不作为新的 `ManipulationSkillAsset` canonical source type。

兼容策略：

- `SimulationEvidenceBundle`、`SimulationTaskSpec`、ManiSkill/SAPIEN batch、accumulation 和旧报告层可继续使用 `simulation`，因为它们描述的是仿真系统自身。
- `ManipulationSkillAsset.source_type` 和 `SkillAssetEvidence.source_type` 使用新的 canonical evidence source 类型。
- 第一版不实现旧 JSON 的自动 migration；仓库内默认生成路径和测试 fixture 必须更新为新口径。
- 如后续需要读取旧 `source_type = simulation` 的 skill asset JSON，应另开兼容任务，而不是在本轮隐式接受混合口径。

### 5.2 A01/H300 Workcell Evidence Mapping

新增最小映射对象，表达 A01 工站回采数据如何进入 A02：

字段建议：

- `mapping_id`
- `source_system = A01_H300_workcell`
- `target_skill_asset_id`
- `evidence_source_type = h300_workcell_run`
- `workcell_fields`
- `skill_asset_field_mapping`
- `context_mapping`
- `quality_feedback_mapping`
- `evidence_boundary`
- `next_step_recommendation`

映射表应覆盖：

| A01/H300 字段 | A02 去向 |
| --- | --- |
| task / weld seam / workpiece | `intent`、`SceneContextAsset` |
| path points / robot pose / torch pose | `motion.tcp_trajectory`、`motion.tool_orientation` |
| process parameters | `constraints` 或 evidence refs |
| manual correction | evidence notes、expert review input |
| execution log / anomaly | evidence boundary、blocking reason |
| quality result | quality feedback evidence，不能直接写成 WPS/PQR |

### 5.3 B06 Physical AI Package Mapping

新增最小映射对象，表达 B06 如何把一次作业窗口交给 A02：

字段建议：

- `mapping_id`
- `source_package_profile`
- `target_skill_asset_id`
- `package_fields`
- `skill_asset_field_mapping`
- `artifact_refs`
- `evidence_boundary`
- `next_step_recommendation`

映射表应覆盖：

| B06 Package 字段 | A02 去向 |
| --- | --- |
| task context | `intent`、source refs |
| coordinate frames | `RobotContextSpec`、`SceneContextAsset` |
| frames / events / labels | evidence refs、review input |
| trajectory / human correction | `motion`、evidence notes |
| metrics / quality labels | quality feedback evidence |
| artifacts / Rerun replay | artifact refs，不直接写成 skill 本体 |

### 5.4 ExpertReviewRecord

新增专家审查记录结构：

- `review_id`
- `skill_asset_id`
- `robot_context_id`
- `scene_context_id`
- `feasibility_result_id`
- `robot_context_snapshot`
- `scene_context_snapshot`
- `feasibility_status_snapshot`
- `source_evidence_summary`
- `review_status`
- `review_conclusion`
- `blocking_reasons`
- `required_real_context`
- `next_actions`
- `review_boundary`
- `reviewer_role`
- `version`

默认报告可以生成一份 `review_status = pending_expert_review` 的记录。它说明当前对象已经进入专家审查候选，但尚未被专家确认，更不表示真实机器人可执行。

`required_real_context` 不能是自由文本。第一版必须显式包含以下必填项，每项至少表达 `field`、`current_status`、`required_evidence` 和 `blocking_if_missing`：

| 必填项 | 当前默认状态 | 所需证据 |
| --- | --- | --- |
| `real_tcp_calibration` | `nominal_from_asset_not_calibrated` | TCP 标定记录、工具坐标系版本、标定时间或来源 |
| `workpiece_frame_measurement` | `default_scene_context_not_measured` | 工件坐标系测量记录、坐标系来源、测量时间或来源 |
| `robot_model_identity` | `urdf_asset_identity_only` | 真实机器人型号/序列或内部资产 ID 与 URDF 的对应关系 |
| `joint_limits_source` | `urdf_joint_limits_not_vendor_validated` | 厂商参数、控制器参数或经确认的关节限制来源 |

`robot_context_snapshot`、`scene_context_snapshot` 和 `feasibility_status_snapshot` 是为了让专家审查记录可审计。它们不需要复制完整大对象，但必须记录关键状态、ID、边界和结论，例如：

- `robot_context_snapshot`: `context_id`、`robot_model`、`tcp_calibration_status`、`workpiece_frame`、`joint_limits_source`、`evidence_notes`。
- `scene_context_snapshot`: `scene_id`、`workpiece_frame`、`validation_status`、`validation_issues`、`evidence_boundary`。
- `feasibility_status_snapshot`: `result_id`、`status`、各子检查状态、`blocking_reasons`、`warning_reasons`、`evidence_boundary`。

### 5.5 A02 -> A01 Product Validation Handoff

新增 A02 输出给 A01 的最小产品验证交付物。它不是机器人程序，也不是生产下发包，而是 A01/H300 可以用于评测、提示或复盘的技能资产候选摘要。

字段建议：

- `handoff_id`
- `skill_asset_id`
- `target_product = A01_H300_workcell`
- `candidate_outputs`
- `trajectory_candidate_ref`
- `posture_parameter_suggestions`
- `failure_boundaries`
- `required_confirmations`
- `not_ready_reasons`
- `evidence_refs`
- `handoff_boundary`
- `next_step_recommendation`

`candidate_outputs` 至少包括：

- `skill_package_candidate`
- `trajectory_candidate`
- `torch_posture_suggestion`
- `process_parameter_hint`
- `failure_boundary_summary`

默认状态必须表达：可供 A01 产品验证或提示参考，但不可直接下发真实机器人。

### 5.6 A02 -> IP Disclosure Support

新增 A02 输出给 IP 交底的最小支撑表，明确 P0-02/P0-03/P0-04 分别由哪些对象和报告支撑。

字段建议：

- `support_id`
- `patent_item_id`
- `patent_item_name`
- `supporting_objects`
- `supporting_reports`
- `evidence_boundaries`
- `missing_real_world_evidence`
- `next_evidence_actions`

首批固定三项：

| 专利项 | 名称 | 支撑对象 |
| --- | --- | --- |
| `P0-02` | 焊接技能包 | `ManipulationSkillAsset`、`SkillAssetEvidence`、`ExpertReviewRecord`、`SkillAssetEvidenceWritebackSummary` |
| `P0-03` | 焊接轨迹结构化转换 | `motion.tcp_trajectory`、`motion.tool_orientation`、A01/B06 映射中的 path / pose / manual correction 字段 |
| `P0-04` | 仿真优先焊接技能数据集 | `SimulationEvidenceBundle`、modeled task specs、100/500/1000 requested samples、evidence writeback summary |

每项都必须写明缺失的真实世界证据，例如真实工站回采、专家审查结论、质量反馈、真机执行日志或 WPS/PQR 之外的质量边界。

## 6. 默认报告调整

当前 `asset_report` 已输出七份 JSON。本轮建议扩展为十二份：

1. `skill_asset_report.json`
2. `robot_body_asset_report.json`
3. `robot_context_spec.json`
4. `scene_context_asset_report.json`
5. `skill_transfer_assessment.json`
6. `robot_feasibility_result.json`
7. `skill_asset_evidence_writeback_summary.json`
8. `skill_asset_evidence_source_catalog.json`
9. `a01_b06_skill_asset_mapping.json`
10. `expert_review_record.json`
11. `a02_to_a01_product_validation_handoff.json`
12. `ip_disclosure_support_matrix.json`

新增五份报告的目的：

- 让 A01 产品经理能看到 H300 回采数据如何成为 A02 evidence。
- 让 B06 负责人能看到 Physical AI Package 哪些字段进入 skill asset，哪些只作为附件或上下文。
- 让 A01 能看到 A02 当前可反哺的技能包候选、轨迹候选、姿态/参数建议和失败边界。
- 让 IP 交底能直接引用 P0-02/P0-03/P0-04 支撑对象和缺失证据。

## 7. 文档调整

### 7.1 根 README

根 README 首页重排为：

1. 项目定位：机器人技能大师的焊接技能资产底座。
2. 当前主链路。
3. 核心对象。
4. A01/B06/A02 接口。
5. 当前可运行能力，只列与主链路直接相关的能力。
6. 下一阶段任务：A01 回采、B06 Package、专家审查和真实上下文替换。
7. 边界。
8. 验证命令。
9. 历史能力索引。

第一段使用新版定位：

> A02 是公司机器人技能大师能力的焊接技能资产底座项目，目标是把焊接操作中的动作、意图、轨迹、姿态、工艺约束、证据边界、迁移契约和质量反馈沉淀为 `ManipulationSkillAsset`。项目通过仿真、真实机器人日志、人工示教、专家标注和智能焊接工站回采数据，形成可学习、可迁移、可评测、可审计的技能资产，为 A01 智能焊接工站和后续机器人执行验证提供能力底座。

### 7.2 details.md

`details.md` 增加 2026-06-22 更新，说明：

- A02 已按母战略重定位为机器人技能大师能力下的焊接技能资产底座。
- 仿真样本数、URDF、precheck 被明确放入 evidence 来源。
- 下一步主线为 A01/B06 evidence handoff、expert review record、真实上下文替换。

### 7.3 当前态架构与技能资产文档

当前态文档中仍使用“平台”或旧对象口径的文件需要同步修订，至少包括：

- `docs/architecture/README.md`
- `docs/skill-assets/weld-skill-package.md`

归档目录 `docs/archive/` 和历史 superpowers spec / plan 不做追溯性改写；它们保留当时阶段语境。

### 7.4 weld-experience-engine/README.md

引擎 README 需要同步说明：

- `weldcore.skill_asset` 是焊接技能资产引擎，不是完整平台。
- `asset_report` 默认服务 A01 产品验证和 IP 交底。
- 新增 mapping / review / A01 handoff / IP support artifact。

### 7.5 HTML 阅读版

更新根 `README.html` 和 `details.html`，保持 Markdown 为维护源。

## 8. 验收标准

本轮完成后，应能回答以下问题：

1. 一个焊接操作技能资产由哪些字段构成。
2. 哪些证据来自仿真、真实工站、真实机器人日志、人工示教和专家审查。
3. `ready_for_expert_review` 与 `ready_for_robot_execution` 的边界是什么。
4. A01 回采数据如何进入 A02。
5. B06 Physical AI Package 如何向 A02 交付 evidence。
6. A02 输出什么能力反哺 A01。
7. P0-02、P0-03、P0-04 分别由哪些对象和报告支撑。
8. 默认验证命令仍能通过，项目默认状态仍可安装、可运行、可测试。

## 9. 测试策略

新增或调整测试：

- `SkillAssetSourceType` 支持新 canonical source 类型。
- 默认 simlite skill asset 使用 `simulation_only`。
- evidence source catalog 至少包含 `simulation_only`、`human_demo`、`real_robot_log`、`h300_workcell_run`、`expert_annotation`。
- A01/B06 mapping artifact 能序列化，并包含 H300 workcell 与 Physical AI Package 字段映射。
- ExpertReviewRecord 默认状态为 `pending_expert_review`，且边界包含 `not_ready_for_robot_execution`。
- ExpertReviewRecord 的 `required_real_context` 必须包含 `real_tcp_calibration`、`workpiece_frame_measurement`、`robot_model_identity`、`joint_limits_source` 四项。
- ExpertReviewRecord 必须包含 robot context、scene context 和 feasibility status 的可审计快照。
- A02 -> A01 handoff artifact 必须包含技能包候选、轨迹候选、姿态/参数建议、失败边界和“不直接下发机器人”的边界。
- IP support matrix 必须包含 P0-02、P0-03、P0-04，并列出 supporting objects、reports、missing real-world evidence。
- `asset_report` 输出十二份 JSON。
- README 第一段必须使用“机器人技能大师能力的焊接技能资产底座”口径。
- 根 README / details 的 HTML 阅读版必须包含与 Markdown 同步的新口径和 `390 passed` 验证记录。
- 当前态 `docs/architecture/README.md` 与 `docs/skill-assets/weld-skill-package.md` 不再把 A02 默认描述为独立“平台”。
- 文档边界必须继续声明不是真实机器人可执行、不是真实焊接质量验证、不是 WPS/PQR、不是最终仿真器选型。
- 旧的 skill asset / contextual precheck / report 测试继续通过。

完整验证：

```bash
cd weld-experience-engine
uv run pytest -q
uv run python -m weldcore.skill_asset.asset_report --outdir /tmp/a02-strategic-asset-report
```

## 10. 风险与取舍

- 将 `ManipulationSkillAsset.source_type` 从 `simulation` 调整为 `simulation_only` 会影响默认 JSON 断言，但这是战略口径要求；低层仿真 bundle 继续保留 `simulation`。
- 不直接读取 B06 仓库的真实 package，避免跨仓库耦合；本轮只定义 mapping contract。
- 不把 expert review record 写成专家已审查结果；默认必须是 pending。
- 不把 A01 回采映射写成真实回采已经完成；默认只是 handoff contract 和 report artifact。
