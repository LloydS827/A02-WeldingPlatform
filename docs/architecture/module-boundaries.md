# 模块边界与 Adapter 原则

## 核心对象

`ManipulationSkillAsset` 是当前 canonical 技能资产本体，承载技能意图、TCP 轨迹、工具姿态、约束、证据来源、质量边界和迁移契约。

`WeldProcedureKnowledgeContract` 是下一阶段 K01 工艺知识合同对象，来源于 `docs/焊接工艺数据库主要参数表.xlsx`，用于定义焊接工艺字段、必填/条件必填/补充分类、来源分类、目标对象路径和证据边界。它约束 `ManipulationSkillAsset`，但不替代 `ManipulationSkillAsset`，也不替代正式 WPS/PQR。

`WeldSkillPackage` 是历史兼容 / facade 对象，用于保留既有技能包生成、迁移评测和旧 evidence 输出入口；它不再是默认主线核心对象。

## 当前代码边界

| 模块 | 当前职责 | 重构后定位 |
| --- | --- | --- |
| `weldcore.model` | 数据模型 | 保留基础模型 |
| `weldcore.skill_asset` | canonical 技能资产、上下文、预检、专家审查和 evidence pack | 默认主线 |
| `weldcore.transfer` | 技能迁移与评测 | 历史兼容 / facade |
| `weldcore.knowledge` | 资料和字段约束 | 工艺知识与证据来源 |
| `weldcore.sim` | simlite/mock 输出 | L0 稳定仿真 |
| `weldcore.ingest` | 仿真 bundle 导入 | Adapter 输入边界 |
| `weldcore.report` | 证据报告 | 证据输出 |

## Adapter 原则

- 仿真器、机器人、焊机、工作站都通过 adapter 接入。
- adapter 必须输出或转换为项目 canonical schema。
- adapter 不能替代 `ManipulationSkillAsset`。
- K01 字段合同必须保留 `not_WPS_PQR` 和人填/专家确认边界，不能把仿真值或系统计算值直接写成工艺合格结论。
- `WeldSkillPackage` 可继续作为历史兼容 / facade，但不能被写成默认主线核心对象。

## NVIDIA-native 边界

K01 焊接工艺知识合同与 OpenUSD / Isaac Sim / Isaac Lab 共同构成下一阶段路线：K01 负责焊接工艺字段约束，NVIDIA 栈负责未来真实仿真训练闭环主底座。它们仍然通过清晰边界接入：

- OpenUSD 是数字孪生交换层，不是 A02 内部 canonical schema 的替代品。
- Isaac Sim 是未来默认目标仿真运行时，不是当前默认测试依赖。
- Isaac Lab 是未来训练闭环目标层，不是当前已经运行的策略训练系统。
- Excel 字段表是 K01 合同源，不是运行时数据库，也不是正式 WPS/PQR。
- Cosmos、Nucleus、Isaac ROS 和 Jetson/边缘部署属于后续增强、协同或部署层，不进入 NV01 默认路径。
- NVIDIA-oriented artifact 必须能追溯到 `WeldProcedureKnowledgeContract`、`ManipulationSkillAsset`、`RobotContextSpec`、`SceneContextAsset`、`RobotFeasibilityResult`、`ExpertReviewRecord` 或其他 A02 canonical evidence。
- 任何 `ready_for_simulation_replay_package_design`、`ready_for_training_design_review` 或类似状态都不能被写成 `ready_for_robot_execution`。
