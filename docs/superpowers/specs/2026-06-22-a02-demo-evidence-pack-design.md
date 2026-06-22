# A02 Demo Evidence Pack 设计

日期：2026-06-22

## 1. 背景

A02 当前已经从“焊接技能大师平台”收束为“机器人技能大师能力的焊接技能资产底座”。当前默认链路已经能从 `SimulationEvidenceBundle` 构建 `ManipulationSkillAsset`，绑定真实 URDF 派生的 nominal `RobotContextSpec`、默认 `SceneContextAsset` 和 lightweight `RobotFeasibilityResult`，再生成 `SkillTransferAssessment`、`ExpertReviewRecord`、A02->A01 handoff 和 IP support matrix。

上一阶段已经解决了“对象和报告是否存在”的问题，但还没有解决“一个非研发读者如何一键看到系统现在能做什么、证据从哪里来、为什么只到专家审查候选、不进入机器人执行”的问题。

因此下一阶段不应急于接真实数据，也不应继续扩充 requested samples 数量。更合适的是做一个 **可用性证据阶段**：用仿真数据、可复跑 demo 和解释型报告证明系统已经能跑通、能审查、能讲清楚。

## 2. 设计目标

本阶段主题是：

```text
A02 Demo Evidence Pack：焊接技能资产可用性证据包
```

目标是新增一个默认 demo 入口：

```bash
uv run python -m weldcore.skill_asset.demo_report --outdir artifacts/demo/skill-asset-evidence
```

该入口生成一组稳定 artifact，用于回答：

1. 一个技能资产由哪些字段构成。
2. 哪些证据来自仿真。
3. 为什么当前状态是 `ready_for_expert_review`，不是 `ready_for_robot_execution`。
4. A02 如何反哺 A01。
5. P0-02、P0-03、P0-04 当前由哪些对象支撑。

## 3. 关键假设

用户已明确要求关键决策由本次工作独立完成，因此本 spec 将需确认事项转为显式假设：

1. 默认样例采用现有 `default_simulation_task_specs()` 的 2 个任务：长直横焊沿缝跟踪、包角横焊转角过渡。
2. 暂不新增第三个任务族。当前代码默认任务就是 2 个，强行加入第三个会扩大建模和测试范围，不符合“范围适中”。
3. demo 只复用现有 simlite reference、skill asset builder、context builder、strategic alignment builder，不新增新的核心模型。
4. demo 输出的每个任务都必须走完整链路：`SimulationEvidenceBundle -> ManipulationSkillAsset -> SkillTransferAssessment -> ExpertReviewRecord`。
5. demo summary 面向非研发读者，但仍保留机器可读 JSON，以便后续 A01/B06/IP 工作继续消费。
6. HTML summary 是 Markdown summary 的阅读副本，不引入前端框架或复杂样式。

## 4. 非目标

本阶段不做以下事情：

- 不接入 A01 H300 真实或脱敏工站数据。
- 不实现 B06 Physical AI Package parser。
- 不新增真实 TCP 标定、工具坐标系标定或工件坐标系测量记录。
- 不实现 MoveIt/Gazebo/ROS adapter。
- 不把 lightweight feasibility 写成完整 IK、真实碰撞检测或真机验证。
- 不宣称真实焊接质量验证、正式 WPS/PQR、最终仿真器选型或真实机器人可执行。
- 不重构 `ManipulationSkillAsset`、`ExpertReviewRecord` 或 IP support matrix 的核心模型。

## 5. 方案比较

### 方案 A：只扩展现有 `asset_report`

优点：改动最少，复用当前命令。

缺点：`asset_report` 当前是单任务 canonical artifact 输出，继续塞入多任务 demo 和解释型 summary 会让默认报告职责变混乱。

### 方案 B：新增完整 demo 子系统

优点：未来可扩展成更大的演示系统。

缺点：范围过大，容易把 A02 拉回“平台化 demo”，也会引入不必要抽象。

### 方案 C：新增轻量 `demo_report` 聚合入口

优点：保留 `asset_report` 的 canonical 单任务职责，同时新增一个可复跑 evidence pack 命令；实现范围小，能完整回答本阶段问题。

缺点：第一版只覆盖 2 个默认任务，不覆盖真实数据和更重 robot adapter。

本阶段采用方案 C。

## 6. 输出契约

默认命令：

```bash
uv run python -m weldcore.skill_asset.demo_report --outdir artifacts/demo/skill-asset-evidence
```

输出目录建议为：

```text
artifacts/demo/skill-asset-evidence/
├── demo_summary.md
├── demo_summary.html
├── demo_summary.json
├── task-<unit-id-1>/
│   ├── simulation_evidence_bundle.json
│   ├── skill_asset_report.json
│   ├── robot_body_asset_report.json
│   ├── robot_context_spec.json
│   ├── scene_context_asset_report.json
│   ├── robot_feasibility_result.json
│   ├── skill_transfer_assessment.json
│   ├── skill_asset_evidence_writeback_summary.json
│   ├── skill_asset_evidence_source_catalog.json
│   ├── a01_b06_skill_asset_mapping.json
│   ├── expert_review_record.json
│   ├── a02_to_a01_product_validation_handoff.json
│   └── ip_disclosure_support_matrix.json
└── task-<unit-id-2>/
    └── ...
```

每个任务目录必须原样写出 `asset_report` 已有的 12 份 canonical artifact 文件名：

```text
skill_asset_report.json
robot_body_asset_report.json
robot_context_spec.json
scene_context_asset_report.json
skill_transfer_assessment.json
robot_feasibility_result.json
skill_asset_evidence_writeback_summary.json
skill_asset_evidence_source_catalog.json
a01_b06_skill_asset_mapping.json
expert_review_record.json
a02_to_a01_product_validation_handoff.json
ip_disclosure_support_matrix.json
```

`simulation_evidence_bundle.json` 是 demo 额外 source artifact，用于解释每个任务的仿真证据来源，不属于上述 12 份 canonical artifact。

其中 `demo_summary.json` 至少包含：

- `demo_id: str`
- `generated_artifacts: list[str]`，使用相对输出目录路径，必须覆盖实际写出的全部文件。
- `task_count: int`，默认值为 `2`。
- `tasks: list[dict]`
- `overall_status: str`，默认值为 `ready_for_expert_review_candidate_pack`。
- `readiness_boundary: list[str]`，必须包含 `ready_for_expert_review`、`not_ready_for_robot_execution`、`simulation_only`、`not_real_welding_quality_validation`。
- `field_explanation: dict[str, str]`，解释 `ManipulationSkillAsset` 的 intent、motion、constraints、context requirements、evidence、transfer contract 和 quality boundary。
- `simulation_evidence_explanation: dict[str, str]`，解释 `SimulationEvidenceBundle`、simlite reference、metrics 和 evidence boundary。
- `a02_to_a01_handoff_summary: dict[str, object]`，至少包含 candidate outputs、required confirmations 和 handoff boundary。
- `ip_support_summary: list[dict]`，至少覆盖 P0-02、P0-03、P0-04。
- `next_step_recommendation: str`

每个 `tasks[]` 至少包含：

- `task_id: str`
- `task_name: str`
- `skill_asset_id: str`
- `simulation_bundle_id: str`
- `transfer_status: str`，默认应为 `ready_for_expert_review`。
- `expert_review_status: str`，默认应为 `pending_expert_review`。
- `feasibility_status: str`，默认应为 `passed`。
- `source_type: str`，默认应为 `simulation_only`。
- `artifact_refs: dict[str, str]`，使用相对输出目录路径，必须包含本任务目录下所有 JSON artifact。
- `boundary_reasons: list[str]`，必须包含来自 skill asset、transfer assessment、feasibility result、expert review、handoff 和 IP support 的关键边界。
- `why_ready_for_expert_review: list[str]`
- `why_not_ready_for_robot_execution: list[str]`，必须包含真实 TCP 标定、工件坐标系测量、机器人身份确认、关节限制来源、完整 IK、真实碰撞验证、真机日志和真实焊接质量反馈缺口。

## 7. 数据流

每个任务的默认数据流为：

```text
SimulationTaskSpec
-> run_simlite_reference
-> SimulationEvidenceBundle
-> ManipulationSkillAsset
-> RobotBodyAsset
-> RobotContextSpec
-> SceneContextAsset
-> RobotFeasibilityResult
-> SkillTransferAssessment
-> ExpertReviewRecord
-> A02ToA01ProductValidationHandoff
-> IPDisclosureSupportMatrix
```

同时生成或汇总三类旁路支撑对象：

```text
SkillAssetEvidenceWritebackSummary
EvidenceSourceCatalogEntry[]
A01B06SkillAssetMapping
```

它们不改变主链路，但分别支撑 P0-02/P0-04 证据候选、canonical evidence source 解释，以及 A01/B06 字段如何成为 `ManipulationSkillAsset` evidence。

聚合报告只读取这些对象的 `to_dict()` 输出，不绕过 builder，也不手工拼接核心对象字段。

## 8. 读者解释口径

`demo_summary.md/html` 采用解释型报告，而不是技术日志。必须讲清楚：

1. `ManipulationSkillAsset` 不是一条轨迹，而是包含意图、运动、约束、上下文要求、证据、迁移契约和质量边界的技能资产。
2. 当前 evidence source 是 `simulation_only`，代表仿真样例可复跑，但不是真实机器人日志。
3. `SkillTransferAssessment.status = ready_for_expert_review` 的含义是：对象、上下文和轻量预检已形成专家审查候选。
4. 不能进入 `ready_for_robot_execution` 的原因包括：缺少真实 TCP 标定、缺少工件坐标系测量、缺少机器人型号身份确认、缺少厂商或控制器确认的关节限制、没有完整 IK、没有真实碰撞验证、没有真机日志和真实焊接质量反馈。
5. A02 反哺 A01 的输出是候选轨迹、姿态/参数提示和失败边界摘要，不是控制器可下载程序。
6. P0-02/P0-03/P0-04 当前有对象和报告支撑，但仍缺专家结论、真实工站回采、真实质量反馈和真机执行日志。

## 9. 模块边界

新增模块建议为：

```text
weldcore.skill_asset.demo_report
```

职责：

- 选择默认任务。
- 对每个任务调用现有 builder。
- 写出 per-task JSON artifact。
- 聚合 `demo_summary.json`。
- 渲染 `demo_summary.md` 和 `demo_summary.html`。

不负责：

- 定义新的 skill asset 模型。
- 解析真实工站数据。
- 运行外部仿真器。
- 生成机器人程序。

`asset_report` 保持原职责：生成单个 canonical skill asset 报告。`demo_report` 是更上层的演示与解释聚合入口。

## 10. 测试策略

新增测试应覆盖：

1. `demo_report` 能写出 `demo_summary.md/json/html`。
2. 默认任务数为 2，且每个任务都有完整 artifact。
3. 每个任务的 `transfer_status` 为 `ready_for_expert_review`。
4. 每个任务的 `expert_review_status` 为 `pending_expert_review`。
5. summary 明确包含 `ready_for_expert_review` 和 `not_ready_for_robot_execution`。
6. summary 明确包含 A02->A01 handoff 和 P0-02/P0-03/P0-04 支撑说明。
7. 现有 `asset_report` 测试继续通过，证明新增 demo 不破坏 canonical 报告入口。
8. 测试断言每个任务目录包含 12 份 canonical artifact 原始文件名，并额外包含 `simulation_evidence_bundle.json`；`generated_artifacts` 必须覆盖这些实际文件。

## 11. 文档更新

需要同步更新：

- `README.md`：新增 demo evidence pack 默认入口、artifact 清单和边界。
- `details.md`：记录本阶段完成内容、当前判断和下一阶段建议。
- `weld-experience-engine/README.md`：新增 `demo_report` 命令。
- `docs/architecture/module-boundaries.md`：修正旧口径，将核心对象从 `WeldSkillPackage` 更新为 `ManipulationSkillAsset`，并说明 `WeldSkillPackage` 是历史兼容 / facade。
- `README.html`、`details.html`：从 Markdown 同步刷新阅读副本。

## 12. 成功标准

本阶段完成时应满足：

1. `uv run python -m weldcore.skill_asset.demo_report --outdir artifacts/demo/skill-asset-evidence` 可复跑。
2. 输出中包含 2 个任务的完整证据链 artifact。
3. `demo_summary.md/json/html` 能解释当前系统能力、证据来源、审查边界、A02->A01 handoff 和 IP support。
4. 默认测试通过。
5. README、details、engine README 和架构边界说明已同步更新。
6. PR 合并后，本地工作分支和 worktree 被清理。

## 13. 下一阶段建议

完成 Demo Evidence Pack 后，下一阶段再进入真实或脱敏证据替换，而不是继续改 demo：

1. 收集最小真实 TCP calibration、tool frame calibration、workpiece frame measurement records。
2. 接入 1-2 条 A01 H300 真实或脱敏回采样本，作为 `h300_workcell_run` evidence。
3. 运行 `ExpertReviewRecord` 的人工结论闭环。
4. 用同一份 `RobotFeasibilityResult` 结构接入一个更重 robot adapter 的反证结果。
5. 把 IP support matrix 中的 missing real-world evidence 逐项补齐。
