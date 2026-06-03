# SyntheticSkillDataset v2 输入规范与船舶焊接任务分类框架 — 设计 Spec

日期：2026-06-02
版本：v0.1
适用项目：A02 焊接技能大师平台
阶段：资料底座 gate 通过后，进入 `SyntheticSkillDataset v2` 小批量生成前

---

## 0. 结论先行

下一阶段不应直接生成 `SyntheticSkillDataset v2` 样本。应先建立一个面向生成的输入规范：

```text
船舶焊接任务分类框架
-> 行业标准关键字段覆盖
-> 字段来源/假设/验证状态映射
-> 仿真生成输入
-> SyntheticSkillDataset v2 小批量样本
```

本 spec 推荐采用 **任务分类框架 + 字段来源映射** 的方案。它比单纯列 3 个 ready 任务族更稳，也比直接做 WPS/PQR 模板更符合当前阶段边界。

第一版要解决的问题不是“完整综述焊接行业知识”，而是回答：

1. 船舶焊接任务如何分类，哪些任务可进入仿真生成，哪些暂缓。
2. 行业标准和工艺文件中哪些关键字段必须被数据结构覆盖。
3. 每个字段来自公开资料、公开数据集、项目内部资料、仿真假设，还是必须后续真机/工艺评定验证。
4. 如何把这些字段转成 `SyntheticSkillDataset v2` 的生成输入，而不把仿真数据说成真实质量验证。

---

## 1. 已确认关键决策

1. 本阶段直接服务 `SyntheticSkillDataset v2` 输入规范，不做百科式行业综述。
2. 先建立更宽的船舶焊接任务分类框架，再从框架中选择第一批生成任务。
3. 第一批生成仍优先落在资料底座已标记 ready 的 3 个任务族：
   - `stiffened-panel-fillet`
   - `panel-butt`
   - `micro-panel-web-bulkhead`
4. `double-bottom-inner-fillet` 和更复杂任务保留在分类框架中，但不进入第一批生成。
5. 标准对齐采用混合口径：
   - schema 命名尽量使用国际通用表达，便于论文、专利、开放数据和仿真系统复用。
   - 中文解释和任务语境贴近国内船舶制造、船级社审查和工艺文件习惯。
6. 标准对齐做到字段 + 来源映射级，不直接做准 WPS/PQR 模板。
7. 本阶段仍然不纳入熔池图像、熔池控制或焊中闭环路线。

---

## 2. 背景与当前缺口

当前项目已经完成：

- 经验结构化 POC。
- 技能迁移 MVP。
- 仿真优先知识闸门。
- Manifest-first 资料底座 gate。

资料底座已经沉淀：

- 20 条资料来源。
- 6 个公开数据集。
- 字段覆盖矩阵。
- 4 个任务证据条目，其中 3 个 ready。
- `docs/data-foundation/reports/synthetic_skilldataset_v2_plan_input.md` 作为下一步规划输入。

但这些产物仍然偏资料 gate 和证据报告，还没有形成正式的 synthetic 样本生成输入规范。尤其缺少：

- 宽任务分类框架与第一批生成任务之间的关系。
- 行业标准关键字段和现有 `WeldCondition` / `SkillSample` / `SimulationScenarioSpec` 的对应关系。
- 参数字段、质量字段、假设字段和后续真实验证字段的统一证据角色。
- 面向仿真生成的输入结构、变体规则和 gate。

---

## 3. 范围边界

### 3.1 本阶段做什么

- 定义船舶焊接任务分类框架。
- 定义标准关键字段集 `WeldProcedureFieldSet`。
- 定义字段来源与证据角色 `EvidenceBinding`。
- 定义仿真生成输入 `SimulationInputSpec`。
- 定义 `SyntheticSkillDatasetV2PlanInput`。
- 规定第一批生成任务的选择规则和暂缓规则。
- 规定 gate，防止把公开资料、仿真假设或 synthetic 标签写成真实质量结论。

### 3.2 本阶段不做什么

- 不生成批量 `SyntheticSkillDataset v2` 样本。
- 不下载公开大数据集。
- 不做生产级数据库或平台界面。
- 不实现真实机器人控制、焊机控制或现场采集接口。
- 不把输入规范写成真实 WPS/PQR。
- 不声称任何 synthetic 样本通过真实焊接质量验证。
- 不纳入熔池图像、熔池形态识别、熔池控制或焊中闭环自适应。

---

## 4. 方案取舍

### 4.1 方案 A：轻量任务字段表

做法：只列任务族、接头、位置、坡口、电参、质量标签等字段。

优点：

- 快速。
- 容易进入实现。

问题：

- 字段来源不清楚。
- 标准对齐弱。
- 后续 synthetic 样本容易变成“看似合理但证据不清”的数据。

### 4.2 方案 B：任务分类框架 + 字段来源映射

做法：先定义船舶焊接任务分类，再为关键字段绑定来源、证据角色、假设和后续验证状态。

优点：

- 能服务仿真生成。
- 能覆盖行业标准关键字段。
- 能保留来源追溯和边界。
- 能解释为什么第一批选 3 个 ready 任务，而不是只做几个孤立场景。

问题：

- schema 比轻量字段表更严格。

结论：**推荐采用。**

### 4.3 方案 C：准 WPS/PQR 输入模板

做法：把输入规范设计成接近真实工艺规程和工艺评定记录。

优点：

- 长期产品化价值高。

问题：

- 当前没有真实焊材、工艺评定、焊后检测和船级审查证据。
- 容易让人误解为 synthetic 样本已经具备真实工艺合格意义。
- 会把当前阶段过早推向合规和验收模板。

结论：暂不采用，但预留字段扩展。

---

## 5. 船舶焊接任务分类框架

第一版 `TaskTaxonomy` 不只覆盖 ready 任务，还要覆盖路线图任务。任务分类至少包含以下维度：

| 维度 | 字段建议 | 说明 |
| --- | --- | --- |
| 船舶制造阶段 | `manufacturing_stage` | panel line / subassembly / block assembly / erection 等 |
| 焊接对象 | `weld_object` | stiffener-to-panel、panel butt、bulkhead web、double bottom inner fillet 等 |
| 接头形式 | `joint_type` | butt / fillet / tee / lap / groove / complex |
| 焊接位置 | `weld_position` | flat / horizontal / vertical-up / overhead / multi-position |
| 坡口和边界 | `groove_geometry` | V/X/K/none、root gap、bevel angle、land 等 |
| 层道结构 | `layer_pass` | single pass / multi-pass / multi-layer，占位到足够承接后续工艺 |
| 空间可达性 | `access_context` | open panel / confined compartment / internal cell / curved surface |
| 运动结构 | `motion_structure` | single seam / seam list / multi-short-seam / curved seam |
| 当前处置 | `readiness` | ready_for_synthetic_v2_plan / needs_more_sources / defer |
| 复杂度 | `modeling_difficulty` | easy / medium / hard |

### 5.1 第一版任务族

| family_id | 分类定位 | 当前处置 | 说明 |
| --- | --- | --- | --- |
| `stiffened-panel-fillet` | 面板线/小组立，加筋板或纵骨角焊 | `ready_for_synthetic_v2_plan` | 第一批生成任务，几何和运动较可控 |
| `panel-butt` | 平面板拼接/简化对接焊 | `ready_for_synthetic_v2_plan` | 第一批生成任务，可承接现有 straight-flat 能力，但需区分船舶板拼 |
| `micro-panel-web-bulkhead` | 微型面板、腹板、隔板多短焊缝 | `ready_for_synthetic_v2_plan` | 第一批生成任务，用于验证多焊缝序列 schema |
| `double-bottom-inner-fillet` | 双层底/双壳内部角焊 | needs_more_sources | 保留任务框架，暂不生成样本 |
| `vertical-overhead-hull-weld` | 立向/仰位船体焊缝 | defer | 作为位置复杂度路线图 |
| `thick-plate-groove-multipass` | 厚板坡口多层多道 | defer | 保留 WPS/PQR 扩展位，第一批只做字段占位 |
| `curved-spatial-complex-weld` | 曲面与空间复杂焊缝 | defer | 暂不进入 synthetic v2 第一批 |

---

## 6. 行业标准关键字段集

第一版定义 `WeldProcedureFieldSet`，用于覆盖行业标准和工艺文件中常见的关键信息。它不是 WPS/PQR，但要能承接 WPS/PQR 的主要字段。

### 6.1 任务与接头字段

| 字段 | 说明 | 第一版用途 |
| --- | --- | --- |
| `welding_process` | GMAW / FCAW / SAW / manual / hybrid 等 | synthetic v2 必填或显式 unknown |
| `joint_type` | 对接、角接、T 型、搭接、坡口等 | 任务分类和仿真几何 |
| `weld_position` | 平焊、横焊、立焊、仰焊等 | 任务筛选和姿态约束 |
| `weld_object` | 船舶构件和焊缝对象 | 船舶语境约束 |
| `manufacturing_stage` | 制造阶段 | 防止脱离船舶制造任务 |

### 6.2 几何与材料字段

| 字段 | 说明 | 第一版用途 |
| --- | --- | --- |
| `base_material` | 母材类别或占位 | 第一版可 unknown，但需保留 |
| `plate_thickness_mm` | 板厚 | 允许假设，但必须标注 |
| `groove_geometry` | 坡口类型、角度、间隙、钝边等 | panel-butt 必须覆盖 |
| `leg_size_mm` | 角焊缝焊脚尺寸 | stiffened-panel-fillet 假设字段 |
| `root_gap_mm` | 根部间隙 | panel-butt 假设字段 |
| `seam_length_mm` | 焊缝长度 | 仿真轨迹生成 |
| `weld_seam_list` | 多短焊缝列表 | micro-panel-web-bulkhead 假设字段 |

### 6.3 工艺参数字段

| 字段 | 说明 | 第一版用途 |
| --- | --- | --- |
| `current` | 电流 | 参数曲线或范围，占位需标注来源 |
| `voltage` | 电压 | 参数曲线或范围，占位需标注来源 |
| `wire_feed` | 送丝速度 | 可选参数曲线 |
| `travel_speed` | 行走速度 | 运动和热输入占位的核心字段 |
| `heat_input_placeholder` | 热输入占位 | 第一版只做可计算占位，不做真实合规判断 |
| `shielding_gas` | 保护气体 | 第一版可 unknown，预留 WPS 扩展 |
| `filler_material` | 焊材 | 第一版可 unknown，预留 WPS 扩展 |

### 6.4 运动与姿态字段

| 字段 | 说明 | 第一版用途 |
| --- | --- | --- |
| `trajectory` | TCP 轨迹 | synthetic 样本核心字段 |
| `robot_pose` | 姿态或机器人位姿 | 姿态约束和可达性占位 |
| `torch_angle` | 工作角/行进角等 | 角焊、面板线任务核心字段 |
| `motion_template` | 直线、摆动、多短焊缝序列等 | 技能包提取和迁移 |
| `sequence_order` | 多焊缝顺序 | micro-panel-web-bulkhead 假设字段 |
| `node_transition` | 节点过渡 | 多短焊缝任务占位 |

### 6.5 质量与检查字段

| 字段 | 说明 | 第一版用途 |
| --- | --- | --- |
| `quality_label` | 质量标签或占位 | 只能作为仿真评分、公开标签词汇或待验证占位 |
| `defect_label` | 缺陷词汇 | 来自公开数据集和缺陷资料 |
| `inspection_reference` | 检查参考 | 标准/资料入口，不替代验收 |
| `requires_real_validation_later` | 后续真实验证标记 | 所有涉及真实质量的字段必须可标注 |

---

## 7. 字段来源与证据角色

定义 `EvidenceBinding`，绑定字段、来源和证据角色。

### 7.1 证据角色

| 角色 | 说明 |
| --- | --- |
| `shipbuilding_case` | 船舶自动化或船厂公开案例，用于任务存在性和场景边界 |
| `public_process_reference` | 公开工艺资料或标准入口，用于字段和参数约束 |
| `public_dataset_schema` | 公开数据集，用于 schema、模态和标签词汇参考 |
| `project_internal` | 项目内部规划，用于项目字段和需求边界 |
| `simulation_assumption` | 当前仿真生成需要的假设字段 |
| `simulation_output` | 由仿真生成的轨迹、参数曲线或标签 |
| `requires_real_validation_later` | 后续需要真机、WPS、PQR、检测或人工审查验证 |

### 7.2 绑定规则

- 每个 synthetic v2 关键字段必须至少有一个 `EvidenceBinding`。关键字段指 `WeldProcedureFieldSet` 中的字段、`SimulationInputSpec` 顶层业务字段，以及 gate 明确要求的字段；`input_id`、`taxonomy_ref`、`evidence_bindings` 这类索引/元数据字段不需要自绑定，普通说明字段和纯报告文本也不需要逐项绑定。
- 所有参数值必须区分来源：
  - 公开资料约束。
  - 公开数据集 schema 线索。
  - 项目内部定义。
  - 仿真假设。
  - 仿真输出。
- 任何质量相关字段默认必须包含 `requires_real_validation_later`，除非它只是纯粹的标签词汇。
- 公开数据集可以提供 schema、模态、标签词汇和 benchmark 参考，不直接证明船舶焊接质量。
- 标准入口可以提供字段覆盖和后续合规验证方向，不替代标准正文、客户 WPS 或船级审查。

### 7.3 最小结构

第一版 `EvidenceBinding` 至少包含：

| 字段 | 说明 |
| --- | --- |
| `field_path` | 被绑定的字段路径，例如 `procedure_fields.joint_type` |
| `source_id` | 来源编号，对应资料底座 manifest；仿真输出可使用内部生成来源编号 |
| `evidence_role` | 证据角色，取自 7.1 |
| `value_status` | 值状态：`constrained` / `assumed` / `generated` / `unknown` / `requires_real_validation_later` |
| `notes` | 使用边界或假设说明 |

同一字段允许多个绑定。例如 `current` 可以同时绑定公开工艺资料、公开数据集 schema 和 `requires_real_validation_later`。

---

## 8. 仿真生成输入规范

定义 `SimulationInputSpec`，作为 `SyntheticSkillDataset v2` 生成器的输入。

### 8.1 顶层字段

| 字段 | 说明 |
| --- | --- |
| `input_id` | 输入编号 |
| `taxonomy_ref` | 对应 `TaskTaxonomy` 的 `family_id` |
| `procedure_fields` | 标准关键字段集 |
| `geometry_spec` | 焊缝、坡口、板厚、焊脚、焊缝列表等 |
| `motion_spec` | 轨迹、姿态、运动模板、多焊缝顺序等 |
| `process_spec` | 电流、电压、送丝、行走速度等 |
| `quality_spec` | 仿真评分、标签占位、缺陷词汇、后续验证标记 |
| `variant_policy` | 样本变体规则 |
| `evidence_bindings` | 字段来源与证据角色 |
| `generation_boundary` | 不可声称事项和后续验证要求 |

### 8.2 变体规则

第一版只允许小批量、可解释的变体：

- `length_variation`：焊缝长度变化。
- `width_or_gap_variation`：坡口宽度、根部间隙或焊脚假设变化。
- `speed_variation`：行走速度变化。
- `torch_angle_variation`：焊枪角度小范围变化。
- `sequence_variation`：多短焊缝顺序和节点过渡变化。

暂不允许：

- 任意曲面焊缝自动生成。
- 高复杂多层多道完整填充规划。
- 真实质量合格/不合格判定。
- 熔池图像、熔池控制或焊中闭环标签。

---

## 9. 第一批 synthetic v2 任务选择

### 9.1 选择规则

第一批任务必须满足：

1. 位于船舶制造任务分类框架中。
2. `readiness = ready_for_synthetic_v2_plan`。
3. 关键字段在 `WeldProcedureFieldSet` 中有定义。
4. 每个关键字段有 `EvidenceBinding`。
5. 假设字段显式标注为 `simulation_assumption`。
6. 质量相关字段显式标注 `requires_real_validation_later`。
7. 不依赖真实 WPS/PQR、真机采集或熔池路线。

### 9.2 第一批建议

| family_id | 首批定位 | 生成重点 |
| --- | --- | --- |
| `stiffened-panel-fillet` | P1 | 面板线角焊、焊枪角度、行走速度、焊脚假设 |
| `panel-butt` | P1 | 板拼对接、坡口/间隙、直线轨迹、电参占位 |
| `micro-panel-web-bulkhead` | P2 | 多短焊缝列表、顺序、节点过渡、姿态占位 |

### 9.3 暂缓任务

| family_id | 暂缓原因 |
| --- | --- |
| `double-bottom-inner-fillet` | 狭小空间、可达性和姿态切换证据不足 |
| `vertical-overhead-hull-weld` | 位置复杂度高，需要更强工艺和姿态约束 |
| `thick-plate-groove-multipass` | 接近 WPS/PQR 和多层多道规划，当前不宜直接生成 |
| `curved-spatial-complex-weld` | 曲面拓扑和空间复杂度超出第一版 |

---

## 10. 与现有代码和资料的关系

本 spec 不替换现有资料底座，而是在其上新增一层生成输入规范。

现有对象关系：

```text
docs/data-foundation/manifests/*
-> DataFoundation
-> TaskEvidenceEntry
-> SyntheticSkillDataset v2 plan input
```

后续新增对象关系：

```text
TaskTaxonomy
WeldProcedureFieldSet
EvidenceBinding
SimulationInputSpec
SyntheticSkillDatasetV2PlanInput
-> SkillDataset
-> WeldSkillPackage
-> TransferExperiment
```

建议保持：

- `docs/data-foundation/` 继续作为资料底座。
- `weldcore.knowledge` 继续负责资料、任务和证据 gate。
- `weldcore.sim` 负责仿真生成。
- `weldcore.model.skill` 继续承接 `SkillDataset` 和 `SkillSample`。
- `weldcore.transfer` 继续承接技能包提取和迁移评测。

---

## 11. Gate 设计

### 11.1 分类 gate

- 每个 synthetic v2 输入必须引用一个存在的 `TaskTaxonomy.family_id`。
- `family_id` 必须有 `readiness`。
- 第一批生成只允许 `ready_for_synthetic_v2_plan`。
- `defer` 和 `needs_more_sources` 只能进入报告和路线图，不进入样本生成。

### 11.2 标准字段 gate

- 每个任务输入必须覆盖：
  - `joint_type`
  - `weld_position`
  - `weld_object`
  - `welding_process`
  - `geometry_spec`
  - `motion_spec`
  - `process_spec`
  - `quality_spec`
- 如果字段未知，必须显式写 `unknown` 或 `requires_real_validation_later`，不能静默缺失。

### 11.3 来源绑定 gate

- 每个关键字段必须有来源绑定。
- 每个 `simulation_assumption` 必须出现在输出报告中。
- 所有质量字段必须说明：
  - 公开标签词汇。
  - 仿真评分。
  - 或后续真实验证占位。
- 禁止把公开数据集标签写成本项目真实质量结果。

### 11.4 禁止字段 gate

当前 JSON/CSV 生成输入不得包含熔池图像、熔池形态、熔池控制或焊中闭环字段。相关内容如被提及，只能出现在 Markdown 边界说明中，表达为“本阶段不纳入”。

---

## 12. 报告设计

后续 `synthetic_v2_input_report` 应输出：

- 任务分类表。
- 标准关键字段覆盖表。
- 字段来源绑定表。
- 第一批 synthetic v2 输入清单。
- 暂缓任务和暂缓原因。
- 假设字段清单。
- 后续真实验证字段清单。

报告结论必须包含：

- 本报告是 synthetic 数据生成输入规范。
- 本报告不是 WPS/PQR。
- 本报告不证明真实焊接质量。
- 第一批 synthetic 样本只能用于结构化、迁移和评测机制验证。

---

## 13. 成功标准

设计进入实施计划前，必须满足：

- 任务分类框架覆盖 `ready_for_synthetic_v2_plan`、`needs_more_sources`、`defer` 三类任务。
- 字段集覆盖行业标准和工艺文件中的关键字段。
- 第一批任务能从宽分类框架中被解释性选出。
- 所有关键字段都有来源/假设/验证状态。
- 质量相关字段不会被误写成真实质量结论。
- `SimulationInputSpec` 能直接指导后续生成器实现。
- 现有 `SkillDataset`、`WeldSkillPackage`、`TransferExperiment` 链路不被替换。
- 本阶段仍排除熔池路线。

---

## 14. 后续实施计划入口

用户审核本 spec 后，下一步应进入 implementation plan。计划建议拆成 6 个任务：

1. 先完成 `SyntheticSkillDataset v2` 输入规范前置调研，汇总船舶焊接任务分类、焊缝/接头/位置/坡口/层道、工艺参数、质量缺陷词汇、公开数据集 schema 和仿真路线约束，并形成字段差距矩阵。
2. 新增 `TaskTaxonomy`、`WeldProcedureFieldSet`、`EvidenceBinding` 数据模型。
3. 从现有资料底座 manifest 和前置调研产物派生第一版输入规范 manifest。
4. 新增 `SimulationInputSpec` loader 和 gate。
5. 新增 synthetic v2 输入报告。
6. 更新 `details.md` 和 README，说明当前完成的是输入规范，不是 synthetic v2 批量生成。
