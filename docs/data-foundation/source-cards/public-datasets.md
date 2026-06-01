# 公开数据集资料卡

本组资料记录公开焊接数据集，包括射线图像、表面图像、过程时序、机器人运动、3D 扫描、视频和元数据等模态。当前仓库只登记数据集来源、schema 摘要、体量说明和下载策略，不下载大体量数据文件。

下载策略：

- `manifest_only`：只记录来源和字段，不下载数据。
- `sample_cache_later`：后续若确有必要，可另建小样本缓存方案、checksum 和裁剪规则。
- `external_cache_only`：大文件只能放在外部缓存或数据目录，不能进入 git。

使用边界：

- 可用于缺陷词汇、视觉 benchmark、过程字段 schema 和后续数据筛选。
- 可用于 `SyntheticSkillDataset v2` 规划中的字段证据和候选标签集合。
- 不能证明本项目船舶焊接仿真样本的真实质量。
- 不能把通用数据集直接等同于船厂现场数据。

机器可读权威记录在 `../manifests/datasets.json`、`../manifests/sources.json` 和 `../manifests/field_coverage.csv`。本 Markdown 只做人工说明，若与 JSON/CSV 不一致，以 JSON/CSV 为准。
