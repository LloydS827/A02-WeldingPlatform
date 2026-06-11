# Canonical Manipulation Skill Asset 设计

日期：2026-06-11

## 1. 背景

上一阶段项目已经形成以下能力：

```text
WeldSkillUnit
-> SimulationTaskSpec
-> modeled SimulationTaskSpec
-> ManiSkill/SAPIEN batch / accumulation
-> SimulationEvidenceBundle
-> RobotProcessPackageDraft
-> RobotContextSpec / RobotFeasibilityResult
```

这些能力证明系统已经能生成仿真任务、积累仿真证据、形成机器人候选草案，并记录真实机器人执行前缺失的上下文。但是项目路线也暴露出一个更根本的问题：当前系统仍然容易围绕仿真器、样本数、URDF 或机器人上下文打转，而没有把“操作技能资产本体”放在最中心。

本项目第一性原理目标应重新表述为：

```text
把 manipulation 中实际发生的动作，沉淀成可保存、可验证、可迁移的 canonical skill asset。
```

焊接是当前 domain；核心不是焊接质量预测，也不是仿真器集成，而是把焊接操作技能中的 intent、轨迹、姿态、约束、上下文、证据和迁移条件保存成稳定结构。仿真、真机日志、人工示教、专家审查和 URDF 都应围绕这个核心对象服务。

本轮新增的 `docs/real-urdf/` 资产包含：

- `robot.urdf`
- 33 个 STL mesh
- 7 个 link
- 6 个 revolute joint
- 所有 mesh 引用均可解析
- 当前 joint limit 统一为 `[-1.57, 1.57]`

这份资产很有价值，但它不是技能本体。它应作为 `RobotBodyAsset` / transfer context，用于回答“某个技能资产能否迁移到这台协作臂和对应场景中执行”。

## 2. 目标

本阶段目标是建立 canonical manipulation skill asset 的最小数据结构和第一条接入链路：

```text
SimulationEvidenceBundle
-> ManipulationSkillAsset
+ RobotBodyAsset(URDF)
-> SkillTransferAssessment
```

具体目标：

1. 定义 `ManipulationSkillAsset`，作为项目新的核心技能资产本体。
2. 支持从当前 `SimulationEvidenceBundle` 提取最小技能资产。
3. 定义 `RobotBodyAsset`，将真实 URDF 资产作为机器人身体模型上下文纳入系统。
4. 定义 `SkillTransferAssessment`，表达技能资产迁移到目标机器人身体时的初步可迁移判断。
5. 为后续真机日志、人工示教、专家审查和产品化技能库保留清晰接口。
6. 更新 README / details，明确项目主线从“扩仿真样本”修订为“canonical skill asset 本体优先”。

## 3. 不做事项

本阶段明确不做：

- 不把 URDF 写成真实机器人已验证结论。
- 不接真实机器人控制器、焊机、PLC 或现场总线。
- 不生成机器人程序、离线编程文件、G-code、URScript 或厂商控制器文件。
- 不实现完整 IK、轨迹规划、碰撞检测或运动学求解。
- 不把 ManiSkill/SAPIEN、Gazebo/MoveIt 或任何仿真器写成最终路线。
- 不证明真实焊接质量。
- 不生成或替代 WPS/PQR。
- 不做产品 UI 或技能库管理界面。
- 不要求真实 TCP 标定、工件坐标系或场景碰撞几何已完成。

## 4. 核心判断

### 4.1 Skill Asset 是本体

`ManipulationSkillAsset` 应是所有来源的共同落点：

```text
仿真动作 -> ManipulationSkillAsset
真机日志 -> ManipulationSkillAsset
人工示教 -> ManipulationSkillAsset
专家标注 -> ManipulationSkillAsset
```

它不应绑定某个仿真器或某台机器人。它保存的是操作技能本身，包括：

- 操作意图
- TCP 轨迹
- 工具姿态
- 运动约束
- 上下文要求
- 证据来源
- 质量与边界声明
- 迁移所需条件

### 4.2 SimulationEvidenceBundle 是来源证据，不是最终资产

`SimulationEvidenceBundle` 仍然重要，但角色应调整为：

```text
证据来源 / provenance source
```

它能生成 skill asset，但不等同于 skill asset。原因是未来真机日志和人工示教也应该能进入同一个 asset schema。

### 4.3 URDF 是 RobotBodyAsset，不是技能本体

真实协作臂 URDF 应作为：

```text
RobotBodyAsset
```

它表达机器人身体信息：

- link / joint 拓扑
- joint limit
- mesh manifest
- collision mesh 可用性
- robot model / family
- evidence boundary

它不表达焊接技能本身，也不证明真实执行成功。它用于迁移评估：

```text
ManipulationSkillAsset + RobotBodyAsset -> SkillTransferAssessment
SkillTransferAssessment + RobotContextSpec + SceneContextAsset(later) -> deeper feasibility
```

### 4.4 Transfer Assessment 是产品化关键中间物

“技能大师”的产品价值不是简单保存轨迹，而是能回答：

```text
这个技能资产换到另一台机器人/另一个工件/另一个场景时，哪些条件已满足，哪些必须重新验证？
```

因此本阶段应引入 `SkillTransferAssessment`，但只做保守结构判断，不做真实运动规划。第一版只判断“技能资产和机器人身体资产是否足以进入下一层上下文绑定”；TCP 标定、工件坐标系和场景碰撞几何属于后续 `RobotContextSpec` / `SceneContextAsset` 绑定阶段。

## 5. 核心对象设计

建议扩展现有命名空间：

```text
weldcore.skill_asset
```

当前 `weldcore.skill_asset` 已存在，并导出 `WeldSkillPackage` / `package_from_sample`。本阶段不得破坏现有公开入口，而是在该命名空间下新增 focused files，例如：

```text
weldcore/skill_asset/model.py
weldcore/skill_asset/builders.py
weldcore/skill_asset/urdf.py
weldcore/skill_asset/assessment.py
weldcore/skill_asset/asset_report.py
```

该命名空间承接 canonical asset，不放在 `simulation_bakeoff` 或 `robot_process` 下，避免核心资产被仿真或机器人执行后处理绑定。

### 5.1 ManipulationSkillAsset

最小字段：

```text
asset_id
name
domain
skill_type
source_type
source_refs
intent
motion
constraints
context_requirements
evidence
transfer_contract
quality_boundary
version
```

建议字段含义：

| 字段 | 含义 |
| --- | --- |
| `asset_id` | 稳定资产 ID，例如 `skill-asset-task-long-straight-horizontal-tracking` |
| `name` | 人可读名称 |
| `domain` | 当前为 `welding` |
| `skill_type` | 例如 `seam_tracking`、`corner_transition` |
| `source_type` | `simulation`、`real_robot_log`、`human_demonstration`、`expert_annotation` |
| `source_refs` | 原始证据 ID，例如 bundle、task、dataset、run id |
| `intent` | 操作意图，例如沿缝跟踪、转角过渡 |
| `motion` | 轨迹、姿态、速度或时间序列摘要 |
| `constraints` | 姿态约束、路径连续性、速度稳定、接触/非接触边界 |
| `context_requirements` | 机器人、TCP、工件、焊缝、坐标系等要求 |
| `evidence` | 证据状态、来源、指标和边界 |
| `transfer_contract` | 迁移到其他机器人必须满足的条件 |
| `quality_boundary` | 质量边界，例如不证明真实焊接质量、不替代 WPS/PQR |
| `version` | schema 或 asset 版本 |

第一版 `motion` 可以是结构化字典，不新增复杂轨迹类型。它至少应包含：

```text
tcp_trajectory
tool_orientation
trajectory_point_count
orientation_point_count
metrics
```

### 5.2 SkillAssetEvidence

最小字段：

```text
source_type
source_id
adapter_name
status
metrics
artifact_refs
evidence_boundary
review_status
```

第一版从 `SimulationEvidenceBundle` 填充：

- `source_type = "simulation"`
- `source_id = bundle_id`
- `adapter_name = adapter_result.adapter_name`
- `status = adapter_result.status`
- `metrics = adapter_result.metrics`
- `artifact_refs = adapter_result.artifacts`
- `evidence_boundary` 继承仿真证据边界
- `review_status = "not_reviewed"`

### 5.3 SkillTransferContract

最小字段：

```text
required_robot_context
required_scene_context
required_checks
transfer_status
blocking_gaps
evidence_notes
```

默认 required checks：

```text
reachability
collision
joint_limits
tcp_calibration
workpiece_frame
path_continuity
orientation_feasibility
expert_review
```

### 5.4 RobotBodyAsset

最小字段：

```text
asset_id
robot_model
robot_family
asset_source
urdf_path
mesh_root
link_names
joint_names
joint_count
revolute_joint_count
joint_limits
mesh_files
collision_mesh_count
visual_mesh_count
evidence_boundary
validation_status
validation_issues
```

从 `docs/real-urdf/robot.urdf` 解析时：

- `robot_model` 第一版可用 URDF root name：`generated_robot`
- `robot_family` 可推断为 `six_axis_collaborative_welding_arm_candidate`
- `asset_source = "uploaded_urdf"`
- `validation_status = "usable_as_robot_body_context"` 当 XML 可解析、所有 mesh 引用存在、至少 6 个 revolute joints，且每个 revolute joint 都有 limit
- 若缺 mesh、缺 revolute joint limit、无 revolute joints，或 XML 不可解析，应进入 `blocked_by_asset_issue`
- 本轮真实 URDF 应报告 `33` 个 unique mesh files 和 `66` 个 mesh references，因为 visual / collision 各引用一次

### 5.5 RobotBodyAsset / RobotContextSpec / SceneContextAsset 边界

三类上下文不得混用：

| 对象 | 本阶段角色 | 负责字段 |
| --- | --- | --- |
| `RobotBodyAsset` | 本阶段实现 | URDF、mesh、link/joint 拓扑、joint limit、collision/visual mesh 可用性、机器人身体证据边界 |
| `RobotContextSpec` | 现有对象，本阶段可引用但不作为默认输入 | robot identity、base frame、tcp frame、tcp calibration、workpiece frame、joint limit source、现场上下文来源 |
| `SceneContextAsset` | future-only，本阶段不实现 | 工件几何、焊缝坐标系、夹具、障碍物、场景碰撞几何 |

本阶段 `SkillTransferAssessment` 默认只接收 `ManipulationSkillAsset + RobotBodyAsset`。它可以在 `warning_gaps` 中列出 `requires_robot_context_spec`、`requires_tcp_calibration`、`requires_workpiece_frame` 和 `requires_scene_context_asset`，但这些不是第一版 assessment 的 blocking condition。

### 5.6 SkillTransferAssessment

最小字段：

```text
assessment_id
skill_asset_id
robot_body_asset_id
status
passed_checks
blocking_gaps
warning_gaps
evidence_boundary
next_step_recommendation
```

第一版支持状态：

```text
ready_for_contextual_precheck
blocked_by_missing_skill_motion
blocked_by_robot_body_asset_issue
```

默认判断规则：

- skill asset 没有 TCP trajectory：`blocked_by_missing_skill_motion`
- robot body asset validation 失败：`blocked_by_robot_body_asset_issue`
- skill motion 存在且 robot body asset 可用：`ready_for_contextual_precheck`

当状态为 `ready_for_contextual_precheck` 时，第一版必须输出：

```text
passed_checks:
- skill_motion_present
- robot_body_asset_usable

blocking_gaps:
[]

warning_gaps:
- requires_robot_context_spec
- requires_tcp_calibration
- requires_workpiece_frame
- requires_scene_context_asset

next_step_recommendation:
Bind RobotContextSpec and SceneContextAsset before any IK, collision, or real robot validation claim.
```

注意：`ready_for_contextual_precheck` 不等于 `ready_for_robot_execution`。

## 6. 数据流设计

### 6.1 从仿真证据生成技能资产

```text
SimulationEvidenceBundle
-> build_manipulation_skill_asset_from_simulation_bundle
-> ManipulationSkillAsset
```

映射规则：

- `asset_id` 来源于 task id 或 bundle id。
- `domain = "welding"`。
- `source_type = "simulation"`。
- `motion.tcp_trajectory` 来源于 `adapter_result.tcp_trajectory`。
- `motion.tool_orientation` 来源于 `adapter_result.tool_orientation`。
- `intent` 来源于 `SimulationTaskSpec.name`、`unit_id` 和 constraints。
- `context_requirements` 至少包含 `tcp_frame`、`workpiece_frame_required`、`robot_body_required`。
- `quality_boundary` 必须包含：
  - `not_real_welding_quality_validation`
  - `not_WPS_PQR`
  - `not_ready_for_robot_execution`

### 6.2 从 URDF 生成 RobotBodyAsset

```text
docs/real-urdf/robot.urdf
-> build_robot_body_asset_from_urdf
-> RobotBodyAsset
```

解析内容：

- link names
- joint names
- revolute joint count
- joint limits
- mesh references
- missing mesh references
- visual / collision mesh count

### 6.3 初步迁移评估

```text
ManipulationSkillAsset
+ RobotBodyAsset
-> build_skill_transfer_assessment
-> SkillTransferAssessment
```

第一版只做结构性判断，不做运动学求解。它的价值是告诉用户：

```text
技能资产已经存在
机器人身体资产已经存在
可以进入下一层上下文绑定
但在任何 IK、碰撞或真机验证前，还必须补 TCP 标定、工件坐标系和场景碰撞几何
```

这正好回答当前困惑：系统现有能力到底是什么、还差什么才能更产品化。

## 7. CLI / 报告建议

新增一个轻量 report CLI：

```text
python -m weldcore.skill_asset.asset_report
```

默认输出：

```text
skill_asset_report.json
robot_body_asset_report.json
skill_transfer_assessment.json
```

第一版可在测试中使用临时目录，不默认写入仓库 artifacts。

## 8. 文档与产品路线更新

README / details / `weld-experience-engine/README.md` 应更新为：

```text
当前主线：canonical manipulation skill asset 本体优先。
```

新的项目路线：

```text
ManipulationSkillAsset
<- simulation evidence
<- real robot log later
<- human demonstration later

ManipulationSkillAsset
+ RobotBodyAsset(URDF)
-> SkillTransferAssessment
+ RobotContextSpec / SceneContextAsset later
-> expert review candidate
-> real robot validation later
```

必须明确：

- URDF 是现实机器人身体上下文，不是技能本体。
- 当前系统能保存仿真动作为技能资产。
- 当前系统能审计真实 URDF 是否可作为机器人身体资产。
- 当前系统还不能证明真实机器人执行、真实焊接质量或 WPS/PQR。

## 9. 成功标准

本阶段完成后，应满足：

1. `ManipulationSkillAsset` 能序列化为 dict。
2. 至少一个默认仿真 evidence bundle 能转换为 `ManipulationSkillAsset`。
3. `docs/real-urdf/robot.urdf` 能转换为 `RobotBodyAsset`。
4. `RobotBodyAsset` 报告 7 links、6 revolute joints、33 unique mesh files，且 mesh 引用完整。
5. `SkillTransferAssessment` 能表达“skill asset + robot body 已具备，因此 `ready_for_contextual_precheck`；但仍需 RobotContextSpec、TCP 标定、workpiece frame 和 SceneContextAsset 后才能做 IK、碰撞或真机验证声明”。
6. `uv run pytest -q` 通过。
7. README / details / `weld-experience-engine/README.md` / HTML 阅读版同步反映新路线和 `asset_report` CLI。

## 10. 风险与边界

| 风险 | 处理 |
| --- | --- |
| 把 URDF 当成真实执行结论 | 在 `RobotBodyAsset.evidence_boundary` 和 docs 中明确 `not_real_robot_validated` |
| Skill Asset 字段过大 | 第一版只保存 intent、motion、constraints、context、evidence、transfer contract |
| 与现有 `WeldSkillUnit` 重叠 | `WeldSkillUnit` 是技能定义模板，`ManipulationSkillAsset` 是带证据和动作数据的资产实例 |
| 与 `SimulationEvidenceBundle` 重叠 | bundle 是证据来源，skill asset 是 canonical asset |
| 与 `RobotProcessPackageDraft` 重叠 | draft 是机器人执行候选包，skill asset 是更上游的技能资产本体 |
| 真实机器人上下文仍不完整 | 用 `SkillTransferAssessment` 明确缺口，而不是伪造 ready |

## 11. 后续阶段

下一阶段可以基于本阶段成果推进：

1. 将 modeled task specs 运行结果批量转换为 `ManipulationSkillAsset`。
2. 引入 `SceneContextAsset`，表达工件、焊缝、夹具和坐标系。
3. 将 `SkillTransferAssessment` 接到 `RobotFeasibilityResult`。
4. 设计产品工作流：技能库、机器人库、场景库、验证报告。
5. 接入真机日志或人工示教，验证非仿真来源能进入同一个 asset schema。
