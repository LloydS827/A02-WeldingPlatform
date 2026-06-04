# 模块边界与 Adapter 原则

## 核心对象

`WeldSkillPackage` 是项目核心对象。

## 当前代码边界

| 模块 | 当前职责 | 重构后定位 |
| --- | --- | --- |
| `weldcore.model` | 数据模型 | 保留基础模型 |
| `weldcore.transfer` | 技能迁移与评测 | 技能资产能力 |
| `weldcore.knowledge` | 资料和字段约束 | 工艺知识与证据来源 |
| `weldcore.sim` | simlite/mock 输出 | L0 稳定仿真 |
| `weldcore.ingest` | 仿真 bundle 导入 | Adapter 输入边界 |
| `weldcore.report` | 证据报告 | 证据输出 |

## Adapter 原则

- 仿真器、机器人、焊机、工作站都通过 adapter 接入。
- adapter 必须输出或转换为项目 canonical schema。
- adapter 不能替代 `WeldSkillPackage`。
