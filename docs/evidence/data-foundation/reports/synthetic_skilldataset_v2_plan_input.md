# SyntheticSkillDataset v2 规划输入

## 使用边界

- 该文件只把通过资料底座门禁的任务族整理为后续合成数据规划输入。
- 参数值、质量结论和设备控制策略仍需后续真实工艺、仿真和人工审核确认。
- 假设字段必须在样本 schema 中显式标注，不得包装成实测字段。

## 门禁汇总

- 资料来源总数：20
- 公开数据集：6
- ready 任务族：3

## ready 任务族输入

### 1. stiffened-panel-fillet

- readiness：ready_for_synthetic_v2_plan
- 必需字段：shipbuilding_context, weld_object, joint_type, torch_angle, travel_speed
- 已覆盖字段：shipbuilding_context, weld_object, joint_type, torch_angle, travel_speed
- 假设字段：leg_size_mm, plate_thickness_mm
- 支撑来源：
  - vendor-kranendonk-panel-welding-gantry｜KRANENDONK Panel Welding Gantry｜边界：可用于任务和字段约束；不可用于过程质量验证或控制器数据复原。
  - project-260522-shipbuilding-welding-brain-plan｜船舶焊接工艺大脑平台整体规划方案｜边界：可用于项目字段定义和任务映射；不可替代真实生产验证。
- 支撑数据集：
  - 无
- 下一步：作为第一批 SyntheticSkillDataset v2 任务族，先生成面板线角焊规划输入。

### 2. panel-butt

- readiness：ready_for_synthetic_v2_plan
- 必需字段：shipbuilding_context, weld_object, joint_type, groove_geometry, current, voltage, travel_speed
- 已覆盖字段：shipbuilding_context, weld_object, joint_type, groove_geometry, current, voltage, travel_speed
- 假设字段：plate_thickness_mm, root_gap_mm
- 支撑来源：
  - vendor-kobelco-shipbuilding-welding｜KOBELCO Shipbuilding Welding Industry Page｜边界：可用于船舶语境和任务字段；不可替代船厂 WPS 或真实检测数据。
  - project-260522-shipbuilding-welding-brain-plan｜船舶焊接工艺大脑平台整体规划方案｜边界：可用于项目字段定义和任务映射；不可替代真实生产验证。
  - standard-aws-swps-public-page｜AWS Standard Welding Procedure Specifications Public Page｜边界：可用于 WPS 概念；不可替代客户 WPS、船级社规则或标准正文。
  - guide-lincoln-electric-gmaw｜Lincoln Electric GMAW Guide｜边界：可用于通用参数字段；不可直接作为船舶 WPS。
- 支撑数据集：
  - dataset-zenodo-metal-arc-welding-10017718｜电弧焊过程测量和元数据，可筛选电流、电压、送丝和标签字段。｜边界：用于过程 schema 和参数字段筛选；不可作为船舶现场验证。
  - dataset-mendeley-gmaw-screening-pool｜GMAW 候选过程字段和标签定义，进入任务前需人工筛选。｜边界：只作为候选数据入口；不可自动进入训练、验证或质量结论。
- 下一步：进入 SyntheticSkillDataset v2 规划，但参数值必须保留 WPS 待验证标记。

### 3. micro-panel-web-bulkhead

- readiness：ready_for_synthetic_v2_plan
- 必需字段：shipbuilding_context, weld_object, trajectory, robot_pose, motion_template
- 已覆盖字段：shipbuilding_context, weld_object, trajectory, robot_pose, motion_template
- 假设字段：weld_seam_list, sequence_order, node_transition
- 支撑来源：
  - case-siemens-hd-hyundai-mipo-autonomous-welding｜HD Hyundai Mipo Autonomous Welding Robot Development Case｜边界：可用于任务拆解和仿真边界；不可声称真实产线质量验证。
  - project-260522-shipbuilding-welding-brain-plan｜船舶焊接工艺大脑平台整体规划方案｜边界：可用于项目字段定义和任务映射；不可替代真实生产验证。
  - paper-shipbuilding-robot-welding-screening｜Shipbuilding Robot Welding Literature Screening Entry｜边界：可用于规划后续文献筛选；不可用于实测结果或质量验证。
- 支撑数据集：
  - dataset-zenodo-tandem-gmaw-17951725｜Tandem-GMAW 过程、机器人、扫描、视频和元数据字段，可作为多模态 schema 参考。｜边界：用于 schema 参考和字段规划；不可直接映射为船舶质量证据。
- 下一步：作为多短焊缝 synthetic v2 规划输入，先输出任务序列 schema。
