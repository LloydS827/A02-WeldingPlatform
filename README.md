# 焊接技能大师平台

本仓库用于沉淀 A02「焊接技能大师平台」的方案文档、论证白皮书、关键预研 POC 与技能迁移 MVP。

当前工作重点已经从 idea / POC 论证推进到 MVP 验证：先用轻量仿真和结构化数据模型证明“焊接技能能否被打包并迁移到相近焊缝条件”，再逐步接入 Rerun、ManiSkill 范式、专家知识和未来真机数据。

## 当前结论

现阶段已经完成两条可运行证据链：

1. **经验结构化 POC**：验证“大师焊接轨迹 -> 结构化工艺参数 -> 机器人可执行轨迹”的闭环。
2. **技能迁移 MVP**：验证“仿真样本 -> SkillDataset -> WeldSkillPackage -> TransferExperiment -> 评测报告”的最小闭环。

MVP 的阶段性判断是：软件与数据结构层面的核心机制已经跑通，可以作为下一阶段真机接入、专家知识整理、专利/论文材料沉淀的基础。但它还不能被表述为真实焊接质量已经被验证；真实焊接质量仍需要真机、焊材、工艺评定和检测结果二次标定。

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
│   └── reference/    # 外部/前序技术方案参考
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

进入 POC/MVP 子项目：

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

`mvp_report` 会生成：

- `mvp_report_out/evidence.json`
- `mvp_report_out/metrics.csv`
- `mvp_report_out/transfer_summary.png`
- `mvp_report_out/ip_notes.md`

## 技术边界

- MVP 优先使用轻量仿真，不等待真机或高保真熔池物理仿真。
- 真机数据价值最高，但当前只预留接口边界，后续应通过同一套 `SkillDataset` 接入。
- Rerun 定位为多源时间轴记录、回放、标注和调试驾驶舱，不是生产数据库或机器人控制总线。
- ManiSkill / SAPIEN 当前作为机器人任务、demonstration 数据和 evaluation benchmark 的范式参考，不是基础测试依赖。
- 核心自有资产应放在 `SkillDataset`、`WeldSkillPackage`、迁移规则、评测协议和工艺语义模型上。

## 阶段判断

现阶段工作可以视为“技能迁移 MVP 第一轮完成”：

- 已有可运行代码。
- 已有自动化测试。
- 已有报告生成命令。
- 已有白皮书与 IP notes 可引用材料。
- 已明确 Rerun、ManiSkill、真机数据和专家知识的边界。

下一阶段建议进入“真实数据与工程化 MVP”：

1. 选择 1 个真实或半真实焊接任务，定义真机数据采集字段和最小采集流程。
2. 复用 Rerun 生态做多源数据回放，不重复建设可视化基础设施。
3. 补充焊接技能大师经验访谈模板，把专家知识转成可进入 `SkillDataset` / `WeldSkillPackage` 的字段。
4. 把 MVP 报告中的 IP notes 扩展为专利交底书、论文提纲和软著材料。
5. 在真机数据到位后，对当前仿真迁移结论做二次标定，避免把仿真结论直接等同于真实焊接质量。
