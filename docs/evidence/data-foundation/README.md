# 数据底座说明

本目录是焊接技能大师平台的 manifest-first 数据底座。它先登记资料、数据集、字段覆盖和任务证据，再由测试和 loader 读取这些机器可读文件；本阶段不把大体量公开数据集下载进 git 仓库。

`source-cards/` 下的 Markdown 资料卡面向人阅读，说明每组资料的来源、用途和边界。真正可执行、可测试的权威数据在 `manifests/` 下的 JSON/CSV 文件中：

- `sources.json`：来源卡，记录公开资料、项目内部资料、标准页、工艺指南和论文筛选入口。
- `datasets.json`：数据集卡，记录模态、体量、下载策略、schema 摘要和使用边界。
- `field_coverage.csv`：字段覆盖矩阵，说明每个字段由哪些来源或数据集支撑，哪些仍是仿真假设。
- `task_evidence_map.json`：任务证据映射，说明哪些船舶焊接任务族可以进入后续 `SyntheticSkillDataset v2` 规划。

本目录不是焊接质量真实验证报告，也不声称任何公开数据集已经验证了本项目的真实焊接质量。当前输出只用于资料追踪、字段约束、任务筛选和后续 `SyntheticSkillDataset v2` 规划输入。真实工艺验证、客户 WPS、现场检测和设备采集数据必须在后续阶段单独建立证据链。

仿真输出接入之后，本目录下的 manifests 仍然被 simulation ingest gate 使用，用来约束 `SimulationOutputBundle` 进入 `SyntheticSkillDataset v2` 时的任务、字段和来源边界。前期 research docs 也仍然保留，作为未来焊接知识嵌入的底座，而不是被改写成真实质量验证、WPS/PQR 或熔池路线。

当前路线不依赖焊中视觉控制或生产闭环控制字段；如未来需要纳入这类路线，必须新建独立设计、manifest 和 gate。
