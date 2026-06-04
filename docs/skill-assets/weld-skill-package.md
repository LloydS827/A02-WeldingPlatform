# WeldSkillPackage

## 定位

`WeldSkillPackage` 是 A02 焊接技能大师平台的核心对象，用于承载可学习、可迁移、可执行、可审计的焊接技能资产。

## 最小字段

- task
- source
- trajectory
- posture
- process parameters
- applicability
- transfer rules
- failure boundary
- robot execution suggestion
- evidence status

## 与 SkillDataset 的关系

`SkillDataset` 提供工艺知识、动作经验和过程数据的结构化输入，`WeldSkillPackage` 在此基础上表达技能资产的适用范围、迁移规则和执行建议。

## 与机器人执行的关系

机器人训练、类机器人仿真和执行基线应读取或生成可回写到 `WeldSkillPackage` 的信息，而不是绕过技能资产直接成为项目主线。

## 与证据边界的关系

`WeldSkillPackage` 必须携带 evidence status 和 failure boundary。证据用于约束技能资产，不等于真实焊接质量验证，不替代 WPS/PQR。

## 当前代码对应

当前基础模型保留在 `weldcore.model`，技能迁移与评测能力主要对应 `weldcore.transfer`。后续重构会围绕技能资产建立更清晰的 import 边界。
