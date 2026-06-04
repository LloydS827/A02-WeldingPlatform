# 焊接技能大师平台

本仓库用于沉淀 A02「焊接技能大师平台」的方案文档、论证白皮书、关键预研 POC 与技能迁移 MVP。

当前工作重点已经从 idea / POC 论证、技能迁移 MVP、资料底座 gate 和仿真输出接入 gate，推进到“场景样板验证”阶段：从公司整体目标倒推，先锁定一个具体船舶焊接场景，围绕该场景补齐资料、设计仿真样板、接入仿真输出，并形成可复盘的 `WeldSkillPackage` 和证据报告。

## 当前结论

现阶段已经完成六条可运行证据链：

1. **经验结构化 POC**：验证“大师焊接轨迹 -> 结构化工艺参数 -> 机器人可执行轨迹”的闭环。
2. **技能迁移 MVP**：验证“仿真样本 -> SkillDataset -> WeldSkillPackage -> TransferExperiment -> 评测报告”的最小闭环。
3. **仿真优先知识闸门**：验证“公开资料来源 -> 船舶焊接任务族 -> 候选 SimulationScenarioSpec -> 场景证据报告”的最小闭环。
4. **资料底座 gate**：验证“资料来源 -> 公开数据集 -> 字段覆盖矩阵 -> 任务证据映射 -> `SyntheticSkillDataset v2` 计划输入”的最小闭环。
5. **`SyntheticSkillDataset v2` 输入规范 gate**：验证“资料底座计划输入 -> 船舶焊接任务分类 -> 行业标准字段 -> 字段来源和仿真假设 -> input-spec 证据报告”的最小闭环。
6. **仿真输出接入与经验沉淀平台设计/实现**：验证“SimulationInputSpec -> SimulationOutputBundle -> 导入 gate -> SyntheticSkillDataset v2 -> 证据报告”的最小闭环。

MVP、场景知识闸门、资料底座 gate、`SyntheticSkillDataset v2` 输入规范 gate 与仿真输出接入 gate 的阶段性判断是：软件与数据结构层面的核心机制已经跑通，可以支撑下一阶段围绕具体场景做仿真样板和技能资产样板。当前平台能够接收 `SimulationOutputBundle`，通过导入 gate 进入 `SyntheticSkillDataset v2`，并生成证据报告。但它还不能被表述为完整 ManiSkill/Isaac 集成，也不能被表述为真实焊接质量已经被验证；真实焊接质量仍需要真机、焊材、工艺评定和检测结果二次标定。输入规范 gate 完成的是 `SyntheticSkillDataset v2` 的输入规范审查，不生成批量 `SyntheticSkillDataset v2` 样本，不是真实焊接质量验证，也不是 WPS/PQR。

下一阶段主线已经收束为：优先选择船舶加筋板 / 纵骨角焊场景（内部标识 `stiffened-panel-fillet`），围绕该场景完成资料补强、仿真输入定义、simlite 样板 bundle、仿真输出接入、`WeldSkillPackage` 样板和证据报告。`panel-butt` 作为第二候选，`micro-panel-web-bulkhead` 暂时保留为复杂任务储备。

## 已完成成果

- 整理项目文档结构：`docs/project/`、`docs/specs/`、`docs/plans/`、`docs/reference/`。
- 完成风险驱动白皮书草稿与配套资产，存放在 `report/`。
- 完成经验结构化 POC：
  - 合成轨迹、扰动注入、decompose、recompose、metrics、report。
  - 支持月牙、锯齿、梯形与 8 字形摆动模板扩展。
  - 可生成 `report_out/` 证据文件。
- 完成技能迁移 MVP：
  - 新增 `SkillDataset`、`SkillSample`、`WeldSkillPackage`、`TransferExperiment` 等核心数据结构。
  - 新增轻量焊接任务仿真与 straight-flat 单道任务样本生成。
  - 新增技能包生成、迁移规则、迁移评测与 pass/review/fail 决策。
  - 新增 Rerun 可选回放边界，不把 Rerun SDK 类型泄漏进核心模型。
  - 新增 ManiSkill adapter 边界说明，不把 `mani_skill` 设为基础运行依赖。
  - 新增 MVP 报告生成器，可输出 JSON、CSV、PNG 与 IP notes。
- 完成仿真优先知识闸门：
  - 新增 `PublicWeldKnowledgeBase`，整理公开焊接数据集、工艺资料、船舶焊接机器人案例和项目规划资料的字段覆盖边界。
  - 新增船舶焊接任务族支持闸门，先从船舶制造典型任务出发，而不是从通用直线焊或真机采集出发。
  - 新增 `SimulationScenarioSpec` 候选场景和 `scenario_report`，输出来源、任务族、字段覆盖和候选场景证据。
- 完成资料底座 gate：
  - 新增 `docs/evidence/data-foundation/`，沉淀中文资料卡、公开数据集说明、字段覆盖矩阵和任务证据映射。
  - 新增 manifest-first 资料底座加载与校验，先通过清单证明资料、数据集、字段和任务证据足够支撑下一步计划。
  - 新增 `data_foundation_report`，生成中文证据报告和 `SyntheticSkillDataset v2` 计划输入。
- 完成 `SyntheticSkillDataset v2` 输入规范 gate：
  - 新增 `synthetic_v2_input_report`，生成 input-spec gate 证据。
  - 输出运行时证据目录 `synthetic_v2_input_report_out/`，并刷新 `docs/evidence/data-foundation/reports/synthetic_v2_input_evidence.md`。
  - 明确该 gate 只完成输入规范审查，不生成批量 `SyntheticSkillDataset v2` 样本，不是真实焊接质量验证，也不是 WPS/PQR。
- 完成仿真输出接入与经验沉淀平台设计/实现：
  - 新增 `simulation_ingest_report`，生成 `SimulationOutputBundle` 导入 gate 证据。
  - 输出运行时证据目录 `simulation_ingest_report_out/`，并刷新 `docs/evidence/data-foundation/reports/simulation_ingest_evidence.md`。
  - 明确该 gate 完成的是平台侧仿真输出接入，当前使用 simlite/mock bundle，不要求完整 ManiSkill/Isaac 集成，不代表真实焊接质量验证，也不是 WPS/PQR 或熔池路线。

## 目录结构

```text
.
├── README.md
├── details.md       # 面向非技术读者的项目进展台账
├── AGENTS.md / CLAUDE.md
├── docs/
│   ├── evidence/
│   │   └── data-foundation/ # 资料底座资料卡、manifest 和报告
│   ├── project/      # 课题定义、总体方案、规划说明
│   ├── specs/        # 白皮书与技能迁移 MVP 设计 spec
│   ├── plans/        # POC、白皮书与 MVP 实施计划
│   ├── reference/    # 外部/前序技术方案参考
│   └── superpowers/  # 仿真优先路线的设计 spec、实施计划和 HTML 阅读版
├── report/
│   ├── 船舶焊接工艺大脑平台_风险驱动论证白皮书.md
│   ├── data/         # 白皮书引用的 POC 数据
│   ├── assets/       # 白皮书引用的图
│   └── exports/      # 导出版本
└── weld-experience-engine/
    ├── README.md
    ├── pyproject.toml
    ├── tests/
    └── weldcore/
```

## 关键文档

- [A02 焊接技能大师平台课题](docs/project/03-A02_焊接技能大师平台课题.md)
- [船舶焊接工艺大脑平台整体规划方案 DOCX](docs/project/260522_船舶焊接工艺大脑平台整体规划方案.docx)
- [船舶焊接工艺大脑平台整体规划方案 HTML](docs/project/船舶焊接工艺大脑平台整体规划方案.html)
- [新增课题规划说明](docs/project/附件2_新增课题规划说明.md)
- [焊接经验结构化论证白皮书设计 spec](docs/specs/2026-05-30-焊接经验结构化论证白皮书-design.md)
- [焊接经验结构化 POC 与论证白皮书实施计划](docs/plans/2026-05-30-焊接经验结构化POC与论证白皮书.md)
- [焊接技能迁移 MVP 设计 spec](docs/specs/2026-05-31-焊接技能迁移MVP-design.md)
- [焊接技能迁移 MVP 实施计划](docs/plans/2026-05-31-焊接技能迁移MVP实施计划.md)
- [仿真优先船舶焊接数据底座设计 spec](docs/superpowers/specs/2026-06-01-仿真优先船舶焊接数据底座-design.md)
- [仿真优先船舶焊接数据底座实施计划](docs/superpowers/plans/2026-06-01-仿真优先船舶焊接数据底座实施计划.md)
- [下一阶段场景仿真与接入计划](docs/plans/2026-06-04-下一阶段场景仿真与接入计划.md)
- [Physical AI 公司顶层战略与方向](docs/strategy/2026-06-04-PhysicalAI公司顶层战略与方向.md)
- [Physical AI 公司初步执行规划](docs/strategy/2026-06-04-PhysicalAI公司初步执行规划.md)
- [风险驱动论证白皮书](report/船舶焊接工艺大脑平台_风险驱动论证白皮书.md)
- [项目进展说明与下一步计划](details.md)

## Agent 维护规则

`details.md` 是本项目面向用户、业务人员和非技术读者的进展台账。后续任何 Agent 在推进本项目时，都必须检查这份文件是否需要同步更新。

需要更新 `details.md` 的情况包括：

- 项目阶段判断发生变化。
- 新增或移除重要能力。
- POC、MVP、真机数据、专家知识、Rerun、ManiSkill、报告或平台能力有实质进展。
- 下一步计划、优先级、风险判断发生变化。
- 新增了面向汇报、专利、论文、软著或交付的关键成果。

更新要求：

- 用非技术人员能理解的直白语言写。
- 明确区分“已经完成”“正在验证”“后续需要补充”。
- 不把仿真或软件原型结果夸大为真实焊接质量结论。
- 修改 README、设计文档、计划文档或核心代码后，如果影响项目状态，也要同步检查 `details.md`。

## 运行方式

进入 `weldcore` 引擎子项目：

```bash
cd weld-experience-engine
uv sync --extra dev --extra viz
uv run pytest -q
```

如果本机尚未安装 `uv`，先参考 Astral 官方安装方式安装；临时备用方式仍可使用 `pip install -e ".[dev,viz]"`。

生成经验结构化 POC 证据：

```bash
uv run python -m weldcore.report.generate
```

生成技能迁移 MVP 证据：

```bash
uv run python -m weldcore.report.mvp_report
```

生成仿真优先船舶焊接场景证据：

```bash
uv run python -m weldcore.report.scenario_report
```

生成数据集与资料底座证据：

```bash
uv run python -m weldcore.report.data_foundation_report
```

生成 `SyntheticSkillDataset v2` 输入规范 gate 证据：

```bash
uv run python -m weldcore.report.synthetic_v2_input_report
```

生成仿真输出接入与经验沉淀证据：

```bash
uv run python -m weldcore.report.simulation_ingest_report
```

`mvp_report` 会生成：

- `mvp_report_out/evidence.json`
- `mvp_report_out/metrics.csv`
- `mvp_report_out/transfer_summary.png`
- `mvp_report_out/ip_notes.md`

`scenario_report` 会生成公开资料来源、船舶焊接任务族、候选仿真场景和字段覆盖证据。它是仿真前的知识闸门，不生成真机结论，也不纳入熔池路线。

`scenario_report` 的默认输出目录是 `scenario_report_out/`，核心文件包括：

- `scenario_report_out/sources.json`
- `scenario_report_out/task_families.json`
- `scenario_report_out/scenarios.json`
- `scenario_report_out/field_coverage.csv`
- `scenario_report_out/evidence.md`

`data_foundation_report` 会生成资料来源、公开数据集、字段覆盖矩阵、任务证据映射和 `SyntheticSkillDataset v2` 计划输入。它完成的是资料底座 gate，不下载大文件，也不生成批量仿真数据。

`data_foundation_report` 的运行时输出目录是 `data_foundation_report_out/`，同时会刷新 `docs/evidence/data-foundation/reports/` 下的中文证据报告和 `SyntheticSkillDataset v2` 计划输入。

`synthetic_v2_input_report` 会生成 `SyntheticSkillDataset v2` 输入规范 gate 证据。它的运行时输出目录是 `synthetic_v2_input_report_out/`，同时会刷新 `docs/evidence/data-foundation/reports/synthetic_v2_input_evidence.md`。它完成的是 input-spec gate，不生成批量 `SyntheticSkillDataset v2` 样本，不是真实焊接质量验证，也不是 WPS/PQR。

`simulation_ingest_report` 会生成仿真输出接入 gate 证据。它的运行时输出目录是 `simulation_ingest_report_out/`，同时会刷新 `docs/evidence/data-foundation/reports/simulation_ingest_evidence.md`。它验证平台可以接收 `SimulationOutputBundle`，导入为 `SyntheticSkillDataset v2`，并输出证据报告；当前使用 simlite/mock bundle，不要求安装 ManiSkill 或 Isaac，不代表真实焊接质量验证，也不是 WPS/PQR 或熔池路线。

## 技术边界

- MVP 与下一阶段数据路线优先使用轻量仿真和公开资料知识闸门，不等待真机或高保真熔池物理仿真。
- 真机数据价值最高，但当前不作为主路径，只预留后续标定、验证和审查边界；后续应通过同一套 `SkillDataset` 接入。
- Rerun 定位为多源时间轴记录、回放、标注和调试驾驶舱，不是生产数据库或机器人控制总线。
- ManiSkill / Isaac / SAPIEN 当前作为外部执行选项和机器人任务、demonstration 数据、evaluation benchmark 的范式参考，不是平台核心，也不是基础测试依赖。
- 核心自有资产应放在 `SkillDataset`、`WeldSkillPackage`、迁移规则、评测协议和工艺语义模型上。

## 阶段判断

现阶段工作可以视为“技能迁移 MVP 第一轮完成，并完成仿真优先知识闸门、资料底座 gate、`SyntheticSkillDataset v2` 输入规范 gate 和仿真输出接入 gate 第一轮”：

- 已有可运行代码。
- 已有自动化测试。
- 已有 POC、MVP、场景证据、资料底座证据、`SyntheticSkillDataset v2` 输入规范 gate 和仿真输出接入 gate 报告生成命令。
- 已有白皮书与 IP notes 可引用材料。
- 已明确 Rerun、ManiSkill、Isaac、真机数据和专家知识的边界。
- 已明确公开资料、资料底座、输入规范 gate 和仿真输出接入 gate 只能作为场景约束、参数参考、标签词汇来源、`SyntheticSkillDataset v2` 输入规范和平台侧数据沉淀能力，不能写成真实焊接质量验证、完整 ManiSkill/Isaac 集成、批量 synthetic samples 生成或 WPS/PQR。

下一阶段进入“场景锁定后的仿真样板与接入闭环”：

1. 优先锁定 `stiffened-panel-fillet`，把它作为第一条样板场景，而不是同时铺开多个任务族。
2. 围绕该场景补齐公开资料、字段覆盖、任务证据和假设边界；资料只服务于场景定义和仿真样板，不做无边界调研。
3. 基于已有 input-spec gate 和 simulation ingest gate，生成一组可复现的 simlite 样板 bundle，并导入为 `SyntheticSkillDataset v2`。
4. 将导入结果组织成围绕该场景的 `WeldSkillPackage` 样板，输出机器人执行基线或调试输入。
5. 生成证据报告，明确区分公开资料、仿真假设、软件验证、真实质量验证和 WPS/PQR 边界。
6. ManiSkill/Isaac/SAPIEN 可作为后续 adapter 评估方向，但不替代平台核心 schema、gate、导入和证据报告能力。
7. 本阶段不纳入熔池图像、熔池控制或焊中闭环；真机采集和专家访谈保留为后续标定、验证和审查。
