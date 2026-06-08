# 焊接技能大师平台项目进展记录

更新时间：2026-06-08

这份文件用于记录 A02「焊接技能大师平台」每一阶段完成了什么、下一步准备做什么、哪些判断发生了变化。它不是项目入口说明；项目入口请看 [README.md](README.md)。

## 文件定位

- `README.md`：项目入口，面向任何新读者说明项目定位、核心链路、当前能力、如何运行和边界。
- `details.md`：阶段更新记录，面向项目讨论记录近期更新、当前判断、下一步计划和风险提醒。

本文件应同步维护 [HTML 阅读版](details.html)。更新根目录 `README.md`、本文件或类似面向读者的阶段/路线说明时，也要同步刷新对应 `.html` 阅读副本。

## 当前一句话状态

项目已经完成从 `WeldSkillUnit`、轻量仿真证据、经验数据到机器人候选草案前置接口的结构链路，并完成统一仿真 adapter 第一轮 facade / registry。下一轮应在该统一入口下推进 ManiSkill/SAPIEN 小批量默认仿真入口。

## 当前主线判断

现在不适合直接扩大仿真规模，也不适合跳到真实机器人控制或完整 MoveIt/Gazebo 集成。

更合理的主线是：

```text
WeldSkillUnit
-> SimulationTaskSpec
-> candidate simulator adapter
-> SimulatorAdapterResult
-> SimulationEvidenceBundle
-> SkillDataset / experience dataset
-> RobotProcessPackageDraft
```

这一段必须先稳定下来。只有当仿真任务契约、输出证据、失败边界和数据转换都可复跑、可比较、可审查之后，项目才适合进入持续数据积累。

这里的“反证工作”很重要：候选仿真软件不是因为名字先进就自动成为主线，而要通过同一组任务、同一套输出契约和同一份证据报告证明它能接入项目数据结构；不能接入的地方也要明确记录失败原因。

## 近期更新

### 2026-06-08

- 完成统一仿真 adapter 第一轮 facade / registry：simlite、ManiSkill/SAPIEN、Gazebo/MoveIt 已进入同一 route 元数据和执行入口。
- `simulation_bakeoff` 已改为消费统一 route registry，scorecard 和 evidence generation 使用同一轮 registry 快照。
- ManiSkill/SAPIEN 仍是阶段性默认入口候选，不是最终仿真器定型。
- 本轮不做小批量样本生成和入口锁定报告；下一轮将围绕 ManiSkill/SAPIEN 小批量默认入口推进。

### 2026-06-07

- 完成机器人上下文与可执行性预检接口，并通过 PR #9 合并。
- 新增 `RobotContextSpec`、`RobotFeasibilityProbe`、`RobotFeasibilityResult`。
- 新增轻量机器人上下文预检函数，用于表达缺少机器人型号、TCP、坐标系、可达性、碰撞和关节限制等上下文时的阻塞原因。
- `RobotProcessPackageDraft` 可以在上下文和预检结果足够时推进到 `ready_for_expert_review`。
- `ready_for_robot_execution` 仍然保留，不作为当前可触达状态。
- 修复 Rerun 新版时间 API 兼容问题。
- 合并后主分支验证通过，最近一次完整测试为 `252 passed`。

### 2026-06-06

- 完成从 `SimulationEvidenceBundle` 到 `RobotProcessPackageDraft` 的最小决策接口，并通过 PR #8 合并。
- 明确机器人候选草案只回答“这条仿真经验能否形成未来可审查候选包”，不输出真实机器人执行结论。
- 明确字段来源、缺失字段、专家审查项、真机验证项和 evidence boundary。
- 将工程师整理的焊接工艺参数 Excel 表格纳入仓库，作为参考资料，不作为当前仿真主流程的主数据源。

### 2026-06-05

- 完成 ManiSkill/SAPIEN 本机轻量仿真闭环。
- 建立 `SimulationTaskSpec` 到 ManiSkill/SAPIEN task config 的转换。
- 通过 raw artifact、adapter result 和 `SimulationEvidenceBundle` 验证外部仿真输出可以进入项目数据结构。
- 保留 Gazebo/MoveIt 候选路线的失败边界记录，避免把环境不可用混同为数据结构失败。

### 2026-06-04

- 完成项目级重构，把默认入口从 POC / MVP / gate / 报告集合收束为 Physical AI 焊接技能资产底座。
- 建立 `WeldSkillUnit` 最小框架。
- 建立仿真路线准备、仿真 bake-off 和 Rerun 证据边界说明。
- 将前期 POC、MVP、gate、白皮书和旧计划归档为历史证据。

## 已完成能力

- 可运行的 `weldcore` 引擎。
- `SkillDataset`、`SkillSample`、`WeldSkillPackage` 和迁移评测基础结构。
- `WeldSkillUnit` 最小技能单元表达。
- `SimulationTaskSpec`、`SimulatorAdapterResult`、`SimulationEvidenceBundle` 仿真证据结构。
- simlite L0 稳定仿真和测试基线。
- ManiSkill/SAPIEN 轻量 adapter 试跑路径。
- Gazebo/MoveIt 候选路线失败边界记录。
- 从仿真证据到机器人候选草案的转换。
- 机器人上下文和轻量可执行性预检接口。
- 统一仿真 adapter facade / registry。
- 报告命令和历史证据归档。

这些能力仍属于软件结构、仿真接入和证据管理能力，不代表真实焊接质量验证。

## 尚未完成

- 最终仿真软件选型尚未完成。
- 持续积累仿真数据的默认入口尚未确定。
- 候选仿真软件的稳定性、可复跑性、输出字段覆盖率和失败边界仍需反证。
- 经验数据与技能资产之间的字段追踪还需要进一步收束。
- 专家审查记录结构尚未作为主线对象实现。
- 真实焊机、机器人、焊材、焊后检测和质量结果尚未接成闭环。
- 当前资料、输入规范、仿真假设和工程师参考表格不能替代正式 WPS/PQR。

## 下一步建议

推荐下一阶段任务是：**ManiSkill/SAPIEN 小批量默认仿真入口**。

目标不是扩大成完整仿真平台，而是在统一 adapter registry 之上，用少量核心 `WeldSkillUnit` 把数据链路推进到可以开始小批量积累：

1. 固定一组最小但代表性的仿真任务。
2. 以 ManiSkill/SAPIEN 作为阶段性默认 route，生成每个任务约 10 条样本。
3. 保持 simlite 作为 L0 对照，Gazebo/MoveIt 作为失败边界和机器人规划候选。
4. 统一生成 raw artifact、`SimulatorAdapterResult`、`SimulationEvidenceBundle` 和 experience dataset。
5. 明确哪些字段可以进入 `SkillDataset` / experience dataset。
6. 明确哪些字段仍是 mock、假设、失败边界或人工补充。
7. 为第三轮入口锁定报告准备字段覆盖和失败边界证据。

这一步完成后，才适合进入“真正开始积累数据”的阶段。

## 暂缓事项

- 暂缓扩大仿真任务数量，避免在接口未收束前积累分散数据。
- 暂缓完整 Gazebo/MoveIt 或 ROS 侧集成，除非它作为候选 adapter 的最小反证实验出现。
- 暂缓专家审核系统化录入，因为当前还需要先稳定“审核什么对象”。
- 暂缓真实机器人执行结论，当前只做候选草案和审查前置条件。

## 当前可交付物清单

- `README.md`：项目默认入口。
- `details.md`：阶段更新记录和下一步计划。
- `docs/strategy/`：公司级 Physical AI 判断与当前项目承接关系。
- `docs/architecture/`：五层架构、模块边界和 adapter 原则。
- `docs/skill-assets/`：`WeldSkillPackage` 与 `WeldSkillUnit`。
- `docs/simulation/`：仿真路线、simlite 边界、外部 adapter 候选和 ManiSkill/SAPIEN 开发环境说明。
- `docs/evidence/`：资料来源、字段覆盖、证据报告和质量边界。
- `docs/archive/`：POC、MVP、gate、白皮书和旧计划归档。
- `docs/superpowers/specs/`：阶段设计文档。
- `docs/superpowers/plans/`：阶段实施计划。
- `docs/焊接工艺数据库主要参数表.xlsx`：工程师参数参考表格。
- `weld-experience-engine/`：可运行的焊接技能资产引擎、测试和报告命令。

## 最近一次验证方式

进入 `weld-experience-engine` 后运行：

```bash
uv sync --extra dev --extra viz
uv run pytest -q
```

本分支最近一次完整验证结果为 `261 passed`。

报告命令可按需运行，用来生成当前证据或历史支撑材料；它们不是默认研发主线本身。

## 风险提醒

- 不要把当前仿真结果写成真实焊接质量验证。
- 不要把候选仿真软件写成已经完成选型。
- 不要把 adapter 失败边界写成项目失败；它是当前反证工作的一部分。
- 不要把 simlite 写成最终仿真器。
- 不要把 Rerun 写成仿真器、机器人控制总线或生产数据库。
- 不要把 `RobotProcessPackageDraft` 写成正式机器人工艺包。
- 不要把 `RobotFeasibilityResult` 写成真实机器人执行验证。
- 不要把工程师参数参考表格写成当前主流程数据源或正式 WPS/PQR。
- 不要删除历史成果；历史材料应继续保留在归档目录中。
