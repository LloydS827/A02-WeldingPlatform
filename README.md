# 焊接技能大师平台

本仓库用于沉淀 A02「焊接技能大师平台」的立项论证、方案文档与关键预研 POC。

当前阶段不是直接建设完整平台，而是先完成两件事：

1. 将既有《船舶焊接工艺大脑平台整体规划方案》做风险拆解，形成可评审的论证白皮书。
2. 用 `weld-experience-engine` 做一个最小可运行 POC，验证“大师焊接轨迹 -> 结构化工艺参数 -> 机器人可执行轨迹”的核心闭环。

## 当前状态

- 已完成 A02 课题定义、总体方案、白皮书设计 spec 与实施 plan。
- 之前的设计 spec 和实施 plan 曾按 Superpowers 标准路径存放；现在已整理到常规项目文档目录。
- POC 已完成阶段一闭环：合成、扰动、decompose、recompose、metrics、report 与 8 字形模板扩展点。
- POC 已加入测试评测和自审记录，可用 `python -m weldcore.report.generate` 产出白皮书可引用的图、JSON 和 CSV 证据。
- 后续白皮书应使用 POC 真实数据回填关键预研结论，避免只写概念论证。

## 目录结构

```text
.
├── README.md
├── AGENTS.md / CLAUDE.md
├── docs/
│   ├── project/      # 课题定义、总体方案、规划说明
│   ├── specs/        # 白皮书与关键预研设计 spec
│   ├── plans/        # POC 与白皮书实施计划
│   └── reference/    # 外部/前序技术方案参考
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

## POC 子项目

`weld-experience-engine` 是焊接经验结构化引擎的 POC 种子。它的核心目标是验证：

```text
合成理想大师轨迹
-> 注入真实扰动
-> decompose 为结构化工艺参数
-> recompose 为机器人可执行轨迹
-> 用 metrics 量化复现误差与失效边界
```

运行方式：

```bash
cd weld-experience-engine
pip install -e ".[dev,viz]"
pytest -q
```

## 建议下一步

1. 用 POC 的真实输出回填风险登记表，再开始撰写正式论证白皮书。
2. 明确一期边界：L1 经验结构化为主，L2 只做探针，L3 焊中闭环自适应暂不承诺。
3. 真机数据到位后，对当前合成+扰动结论做二次标定。
