# 焊接技能大师平台

本仓库用于沉淀 A02「焊接技能大师平台」的方案文档、论证白皮书、关键预研 POC 与技能迁移 MVP。

当前工作重点已经从 idea / POC 论证推进到 MVP 验证和仿真优先路线：先用轻量仿真和结构化数据模型证明“焊接技能能否被打包并迁移到相近焊缝条件”，再用公开资料和船舶制造任务族建立仿真前的知识闸门，后续再逐步接入真机标定和审查。

## 当前结论

现阶段已经完成三条可运行证据链：

1. **经验结构化 POC**：验证“大师焊接轨迹 -> 结构化工艺参数 -> 机器人可执行轨迹”的闭环。
2. **技能迁移 MVP**：验证“仿真样本 -> SkillDataset -> WeldSkillPackage -> TransferExperiment -> 评测报告”的最小闭环。
3. **仿真优先知识闸门**：验证“公开资料来源 -> 船舶焊接任务族 -> 候选 SimulationScenarioSpec -> 场景证据报告”的最小闭环。

MVP 与知识闸门的阶段性判断是：软件与数据结构层面的核心机制已经跑通，可以作为下一阶段仿真数据生成、真机标定、专家知识整理、专利/论文材料沉淀的基础。但它还不能被表述为真实焊接质量已经被验证；真实焊接质量仍需要真机、焊材、工艺评定和检测结果二次标定。

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

## 目录结构

```text
.
├── README.md
├── details.md       # 面向非技术读者的项目进展台账
├── AGENTS.md / CLAUDE.md
├── docs/
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

## 技术边界

- MVP 与下一阶段数据路线优先使用轻量仿真和公开资料知识闸门，不等待真机或高保真熔池物理仿真。
- 真机数据价值最高，但当前不作为主路径，只预留后续标定、验证和审查边界；后续应通过同一套 `SkillDataset` 接入。
- Rerun 定位为多源时间轴记录、回放、标注和调试驾驶舱，不是生产数据库或机器人控制总线。
- ManiSkill / SAPIEN 当前作为机器人任务、demonstration 数据和 evaluation benchmark 的范式参考，不是基础测试依赖。
- 核心自有资产应放在 `SkillDataset`、`WeldSkillPackage`、迁移规则、评测协议和工艺语义模型上。

## 阶段判断

现阶段工作可以视为“技能迁移 MVP 第一轮完成，并完成仿真优先知识闸门第一轮”：

- 已有可运行代码。
- 已有自动化测试。
- 已有 POC、MVP 和场景证据报告生成命令。
- 已有白皮书与 IP notes 可引用材料。
- 已明确 Rerun、ManiSkill、真机数据和专家知识的边界。
- 已明确公开资料只能作为场景约束、参数参考或标签词汇来源，不能写成真实焊接质量验证。

下一阶段建议进入“仿真优先的船舶焊接数据与工艺知识底座”：

1. 先建立公开焊接数据集与工艺资料底座，形成 `PublicWeldKnowledgeBase`。
2. 先调研船舶制造焊接任务族，再确认 2-3 个候选 `SimulationScenarioSpec`。
3. 用公开资料约束仿真场景字段和参数范围；本轮只完成知识底座与任务族闸门，不直接宣称 `SyntheticSkillDataset v2` 已完成。
4. 真机采集和专家访谈保留为后续标定、验证和审查，不作为当前主路径。
5. 本阶段不纳入熔池图像、熔池控制或焊中闭环。
