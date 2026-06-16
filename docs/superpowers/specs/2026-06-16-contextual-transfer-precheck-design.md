# Contextual Transfer Precheck 设计

日期：2026-06-16

## 1. 背景

上一阶段已经把项目主线收束为：

```text
SimulationEvidenceBundle
-> ManipulationSkillAsset

ManipulationSkillAsset + RobotBodyAsset(URDF)
-> SkillTransferAssessment
-> ready_for_contextual_precheck
```

这条链路是正确的，但目前 `ready_for_contextual_precheck` 仍然停留在“技能运动存在、URDF 机器人身体资产可用”的第一层结构判断。系统已经诚实地列出 `requires_robot_context_spec`、`requires_tcp_calibration`、`requires_workpiece_frame`、`requires_scene_context_asset` 等缺口，但这些缺口还没有变成可记录、可复跑、可测试的下一层对象。

同时，项目已经完成 1000 requested samples 运行审查和 modeled `SimulationTaskSpec` 建模闭环。继续单纯扩大样本数量会偏离当前主线；更合理的下一步是把这些任务规格和样本结果重新解释为 `ManipulationSkillAsset` 的 evidence 来源，并让资产进入真实机器人上下文绑定前的轻量 feasibility 预检。

本阶段要推进的是：

```text
ManipulationSkillAsset
+ RobotBodyAsset(URDF)
+ RobotContextSpec
+ SceneContextAsset
-> SkillTransferAssessment
-> lightweight IK / collision / joint-limit feasibility precheck
-> expert review candidate
```

这里的 `IK / collision / joint-limit` 仍是 lightweight precheck。它只表达“结构信息是否足够进入专家审查或更重的机器人 adapter”，不表达真实机器人可执行、真实碰撞验证、正式运动规划或焊接质量结论。

## 2. 头脑风暴选项

### 方案 A：只做文档和状态重命名

优点是风险很低，能快速把下一步说清楚。缺点是项目仍然没有新的可验证对象，`requires_scene_context_asset` 继续只是字符串，`SkillTransferAssessment` 也无法消费真实上下文。

该方案野心过小，不适合作为本阶段主交付。

### 方案 B：建立上下文资产和轻量预检闭环

定义 `SceneContextAsset`，把真实 URDF `RobotBodyAsset` 绑定为 `RobotContextSpec`，让 `SkillTransferAssessment` 可消费 `RobotContextSpec + SceneContextAsset + RobotFeasibilityResult`，并输出更具体的 contextual precheck 状态。同时增加一条 evidence writeback 摘要，把 modeled tasks 和 1000 next-batch 样本定位为 `ManipulationSkillAsset` evidence 来源。

该方案能产出可测试的数据结构、报告和文档更新，又不会声称已经完成真实机器人控制或完整 MoveIt/Gazebo 集成。它是本阶段推荐方案。

### 方案 C：直接接完整 MoveIt/Gazebo 或真实机器人

优点是看起来更接近机器人执行。缺点是当前仍缺 TCP 标定、工件坐标系、场景障碍、焊枪模型和真实控制接口，直接上完整机器人栈会把“资产本体和上下文契约”问题埋进外部依赖里。

该方案野心过大，容易制造虚假执行结论，本阶段不采用。

## 3. 本阶段目标

采用方案 B，目标是建立可复跑、可审查、保守的 contextual transfer precheck 层：

1. 定义 `SceneContextAsset`，表达工件坐标系、焊缝路径、夹具/障碍、安全边界和 evidence boundary。
2. 将真实 URDF `RobotBodyAsset` 绑定为 `RobotContextSpec`，表达机器人型号、base/TCP/tool/workpiece frame、关节限制来源和仍未完成的 TCP 标定边界。
3. 扩展 `SkillTransferAssessment`，让它在已有 `ManipulationSkillAsset + RobotBodyAsset` 基础上可选消费 `RobotContextSpec`、`SceneContextAsset` 和 `RobotFeasibilityResult`。
4. 提供 lightweight contextual feasibility precheck：基于 skill motion、robot context、scene context、workspace hint 和 joint limit 来源做结构级 IK/reachability、collision、joint-limit、path continuity、orientation 检查。
5. 建立 evidence writeback 摘要结构，把 modeled task specs 和 1000 next-batch 样本回填为 `ManipulationSkillAsset` 的 evidence candidates，而不是继续孤立扩样本数。
6. 更新 README、details 和 HTML 阅读版，明确当前阶段已从“ready for contextual precheck”推进到“contextual lightweight precheck”，但仍不触达 `ready_for_robot_execution`。

## 4. 不做事项

本阶段明确不做：

- 不接真实机器人、焊机、PLC、现场总线或控制器。
- 不生成机器人程序、离线编程文件、G-code、URScript 或厂商程序。
- 不引入 MoveIt、Gazebo、ROS、Isaac、RoboDK、RobotStudio 或 Process Simulate 作为默认依赖。
- 不实现完整 IK 求解器、轨迹规划器、连续碰撞检测或动态仿真。
- 不把 lightweight collision 写成真实碰撞验证；第一版只判断障碍/安全边界上下文是否足够，并记录 `assumed` / `missing` / `not_checked` 边界。
- 不把 TCP `nominal`、`mock` 或 `asset_bound` 写成真实 TCP 标定。
- 不扩大默认任务族或继续新增更大 requested samples 批次。
- 不证明真实焊接质量，不替代 WPS/PQR。
- 不把 `ready_for_expert_review` 或 `ready_for_contextual_precheck` 写成 `ready_for_robot_execution`。

## 5. 核心对象设计

### 5.1 SceneContextAsset

新增到 `weldcore.skill_asset.model`。它属于 skill asset 的迁移上下文，不放到 `simulation_bakeoff`，避免场景上下文被绑定成某个仿真器的私有对象。

建议字段：

```text
scene_id
scene_type
workpiece_frame
seam_path
fixture_obstacles
safety_boundary
target_region
source_refs
validation_status
validation_issues
evidence_boundary
version
```

字段含义：

| 字段 | 含义 |
| --- | --- |
| `scene_id` | 场景资产 ID |
| `scene_type` | 例如 `welding_transfer_precheck` |
| `workpiece_frame` | 工件坐标系名称，应与 `RobotContextSpec.workpiece_frame` 对齐 |
| `seam_path` | 从 `SimulationTaskSpec.seam_path` 或 skill motion 派生的路径点 |
| `fixture_obstacles` | 夹具/障碍摘要。第一版允许为空，但空值必须留下边界 |
| `safety_boundary` | 安全边界摘要，例如工作空间 bbox、最小 clearance 等 |
| `target_region` | 任务目标区域摘要 |
| `source_refs` | task、bundle、asset 等来源引用 |
| `validation_status` | `usable_as_scene_context` 或 `blocked_by_scene_context_issue` |
| `validation_issues` | 缺失 workpiece frame、seam path、安全边界等问题 |
| `evidence_boundary` | `scene_context_asset_precheck_only`、`not_real_fixture_validated` 等 |

第一版 `seam_path` 复用 `SimulationPathPoint` 的 dict 序列，避免引入新的几何类型。

### 5.2 RobotContextSpec 与 RobotBodyAsset 绑定

现有 `RobotContextSpec` 已能表达机器人型号、base frame、TCP frame、workpiece frame、tool payload、joint limit 来源和 workspace hint。本阶段不新增第二套 robot context 类型，而是在 `weldcore.robot_process.feasibility` 中提供一个绑定构建器：

```text
build_robot_context_from_body_asset(robot_body_asset, ...)
```

默认用于真实 URDF 的上下文应满足：

- `robot_model` 来自 `RobotBodyAsset.robot_model`
- `robot_family` 来自 `RobotBodyAsset.robot_family`
- `base_frame` 默认取第一个 link，或显式传入
- `tcp_frame` 默认 `torch_tcp_nominal`
- `tcp_calibration_status` 默认 `nominal_from_asset_not_calibrated`
- `workpiece_frame` 默认 `workpiece`
- `joint_limits_source` 指向 `RobotBodyAsset.source_urdf`
- `workspace_hint` 使用保守规则生成，例如 `max_radius_m`、`z_min_m`、`z_max_m`
- `evidence_notes` 必须包含 `uploaded_urdf_asset`、`not_tcp_calibrated`、`not_vendor_validated`、`not_ready_for_robot_execution`

如果 `RobotBodyAsset.validation_status != usable_as_robot_body_context`，构建器仍可返回上下文，但应在 evidence notes 中保留 asset issue；后续 assessment 必须继续 blocked。

### 5.3 SkillTransferAssessment 扩展

现有 `SkillTransferAssessment` 状态过少，只能表达：

```text
ready_for_contextual_precheck
blocked_by_missing_skill_motion
blocked_by_robot_body_asset_issue
```

本阶段扩展但保持保守：

```text
ready_for_contextual_precheck
ready_for_lightweight_feasibility_precheck
ready_for_expert_review
blocked_by_missing_skill_motion
blocked_by_robot_body_asset_issue
blocked_by_missing_robot_context
blocked_by_missing_scene_context
blocked_by_incomplete_feasibility_result
blocked_by_failed_feasibility_check
```

判断规则：

1. skill motion 或 robot body 不通过时，沿用现有 blocked 状态。
2. 如果只调用旧版两输入评估，即只传入 `ManipulationSkillAsset + RobotBodyAsset`，且两者结构可用，则保持兼容状态 `ready_for_contextual_precheck`，并继续在 warning gaps 中列出 robot / scene context 缺口。
3. 如果调用者显式进入 contextual assessment，即传入了 `contextual_precheck_requested=True` 或传入任一 contextual 对象，那么缺 `RobotContextSpec` 时状态为 `blocked_by_missing_robot_context`，缺 `SceneContextAsset` 时状态为 `blocked_by_missing_scene_context`。
4. 有 robot context 和 scene context，但没有 feasibility result 时，状态为 `ready_for_lightweight_feasibility_precheck`。
5. 有 feasibility result 且通过，无 blocking reasons 时，状态为 `ready_for_expert_review`。
6. feasibility result 为 failed，或关键检查项 failed，状态为 `blocked_by_failed_feasibility_check`。
7. feasibility result incomplete 或存在 blocking reasons，状态为 `blocked_by_incomplete_feasibility_result`。

所有状态都必须保留 `not_ready_for_robot_execution`，不得默认生成 `ready_for_robot_execution`。

### 5.4 Lightweight Contextual Feasibility

现有 `build_robot_feasibility_result` 消费 `RobotProcessPackageDraft`，服务 robot process draft。为了让 canonical skill asset 主线不绕回 legacy draft，本阶段新增一个 skill asset 侧轻量预检入口：

```text
build_contextual_feasibility_result(
    skill_asset: ManipulationSkillAsset,
    robot_context: RobotContextSpec | None,
    scene_context: SceneContextAsset | None,
) -> RobotFeasibilityResult
```

第一版规则：

- `robot_context is None`：所有机器人检查为 `missing` / `not_checked`，blocking `missing_robot_context`。
- `scene_context is None`：collision 和 path context 为 `missing`，blocking `missing_scene_context`。
- skill motion 缺 TCP trajectory：reachability `missing`，blocking `missing_tcp_trajectory`。
- skill motion 缺 tool orientation：orientation `missing`，blocking `missing_tool_orientation`。
- `joint_limits_source` 缺失：joint limit `missing`，blocking `missing_joint_limits_source`。
- `workspace_hint.max_radius_m` 存在时，对 TCP 点做半径级 reachability 规则；超出则 reachability `failed`，blocking `tcp_trajectory_outside_workspace_hint`。
- `SceneContextAsset.validation_status` blocked 时，collision/path context 进入 `missing` 或 `not_checked`，blocking 对应 scene issue。
- fixture/obstacle 第一版不做几何碰撞，只在存在 scene context 且 scene validation 可用时把 collision 标为 `assumed`，并加 `collision_geometry_not_validated` warning。
- path continuity 基于 trajectory 点数和 seam path 点数做最小结构判断：至少两个点为 passed，否则 missing。

结果必须带 evidence boundary：

```text
lightweight_feasibility_precheck_only
not_full_ik_solver
not_collision_validated
not_moveit_validated
not_gazebo_validated
not_real_robot_validated
not_ready_for_robot_execution
```

### 5.5 Evidence Writeback 摘要

本阶段不把 1000 个样本全部展开写入默认报告，避免生成巨大 artifact，也不引入新的数据库。新增轻量 `SkillAssetEvidenceWritebackSummary`：

```text
summary_id
skill_asset_id
modeled_task_count
simulation_sample_count
completed_sample_count
failed_sample_count
candidate_evidence_refs
writeback_status
evidence_boundary
next_step_recommendation
```

第一版可从 modeled task specs payload 和 accumulation report payload 的 dict 构建摘要，也可以在默认报告中使用保守的内置 summary，说明：

- 8 个 modeled task specs 是 expert review candidates。
- 1000 next-batch samples 是 simulation evidence candidates。
- 当前只是 evidence writeback summary，不表示真实焊接质量或真实机器人执行。

这样做的边界清晰：既不继续孤立扩样本，也不把所有历史 artifact 强行重构成新资产库。

## 6. 报告与文档

`weldcore.skill_asset.asset_report` 应继续是默认 canonical 报告入口，并扩展输出：

```text
skill_asset_report.json
robot_body_asset_report.json
robot_context_spec.json
scene_context_asset_report.json
skill_transfer_assessment.json
robot_feasibility_result.json
skill_asset_evidence_writeback_summary.json
```

报告中的默认链路应达到：

```text
transfer_assessment.status == ready_for_expert_review
robot_feasibility_result.status == passed
```

但 evidence boundary 必须包含：

```text
not_ready_for_robot_execution
not_full_ik_solver
not_collision_validated
not_real_robot_validated
```

README、details、`weld-experience-engine/README.md` 和对应 HTML 阅读版需要同步更新：

- 当前已完成 contextual lightweight transfer precheck。
- 1000 next-batch 和 modeled task specs 被重新纳入 skill asset evidence writeback 口径。
- 下一阶段不再建议优先扩大样本数，而是进入专家审查对象结构、真实 TCP/工件标定记录和更重 robot adapter 反证。

## 7. 测试策略

新增或更新测试：

1. `SceneContextAsset` 可序列化，并能阻止缺失 workpiece frame / seam path 的场景。
2. 可从默认 simulation task / skill asset 构建默认 scene context。
3. 可从真实 URDF `RobotBodyAsset` 构建 `RobotContextSpec`，并保留 `not_tcp_calibrated` 边界。
4. `build_contextual_feasibility_result` 在完整默认上下文下 passed，但 collision 为 `assumed` 且 evidence boundary 正确。
5. 旧版两输入 `build_skill_transfer_assessment(skill, robot)` 继续返回 `ready_for_contextual_precheck`，保持现有报告兼容。
6. 显式 contextual assessment 缺 robot context 时 blocked by missing robot context。
7. 显式 contextual assessment 缺 scene context 时 blocked by missing scene context。
8. workspace hint 半径过小时 feasibility failed，assessment blocked by failed feasibility check。
9. asset report 写出七个 JSON artifact。
10. evidence writeback summary 记录 modeled task 和 1000 next-batch 为 evidence candidates，而不是真实执行结论。
11. 全量 `uv run pytest -q` 保持通过。

## 8. 成功标准

本阶段完成后，一个新读者应能沿 README 默认路径理解并复跑：

```text
SimulationEvidenceBundle
-> ManipulationSkillAsset
+ RobotBodyAsset
+ RobotContextSpec
+ SceneContextAsset
-> SkillTransferAssessment
+ RobotFeasibilityResult
-> ready_for_expert_review
```

同时不会误解为：

```text
ready_for_robot_execution
real collision validation
real welding quality validation
WPS/PQR
final simulator selection
```

验收条件：

- `uv run pytest -q` 通过。
- `weldcore.skill_asset.asset_report` 可生成扩展后的七个 artifact。
- README/details/HTML 阅读版同步更新。
- spec 和 implementation plan 均通过 review。
- PR 合并后默认分支仍可安装、运行、测试。

## 9. 下一阶段建议

本阶段之后，下一阶段不建议继续优先扩大 requested samples。更合适的顺序是：

1. 定义专家审查对象：审什么 skill asset、scene context、robot context 和 feasibility result。
2. 引入真实 TCP 标定记录和工件坐标系测量记录，替换 `nominal_from_asset_not_calibrated`。
3. 选择一个最小 robot adapter 反证实验，例如 MoveIt/Gazebo 中只验证同一份 `RobotFeasibilityResult` 契约能否被填充。
4. 将 modeled task specs 的小批量 ManiSkill/SAPIEN 验证接回 evidence writeback summary。
5. 在专家审查和真实上下文标定稳定后，再考虑新的任务族或更大批次数据积累。
