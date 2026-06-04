# 数据集与资料底座证据报告

## 结论

- 本报告是资料、数据集、字段覆盖和任务证据门禁，用于后续 SyntheticSkillDataset v2 规划。
- 本报告不声称真实焊接质量验证，不替代船厂 WPS、实测生产数据或设备控制参数确认。
- 公开来源仅作为场景、字段、schema 和任务边界证据；内部资料仅作为项目字段定义和需求边界。

## 汇总

- 资料来源总数：20
- 公开资料来源：19
- 强船舶相关来源：8
- 数据集总数：6
- 公开数据集：6
- 可进入 SyntheticSkillDataset v2 规划的任务族：3

## 资料来源证据

| source_id | title | url | 船舶相关性 | 使用边界 |
| --- | --- | --- | --- | --- |
| vendor-hyundai-welding-cobot-shipbuilding-2024 | Hyundai Welding Cobot Solution (Shipbuilding) Leaflet 2024 | https://www.hyundaiwelding.com/data/file/download/brochures/Hyundai_Welding_Cobot%20Solution%20%28Shipbuilding%29_Leaflet_2024.pdf | 船舶协作机器人焊接场景资料，可支撑任务族发现和自动化应用边界。 | 可用于任务选择和字段覆盖；不可用于真实焊接质量验证或设备控制参数确认。 |
| vendor-kobelco-shipbuilding-welding | KOBELCO Shipbuilding Welding Industry Page | https://www.kobelco.co.jp/english/products/welding/industries/shipbuilding.html | 船舶制造行业页，可支撑制造阶段、焊接对象、焊接位置和工艺类别。 | 可用于船舶语境和任务字段；不可替代船厂 WPS 或真实检测数据。 |
| case-siemens-hd-hyundai-mipo-autonomous-welding | HD Hyundai Mipo Autonomous Welding Robot Development Case | https://resources.sw.siemens.com/en-US/case-study-hd-hyundai-mipo/ | 公开案例涉及小组立、分段约束、仿真和机器人程序开发边界。 | 可用于任务拆解和仿真边界；不可声称真实产线质量验证。 |
| vendor-kranendonk-panel-welding-gantry | KRANENDONK Panel Welding Gantry | https://kranendonk.com/applications/panel-welding-gantry/ | 面板线焊接自动化资料，直接支撑加筋板、纵骨角焊和大型平板构件场景。 | 可用于任务和字段约束；不可用于过程质量验证或控制器数据复原。 |
| vendor-kranendonk-block-welding-line | KRANENDONK Shipbuilding Applications | https://kranendonk.com/applications/shipbuilding/ | 船舶应用总览页，可支撑 KRANENDONK 船舶自动化语境和后续块体焊接资料筛选入口。 | 可用于复杂船体构件资料筛选；不可声称已取得具体块体焊接产线证据或质量验证。 |
| project-260522-shipbuilding-welding-brain-plan | 船舶焊接工艺大脑平台整体规划方案 | docs/project/船舶焊接工艺大脑平台整体规划方案.html | 项目内部规划定义焊接对象、坡口、轨迹对象、质量对象和平台边界。 | 可用于项目字段定义和任务映射；不可替代真实生产验证。 |
| dataset-gdxray-weld-xray | GDXray Weld X-ray Dataset | https://github.com/computervision-xray-testing/GDXray | 通用焊缝射线图像数据，可支撑缺陷标签和无损检测词汇。 | 可用于标签词汇；不可用于船舶焊接质量真实验证。 |
| dataset-zenodo-metal-arc-welding-10017718 | Zenodo Metal Arc Welding Dataset | https://zenodo.org/records/10017718 | 通用金属电弧焊数据，可用于过程字段 schema 和参数筛选线索。 | 可用于 schema 和参数字段参考；不可用于船舶任务质量验证。 |
| dataset-zenodo-tandem-gmaw-17951725 | Tandem-GMAW Dataset | https://zenodo.org/records/17951725 | 通用 Tandem-GMAW 多模态数据，可用于机器人、过程、扫描和视频 schema 参考。 | 可用于 schema 参考；不可直接映射为船舶现场质量证据。 |
| dataset-riawelc-weld-image | RIAWELC Weld Image Dataset | https://github.com/stefyste/RIAWELC | 公开焊缝图像分类数据，可用于视觉标签和缺陷词汇参考。 | 可用于标签词汇和 benchmark；不可证明船舶焊缝质量。 |
| dataset-lohi-weld | LoHi-Weld Dataset | https://github.com/aciditeam/LoHi-WELD | 公开焊缝视觉质量数据，可用于视觉质量标签和 benchmark 参考。 | 可用于视觉标签参考；不可作为船舶质量验证结果。 |
| dataset-mendeley-gmaw-screening-pool | Mendeley GMAW Screening Source | https://data.mendeley.com/datasets/52jzvspw75/1 | 公开 GMAW 候选数据来源，用于后续筛选过程字段和标签定义。 | 可作为候选数据来源；不可自动进入训练或质量验证。 |
| standard-aws-swps-public-page | AWS Standard Welding Procedure Specifications Public Page | https://www.aws.org/about/get-involved/committees/b2-committee-on-procedure-and-performance-qualification/swps/ | 公开 SWPS 页面，可支撑 WPS 概念、工艺变量和程序边界。 | 可用于 WPS 概念；不可替代客户 WPS、船级社规则或标准正文。 |
| standard-aws-standards-index | AWS Standards Index | https://www.aws.org/standards/ | 公开标准索引，可作为标准族、程序资格和引用边界入口。 | 可用于标注后续合规验证需求；不可替代标准采购和项目审查。 |
| guide-twi-weld-defects | TWI Defects and Imperfections in Welds: Porosity | https://www.twi-global.com/technical-knowledge/job-knowledge/defects-imperfections-in-welds-porosity-042 | 公开缺陷/不连续性资料，可支撑缺陷标签和检查词汇。 | 可用于缺陷词汇；不可用于真实质量判定或验收。 |
| encyclopedia-wartsila-weld-defects | Wartsila Encyclopedia: Weld Defects | https://www.wartsila.com/encyclopedia/term/weld-defects | 海工/船舶语境中的缺陷词汇，可支撑检查参考和质量标签边界。 | 可用于船舶语境的缺陷词汇；不可替代项目验收标准。 |
| guide-lincoln-electric-gmaw | Lincoln Electric GMAW Guide | https://www.lincolnelectric.com/en/welding-and-cutting-resource-center/process-and-theory/gas-metal-arc-welding-basics | 公开 GMAW 工艺说明，可支撑电流、电压、送丝和行走速度字段的通用边界。 | 可用于通用参数字段；不可直接作为船舶 WPS。 |
| guide-esab-fcaw-gmaw | ESAB GMAW/FCAW Process Guide | https://esab.com/us/nam_en/esab-university/ | 公开工艺资料入口，可支撑 GMAW/FCAW 参数和接头准备字段筛选。 | 可用于通用工艺字段参考；不可替代项目 WPS 或质量验证。 |
| guide-miller-gmaw | Miller GMAW/MIG Welding Guide | https://www.millerwelds.com/resources/article-library/mig-welding-the-basics-for-mild-steel | 公开 GMAW/MIG 入门资料，可支撑通用参数、接头和位置字段。 | 可用于参数字段参考；不可替代船舶工艺规程。 |
| paper-shipbuilding-robot-welding-screening | Shipbuilding Robot Welding Literature Screening Entry | https://www.sciencedirect.com/topics/engineering/robotic-welding | 作为船舶机器人焊接文献筛选入口，帮助标注自动化、可达性和任务分解边界。 | 可用于规划后续文献筛选；不可用于实测结果或质量验证。 |

## 数据集证据

| dataset_id | source_id | 模态 | schema 摘要 | 使用边界 |
| --- | --- | --- | --- | --- |
| dataset-gdxray-weld-xray | dataset-gdxray-weld-xray | xray_image, metadata | 焊缝射线图像文件与缺陷类别，适合记录标签词汇和 benchmark 方向。 | 仅用于缺陷词汇和 benchmark 方向；不可用于船舶焊接质量真实验证。 |
| dataset-zenodo-metal-arc-welding-10017718 | dataset-zenodo-metal-arc-welding-10017718 | current_voltage_timeseries, metadata | 电弧焊过程测量和元数据，可筛选电流、电压、送丝和标签字段。 | 用于过程 schema 和参数字段筛选；不可作为船舶现场验证。 |
| dataset-zenodo-tandem-gmaw-17951725 | dataset-zenodo-tandem-gmaw-17951725 | current_voltage_timeseries, robot_pose, scan_3d, video, metadata | Tandem-GMAW 过程、机器人、扫描、视频和元数据字段，可作为多模态 schema 参考。 | 用于 schema 参考和字段规划；不可直接映射为船舶质量证据。 |
| dataset-riawelc-weld-image | dataset-riawelc-weld-image | surface_image, metadata | 焊缝表面图像及分类标签，可用于视觉标签词汇筛选。 | 用于视觉标签和 benchmark；不可作为船舶焊缝真实质量判定。 |
| dataset-lohi-weld | dataset-lohi-weld | surface_image, metadata | 焊缝视觉质量图像与标签，可用于质量标签词汇和后续映射。 | 用于视觉质量标签参考；不可替代真实检测和验收。 |
| dataset-mendeley-gmaw-screening-pool | dataset-mendeley-gmaw-screening-pool | current_voltage_timeseries, metadata | GMAW 候选过程字段和标签定义，进入任务前需人工筛选。 | 只作为候选数据入口；不可自动进入训练、验证或质量结论。 |

## 任务证据门禁

| family_id | readiness | 支撑来源 | 支撑数据集 | 下一步 |
| --- | --- | --- | --- | --- |
| stiffened-panel-fillet | ready_for_synthetic_v2_plan | vendor-kranendonk-panel-welding-gantry<br>project-260522-shipbuilding-welding-brain-plan | 无 | 作为第一批 SyntheticSkillDataset v2 任务族，先生成面板线角焊规划输入。 |
| panel-butt | ready_for_synthetic_v2_plan | vendor-kobelco-shipbuilding-welding<br>project-260522-shipbuilding-welding-brain-plan<br>standard-aws-swps-public-page<br>guide-lincoln-electric-gmaw | dataset-zenodo-metal-arc-welding-10017718<br>dataset-mendeley-gmaw-screening-pool | 进入 SyntheticSkillDataset v2 规划，但参数值必须保留 WPS 待验证标记。 |
| micro-panel-web-bulkhead | ready_for_synthetic_v2_plan | case-siemens-hd-hyundai-mipo-autonomous-welding<br>project-260522-shipbuilding-welding-brain-plan<br>paper-shipbuilding-robot-welding-screening | dataset-zenodo-tandem-gmaw-17951725 | 作为多短焊缝 synthetic v2 规划输入，先输出任务序列 schema。 |
| double-bottom-inner-fillet | needs_more_sources | vendor-kobelco-shipbuilding-welding<br>case-siemens-hd-hyundai-mipo-autonomous-welding<br>vendor-kranendonk-block-welding-line<br>project-260522-shipbuilding-welding-brain-plan | 无 | 暂不进入 ready；先补充分段内部空间、姿态和可达性证据。 |
