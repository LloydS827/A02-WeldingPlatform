# A02 机器人技能大师焊接技能资产底座

## 项目定位

A02 是公司机器人技能大师能力的焊接技能资产底座项目，目标是把焊接操作中的动作、意图、轨迹、姿态、工艺约束、证据边界、迁移契约和质量反馈沉淀为 `ManipulationSkillAsset`。项目通过仿真、真实机器人日志、人工示教、专家标注和智能焊接工站回采数据，形成可学习、可迁移、可评测、可审计的技能资产，为 A01 智能焊接工站和后续机器人执行验证提供能力底座。

本项目对应公司 MAS 中的 M，也就是机器人技能大师能力。它不是一个独立对外讲述的平台概念，而是公司长期积累机器人操作能力的技术底座。当前第一场景是焊接，后续可以承接打磨、喷涂、切割、装配、检测等工业操作技能。

## 文件入口

- [README HTML 阅读版](README.html)
- [项目进展记录 HTML 阅读版](details.html)

`README.md` 是项目入口，说明项目定位、当前主链路、核心对象、接口关系、可运行能力、边界和验证方式。

`details.md` 是阶段更新记录，说明每轮完成内容、下一步计划和风险判断。更新根目录 Markdown 时，需要同步刷新对应 HTML 阅读副本。

## 当前主链路

当前主链路是：

```text
SimulationEvidenceBundle / real robot log / human demonstration / H300 workcell run
-> ManipulationSkillAsset
-> SkillTransferAssessment
-> expert review candidate
```

展开到当前默认可运行路径：

```text
SimulationEvidenceBundle
-> ManipulationSkillAsset
+ RobotBodyAsset(URDF)
+ RobotContextSpec
+ SceneContextAsset
+ lightweight RobotFeasibilityResult
-> SkillTransferAssessment
-> ExpertReviewRecord
-> A02->A01 product validation handoff / IP evidence support
```

这条链路的含义是：

- `ManipulationSkillAsset` 是当前 canonical 技能资产本体，描述技能意图、TCP 轨迹、工具姿态、约束、证据来源、质量边界和迁移契约。
- 仿真样本、真实 URDF、robot precheck、modeled task specs 和 1000 next-batch 样本都应写成技能资产 evidence，而不是各自形成平行主线。
- `ready_for_expert_review` 表示资产、机器人上下文、场景上下文和轻量预检足以进入专家审查候选；它不是 `ready_for_robot_execution`。

## 核心对象

- `ManipulationSkillAsset`：技能资产本体，承载意图、运动、约束、证据、质量边界和迁移契约。
- `SkillAssetEvidence`：记录 evidence source、artifact refs、metrics、review status 和 evidence boundary。
- `RobotBodyAsset`：由真实 URDF 和 mesh 解析出的机器人身体资产。
- `RobotContextSpec`：机器人型号、base/TCP/tool/workpiece frame、关节限制来源和真实标定边界。
- `SceneContextAsset`：工件坐标系、焊缝路径、夹具/障碍、安全边界和场景证据边界。
- `RobotFeasibilityResult`：lightweight reachability / collision-assumed / joint-limit / path-continuity / orientation 预检结果。
- `SkillTransferAssessment`：把技能资产、机器人身体、机器人上下文、场景上下文和 feasibility result 汇总成迁移评估。
- `ExpertReviewRecord`：绑定技能资产、机器人上下文、场景上下文、预检结果、人工结论、阻塞原因和下一步动作。
- `A01B06SkillAssetMapping`：把 A01 H300 工站回采和 B06 Physical AI Package 字段映射到 `ManipulationSkillAsset`。
- `A02ToA01ProductValidationHandoff`：A02 反哺 A01 的候选技能包、轨迹候选、姿态/参数建议和失败边界。
- `IPDisclosureSupportMatrix`：把 P0-02、P0-03、P0-04 对应到支撑对象、报告和缺失真实证据。

## A01/B06/A02 接口

`A01 -> A02`：

- 从智能焊接工站的真实或脱敏作业数据生成技能资产 evidence。
- 重点字段包括 task、weld seam、workpiece、path points、robot pose、torch pose、process parameters、manual correction、execution log、anomaly 和 quality result。
- 默认 evidence source type 为 `h300_workcell_run`。

`B06 -> A02`：

- 从 Physical AI Package 读取 task context、coordinate frames、frames、events、labels、trajectory、human correction、metrics、quality labels 和 rerun replay ref。
- B06 不作为本仓库 runtime 依赖；本轮只定义字段合同和报告 artifact。

`A02 -> A01`：

- 输出可供 H300 产品验证或提示的 skill package candidate、trajectory candidate、torch posture suggestion、process parameter hint 和 failure boundary summary。
- 输出不是控制器可下载程序，不是生产派发包，不是 `ready_for_robot_execution`。

`A02 -> IP`：

- P0-02“焊接技能包”由 `ManipulationSkillAsset`、`SkillAssetEvidence`、`ExpertReviewRecord` 和 evidence writeback report 支撑。
- P0-03“焊接轨迹结构化转换”由 `motion.tcp_trajectory`、tool orientation、A01/B06 mapping 和 manual correction 字段支撑。
- P0-04“仿真优先焊接技能数据集”由 `SimulationEvidenceBundle`、modeled task specs、100/500/1000 requested samples 和 evidence source catalog 支撑。

## 当前可运行能力

- 可运行的 `weldcore` 引擎，详见 [weld-experience-engine/README.md](weld-experience-engine/README.md)。
- 从 `SimulationEvidenceBundle` 构建 `ManipulationSkillAsset`，canonical evidence source type 为 `simulation_only`。
- 从 `docs/real-urdf/robot.urdf` 解析 `RobotBodyAsset`，当前真实 URDF 可解析为 7 links、6 revolute joints、33 unique mesh files 和 66 mesh references。
- 从 `RobotBodyAsset` 构建 nominal `RobotContextSpec`，保留 `nominal_from_asset_not_calibrated`、`not_tcp_calibrated`、`not_vendor_validated` 和 `not_ready_for_robot_execution` 边界。
- 构建默认 `SceneContextAsset`，表达工件坐标系、焊缝路径、安全边界和夹具/障碍占位。
- 构建 lightweight `RobotFeasibilityResult`，当前只做结构性 reachability、collision assumed、joint-limit source、path continuity 和 orientation 预检。
- `SkillTransferAssessment` 在默认上下文齐备时推进到 `ready_for_expert_review`。
- `ExpertReviewRecord` 记录四项从 nominal context 走向真实上下文的必填项：真实 TCP 标定、工件坐标系测量、机器人型号身份确认和关节限制来源确认。
- `SkillAssetEvidenceWritebackSummary` 把 8 个 modeled task specs 和 1000 next-batch samples 记录为技能资产 evidence candidates。
- `weldcore.skill_asset.asset_report` 默认生成 12 份 JSON artifact，服务 A01 产品验证和 IP 交底准备。

## 下一阶段任务

1. 用真实 TCP calibration record、tool frame calibration 和 workpiece frame measurement 替换当前 nominal context。
2. 接入 A01 H300 工站真实或脱敏回采样本，填充 `h300_workcell_run` evidence。
3. 从 B06 Physical AI Package 读取作业窗口、轨迹、事件、人工修正和质量标签，回填为 `ManipulationSkillAsset` evidence。
4. 运行 `ExpertReviewRecord` 工作流，让专家结论、阻塞原因和下一步动作成为默认审查对象。
5. 将 A02 输出回送 A01 产品验证，明确候选轨迹、姿态/参数建议和失败边界。
6. 为 P0-02、P0-03、P0-04 补齐真实工站证据、专家审查证据和质量反馈证据。
7. 在同一 `RobotFeasibilityResult` 结构下引入 MoveIt/Gazebo 或其他 robot adapter 的反证结果，不另建平行机器人主线。

## 边界

- 当前不宣称真实机器人可执行。
- 当前不宣称真实焊接质量验证。
- 当前不宣称正式 WPS/PQR。
- 当前不宣称最终仿真器选型。
- `ready_for_expert_review` 不是 `ready_for_robot_execution`。
- `RobotFeasibilityResult` 不是完整 IK solver，不是真实 collision validation，不是真机日志验证。
- ManiSkill/SAPIEN、Gazebo/MoveIt 和其他 robot adapter 都是同一技能资产主线下的 evidence source 或反证来源，不是平行主线。

## 验证命令

默认验证路径：

```bash
cd weld-experience-engine
uv sync --extra dev --extra viz
uv run pytest -q
```

默认技能资产报告入口：

```bash
uv run python -m weldcore.skill_asset.asset_report \
  --outdir artifacts/skill-assets/canonical
```

该命令生成 12 份 JSON：

- `skill_asset_report.json`
- `robot_body_asset_report.json`
- `robot_context_spec.json`
- `scene_context_asset_report.json`
- `skill_transfer_assessment.json`
- `robot_feasibility_result.json`
- `skill_asset_evidence_writeback_summary.json`
- `skill_asset_evidence_source_catalog.json`
- `a01_b06_skill_asset_mapping.json`
- `expert_review_record.json`
- `a02_to_a01_product_validation_handoff.json`
- `ip_disclosure_support_matrix.json`

默认结果中，`transfer_assessment.status` 为 `ready_for_expert_review`，`expert_review_record.review_status` 为 `pending_expert_review`，`robot_feasibility_result.status` 为 `passed`，但 evidence boundary 仍包含 `not_ready_for_robot_execution`、`not_full_ik_solver`、`not_collision_validated` 和相关真实上下文缺口。

## 历史能力索引

以下能力仍可作为 evidence source、历史支撑或反证来源，不再作为默认项目主线：

- 经验结构化 POC、技能迁移 MVP、资料底座 gate、`SyntheticSkillDataset v2` 输入规范 gate 和仿真输出接入 gate。
- `SkillDataset`、`WeldSkillPackage`、`WeldSkillUnit`、迁移评测和旧 evidence 输出结构。
- simlite/mock bundle 作为 L0 稳定仿真和测试基线。
- ManiSkill/SAPIEN 小批量默认仿真入口、Phase 1 accumulation、Phase 2 sharded accumulation、1000 requested samples next-batch。
- 批量焊接任务建模与验证闭环，默认 8 个 modeled task specs。
- Gazebo/MoveIt 候选路线失败边界记录。
- 从 `SimulationEvidenceBundle` 到 `RobotProcessPackageDraft` 的机器人候选草案转换。
- Rerun 证据回放兼容处理。
- 焊接工艺参数 Excel 表格；它是工程师参数参考，不是正式 WPS/PQR。
- 前期 POC、MVP、gate、白皮书和旧计划材料，统一保留在 `docs/archive/`。

## 当前目录结构

```text
.
├── README.md
├── README.html
├── details.md
├── details.html
├── docs/
│   ├── strategy/
│   ├── architecture/
│   ├── skill-assets/
│   ├── simulation/
│   ├── evidence/
│   ├── real-urdf/
│   ├── archive/
│   └── superpowers/
└── weld-experience-engine/
    ├── README.md
    ├── pyproject.toml
    ├── tests/
    └── weldcore/
```

## Agent 维护规则

后续推进本项目时，应先判断是否需要同步更新 [details.md](details.md)。

需要更新 `details.md` 的情况包括：

- 项目阶段、范围或默认主线发生变化。
- `ManipulationSkillAsset`、A01/B06 mapping、专家审查、IP 支撑矩阵、仿真路线、证据边界或 adapter 边界发生变化。
- 新增或移除重要基础能力、报告命令、验证路径或交付物。
- 下一步计划、风险判断或阶段优先级发生变化。
- 真实焊接质量验证、WPS/PQR、最终仿真器选择等边界判断发生变化。

更新入口文档、阶段说明或路线说明时，必须同步刷新同目录 HTML 阅读版。尤其是根目录 `README.md` 和 `details.md`：Markdown 是维护源，HTML 是面向项目负责人、业务人员、工艺人员和非技术读者的阅读副本。
