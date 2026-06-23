# K01 + NV01 Weld Procedure Knowledge Contract and NVIDIA-Native Digital Twin Foundation 设计

日期：2026-06-23

## 1. 背景

A02 当前已经稳定收束为“机器人技能大师能力的焊接技能资产底座”。默认可运行路径已经能从 `SimulationEvidenceBundle` 构建 `ManipulationSkillAsset`，绑定 `RobotBodyAsset`、`RobotContextSpec`、`SceneContextAsset` 和 lightweight `RobotFeasibilityResult`，生成 `SkillTransferAssessment`、`ExpertReviewRecord`、A02->A01 handoff、IP support matrix，以及 2 个默认仿真任务的 Demo Evidence Pack。

上一阶段回答了“技能资产链路能否跑通、能否解释、能否进入专家审查候选”。新的问题是：如果 A02 的长期目标是成为真实仿真、合成数据和训练闭环的技术底座，是否还应继续把 ManiSkill/SAPIEN、Gazebo/MoveIt、Isaac 等作为平行候选反复 bake-off？

结合项目现状、`docs/Nvidia技术框架调研.md` 和 `docs/焊接工艺数据库主要参数表.xlsx` 的判断，本阶段设计结论是：**不应重复造重底座，也不应把所有仿真/训练框架长期平行化。A02 应把 NVIDIA OpenUSD / Isaac Sim / Isaac Lab 作为未来真实仿真与训练闭环的主底座，同时把焊接工艺数据库参数表提升为焊接知识资产合同源。**

这不是把 A02 改造成 Omniverse 应用，也不是马上引入 Isaac Sim 作为默认依赖。更准确的定位是：

```text
A02 = Weld Skill Digital Twin & Training Orchestrator

Excel weld procedure parameter dictionary = welding knowledge contract source
NVIDIA OpenUSD / Isaac Sim / Isaac Lab = future physical AI simulation and training foundation
A02 canonical schema = welding domain asset, procedure knowledge, evidence governance, expert review, A01/IP handoff
```

`docs/焊接工艺数据库主要参数表.xlsx` 当前包含 47 个字段、8 个参数类别，其中 21 个必填、12 个条件必填、14 个可选/补充字段。它表达的是人对焊接工艺参数结构化的具体要求，不能再只作为工程师参考表格存在；它应成为 NV01 之前的 **K01 Weld Procedure Knowledge Contract** 输入。

## 2. 设计目标

本阶段主题是：

```text
K01 + NV01 Weld Procedure Knowledge Contract and NVIDIA-Native Digital Twin Foundation
```

目标是把下一阶段从“泛泛兼容 NVIDIA 生态”推进为“由焊接工艺知识合同约束的 NVIDIA-native 底座准备”。第一轮交付不直接运行 Isaac Sim，而是定义并生成一个可验证的 **Weld Procedure Knowledge Contract + Weld Skill Digital Twin Package** 合同，让 A02 当前的技能资产、机器人上下文、场景上下文、工艺字段和证据链可以被明确编译到 OpenUSD/Isaac 工作流。

该包要回答：

1. Excel 中 47 个焊接工艺字段如何变成 A02 可审计的字段合同。
2. 哪些字段是核心必填、条件必填、补充增强；哪些必须由人填写或确认，哪些可由系统计算、仿真推导、工站回采或资料库引用。
3. A02 哪些 canonical 对象映射到 OpenUSD 世界模型。
4. 一个焊接任务进入 Isaac Sim replay / sensor simulation / synthetic data 前需要哪些 procedure metadata 和 manifest。
5. 哪些字段已经由当前 Demo Evidence Pack 支撑，哪些字段仍缺真实工位、标定、传感器、机器人模型、工艺人员确认或质量反馈。
6. 为什么当前目标是 `ready_for_procedure_contract_review`、`ready_for_simulation_replay_package_design` / `ready_for_training_design_review`，不是 `ready_for_robot_execution` 或正式 WPS/PQR。
7. 后续 Isaac Lab 训练闭环需要哪些 observation、action、reward、randomization、dataset 和 evaluation 契约。
8. Cosmos、Omniverse/Nucleus、Isaac ROS 等能力应处在什么后续阶段，而不是提前塞进默认路径。

## 3. 关键决策

### 3.1 OpenUSD 不是旁路导出，而是主交换层

OpenUSD 应成为 A02 面向数字孪生、仿真、合成数据和训练闭环的主交换模型。A02 不把内部 canonical schema 直接替换成 USD schema，但必须能从 `ManipulationSkillAsset`、`RobotContextSpec`、`SceneContextAsset` 和 `RobotBodyAsset` 生成 OpenUSD-oriented manifest。

第一版不要求写出完整 `.usd/.usda` 文件，因为这会过早引入 OpenUSD SDK、资产坐标系和材质/几何细节问题。第一版应先生成 `openusd_scene_manifest.json`，把未来 USD stage 的 prim 路径、资产引用、坐标系、语义标签、焊缝路径和工艺 metadata 说清楚。

### 3.2 Isaac Sim 是默认目标仿真运行时，但不是默认本地依赖

Isaac Sim 应被确认为未来真实仿真、传感器、domain randomization、Replicator 合成数据和 replay validation 的默认目标运行时。当前仓库仍不能把 Isaac Sim 加入默认依赖或默认测试，因为它依赖较重的 GPU、系统环境和版本锁定。

因此第一版交付的是 `isaac_sim_replay_config.json` 和 `nvidia_stack_alignment_matrix.json`，用于描述一个任务如何进入 Isaac Sim，以及当前缺哪些输入。若本机没有 Isaac Sim，默认验证仍应通过结构校验和文档检查。

### 3.3 Isaac Lab 是训练闭环目标层，不是当前训练任务

Isaac Lab 应作为策略训练、sim-to-real 和 manager-based training workflow 的目标层。当前阶段不训练 RL/IL 模型，不定义具体网络结构，不承诺策略可部署。

第一版只输出 `training_readiness_report.json`，描述 observation/action/reward/randomization/dataset/evaluation 的准备度，并明确哪些内容来自当前 A02 对象，哪些内容仍需要 Isaac Sim scene、Replicator dataset、真实标定和专家标注。

### 3.4 Cosmos 后置

Cosmos 适合作为长尾视觉增强、视频/世界模型推理、罕见工况扩展和 photoreal augmentation 层。它不应进入 NV01 默认路径，也不应被写成焊接控制大脑或 Isaac Sim 替代品。

NV01 只保留 `cosmos_future_extension_notes`，说明它未来如何接在 OpenUSD/Isaac/Replicator 数据之后。

### 3.5 A02 保持 canonical truth

`ManipulationSkillAsset` 仍是 A02 的 canonical 技能资产本体。OpenUSD/Isaac 是外部重底座和目标运行时，不能反过来吞掉 A02 的领域模型。

A02 自己负责：

- 焊接技能资产语义。
- 工艺参数、焊枪姿态、质量边界和任务分解。
- 证据来源、审查状态、失败边界。
- 专家复核与 A01/IP handoff。
- 从 demo evidence 到真实工位 evidence 的版本化治理。

NVIDIA 栈负责或承接：

- 3D 世界表达、资产组合和协作基础。
- 机器人仿真、传感器仿真、replay、碰撞/可达性验证。
- Replicator 合成数据与 domain randomization。
- Isaac Lab 训练环境和策略评测。

### 3.6 K01 是 NV01 的焊接知识前置合同

NV01 不能只表达机器人、场景和轨迹。它必须先消费 K01 输出的焊接工艺知识合同，否则数字孪生包会退化成“机器人仿真包”，而不是“焊接技能资产包”。

K01 第一版从 `docs/焊接工艺数据库主要参数表.xlsx` 读取字段字典，并生成：

- `WeldProcedureKnowledgeContract`：字段定义、必要性、数据类型、单位、条件必填规则、来源模式、目标对象路径和证据边界。
- `WeldProcedureParameterSet`：某个 demo task / skill asset 当前已有的工艺参数值、来源、审查状态和缺失项。
- `WeldProcedureValidationReport`：必填、条件必填和补充字段的覆盖情况，以及是否阻塞 expert review、simulation replay design 或 training design。
- `ProcedureToNV01MappingMatrix`：每个工艺字段如何进入 `ManipulationSkillAsset`、OpenUSD metadata、Isaac replay config、domain randomization、training readiness 或 expert gate。

字段必须按两轴分类：

| 分类轴 | 建议枚举 | 含义 |
| --- | --- | --- |
| `requirement_level` | `required` / `conditional_required` / `supplemental` | 对应 Excel 的必填、条件必填、可选/补充 |
| `acquisition_mode` | `human_required` / `human_confirmed_or_imported` / `system_computed` / `asset_or_simulation_inferred` / `workcell_logged` / `reference_catalog` | 表示字段由人填、系统算、仿真推导、工站回采或资料库引用 |

默认分类原则：

- `human_required`：WPS/PQR 编号、质量验收要求、无损检测等级、适用设备/产线、标准编号等必须由工艺/质量/项目人员确认的字段。
- `human_confirmed_or_imported`：母材、焊材、接头、坡口、焊接方法等可从任务资料导入但仍需人确认的字段。
- `system_computed`：热输入、单位换算、字段覆盖率和缺失状态等可由系统计算的字段。
- `asset_or_simulation_inferred`：焊接速度、摆弧宽度/频率、焊枪角度、焊枪干伸长、焊道布置等可由技能资产或仿真候选推导但仍需审查的字段。
- `workcell_logged`：实际电流、电压、送丝速度、机器人轨迹、执行异常和质量反馈等来自真实工站或设备日志的字段。
- `reference_catalog`：材料牌号、焊材型号、焊接方法编码、标准/检测术语等来自资料库或标准库的字段。

## 4. 非目标

本阶段不做以下事情：

- 不安装、封装或强依赖 Isaac Sim。
- 不实现完整 OpenUSD writer，也不要求写出 `.usd/.usda` 文件。
- 不引入 Omniverse/Nucleus 服务。
- 不训练 Isaac Lab 策略。
- 不接入 Cosmos API 或模型。
- 不接入 Isaac ROS、Jetson、真实机器人控制器、PLC 或安全回路。
- 不替换 `ManipulationSkillAsset` canonical schema。
- 不建设完整工艺数据库、录入 UI、权限系统或 WPS/PQR 审批系统。
- 不把 Excel 字段表、K01 参数集或任何计算结果写成正式 WPS/PQR。
- 不把 lightweight `RobotFeasibilityResult` 升级成完整 IK、真实碰撞检测或真实机器人执行验证。
- 不宣称真实焊接质量验证、正式 WPS/PQR、熔池/热过程物理仿真或机器人可执行。

## 5. 方案比较

### 方案 A：保守兼容层

只增加 NVIDIA alignment report，说明现有对象如何对应 OpenUSD/Isaac。

优点：改动小，风险低。

缺点：仍停留在“生态兼容说明”，不能真正推动 A02 成为仿真训练闭环底座。

### 方案 B：NVIDIA-native 数字孪生包

新增 K01 + NV01 合同，让 Excel 工艺字段、demo evidence pack 和技能资产一起编译成 OpenUSD/Isaac-oriented manifest、replay config、randomization recipe 和 training readiness report。

优点：把 OpenUSD/Isaac 提升为一等目标，同时用焊接工艺知识合同守住 A02 的领域资产核心；不把重依赖塞进默认测试，保持项目可运行。

缺点：第一版还不能证明 Isaac Sim 内部真实运行，也不能生成正式 WPS/PQR；它只能证明 A02 的知识合同和输出合同已经为 NVIDIA workflow 准备好。

### 方案 C：完整 Isaac Sim/Isaac Lab 集成

直接加入 Isaac Sim 环境、USD scene writer、Replicator 任务和 Isaac Lab training environment。

优点：融合程度最高。

缺点：范围过大，依赖 GPU/系统/版本，容易让默认仓库变成不可复跑的环境工程；也会把当前尚未真实标定的焊接任务包装成过早的仿真结论。

本阶段采用 **方案 B**。

## 6. 输出契约

新增默认目标命令建议为：

```bash
uv run python -m weldcore.skill_asset.nvidia_digital_twin_report \
  --source-demo-dir artifacts/demo/skill-asset-evidence \
  --outdir artifacts/demo/nvidia-digital-twin-foundation
```

第一版默认行为：如果 `--source-demo-dir` 缺失或目录不存在，命令内部应自动复用现有 2 个默认仿真任务生成 source demo evidence，避免用户必须先手工跑 `demo_report`。如果用户显式传入的目录存在但缺少必需 artifact，则应返回明确错误或 blocked report，不静默补默认值。无论入口如何，输出必须基于 A02 canonical builder 和现有 evidence pack，不应手工伪造技能资产字段。

建议输出结构：

```text
artifacts/demo/nvidia-digital-twin-foundation/
├── nv01_summary.md
├── nv01_summary.json
├── weld_procedure_knowledge_contract.json
├── weld_procedure_parameter_set.json
├── weld_procedure_validation_report.json
├── procedure_to_nv01_mapping_matrix.json
├── weld_skill_digital_twin_package.json
├── openusd_scene_manifest.json
├── isaac_sim_replay_config.json
├── domain_randomization_recipe.json
├── training_readiness_report.json
├── nvidia_stack_alignment_matrix.json
└── task-<unit-id>/
    ├── skill_asset_ref.json
    ├── weld_procedure_parameter_set.json
    ├── weld_procedure_validation_report.json
    ├── openusd_task_manifest.json
    ├── isaac_replay_task_config.json
    ├── sensor_and_annotation_manifest.json
    └── training_task_readiness.json
```

### 6.0 K01 工艺知识合同 artifact

`weld_procedure_knowledge_contract.json` 必须从 `docs/焊接工艺数据库主要参数表.xlsx` 生成，且至少包含：

- `source_workbook_ref`
- `contract_version`
- `field_count`，默认应为 `47`
- `category_count`，默认应为 `8`
- `requirement_summary`，默认应包含 `required=21`、`conditional_required=12`、`supplemental=14`
- `categories`
- `fields`
- `a02_target_paths`
- `nv01_usage_tags`
- `evidence_boundary`

每个字段定义至少包含：

- `field_id`
- `category`
- `display_name`
- `description`
- `data_type`
- `unit`
- `requirement_level`
- `required_when`
- `acquisition_mode`
- `human_role`
- `a02_target_path`
- `nv01_usage`
- `blocks`
- `evidence_boundary`

`weld_procedure_parameter_set.json` 表达某个 demo pack 或 task 当前已有的工艺参数值，至少包含：

- `parameter_set_id`
- `skill_asset_id`
- `contract_version`
- `values`
- `missing_required_fields`
- `missing_conditional_fields`
- `supplemental_gaps`
- `source_summary`
- `review_boundary`

`weld_procedure_validation_report.json` 至少包含：

- `validation_status`
- `ready_for_procedure_contract_review`
- `ready_for_expert_review`
- `ready_for_simulation_replay_package_design`
- `ready_for_training_design_review`
- `not_ready_reasons`
- `field_coverage`
- `human_required_gaps`
- `computed_fields`
- `inferred_fields`
- `workcell_logged_gaps`
- `wps_pqr_boundary`

默认允许 `ready_for_simulation_replay_package_design=true` 同时 `ready_for_expert_review=false`，前提是缺失项已清楚写入 validation report。原因是 Isaac manifest 可以先形成设计包，但正式专家审查必须等待人填/确认字段。

`procedure_to_nv01_mapping_matrix.json` 必须说明每个字段如何进入：

- `ManipulationSkillAsset.constraints`
- `ManipulationSkillAsset.context_requirements`
- `ExpertReviewRecord.required_real_context`
- `OpenUSD process_metadata`
- `Isaac Sim replay config`
- `domain_randomization_recipe`
- `training_readiness_report`
- `A02ToA01ProductValidationHandoff`

### 6.1 `weld_skill_digital_twin_package.json`

必须包含：

- `package_id`
- `package_version`
- `source_demo_pack_ref`
- `procedure_contract_ref`
- `procedure_parameter_set_refs`
- `procedure_validation_report_refs`
- `canonical_object_refs`
- `task_count`
- `tasks`
- `overall_status`
- `readiness_boundary`
- `nvidia_stack_targets`
- `next_required_real_world_evidence`

默认 `overall_status` 建议为：

```text
ready_for_simulation_replay_package_design
```

这表示 A02 已能形成面向 Isaac Sim replay 的包设计和 manifest，不表示已在 Isaac Sim 中完成 replay。

### 6.2 `openusd_scene_manifest.json`

必须表达未来 USD stage 的结构，而不是只列文件名：

- `stage_unit`
- `up_axis`
- `root_prim`
- `prim_plan`
- `asset_references`
- `coordinate_frames`
- `semantic_labels`
- `weld_seam_prims`
- `robot_prims`
- `workpiece_prims`
- `fixture_and_obstacle_prims`
- `sensor_prims`
- `process_metadata`
- `procedure_parameter_bindings`
- `a02_evidence_bindings`
- `missing_usd_authoring_inputs`

建议 prim 命名：

```text
/World
/World/Robots/<robot_id>
/World/Workpieces/<workpiece_id>
/World/Fixtures
/World/WeldTasks/<task_id>
/World/WeldTasks/<task_id>/SeamPath
/World/WeldTasks/<task_id>/TcpTrajectory
/World/Sensors/<sensor_id>
/World/SafetyZones
```

### 6.3 `isaac_sim_replay_config.json`

必须描述如何进入 Isaac Sim，而不是假装已经运行：

- `isaac_sim_target`
- `required_extensions`
- `stage_manifest_ref`
- `robot_import_requirements`
- `task_replay_plan`
- `physics_assumptions`
- `procedure_parameter_inputs`
- `sensor_simulation_plan`
- `replicator_dataset_plan`
- `validation_checks`
- `not_ready_reasons`

默认 `validation_checks` 至少包含：

- robot asset importability
- joint limit source check
- frame consistency check
- TCP trajectory replay check
- tool orientation continuity check
- collision validation placeholder
- sensor coverage placeholder
- generated annotation coverage placeholder

### 6.4 `domain_randomization_recipe.json`

必须围绕焊接有效扰动，不只随机灯光和材质。扰动项应优先来自 K01 字段合同和当前 task 的 parameter set：

- groove gap / bevel / root face / plate thickness
- workpiece and fixture offset
- seam path perturbation
- robot base/TCP calibration error
- camera/laser extrinsic noise
- reflectance / arc glare / smoke / spatter / lens contamination
- travel speed / current / voltage / wire feed process window
- joint friction / cable drag / controller latency placeholders

每个 randomization item 至少包含：

- `name`
- `category`
- `range_or_distribution`
- `source_assumption`
- `linked_a02_fields`
- `linked_procedure_fields`
- `requires_real_calibration`
- `requires_human_confirmation`
- `training_use`

### 6.5 `training_readiness_report.json`

必须面向 Isaac Lab 训练闭环：

- `training_status`
- `candidate_training_tasks`
- `observation_contract`
- `action_contract`
- `reward_terms`
- `termination_conditions`
- `curriculum_notes`
- `dataset_requirements`
- `sim_to_real_gap`
- `expert_review_gates`
- `procedure_contract_gates`
- `blocked_by`

默认 `training_status` 建议为：

```text
not_ready_for_policy_training
```

原因是当前缺 Isaac Sim 场景、传感器标注、真实标定、真实失败回放和专家审查结论。即使训练未就绪，也应能清楚说明“还差什么”。

### 6.6 `nvidia_stack_alignment_matrix.json`

必须把 A02 对象映射到 NVIDIA 层：

| A02 对象 | NVIDIA 层 | 当前状态 |
| --- | --- | --- |
| `RobotBodyAsset` | OpenUSD robot prim / Isaac robot import | URDF 可解析，但未 vendor validated |
| `WeldProcedureKnowledgeContract` | OpenUSD process metadata / Isaac task context / Isaac Lab env config | Excel 字段可生成合同，但尚未实现 |
| `WeldProcedureParameterSet` | per-task process inputs / randomization anchors / expert gate | 当前缺人填字段和真实工站确认 |
| `RobotContextSpec` | frames, TCP, joint limits, robot metadata | nominal context，未真实标定 |
| `SceneContextAsset` | workpiece, seam, fixtures, safety zones | 默认场景，可生成 manifest |
| `ManipulationSkillAsset.motion` | TCP trajectory / replay path | simulation-only evidence |
| `SkillAssetEvidence` | evidence binding / dataset lineage | 已有 demo evidence |
| `RobotFeasibilityResult` | future Isaac validation checks | 当前是 lightweight precheck |
| `ExpertReviewRecord` | human gate before simulation/training escalation | pending expert review |
| `A02ToA01ProductValidationHandoff` | downstream product validation package | candidate only |

## 7. 数据流

K01 + NV01 默认数据流：

```text
docs/焊接工艺数据库主要参数表.xlsx
-> WeldProcedureKnowledgeContract
Demo Evidence Pack
-> per-task SimulationEvidenceBundle
-> ManipulationSkillAsset
-> WeldProcedureParameterSet
-> WeldProcedureValidationReport
-> RobotBodyAsset / RobotContextSpec / SceneContextAsset
-> SkillTransferAssessment / ExpertReviewRecord
-> WeldSkillDigitalTwinPackage
-> OpenUSDSceneManifest
-> IsaacSimReplayConfig
-> DomainRandomizationRecipe
-> TrainingReadinessReport
-> NVIDIA stack alignment summary
```

关键约束：

- 所有 NVIDIA-oriented artifact 必须能追溯到 A02 canonical artifact。
- 所有 procedure metadata 必须能追溯到 `WeldProcedureKnowledgeContract` 或 `WeldProcedureParameterSet`。
- 任何缺失字段必须进入 `missing_*` 或 `blocked_by`，不能被默认值掩盖。
- 人必须填写或确认的字段不得被仿真值、默认值或计算值自动降级为“已满足”。
- Excel 字段表是 WPS/PQR-ready 字段合同，不是正式 WPS/PQR。
- `ready_for_simulation_replay_package_design` 不能升级成 `ready_for_simulation_replay`，除非真实 Isaac Sim runtime 完成运行。
- `not_ready_for_policy_training` 是训练准备报告的正常初始状态，不是失败。

## 8. 模块边界

建议新增模块：

```text
weldcore.skill_asset.nvidia_digital_twin_report
```

职责：

- 读取或生成 Demo Evidence Pack。
- 从 `docs/焊接工艺数据库主要参数表.xlsx` 构建 K01 procedure contract payload。
- 为每个 demo task 构建 procedure parameter set 和 validation report。
- 构建 NVIDIA-oriented manifest/report。
- 写出 NV01 summary 和 JSON artifacts。
- 验证 artifact 之间的引用完整性。

建议新增内部 helper 模块：

```text
weldcore.skill_asset.nvidia_digital_twin
```

职责：

- 从 canonical artifact 生成 `WeldSkillDigitalTwinPackage` payload。
- 生成 `WeldProcedureKnowledgeContract`、`WeldProcedureParameterSet`、`WeldProcedureValidationReport` 和 procedure mapping payload。
- 构建 OpenUSD manifest payload。
- 构建 Isaac Sim replay config payload。
- 构建 domain randomization recipe payload。
- 构建 training readiness report payload。

不负责：

- 调用 Isaac Sim。
- 写真实 USD stage。
- 训练模型。
- 生成机器人程序。
- 生成、审批或替代正式 WPS/PQR。
- 建设完整工艺数据库、录入 UI 或权限系统。
- 修改 A02 canonical schema 的含义。

## 9. 状态与门控

新增状态建议：

- `ready_for_simulation_replay_package_design`：manifest 和 config 可审查，但未在 Isaac Sim 运行。
- `ready_for_procedure_contract_review`：K01 字段合同和缺口报告可供工艺/质量人员审查。
- `blocked_by_missing_human_required_fields`：缺少必须由人填写或确认的字段，不能进入专家审查结论。
- `blocked_by_missing_conditional_procedure_fields`：场景触发了条件必填字段，但参数集未覆盖。
- `computed_not_wps_validated`：字段由系统计算得到，可用于设计审查，但不能作为 WPS/PQR 结论。
- `blocked_by_missing_openusd_scene_inputs`：缺 USD stage 必需的机器人/场景/坐标系输入。
- `blocked_by_missing_isaac_runtime`：缺 Isaac Sim 环境，不影响默认结构验证。
- `not_ready_for_policy_training`：训练闭环合同已描述，但缺训练数据、环境、reward validation 或专家 gate。
- `ready_for_training_design_review`：training readiness report 足以让专家和研发评审训练方案。

`ready_for_training_design_review` 和 `not_ready_for_policy_training` 可以同时成立：前者表示训练方案合同足以进入设计评审，后者表示尚未具备真实策略训练条件。实现和报告中必须把这两个状态分层展示，避免读者误解为矛盾。

禁止状态升级：

- 不得从 NV01 artifact 直接得出 `ready_for_robot_execution`。
- 不得从 K01 artifact 直接得出正式 WPS/PQR 或真实焊接质量结论。
- 不得从 `ready_for_simulation_replay_package_design` 直接得出 `ready_for_policy_training`。
- 不得把 `blocked_by_missing_isaac_runtime` 写成项目失败；它只是当前本地没有重运行时。

## 10. 错误处理

第一版错误处理应保持简单：

1. 缺少 source demo pack 时，命令默认自动生成默认 demo pack。
2. 缺少 `docs/焊接工艺数据库主要参数表.xlsx` 时应失败，因为 K01 是 NV01 的前置知识合同源。
3. Excel 字段表结构无法解析、字段数不符合预期或缺少关键列时应失败，避免生成不可信合同。
4. 某个任务缺 canonical artifact 时，该任务进入 blocked 状态，整体 summary 保留其他任务结果。
5. 缺人填字段、真实 URDF、真实 TCP 标定、工件坐标系测量、传感器标定或质量反馈时，不抛异常；写入 validation report 和 readiness boundary。
6. artifact 引用不一致时应失败，因为这会破坏证据可审计性。
7. Isaac Sim 未安装不应导致失败，因为 NV01 第一版不运行 Isaac Sim。

## 11. 测试策略

新增测试应覆盖：

1. NV01 命令能生成顶层 K01 + NV01 JSON/Markdown artifact。
2. `weld_procedure_knowledge_contract.json` 从 Excel 生成，字段数为 47，类别数为 8，requirement summary 为 21 必填、12 条件必填、14 补充/可选。
3. 字段定义包含 `requirement_level`、`acquisition_mode`、`a02_target_path`、`nv01_usage` 和 `blocks`。
4. `weld_procedure_validation_report.json` 能区分人填缺口、条件必填缺口、系统计算字段、仿真推导字段和真实工站回采缺口。
5. `procedure_to_nv01_mapping_matrix.json` 能把工艺字段映射到 `ManipulationSkillAsset`、OpenUSD process metadata、Isaac replay、domain randomization 和 training readiness。
6. 输出能覆盖默认 2 个 demo task。
7. `openusd_scene_manifest.json` 包含 root prim、robot/workpiece/weld task/sensor/safety prim plan 和 procedure parameter bindings。
8. `isaac_sim_replay_config.json` 明确写出 `blocked_by_missing_isaac_runtime` 或等价 runtime boundary。
9. `domain_randomization_recipe.json` 包含焊接有效扰动，且扰动项能追溯到 K01 procedure fields。
10. `training_readiness_report.json` 默认状态为 `not_ready_for_policy_training`，并列出 procedure contract gates。
11. 所有 NVIDIA-oriented artifact 都能追溯到 `ManipulationSkillAsset` 或 Demo Evidence Pack artifact。
12. 每个 `task-<unit-id>/` 目录都包含 `skill_asset_ref.json`、`weld_procedure_parameter_set.json`、`weld_procedure_validation_report.json`、`openusd_task_manifest.json`、`isaac_replay_task_config.json`、`sensor_and_annotation_manifest.json` 和 `training_task_readiness.json`。
13. README/details/仿真路线文档中的路线表述与 K01 + NV01 一致。
14. 现有 `asset_report` 和 `demo_report` 测试继续通过。

## 12. 文档更新

本阶段需要同步更新：

- `README.md`：增加 K01 焊接工艺知识合同与 NVIDIA-native physical AI 底座路线。
- `details.md`：记录 2026-06-23 路线判断变化，并把下一步建议改为 K01 + NV01。
- `docs/simulation/README.md`：从旧的候选仿真路线更新为 OpenUSD/Isaac 主底座路线。
- `docs/simulation/robot-like-simulation-route.md`：更新 R 层角色、决策矩阵和第一轮验证建议。
- `docs/architecture/module-boundaries.md`：补充 K01 和 NVIDIA adapter 边界，明确 Excel/K01/OpenUSD/Isaac 都不能替代 `ManipulationSkillAsset`。
- `weld-experience-engine/README.md`：说明 NV01 是下一阶段目标，不是当前默认 runtime。
- `README.html`、`details.html`：从 Markdown 同步刷新阅读副本。

## 13. 成功标准

本阶段完成时应满足：

1. NV01 spec 已修订为 K01 + NV01，并通过 spec review。
2. README、details、simulation docs、module boundary docs 和 engine README 已同步到 K01 + NVIDIA-native 路线。
3. 文档明确表达 Excel 字段表是焊接工艺知识合同源，OpenUSD/Isaac Sim/Isaac Lab 是未来真实仿真训练闭环主底座。
4. 文档同时明确 A02 canonical truth 仍是 `ManipulationSkillAsset`、工艺知识合同和证据链。
5. 文档明确当前不生成正式 WPS/PQR、不引入 Isaac Sim 默认依赖、不训练模型、不宣称真实机器人执行。
6. 下一阶段 implementation plan 可以直接围绕 `nvidia_digital_twin_report`、K01 procedure payload、NV01 manifest/report payload、测试和文档展开。

## 14. 后续阶段路线

NV01 之后建议按以下顺序推进：

1. **K01 + NV01-A：Procedure-Constrained Manifest Evidence Pack**：从 Excel 生成 procedure knowledge contract、parameter set、validation report，再生成 OpenUSD/Isaac-oriented manifest、randomization recipe 和 training readiness report。

2. **NV01-B：OpenUSD Authoring Spike**：在可选依赖下尝试写出最小 `.usda` stage，优先保证 frames、prim path、semantic label 和 evidence binding 正确。

3. **NV01-C：Isaac Sim Replay Spike**：在外部 Isaac Sim 环境中导入 stage/manifest，跑 1 个任务的 TCP trajectory replay、基础 collision/reachability 检查和传感器视野检查。

4. **NV02：Replicator Synthetic Welding Perception Dataset**：使用 Isaac Sim/Replicator 生成焊缝检测、轮廓、关键点和遮挡/烟尘/反光增强数据。

5. **NV03：Isaac Lab Training Environment Design Review**：基于 observation/action/reward/randomization 合同，设计受约束局部位姿修正或 seam tracking 策略训练环境。

6. **NV04：Real Calibration and Expert-Gated Sim-to-Real Loop**：接入真实 TCP/tool/workpiece/sensor 标定、真实或脱敏工站回放和专家审查结论，让训练闭环开始面对真实误差。

Cosmos、Nucleus、Isaac ROS 和 Jetson/边缘部署应分别进入更后续阶段：前者用于长尾数据增强，Nucleus 用于企业资产协同，Isaac ROS/Jetson 用于真实工位推理部署。它们都不应抢在 NV01 的数字孪生包合同之前成为默认主线。
