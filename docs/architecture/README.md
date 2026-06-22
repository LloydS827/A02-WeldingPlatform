# 架构总览

本目录描述 A02 作为机器人技能大师能力的焊接技能资产底座时的当前架构。

当前主线不是单一仿真器、机器人程序、报告命令或平台化业务系统，而是围绕 `ManipulationSkillAsset` 沉淀可学习、可迁移、可评测、可审计的焊接操作技能资产。

## 当前入口

- [五层系统架构](five-layer-system.md)
- [模块边界与 adapter 原则](module-boundaries.md)

## 核心判断

```text
仿真证据 / 真实机器人日志 / 人工示教 / 专家标注 / A01 H300 工站回采
-> ManipulationSkillAsset
-> RobotBodyAsset + RobotContextSpec + SceneContextAsset
-> lightweight RobotFeasibilityResult
-> SkillTransferAssessment
-> ExpertReviewRecord
-> A01 产品验证 / IP evidence support
```

`WeldSkillPackage` 仍作为历史兼容层和技能包 facade 保留，用于复用早期评测、迁移和报告能力。当前 canonical object 是 `ManipulationSkillAsset`；后续新增仿真器、robot adapter、A01 回采或 B06 Physical AI Package 字段，都应写成它的 evidence source、上下文对象或反证来源。

## 当前边界

- `ready_for_expert_review` 不是 `ready_for_robot_execution`。
- `RobotFeasibilityResult` 当前不是完整 IK solver、真实碰撞检测或真机验证。
- 仿真样本数、URDF、robot precheck、A01/B06 mapping 和 IP support matrix 都服务于技能资产主线。
- 当前不宣称真实机器人可执行、真实焊接质量验证、正式 WPS/PQR 或最终仿真器选型。
