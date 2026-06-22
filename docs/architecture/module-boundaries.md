# 模块边界与 Adapter 原则

## 核心对象

`ManipulationSkillAsset` 是当前 canonical 技能资产本体，承载技能意图、TCP 轨迹、工具姿态、约束、证据来源、质量边界和迁移契约。

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
- `WeldSkillPackage` 可继续作为历史兼容 / facade，但不能被写成默认主线核心对象。
