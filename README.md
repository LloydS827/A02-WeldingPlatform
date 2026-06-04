# Physical AI 焊接技能资产底座

## 一句话定义

本仓库支撑 A02「焊接技能大师平台」在 Physical AI 方向下的研发，目标是把焊接经验、工艺知识、动作数据、仿真结果和证据边界沉淀为可学习、可迁移、可执行、可审计的工业技能资产。

## 阅读版

- [README HTML 阅读版](README.html)
- [项目进展说明 HTML 阅读版](details.html)

## 当前阶段

当前工作是第一阶段项目级重构：把默认入口从 POC / MVP / gate / 报告集合，收束为以 `WeldSkillPackage` 为核心对象的 Physical AI 焊接技能资产底座。

这一阶段重点不是新增仿真器、锁定单一场景或扩展业务页面，而是让仓库默认结构、文档入口、运行验证和证据边界与公司级 Physical AI for Welding 方向一致。

第二阶段才进入焊缝技能单元与类机器人仿真路线。`stiffened-panel-fillet` 现在保留为历史资料 gate 和行业实例，不再作为仓库默认研发主线。

## 核心对象：WeldSkillPackage

`WeldSkillPackage` 是本项目的核心对象，用于承载一个焊接技能资产的来源、任务语义、轨迹、姿态、工艺参数、适用范围、迁移规则、失败边界、机器人执行建议和证据状态。

当前核心链路是：

```text
工艺知识 / 动作经验 / 过程数据 / 仿真输出
-> SkillDataset
-> WeldSkillPackage
-> evaluation / evidence
```

外部仿真器、机器人生态、报告命令和可视化工具都应围绕这条链路提供输入、适配、评测或证据，而不是替代 `WeldSkillPackage` 成为项目核心。

## 当前主线

1. 对齐战略：以 [战略文档](docs/strategy/README.md) 中的 Physical AI 公司顶层判断为依据，明确本仓库服务工业技能资产沉淀。
2. 对齐架构：用 [架构总览](docs/architecture/README.md) 约束模块边界、adapter 原则和五层系统关系。
3. 对齐资产对象：用 [技能资产](docs/skill-assets/README.md) 说明 `WeldSkillPackage` 和后续焊缝技能单元的关系。
4. 对齐仿真边界：用 [仿真路线](docs/simulation/README.md) 说明 simlite、类机器人仿真和外部仿真器 adapter 的边界。
5. 对齐证据边界：用 [证据与边界](docs/evidence/README.md) 区分软件验证、资料证据、仿真假设、真实质量验证和 WPS/PQR。
6. 保留历史成果：通过 [历史证据与归档](docs/archive/README.md) 保存 POC、MVP、gate、白皮书和旧计划。

## 已完成基础能力

- 已有可运行的 `weldcore` 引擎，详见 [weld-experience-engine/README.md](weld-experience-engine/README.md)。
- 已有 `SkillDataset`、`SkillSample`、`WeldSkillPackage`、迁移评测和 evidence 输出的基础数据结构。
- 已跑通经验结构化 POC、技能迁移 MVP、资料底座 gate、`SyntheticSkillDataset v2` 输入规范 gate 和仿真输出接入 gate。
- 已有 simlite/mock bundle 作为 L0 稳定仿真和测试工具。
- 已明确 ManiSkill、SAPIEN、Isaac、ROS、MoveIt、Gazebo 等外部生态只能作为 adapter 候选或后续评估对象。
- 已归档前期 POC、MVP、gate、白皮书和旧计划材料，避免把历史阶段误当成当前默认主线。

这些基础能力说明软件和数据结构层面的验证路径已经存在，但不代表真实焊接质量、WPS/PQR 或最终仿真器路线已经完成。

## 当前目录结构

```text
.
├── README.md
├── details.md                         # 面向非技术读者的阶段说明和维护台账
├── docs/
│   ├── strategy/                       # Physical AI 公司战略与项目承接关系
│   ├── architecture/                   # 五层架构、模块边界和 adapter 原则
│   ├── skill-assets/                   # WeldSkillPackage 与焊接技能单元
│   ├── simulation/                     # 类机器人仿真路线和 simlite 边界
│   ├── evidence/                       # 资料来源、字段覆盖、证据报告和质量边界
│   └── archive/                        # POC、MVP、gate、白皮书和旧计划归档
└── weld-experience-engine/
    ├── README.md
    ├── pyproject.toml
    ├── tests/
    └── weldcore/
```

## 如何验证

默认验证路径保持为可安装、可运行、可测试：

```bash
cd weld-experience-engine
uv sync --extra dev --extra viz
uv run pytest -q
```

报告命令仍然可用，但它们是技能资产证据、证据边界/仿真接入证据或历史支撑，不是默认研发主线本身。

技能资产证据命令：

```bash
uv run python -m weldcore.report.mvp_report
```

`mvp_report` 用于证明早期 `WeldSkillPackage` 闭环仍有效。

证据边界/仿真接入证据命令：

```bash
uv run python -m weldcore.report.data_foundation_report
uv run python -m weldcore.report.synthetic_v2_input_report
uv run python -m weldcore.report.simulation_ingest_report
```

历史支撑命令：

```bash
uv run python -m weldcore.report.generate
uv run python -m weldcore.report.scenario_report
```

这些命令用于复盘 POC、MVP、资料 gate、输入规范 gate 和仿真输出接入 gate 的证据链。它们不能被写成真实焊接质量验证、完整外部仿真器集成或 WPS/PQR。

## 当前不做事项

- 不把 `stiffened-panel-fillet` 作为默认项目主线；它现在是历史资料 gate 和行业实例。
- 不在第一阶段选择最终仿真器。
- 不把 simlite 夸大为类机器人仿真路线；simlite 只是 L0 稳定仿真和测试工具。
- 不把 ManiSkill、SAPIEN、Isaac、ROS、MoveIt、Gazebo 等 adapter 候选变成基础依赖。
- 不把公开资料、合成样本、仿真输出或报告结论写成真实焊接质量验证。
- 不把当前输入规范、资料证据或仿真假设写成 WPS/PQR。
- 不删除历史成果；历史材料统一保留在归档目录。

## 历史证据与归档

历史 POC、MVP、gate、旧计划和白皮书已统一归档，入口见 [docs/archive/README.md](docs/archive/README.md)。

白皮书历史材料位于 [docs/archive/whitepaper/report/](docs/archive/whitepaper/report/)，仅作为历史论证和支撑材料引用，不再作为默认项目入口。

## Agent 维护规则

`details.md` 是面向用户、业务人员和非技术读者的项目阶段台账。后续任何 Agent 在推进本项目时，都必须检查 [details.md](details.md) 是否需要同步更新。

需要更新 `details.md` 的情况包括：

- 项目阶段、范围或默认主线发生变化。
- `WeldSkillPackage`、焊缝技能单元、仿真路线、证据边界或 adapter 边界发生变化。
- 新增或移除重要基础能力、报告命令、验证路径或交付物。
- 真实焊接质量验证、WPS/PQR、最终仿真器选择等边界判断发生变化。

更新时必须用非技术读者能理解的直白语言，明确区分“已经完成”“正在验证”“后续需要补充”，不要把软件原型、仿真结果或公开资料证据夸大为真实生产结论。

面向读者的入口文档、阶段说明和路线说明更新时，必须同步创建或刷新同目录 HTML 阅读版。尤其是根目录 `README.md` 和 `details.md`：Markdown 是维护源，HTML 是面向项目负责人、业务人员和非技术读者的阅读副本；后续新增 README 或类似说明文档时，也应保留相邻的 `.html` 阅读版链接。
