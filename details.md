# 焊接技能大师平台项目进展说明

更新时间：2026-06-03

这份文件用于跟踪 A02「焊接技能大师平台」的实际进展、已有能力、待补能力和下一步计划。它面向项目负责人、业务人员、工艺人员和非技术读者，尽量用直白语言说明项目现在到底走到哪一步。

## 维护方式

这份文件需要随着项目推进及时更新。凡是项目阶段、已有能力、待补能力、下一步计划、风险判断或关键交付物发生变化，都应该同步修改本文件。

更新时请保持面向非技术读者的表达方式，明确区分“已经完成”“正在验证”“后续需要补充”，不要把仿真或软件原型结果夸大为真实焊接质量结论。

## 一句话说明

本项目想解决的问题是：把焊接技能大师的经验，不只停留在口头描述或纸面工艺卡上，而是转成机器可以记录、分析、复现和迁移的数据资产。

更具体地说，我们希望逐步做到：

1. 记录焊接动作、姿态、电流电压等过程数据。
2. 把这些数据整理成结构化的“焊接技能包”。
3. 在焊缝条件发生小范围变化时，仍能复用和调整这个技能包。
4. 最终服务于机器人焊接、工艺知识沉淀、质量追溯、专利论文和软件平台建设。

## 当前阶段判断

项目已经完成了从概念论证到第一轮 MVP，并继续推进到资料底座 gate 和 `SyntheticSkillDataset v2` 输入规范 gate 的第一轮落地。

现在可以说已经完成的是：软件和数据结构层面的最小闭环已经跑通。也就是说，我们已经能用一个简化的焊接任务证明“轨迹可以结构化”“技能可以形成包”“技能包可以迁移到相近条件并被评测”。在场景闸门之后，项目又新增了可执行的资料底座 gate：用 manifest 和报告检查资料来源、公开数据集、字段覆盖、任务证据映射是否足够支撑下一步 `SyntheticSkillDataset v2` 计划输入。最新完成的是 `SyntheticSkillDataset v2` 输入规范 gate：把这些计划输入进一步整理成船舶焊接任务分类、行业标准字段、字段来源和仿真假设边界，并形成证据报告。

根据最新路线调整，下一阶段不再把真机采集作为主路径，而是先建设“仿真优先的船舶焊接数据与工艺知识底座”。目前已经完成公开资料来源、船舶焊接任务族和候选仿真场景的第一道可执行证据闸门，也已经完成资料底座 gate 的 manifest、校验逻辑、中文报告和 `SyntheticSkillDataset v2` 输入规范 gate；它还不是 bulk synthetic sample generation，也不是 `SyntheticSkillDataset v2` 的批量样本生成完成结论，不是真实焊接质量验证，也不是 WPS/PQR。

现在还不能说已经完成的是：真实焊接质量验证。因为目前主要依赖轻量仿真和合成数据，还没有把真机焊接、焊材、工艺评定、焊后检测结果接入完整闭环。

## 已有能力

### 1. 文档和论证材料

已经整理了项目的核心文档结构：

- `docs/project/`：课题定义、总体方案、规划说明。
- `docs/specs/`：关键设计说明，包括白皮书设计和技能迁移 MVP 设计。
- `docs/plans/`：实施计划，包括 POC、白皮书和 MVP 计划。
- `docs/reference/`：外部或前序技术方案参考。
- `docs/data-foundation/`：资料底座的中文资料卡、manifest、字段覆盖矩阵、任务证据映射和报告。
- `report/`：风险驱动论证白皮书、图表、数据和导出版本。

这些材料已经能支撑项目复盘、阶段汇报和下一轮研发讨论。

### 2. 经验结构化 POC

已经完成一个最小验证：把一段“理想大师焊接轨迹”拆解成结构化工艺参数，再重组为机器人可执行轨迹。

这部分证明了：

- 焊枪运动轨迹可以被记录成数据。
- 摆动方式、摆幅、摆频、姿态角、行进速度等信息可以被提取出来。
- 提取后的结构化参数可以重新生成轨迹。
- 系统可以用指标判断复现误差和失效边界。

目前支持的摆动模板包括：

- 月牙形。
- 锯齿形。
- 梯形。
- 8 字形扩展点。

### 3. 技能迁移 MVP

已经完成第一轮技能迁移 MVP。它验证的是比 POC 更核心的问题：技能大师的焊接技能能否被结构化为“技能包”，并迁移到相近但变化后的焊缝条件。

现在已经有这些核心对象：

- `SkillDataset`：统一保存仿真、未来真机、专家知识等来源的数据。
- `SkillSample`：一条具体焊接样本，包括焊缝条件、轨迹、过程参数等。
- `WeldSkillPackage`：结构化后的焊接技能包，是后续知识产权和复用能力的核心载体。
- `TransferExperiment`：记录一次从源条件到目标条件的迁移实验。

目前已经能跑通的流程是：

```text
轻量仿真生成样本
-> 保存为 SkillDataset
-> 提取为 WeldSkillPackage
-> 应用迁移规则
-> 生成目标条件下的轨迹
-> 输出评测指标和报告
```

### 4. 报告生成能力

现在有四类报告命令：

```bash
cd weld-experience-engine
uv sync --extra dev --extra viz
uv run python -m weldcore.report.generate
uv run python -m weldcore.report.mvp_report
uv run python -m weldcore.report.scenario_report
uv run python -m weldcore.report.data_foundation_report
uv run python -m weldcore.report.synthetic_v2_input_report
```

第一条命令生成经验结构化 POC 证据。

第二条命令生成技能迁移 MVP 证据，包括：

- `evidence.json`：完整证据数据。
- `metrics.csv`：评测指标。
- `transfer_summary.png`：迁移轨迹图。
- `ip_notes.md`：专利、论文、软著等成果线索。

第三条命令生成仿真优先船舶焊接场景证据，包括公开资料来源、船舶焊接任务族、候选 `SimulationScenarioSpec` 和字段覆盖说明。默认输出目录是 `scenario_report_out/`，包含 `sources.json`、`task_families.json`、`scenarios.json`、`field_coverage.csv` 和 `evidence.md`。它是 `SyntheticSkillDataset v2` 之前的场景知识闸门，不生成真机结论，也不纳入熔池路线。

第四条命令生成数据集与资料底座证据，包括资料来源、公开数据集、字段覆盖矩阵、任务证据映射和 `SyntheticSkillDataset v2` 计划输入。默认运行时输出目录是 `data_foundation_report_out/`，同时会刷新 `docs/data-foundation/reports/` 下的中文证据报告和 `synthetic_skilldataset_v2_plan_input.md`。它完成的是资料底座 gate，不下载大文件，也不生成批量仿真数据。

第五条命令生成 `SyntheticSkillDataset v2` 输入规范 gate 证据。默认运行时输出目录是 `synthetic_v2_input_report_out/`，同时会刷新 `docs/data-foundation/reports/synthetic_v2_input_evidence.md`。它完成的是输入规范 gate，不是 bulk synthetic sample generation，不生成批量 `SyntheticSkillDataset v2` 样本，不是真实焊接质量验证，也不是 WPS/PQR。

### 5. 可选可视化和生态边界

项目已经明确 Rerun 和 ManiSkill 的定位：

- Rerun 用作多源数据记录、回放、标注和调试工具。
- ManiSkill 用作机器人任务、示教数据和评测基准的参考范式。

重要的是：这两个工具目前都不是项目运行的强制依赖。没有安装它们，基础测试和报告生成仍然可以运行。

## 尚未完成的能力

### 1. 真机数据闭环

目前还没有完成真实机器人、真实焊机、传感器和焊后检测数据的完整采集闭环。

后续需要明确：

- 采集哪些数据。
- 由谁采集。
- 采集频率和格式。
- 数据如何进入 `SkillDataset`。
- 如何把真机结果和仿真结果对齐。

### 2. 专家知识系统化整理

目前专家经验还没有形成稳定的访谈模板和知识录入格式。

后续需要把技能大师的经验整理成可以进入系统的数据，例如：

- 为什么这样摆动。
- 什么情况下调电流。
- 什么情况下改角度。
- 哪些焊缝条件可以迁移，哪些不可以。
- 什么结果需要人工复核。

### 3. 多焊缝、多姿态、多层多道

当前 MVP 主要聚焦直线平焊、单道、简单条件变化。

后续需要扩展到：

- 角焊缝。
- 对接焊缝。
- 立焊、横焊、仰焊等姿态。
- 多层多道。
- 更复杂坡口。

### 4. 真实焊接质量评价

当前评测主要是轨迹和参数层面的评测，还没有纳入完整焊接质量结果。

后续需要接入：

- 焊缝成形。
- 熔深。
- 缺陷检测。
- 无损检测结果。
- 工艺评定结论。
- 工艺人员人工确认。

### 5. 工程化软件平台

目前成果主要是代码原型、数据结构、报告和验证流程，还不是完整业务软件平台。

后续平台可能需要补充：

- 项目和任务管理界面。
- 数据上传和浏览。
- 技能包管理。
- 实验对比和报告导出。
- 权限和版本管理。
- 与机器人、焊机、传感器、MES/PLM/QMS 的接口。

## 下一步计划

### 第一优先级：基于已完成输入规范 gate 的小批量设计

现在已经完成面向 `SyntheticSkillDataset v2` 的输入规范 gate。下一步是在这个 gate 的基础上，选择少量 ready 任务进入样本设计和小批量生成方案。这里仍然只是进入生成计划和小批量设计，不代表已经完成批量数据生产。

### 第二优先级：继续收敛船舶焊接任务族

继续围绕加筋板/纵骨角焊、平面板拼接、微型面板/腹板/隔板多短焊缝、双层底/双壳内部角焊等任务族收敛字段和假设。只有当任务族有船舶制造上下文、公开来源支撑和字段覆盖说明后，才进入候选仿真场景或 `SyntheticSkillDataset v2` 计划。

### 第三优先级：候选仿真场景规格

生成 2-3 个候选 `SimulationScenarioSpec`，明确哪些字段来自公开资料约束，哪些是仿真假设，哪些后续需要真机标定。本阶段不把这些候选场景说成真实焊接质量验证。

### 第四优先级：后续仿真数据生成计划

在资料底座 gate 通过后，再进入 `SyntheticSkillDataset v2` 的生成计划和小批量样本验证。真机采集和专家访谈作为后续校准、验证和审查，不作为当前主路径。

## 风险提醒

- 不要把仿真结果直接说成真实焊接质量已经验证。
- 不要把公开资料约束、仿真样本或候选场景写成真实焊接质量已经验证。
- 不要把资料底座 gate 或 `SyntheticSkillDataset v2` 输入规范 gate 写成 `SyntheticSkillDataset v2` 已经批量生成。
- 不要把输入规范 gate 写成 bulk synthetic sample generation。
- 不要把资料底座、公开数据集或场景报告写成真实焊接质量验证。
- 不要把输入规范、资料底座或仿真计划写成 WPS/PQR。
- 当前阶段不包含熔池图像、熔池控制或焊中闭环路线。
- 不要为了等真机条件完全成熟而停止软件和数据结构建设。
- 不要让 Rerun、ManiSkill 或某个仿真平台替代自有核心模型。
- 不要一开始就做完整平台页面，当前更重要的是数据闭环和证据闭环。
- 不要只整理专家文字经验，必须尽量转成字段、规则和可评测数据。

## 当前可交付物清单

- 根目录 `README.md`：项目总览。
- 根目录 `details.md`：项目进展跟踪和下一步计划。
- `docs/specs/2026-05-31-焊接技能迁移MVP-design.md`：技能迁移 MVP 设计。
- `docs/plans/2026-05-31-焊接技能迁移MVP实施计划.md`：技能迁移 MVP 实施计划。
- `docs/superpowers/specs/2026-06-01-仿真优先船舶焊接数据底座-design.md`：仿真优先路线设计。
- `docs/superpowers/plans/2026-06-01-仿真优先船舶焊接数据底座实施计划.md`：仿真优先知识闸门实施计划。
- `docs/superpowers/specs/2026-06-02-synthetic-skilldataset-v2-input-spec-design.md`：`SyntheticSkillDataset v2` 输入规范与船舶焊接任务分类框架设计。
- `docs/data-foundation/`：资料底座中文资料卡、manifest、字段覆盖矩阵、任务证据映射和报告。
- `weld-experience-engine/data_foundation_report_out/`：资料底座报告命令生成的运行时输出目录。
- `docs/data-foundation/reports/synthetic_skilldataset_v2_plan_input.md`：面向 `SyntheticSkillDataset v2` 的计划输入文档。
- `weld-experience-engine/synthetic_v2_input_report_out/`：`SyntheticSkillDataset v2` 输入规范 gate 的运行时输出目录。
- `docs/data-foundation/reports/synthetic_v2_input_evidence.md`：`SyntheticSkillDataset v2` 输入规范 gate 证据报告。
- `report/船舶焊接工艺大脑平台_风险驱动论证白皮书.md`：风险驱动白皮书。
- `weld-experience-engine/`：可运行 POC、MVP、仿真优先知识闸门与资料底座 gate 代码。

## 最近一次验证方式

进入 `weld-experience-engine` 后运行：

```bash
uv sync --extra dev --extra viz
uv run pytest -q
uv run python -m weldcore.report.generate
uv run python -m weldcore.report.mvp_report
uv run python -m weldcore.report.scenario_report
uv run python -m weldcore.report.data_foundation_report
uv run python -m weldcore.report.synthetic_v2_input_report
```

如果上述命令都通过，说明当前软件原型的基础验证仍然有效。若本机尚未安装 `uv`，可以先安装 `uv`；临时备用方式是使用当前 Python 环境直接运行 `pytest` 和 `python -m ...`。
