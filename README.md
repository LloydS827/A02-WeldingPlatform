# Physical AI 焊接技能资产底座

## 一句话定义

本仓库支撑 A02「焊接技能大师平台」在 Physical AI for Welding 方向下的研发。当前目标不是先做完整业务系统、真实机器人控制或正式焊接工艺评定，而是把焊接经验、工艺语义、动作轨迹、仿真输出和证据边界沉淀为可学习、可迁移、可审计、后续可接机器人执行验证的技能资产数据结构。

## 文件入口

- [README HTML 阅读版](README.html)
- [项目进展记录 HTML 阅读版](details.html)

`README.md` 是项目入口，面向任何新读者说明项目定位、当前能力、如何运行和边界。

`details.md` 是阶段更新记录，面向项目讨论记录每天或每一轮完成了什么、下一步要做什么、哪些判断发生了变化。

## 当前定位

当前项目已经从早期 POC / MVP / gate / 报告集合，收束为以 `WeldSkillPackage` 和 `WeldSkillUnit` 为核心的焊接技能资产底座。

现阶段主线是：**把仿真路线到技能数据结构这段做扎实，并通过反证工作确认候选仿真软件和 adapter 是否真的能稳定产生可积累的数据**。

这意味着当前重点不是扩大仿真规模，也不是直接进入真实机器人执行，而是先回答：

1. 一个焊接技能单元能否稳定生成仿真任务。
2. 不同仿真路线能否按同一输出契约返回结果。
3. 仿真结果能否转成经验数据、证据包和机器人候选草案。
4. 哪些结论来自软件和仿真证据，哪些必须等待专家或真机验证。
5. 哪个仿真软件和 adapter 路线适合成为后续数据积累的默认入口。

## 核心链路

当前核心链路是：

```text
WeldSkillUnit
-> SimulationTaskSpec
-> simlite / ManiSkill-SAPIEN / Gazebo-MoveIt candidate adapter
-> SimulatorAdapterResult
-> SimulationEvidenceBundle
-> SkillDataset / experience dataset
-> RobotProcessPackageDraft
-> RobotContextSpec + RobotFeasibilityResult
-> ready_for_expert_review 或 blocked_*
```

这条链路的含义是：

- `WeldSkillUnit` 描述可复用、可训练、可评测的焊接动作能力。
- `SimulationTaskSpec` 把技能单元转成仿真任务输入。
- 仿真 adapter 负责尝试运行或明确记录失败边界。
- `SimulationEvidenceBundle` 汇总任务、adapter 结果、转换后的数据和证据状态。
- `SkillDataset` / experience dataset 是技能数据积累的当前承载形态。
- `RobotProcessPackageDraft` 是未来机器人执行候选包草案，不是正式工艺包。
- `RobotContextSpec` 与 `RobotFeasibilityResult` 只做上下文表达和轻量可行性预检，不代表真实机器人已可执行。

`ready_for_expert_review` 只表示这条候选草案具备进入专家审查的结构条件；`ready_for_robot_execution` 当前仍是保留状态，不应被默认触达。

## 已完成能力

项目当前已经完成以下基础能力：

- 可运行的 `weldcore` 引擎，详见 [weld-experience-engine/README.md](weld-experience-engine/README.md)。
- `SkillDataset`、`SkillSample`、`WeldSkillPackage`、迁移评测和 evidence 输出的基础数据结构。
- 经验结构化 POC、技能迁移 MVP、资料底座 gate、`SyntheticSkillDataset v2` 输入规范 gate 和仿真输出接入 gate。
- `WeldSkillUnit` 最小框架，以及长直横焊沿缝跟踪、包角横焊转角过渡等默认技能单元。
- `SimulationTaskSpec`、`SimulatorAdapterResult` 和 `SimulationEvidenceBundle` 最小仿真证据结构。
- simlite/mock bundle 作为 L0 稳定仿真和测试基线。
- ManiSkill/SAPIEN 本机轻量闭环，用于验证外部仿真输出能否接入项目数据结构。
- Gazebo/MoveIt 候选路线的统一失败边界记录。
- 从 `SimulationEvidenceBundle` 到 `RobotProcessPackageDraft` 的机器人候选草案转换。
- `RobotContextSpec`、`RobotFeasibilityProbe`、`RobotFeasibilityResult` 和轻量机器人上下文预检接口。
- Rerun 证据回放兼容处理。
- 焊接工艺参数 Excel 表格作为参考资料纳入仓库；它是工程师参数参考，不是当前主流程的主数据源。
- 前期 POC、MVP、gate、白皮书和旧计划材料已归档，避免历史阶段继续占据默认入口。

这些能力说明软件结构、仿真接入和数据证据路径已经有了前半段闭环，但不代表真实焊接质量、正式 WPS/PQR、最终仿真软件选择或真实机器人执行已经完成。

## 下一阶段方向

下一阶段应优先做 **ManiSkill/SAPIEN 小批量默认仿真入口**。

具体来说，先不要急着扩大仿真任务数量，也不要直接投入重型机器人集成。更合适的任务是在统一仿真 adapter registry 之上，围绕少量核心 `WeldSkillUnit`，把 ManiSkill/SAPIEN 作为阶段性默认 route 跑通小批量样本入口，并继续保留 simlite 与 Gazebo/MoveIt 的对照和失败边界角色。

下一阶段要形成的判断包括：

- `SimulationBatchSpec` / `SimulationBatchResult` 如何表达小批量运行请求和结果。
- 两个核心 `WeldSkillUnit` 每个约 10 条运行样本能否稳定形成 raw artifact、adapter result、`SimulationEvidenceBundle` 和 experience dataset。
- 每条样本如何追踪 `batch_id`、`task_id`、`sample_id`、`seed`、`variation_policy`、证据路径和失败边界。
- 哪些字段可以作为后续技能数据积累的稳定字段，哪些仍是假设、mock、adapter 占位或人工补充。
- 第三轮进入数据积累前，默认仿真入口锁定和字段覆盖报告还缺什么证据。

## 如何验证

默认验证路径保持为可安装、可运行、可测试：

```bash
cd weld-experience-engine
uv sync --extra dev --extra viz
uv run pytest -q
```

常用报告命令：

```bash
uv run python -m weldcore.report.mvp_report
uv run python -m weldcore.report.data_foundation_report
uv run python -m weldcore.report.synthetic_v2_input_report
uv run python -m weldcore.report.simulation_ingest_report
uv run python -m weldcore.report.simulation_bakeoff_report
```

其中 `simulation_bakeoff_report` 用于生成 `WeldSkillUnit` 仿真 bake-off 证据；它记录 simlite、ManiSkill/SAPIEN 和 Gazebo/MoveIt 候选路线在同一任务契约下的尝试与失败边界，不表示最终仿真器已经选择。

历史支撑命令仍然保留：

```bash
uv run python -m weldcore.report.generate
uv run python -m weldcore.report.scenario_report
```

这些报告只能用于软件证据、资料证据、仿真接入证据和历史复盘，不能写成真实焊接质量验证、完整外部仿真器集成或正式 WPS/PQR。

## 当前目录结构

```text
.
├── README.md
├── README.html
├── details.md                         # 阶段更新记录和下一步计划
├── details.html
├── docs/
│   ├── strategy/                       # Physical AI 公司战略与项目承接关系
│   ├── architecture/                   # 五层架构、模块边界和 adapter 原则
│   ├── skill-assets/                   # WeldSkillPackage 与 WeldSkillUnit
│   ├── simulation/                     # 仿真路线、simlite 边界和外部 adapter 候选
│   ├── evidence/                       # 资料来源、字段覆盖、证据报告和质量边界
│   ├── archive/                        # POC、MVP、gate、白皮书和旧计划归档
│   └── superpowers/                    # 设计与实施计划记录
└── weld-experience-engine/
    ├── README.md
    ├── pyproject.toml
    ├── tests/
    └── weldcore/
```

## 当前不做事项

- 不把 `stiffened-panel-fillet` 作为默认项目主线；它现在是历史资料 gate 和行业实例。
- 不把 simlite 写成最终仿真器；它只是 L0 稳定基线。
- 不把 ManiSkill/SAPIEN、Gazebo/MoveIt、Isaac、ROS 等候选路线写成已经完成选型。
- 不把候选 adapter 的失败记录写成项目失败；失败边界本身就是当前反证工作的一部分。
- 不把 `RobotProcessPackageDraft` 写成正式机器人工艺包。
- 不把 `RobotFeasibilityResult` 写成真实机器人可达性、碰撞或关节限制验证。
- 不把公开资料、合成数据、仿真输出或报告结论写成真实焊接质量验证。
- 不把资料证据、输入规范、仿真假设或工程师参考表格写成 WPS/PQR。
- 不删除历史成果；历史材料统一保留在归档目录。

## Agent 维护规则

后续推进本项目时，应先判断是否需要同步更新 [details.md](details.md)。

需要更新 `details.md` 的情况包括：

- 项目阶段、范围或默认主线发生变化。
- `WeldSkillPackage`、`WeldSkillUnit`、仿真路线、证据边界或 adapter 边界发生变化。
- 新增或移除重要基础能力、报告命令、验证路径或交付物。
- 下一步计划、风险判断或阶段优先级发生变化。
- 真实焊接质量验证、WPS/PQR、最终仿真器选择等边界判断发生变化。

更新入口文档、阶段说明或路线说明时，必须同步刷新同目录 HTML 阅读版。尤其是根目录 `README.md` 和 `details.md`：Markdown 是维护源，HTML 是面向项目负责人、业务人员、工艺人员和非技术读者的阅读副本。
