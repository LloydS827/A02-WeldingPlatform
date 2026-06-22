# WeldSkillPackage

## 定位

`WeldSkillPackage` 是 A02 早期技能包 facade 和历史兼容层，用于承接既有 `SkillDataset`、迁移评测、MVP 报告和旧 evidence 输出。当前 canonical 技能资产对象已经收束为 `ManipulationSkillAsset`。

因此，后续新增字段和报告应优先围绕 `ManipulationSkillAsset`、`SkillAssetEvidence`、`RobotBodyAsset`、`RobotContextSpec`、`SceneContextAsset`、`SkillTransferAssessment`、`RobotFeasibilityResult` 和 `ExpertReviewRecord` 建模。`WeldSkillPackage` 可以作为对外技能包视图或兼容 facade，但不再承担项目主线本体角色。

## 与 `ManipulationSkillAsset` 的关系

`ManipulationSkillAsset` 描述：

- skill intent
- TCP trajectory
- tool orientation
- process constraints
- evidence source
- quality boundary
- transfer contract
- robot and scene context requirements

`WeldSkillPackage` 可以从这些信息中派生技能包视图，但不应绕过 `ManipulationSkillAsset` 直接成为新 evidence、A01 回采、B06 Physical AI Package 或专家审查的承载对象。

## 与 SkillDataset 的关系

`SkillDataset` 继续提供工艺知识、动作经验和过程数据的结构化输入。新的默认路径是把这些输入沉淀为 `ManipulationSkillAsset` evidence；`WeldSkillPackage` 只保留对既有迁移评测和报告的兼容作用。

## 与机器人执行的关系

机器人训练、类机器人仿真、A01 H300 工站回采和 B06 Physical AI Package 应读取或生成可回写到 `ManipulationSkillAsset` 的信息。`WeldSkillPackage` 中出现的执行建议只能是候选说明，不能写成真实机器人可执行、生产派发包或控制器程序。

`ready_for_expert_review` 只表示专家审查候选；当前不宣称 `ready_for_robot_execution`。

## 与证据边界的关系

任何从 `WeldSkillPackage` 或历史报告继承的结论，都必须携带 evidence status 和 failure boundary。证据用于约束技能资产，不等于真实焊接质量验证，不替代 WPS/PQR，不表示最终仿真器选型。

## 当前代码对应

- 当前 canonical 技能资产主线在 `weldcore.skill_asset`。
- `WeldSkillPackage` 和 `package_from_sample` 保留在 `weldcore.skill_asset` 的兼容导出中。
- 早期迁移评测能力主要对应 `weldcore.transfer`。
- 默认技能资产报告入口是 `weldcore.skill_asset.asset_report`。
