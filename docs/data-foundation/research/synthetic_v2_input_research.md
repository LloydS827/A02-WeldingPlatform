# SyntheticSkillDataset v2 输入规范前置调研
## 结论

本阶段可以进入 SyntheticSkillDataset v2 输入结构设计，但边界必须明确：当前产物是 schema 和 vocabulary 的前置研究，不是 WPS/PQR，不证明真实焊接质量，也不替代船级、客户规范、项目 WPS/PQR 或现场试焊验证。

依据清单核验：`docs/data-foundation/manifests/sources.json` 有 20 条来源，`docs/data-foundation/manifests/datasets.json` 有 6 个公开数据集，`docs/data-foundation/manifests/field_coverage.csv` 存在且覆盖 19 个字段；`docs/data-foundation/manifests/task_evidence_map.json` 中 `stiffened-panel-fillet`、`panel-butt`、`micro-panel-web-bulkhead` 三个任务族为 `ready_for_synthetic_v2_plan`。第一版输入规范应先承接任务分类、焊缝/接头/位置/坡口/层道、工艺字段、运动字段、质量标签和证据绑定，不纳入真实参数合格性判断。

- 进入第一层字段：`manufacturing_stage`、`weld_object`、`joint_type`、`weld_position`、`groove_geometry`、`layer_pass`、`welding_process`、`plate_thickness_mm`、`current`、`voltage`、`travel_speed`、`trajectory`、`torch_angle`、`motion_template`、`quality_label`、`defect_label`、`inspection_reference`、`requires_real_validation_later`。
- 公开约束：船舶自动化案例和工艺指南可提供任务、对象、接头、位置和参数字段存在性；公开数据集只提供 schema、vocabulary 和 benchmark 参考。
- 仿真假设：板厚、根部间隙、焊脚、层道数量、轨迹模板、节点过渡和参数曲线可作为 synthetic v2 假设字段，但必须标注来源和验证状态。
- 后续真实验证：电流、电压、速度、热输入、层间温度、质量判据、检测结论、焊材/保护气体和船级适用性必须由真实 WPS/PQR、试焊、检测或工艺人员确认。
- 排除项：熔池视觉闭环、声纹缺陷归因、真实机器人控制程序、AMR 跨工位长焊缝分段、曲面复杂空间焊缝、准 WPS/PQR 模板和质量合格声明均 out of scope。

## 1. 船舶焊接任务分类

来源：`vendor-kobelco-shipbuilding-welding`、`vendor-kranendonk-panel-welding-gantry`、`case-siemens-hd-hyundai-mipo-autonomous-welding`、`vendor-hyundai-welding-cobot-shipbuilding-2024`、`vendor-kranendonk-block-welding-line`、`project-260522-shipbuilding-welding-brain-plan`、`paper-shipbuilding-robot-welding-screening`。

第一版任务分类应覆盖制造阶段、焊接对象、接头形式、焊接位置、空间可达性和当前处置。首批 ready 任务为加筋板/纵骨角焊、平面板拼接/简化对接、多短焊缝小组立；双层底内部角焊保留为 `needs_more_sources`，立向/仰位、厚板多层多道、曲面复杂焊缝暂缓。

- 进入第一层字段：`task_taxonomy.manufacturing_stage`、`task_taxonomy.weld_object`、`task_taxonomy.joint_type`、`task_taxonomy.weld_position`、`task_taxonomy.readiness`。
- 扩展/后续字段：`access_context`、工装空间、节拍和安全边界，先不作为第一版必备盘点字段。
- 公开约束 vs 仿真假设：公开案例证明任务族和自动化方向存在；具体构件尺寸、焊缝长度、焊脚、工装空间和节拍只能作为仿真假设。
- 后续真实验证：船厂现场工位、图纸、工艺文件、机器人可达性和安全边界。
- 不纳入：仅凭现有 straight-flat 能力倒推船舶任务；不把宣传资料中的场景写成生产合格率或质量结论。

## 2. 焊缝、接头、位置、坡口和层道知识

来源：`project-260522-shipbuilding-welding-brain-plan`、`vendor-kobelco-shipbuilding-welding`、`vendor-kranendonk-panel-welding-gantry`、`guide-esab-fcaw-gmaw`、`guide-miller-gmaw`、`guide-lincoln-electric-gmaw`。

项目规划把焊缝对象、坡口对象、层道对象、轨迹对象和质量对象列为主数据对象；公开船舶资料和工艺指南支持 butt、fillet、tee、lap、flat、horizontal、vertical-up、overhead 等 vocabulary。坡口几何目前主要由项目规划支撑，应先作为结构字段，不做合规参数。

- 进入第一层字段：`joint_type`、`weld_position`、`groove_geometry`、`layer_pass`、`plate_thickness_mm`。
- 扩展/后续字段：`root_gap_mm`、`leg_size_mm`、`seam_length_mm` 只作为后续几何细化或任务假设，不作为已盘点的一层字段。
- 公开约束 vs 仿真假设：接头和位置可用公开 vocabulary；V/X/K/none、坡口角度、间隙、钝边、错边量、层序/道序可作为仿真输入占位。
- 后续真实验证：坡口尺寸、板厚、焊脚、层间搭接、层间温度、清根/清渣和暂停检查点。
- 不纳入：厚板多层多道自动排布的完整工艺优化；曲面空间焊缝和复杂节点的一版生成。

## 3. 工艺参数和 WPS/PQR 相关字段

来源：`standard-aws-swps-public-page`、`standard-aws-standards-index`、`guide-lincoln-electric-gmaw`、`guide-esab-fcaw-gmaw`、`guide-miller-gmaw`、`dataset-zenodo-metal-arc-welding-10017718`、`dataset-zenodo-tandem-gmaw-17951725`、`dataset-mendeley-gmaw-screening-pool`、`project-260522-shipbuilding-welding-brain-plan`。

第一版应定义能承接 WPS/PQR 主要字段的 procedure field set，但它不是 WPS/PQR。公开标准页和工艺指南可支撑字段存在性与术语，公开过程数据集可支撑 current/voltage/wire_feed/travel_speed 的 schema；真实数值窗口、热输入和合格性不能由这些资料直接证明。

- 进入第一层字段：`welding_process`、`current`、`voltage`、`travel_speed`、`requires_real_validation_later`。
- 扩展/后续字段：`wire_feed`、`heat_input_placeholder`、`shielding_gas`、`filler_material` 先保留为 WPS/PQR 扩展位，不作为第一版模型必备字段。
- 公开约束 vs 仿真假设：公开来源提供参数字段和通用范围线索；synthetic v2 可生成参数曲线或范围占位，但必须标注 `simulation_assumption` 或 `simulation_output`。
- 后续真实验证：客户 WPS、PQR、焊材、保护气体、预热/层间温度、极性、脉冲参数、热输入限制和船级适用性。
- 不纳入：准 WPS/PQR 模板、标准正文替代、船级审查结论、真实工艺合格判断。

## 4. 质量、缺陷和检查词汇

来源：`dataset-gdxray-weld-xray`、`dataset-riawelc-weld-image`、`dataset-lohi-weld`、`guide-twi-weld-defects`、`encyclopedia-wartsila-weld-defects`、`standard-aws-swps-public-page`、`standard-aws-standards-index`、`project-260522-shipbuilding-welding-brain-plan`。

公开数据集和缺陷词汇资料可以提供 defect_label、quality_label、inspection_reference 的 vocabulary 和 benchmark 线索。项目规划中的质量对象包括余高、宽度、咬边、探伤、返修等闭环字段，但当前研究只把它们登记为输入规范可承接的词汇层。

- 进入第一层字段：`quality_label`、`defect_label`、`inspection_reference`、`requires_real_validation_later`。
- 扩展/后续字段：`quality_source_type` 可由证据绑定和 `requires_real_validation_later` 推导，暂不单列为第一版字段。
- 公开约束 vs 仿真假设：公开数据集可提供表面图像、射线图像、过程 metadata 的标签结构；仿真可生成质量占位或评分标签。
- 后续真实验证：项目验收标准、无损检测报告、焊后扫描实测、返修记录和工艺人员复核。
- 不纳入：把公开标签当作船舶焊缝质量判定；把 benchmark 结果当作真实质量；不证明真实焊接质量。

## 5. 公开数据集与 schema 参考

来源：`dataset-gdxray-weld-xray`、`dataset-zenodo-metal-arc-welding-10017718`、`dataset-zenodo-tandem-gmaw-17951725`、`dataset-riawelc-weld-image`、`dataset-lohi-weld`、`dataset-mendeley-gmaw-screening-pool`。

六个公开数据集只作为 manifest/schema 参考：射线图像和表面图像用于缺陷/质量 vocabulary，过程时序用于 current/voltage/wire_feed，Tandem-GMAW 多模态数据用于 robot_pose、scan_3d、video 和 metadata 的字段形态。它们可用于 schema_reference、vocabulary 和 benchmark，不可直接映射为船舶现场质量证据。

- 进入第一层字段：`process_spec.current`、`motion_spec.motion_template`、`quality_spec.quality_label`。
- 扩展/后续字段：`source_schema.modalities`、`source_schema.quality_label_type`、`process_spec.voltage`、`process_spec.travel_speed` 作为数据集筛选和后续 schema 细化字段，不进入第一版必备矩阵。
- 公开约束 vs 仿真假设：公开数据集约束字段形态和模态；synthetic v2 仍需生成自己的任务、几何和运动输入。
- 后续真实验证：数据许可、字段语义、抽样 checksum、标签定义、与船舶任务的映射有效性。
- 不纳入：大文件下载入 git、未筛选数据直接训练、公开数据集质量标签直接作为项目质量结论。

## 6. 仿真优先路线对字段的约束

来源：`case-siemens-hd-hyundai-mipo-autonomous-welding`、`vendor-kranendonk-panel-welding-gantry`、`project-260522-shipbuilding-welding-brain-plan`、`paper-shipbuilding-robot-welding-screening`、`dataset-zenodo-tandem-gmaw-17951725`。

仿真优先路线要求输入规范先能生成可解释的任务、几何、运动和参数占位，再进入真实验证。第一版要支持单条焊缝、面板线角焊、简化对接和多短焊缝序列；每个样本必须区分公开约束、仿真假设、仿真输出和后续真实验证。

- 进入第一层字段：`geometry_spec.groove_geometry`、`motion_spec.motion_template`、`trajectory`、`torch_angle`、`process_spec.current`、`quality_spec.quality_label`。
- 扩展/后续字段：`sequence_order`、`node_transition` 用于多短焊缝增强版，首批只通过 `motion_template` 保留方向。
- 公开约束 vs 仿真假设：公开案例支持仿真任务边界和运动模板；轨迹点、焊枪角、节点过渡、参数曲线和质量占位由仿真生成。
- 后续真实验证：机器人 TCP 误差、碰撞、可达性、工艺参数窗口、焊后质量和现场节拍。
- 不纳入：熔池闭环、声纹同步、真实控制器程序、未经人工确认的全无人自主焊接。

## 7. 进入数据结构设计的字段原则

来源：`field_coverage.csv`、`task_evidence_map.json`、`project-260522-shipbuilding-welding-brain-plan`、`standard-aws-swps-public-page`、`standard-aws-standards-index`。

下一步数据结构应以 EvidenceBinding 为核心，字段必须可追溯到来源、证据角色和值状态。第一版只做输入规范，不做生成器批量输出和质量合格声明。

- 进入第一层字段：`field_path`、`field_group`、`source_ids`、`source_category`、`source_categories`、`simulation_role`、`evidence_role`、`value_status`、`requires_real_validation_later`、`first_batch_required`。
- 公开约束 vs 仿真假设：同一个字段可同时有公开资料约束和仿真假设，但值必须分层记录。
- 后续真实验证：所有质量、参数合格性、标准适用性和船级相关字段。
- 不纳入：无来源字段、无法区分假设与实测的字段、把标准入口当标准正文的字段。

## 8. 暂不进入第一版的内容

以下内容 out of scope，不纳入第一版输入规范的必填层：真实 WPS/PQR 模板、PQR 合格记录、船级社审查结论、焊材批次与保护气体合规性、真实热输入合格判断、熔池视频闭环、声纹缺陷归因、真实机器人控制程序、AMR 跨工位长焊缝分段、曲面船体空间焊缝、厚板坡口多层多道完整优化、公开数据集直接训练门禁、质量合格声明。

这些内容可以保留扩展位或 `requires_real_validation_later` 标记，但不得在 synthetic v2 输入规范第一版中作为已验证能力、真实质量证据或标准合规结论出现。
