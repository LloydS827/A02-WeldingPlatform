# 五层系统架构

## 1. 工艺知识层

- 职责：沉淀焊接术语、工艺约束、任务分类和资料来源。
- 输入：标准、工艺手册、项目资料、现场经验和公开数据。
- 输出：字段约束、任务证据、source cards 和知识边界说明。
- 当前项目对应物：`weldcore.knowledge`、`docs/evidence/data-foundation/`、资料 manifest。
- 不做事项：不把资料整理等同于真实焊接质量验证，不替代 WPS/PQR。

## 2. 技能数据层

- 职责：把工艺知识、动作经验和过程数据组织为可训练、可复用的数据输入。
- 输入：轨迹、姿态、工艺参数、任务标签、仿真 bundle 和证据字段。
- 输出：`SkillDataset`、字段覆盖矩阵、任务样本和导入后的 canonical schema。
- 当前项目对应物：`weldcore.ingest`、`weldcore.model`、synthetic v2 input 相关报告。
- 不做事项：不承诺数据样本自动代表真实生产质量，不绕过证据边界。

## 3. 技能资产层

- 职责：围绕 `WeldSkillPackage` 表达焊接技能的适用范围、迁移规则、失败边界和执行建议。
- 输入：`SkillDataset`、工艺约束、轨迹经验、评测结果和证据状态。
- 输出：可学习、可迁移、可执行、可审计的焊接技能资产。
- 当前项目对应物：`WeldSkillPackage`、`weldcore.transfer`、技能迁移 MVP 能力。
- 不做事项：不把单次 POC 或报告输出当作完整技能资产。

## 4. 机器人执行层

- 职责：把技能资产转化为机器人训练、类机器人仿真、执行基线和可达性评估。
- 输入：`WeldSkillPackage`、机器人约束、工位信息、轨迹和姿态要求。
- 输出：执行建议、仿真评估、训练输入和 adapter 输出。
- 当前项目对应物：`weldcore.sim`、simulation ingest gate、simlite/mock bundle。
- 不做事项：不在当前阶段绑定唯一机器人生态，不把 L0 仿真当作真实机器人验证。

## 5. 证据与边界层

- 职责：说明资料来源、字段覆盖、验证状态、质量边界和不可替代事项。
- 输入：source cards、manifest、评测结果、报告命令输出和人工判断。
- 输出：证据报告、边界说明、归档索引和当前路线判断。
- 当前项目对应物：`weldcore.report`、`docs/evidence/data-foundation/reports/`、历史 POC/MVP/gate 材料。
- 不做事项：不声称仿真或资料证据等于真实焊接质量验证，不替代 WPS/PQR。

## 不做事项

- 不选择或实现新的唯一仿真器。
- 已归档旧材料但不删除历史成果；后续新增归档必须同步维护 `docs/archive/README.md`。
- 不生成新的大规模数据集。
- 不声称当前系统已完成真实焊接质量验证。
- 不把报告命令替代为项目核心对象。
