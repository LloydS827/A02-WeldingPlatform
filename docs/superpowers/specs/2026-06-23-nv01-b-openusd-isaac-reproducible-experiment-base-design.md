# NV01-B OpenUSD / Isaac Sim 可复现实验底座设计

日期：2026-06-23

## 1. 背景

A02 当前已经从“焊接技能大师平台”收束为“机器人技能大师能力的焊接技能资产底座”。主线对象是 `ManipulationSkillAsset`，并已能把 `SimulationEvidenceBundle`、真实 URDF、nominal robot context、scene context、lightweight feasibility、expert review record、A01/B06 mapping 和 IP support matrix 汇总为可审查 evidence pack。

上一阶段 K01 + NV01-A 已完成 `Procedure-Constrained Manifest Evidence Pack`：

- 从 `docs/焊接工艺数据库主要参数表.xlsx` 生成 K01 焊接工艺知识合同。
- 为默认 demo evidence pack 生成 `WeldProcedureParameterSet`、`WeldProcedureValidationReport` 和 `ProcedureToNV01MappingMatrix`。
- 输出 `weld_skill_digital_twin_package`、`openusd_scene_manifest`、`isaac_sim_replay_config`、`domain_randomization_recipe`、`training_readiness_report` 和 `nvidia_stack_alignment_matrix`。
- 明确状态是 `ready_for_simulation_replay_package_design` / `ready_for_training_design_review`，不是 Isaac Sim runtime 验证、policy training、正式 WPS/PQR 或真实机器人可执行。

因此 NV01-B 不应跳到策略训练，也不应把 Isaac Sim、OpenUSD SDK、Nucleus 或 Isaac Lab 作为默认依赖。更合适的下一步是把 NV01-A 的 JSON manifest/report 推进为一个**可复现实验底座**：新读者可以运行默认命令，得到可解析的最小 `.usda` stage、Isaac replay fixture、K01 参数到仿真参数的审计映射、传感器与标注清单，以及一个明确说明“哪些字段缺失会阻塞真实仿真”的自动报告。

## 2. 目标

本阶段主题是：

```text
NV01-B OpenUSD / Isaac Sim Reproducible Experiment Base
```

目标是在不引入重运行时依赖的前提下，把当前 K01 + NV01-A 输出推进到以下可复跑 artifact：

1. **最小 OpenUSD `.usda` stage authoring 原型**：包含 `/World`、robot、workpiece、weld task、seam path、TCP trajectory candidate、sensor placeholder、safety boundary 和 procedure metadata。
2. **USD artifact validation gate**：检查 `.usda` 文件存在、关键 prim 路径存在、customData / metadata 中保留 K01 contract refs、parameter refs、canonical demo refs 和 readiness boundary。
3. **Isaac replay fixture**：从 `isaac_sim_replay_config` 派生可审查的 replay fixture JSON，描述 robot asset、stage path、trajectory source、TCP frame、tool frame、step timing、parameter bindings 和当前 blocked reasons。
4. **K01 参数到仿真参数的可审计映射**：把 K01 字段、A02 target、USD metadata path、Isaac replay parameter、domain randomization usage 和 blocking scope 汇总到 per-task / top-level report。
5. **传感器与标注清单**：列出相机、TCP trace、seam annotation、procedure overlay、质量/缺陷标签占位和缺失真实标定。
6. **阻塞字段自动报告**：明确哪些字段缺失会阻塞 `real_isaac_sim_replay`、`sensor_simulation`、`replicator_dataset`、`policy_training`、`expert_review` 或 `wps_pqr_release`。

成功标准：

- 默认命令可以生成 NV01-A source pack 和 NV01-B experiment base。
- 默认验证不需要 Isaac Sim、OpenUSD SDK 或 GPU。
- 输出中有真实 `.usda` 文本文件，但只要求静态结构可验证，不宣称已经被 Isaac Sim 打开运行。
- 缺失真实 TCP/tool/workpiece/sensor 标定、H300 工站日志、电流/电压、WPS/PQR、专家审查和质量反馈时，报告必须阻塞真实仿真或训练，不允许用默认值伪造 ready。
- README、details 和 engine README 同步说明新入口、产物和边界。

## 3. 关键假设

1. A02 的 canonical truth 仍是 `ManipulationSkillAsset` 和 K01 procedure contract；USD / Isaac artifact 是可消费输出，不反向替换 A02 本体。
2. NV01-B 只覆盖 1-2 个默认 demo 任务，沿用现有 `demo_report` 默认任务，不扩大任务族。
3. `.usda` 第一版采用 ASCII 文本 authoring，使用最小合法结构和 `customData` 保存审计 metadata；不依赖 `pxr` Python 包。
4. USD validation 第一版做静态文本/JSON gate：关键 prim、refs、metadata、blocked reason、source refs 必须存在。正式 USD parser validation 放到 NV01-C 或 OpenUSD SDK 可用环境。
5. Isaac replay fixture 是 Isaac Sim script / extension 的输入合同，不是当前运行结果。
6. 真实 robot USD asset conversion、collision validation、sensor calibration、Replicator dataset 和 Isaac Lab training 都是后续阶段输入，不能在 NV01-B 中伪装完成。

## 4. 方案比较

### 方案 A：只补 OpenUSD 文档

只在 README/details 中说明下一阶段如何接 OpenUSD / Isaac Sim。

优点：改动最小。

缺点：无法形成可复跑 artifact，也不能验证 K01 字段、canonical refs 和 USD/Isaac fixture 是否持续一致。

### 方案 B：最小可复现实验底座

新增轻量 builder/report：基于 NV01-A artifact 写出 `.usda` 原型、replay fixture、sensor/annotation manifest、parameter mapping audit 和 blocking report，并配套静态 validation gate。

优点：形成真实可复跑输出，能持续约束后续 Isaac Sim 集成；范围仍然可控，不引入重依赖。

缺点：不能证明 Isaac Sim runtime 已经打开 stage 或完成 replay，只能证明输入合同和静态 authoring 已准备好。

### 方案 C：完整 Isaac Sim runtime spike

安装/调用 Isaac Sim，导入机器人，打开 USD stage，执行 trajectory replay 并产出传感器数据。

优点：最贴近最终目标。

缺点：依赖 GPU、系统版本和 Isaac Sim 安装，容易让默认仓库不可复跑；当前缺真实标定和工站数据，过早 runtime 只能得到环境工程结果，不能得到可信焊接仿真结论。

本阶段采用 **方案 B**。

## 5. 输出契约

新增默认命令建议为：

```bash
cd weld-experience-engine
uv run python -m weldcore.skill_asset.nv01_b_experiment_base_report \
  --outdir artifacts/demo/nv01-b-experiment-base
```

如果未传入 `--source-nv01a-dir`，命令应在输出目录下生成或复用 `_source_nv01a/`：

```text
artifacts/demo/nv01-b-experiment-base/
├── nv01_b_summary.md
├── nv01_b_summary.json
├── openusd_stage.usda
├── openusd_stage_validation_report.json
├── isaac_replay_fixture.json
├── procedure_sim_parameter_audit.json
├── sensor_annotation_manifest.json
├── simulation_blocking_report.json
├── experiment_reproducibility_manifest.json
├── _source_nv01a/
│   └── ... K01 + NV01-A artifacts ...
└── task-<unit-id>/
    ├── openusd_task_stage_fragment.usda
    ├── isaac_replay_task_fixture.json
    ├── procedure_sim_parameter_audit.json
    ├── sensor_annotation_manifest.json
    └── simulation_blocking_report.json
```

### 5.1 `openusd_stage.usda`

第一版 `.usda` 必须包含：

- `#usda 1.0`
- `def Xform "World"`
- `def Xform "Robot"`
- `def Xform "Workpiece"`
- `def Xform "WeldTasks"`
- 每个 task 一个 `def Xform "<sanitized_task_id>"`
- 每个 task 下包含 `SeamPath`、`TcpTrajectoryCandidate`、`Torch`、`Sensors`、`SafetyBoundary`
- `customData` 中至少包含：
  - `a02:report_id`
  - `a02:procedure_contract_ref`
  - `a02:procedure_parameter_set_ref`
  - `a02:skill_asset_ref`
  - `a02:robot_body_asset_ref`
  - `a02:scene_context_asset_ref`
  - `a02:readiness_boundary`
  - `a02:not_ready_reasons`

第一版 `.usda` 的 `customData` key 以静态 gate 可验证的 USDA 文本约定为准，不宣称已经通过 OpenUSD SDK schema validation。

最小 schema 必须能稳定验收“焊缝 / 工件 / 焊枪 / 轨迹 / 安全边界”五类对象：

| Prim | 最小属性或 customData | 单位 / frame | source ref |
| --- | --- | --- | --- |
| `/World/Workpiece` | `a02:workpiece_frame`、`a02:workpiece_geometry_status`、`a02:scene_context_asset_ref` | `workpiece_frame`，长度单位 `mm` | `scene_context_asset_report.json` |
| `/World/WeldTasks/<task>/SeamPath` | `a02:seam_path_ref`、`a02:point_count`、`a02:path_units`、`a02:frame_ref` | `mm`，默认 `workpiece_frame` | `scene_context_asset_report.json` |
| `/World/WeldTasks/<task>/TcpTrajectoryCandidate` | `a02:trajectory_ref`、`a02:trajectory_units`、`a02:sample_count`、`a02:tcp_frame_ref` | `mm` / `s`，默认 `tool_tcp_frame` | `skill_asset_report.json` |
| `/World/WeldTasks/<task>/Torch` | `a02:torch_frame_ref`、`a02:tool_frame_ref`、`a02:torch_geometry_status`、`a02:procedure_parameter_set_ref` | `tool_frame` / `tool_tcp_frame` | `robot_context_spec.json`、`weld_procedure_parameter_set.json` |
| `/World/WeldTasks/<task>/Sensors` | `a02:sensor_manifest_ref`、`a02:sensor_layout_status`、`a02:required_calibration` | sensor frames pending calibration | `sensor_annotation_manifest.json` |
| `/World/WeldTasks/<task>/SafetyBoundary` | `a02:safety_boundary_ref`、`a02:boundary_status`、`a02:collision_validation_status` | `workpiece_frame`，长度单位 `mm` | `scene_context_asset_report.json`、`robot_feasibility_result.json` |

第一版不要求真实 mesh、材质、physics schema 或 articulation schema；这些进入 NV01-C。

### 5.1.1 Canonical status vocabulary

NV01-B 新增 artifact 应统一使用以下状态 token：

| Token | 用途 |
| --- | --- |
| `ready_for_static_openusd_review` | `.usda` 文本已写出并通过静态 prim/ref/metadata gate |
| `blocked_by_openusd_stage_contract_issue` | `.usda` 缺关键 prim、metadata 或 canonical refs |
| `blocked_by_missing_isaac_runtime` | 未运行 Isaac Sim，不能宣称 runtime replay |
| `not_isaac_sim_runtime_validation` | readiness boundary，说明不是 Isaac Sim runtime 验证 |
| `blocked_for_real_isaac_sim_replay` | 缺真实 runtime、标定、工站日志或关键工艺输入，阻塞真实 replay |
| `blocked_by_missing_sensor_calibration` | 缺 sensor layout / calibration，阻塞 sensor simulation / Replicator dataset |
| `blocked_by_missing_real_process_inputs` | 缺电流、电压、工站日志等真实工艺输入 |
| `not_policy_training_result` | readiness boundary，说明不是 Isaac Lab policy training |
| `not_formal_WPS_PQR` | readiness boundary，说明不是正式 WPS/PQR |
| `not_ready_for_robot_execution` | readiness boundary，说明不是机器人可执行结论 |

计划和测试不得新增同义 runtime token。如果消费 NV01-A 或早期草案中的旧 token，应在 NV01-B 输出中归一为上表词汇，同时保留 source artifact ref。

### 5.2 `openusd_stage_validation_report.json`

至少包含：

- `validation_status`
- `stage_ref`
- `required_prim_paths`
- `missing_prim_paths`
- `metadata_checks`
- `canonical_ref_checks`
- `procedure_metadata_checks`
- `not_ready_reasons`
- `readiness_boundary`

默认情况下，关键 prim 和 refs 应通过；runtime 相关项应保留 `not_isaac_sim_runtime_validation`。

### 5.3 `isaac_replay_fixture.json`

至少包含：

- `fixture_id`
- `stage_ref`
- `runtime_target`
- `runtime_status`
- `robot_asset`
- `frame_bindings`
- `trajectory_bindings`
- `procedure_parameter_bindings`
- `task_fixtures`
- `blocked_by`
- `readiness_boundary`

默认 `runtime_status` 应是 `blocked_by_missing_isaac_runtime`，不是 `ready_for_simulation_replay`。

### 5.4 `procedure_sim_parameter_audit.json`

至少包含：

- `audit_id`
- `contract_version`
- `field_count`
- `mappings`
- `mapped_field_count`
- `blocking_field_count_by_scope`
- `source_refs`

每个 mapping 至少包含：

- `field_id`
- `display_name`
- `requirement_level`
- `acquisition_mode`
- `a02_target_path`
- `usd_metadata_path`
- `isaac_replay_parameter`
- `domain_randomization_usage`
- `coverage_status`
- `value_source`
- `blocks`
- `blocking_scopes`
- `source_ref`

`blocking_scopes` 建议按字段 blocks 和 acquisition mode 计算：

- 缺少 `human_required` / `human_confirmed_or_imported` 的必填或条件必填字段：阻塞 `expert_review`，若字段 blocks 包含 `wps_pqr_release` 也阻塞 `wps_pqr_release`。条件必填字段必须同时记录 `condition_unresolved` 或具体 `required_when` 来源，不能当作可选字段忽略。
- 缺少 `workcell_logged` 的关键工艺字段：阻塞 `real_isaac_sim_replay`、`sensor_simulation` 和 `expert_review`。
- 缺少 `system_computed` 所需真实输入：阻塞 `policy_training` 和 `wps_pqr_release`，同时记录 `blocked_by_missing_real_process_inputs`。
- 缺少 sensor calibration / layout：阻塞 `sensor_simulation` 和 `replicator_dataset`。

### 5.5 `sensor_annotation_manifest.json`

至少包含：

- `manifest_id`
- `stage_ref`
- `sensor_placeholders`
- `annotation_layers`
- `required_real_calibration`
- `blocked_by`
- `readiness_boundary`

默认 sensor placeholders 不应超过当前所需最小集合：

- `overview_camera_placeholder`
- `torch_camera_placeholder`
- `tcp_pose_trace`
- `weld_seam_annotation`
- `procedure_parameter_overlay`

### 5.6 `simulation_blocking_report.json`

至少包含：

- `report_id`
- `overall_status`
- `scope_status`
- `blocking_items`
- `missing_fields_by_scope`
- `missing_calibrations`
- `missing_runtime_inputs`
- `next_required_inputs`
- `readiness_boundary`

默认 `overall_status` 应是 `blocked_for_real_isaac_sim_replay` 或更保守状态；同时允许 `openusd_authoring_status=ready_for_static_openusd_review`。

### 5.7 `experiment_reproducibility_manifest.json`

至少包含：

- `manifest_id`
- `source_nv01a_root_ref`
- `source_nv01a_summary_ref`
- `generated_artifacts`
- `command`
- `default_dependency_boundary`
- `source_artifact_refs`
- `validation_commands`

用途是让后续 reviewer 能检查：本轮 NV01-B 是否来自 NV01-A artifact，而不是手写孤立 JSON。

## 6. 数据流

默认数据流：

```text
run_demo_evidence_pack
-> run_nvidia_digital_twin_report (K01 + NV01-A)
-> load NV01-A artifacts
-> build NV01-B task experiment payloads
-> author openusd_stage.usda / task fragments
-> validate static stage contract
-> build Isaac replay fixture
-> build procedure simulation parameter audit
-> build sensor and annotation manifest
-> build simulation blocking report
-> write summary / reproducibility manifest
```

已有 `nvidia_digital_twin_report` 保持不变；NV01-B 新增独立模块消费其输出，避免把 NV01-A 逻辑继续加厚。

## 7. 文件设计

建议新增：

- `weld-experience-engine/weldcore/skill_asset/nv01_b_experiment_base.py`
  - 负责加载 NV01-A artifact、构建 task payload、author `.usda` 文本、构建 replay fixture、parameter audit、sensor manifest、blocking report 和 validation report。
- `weld-experience-engine/weldcore/skill_asset/nv01_b_experiment_base_report.py`
  - CLI/report 入口。
  - 若未传入 `--source-nv01a-dir`，内部调用 `run_nvidia_digital_twin_report` 生成 `_source_nv01a/`。
  - 若显式传入的 `--source-nv01a-dir` 不存在或 artifact 不完整，直接失败并报告缺失项。
  - 写出顶层和 per-task artifacts。
- `weld-experience-engine/tests/test_nv01_b_experiment_base.py`
  - 覆盖 builder、`.usda` authoring、validation gate、parameter audit、blocking report。
- `weld-experience-engine/tests/test_nv01_b_experiment_base_report.py`
  - 覆盖默认 CLI/report artifact 输出和 source refs。

建议修改：

- `README.md`
- `details.md`
- `weld-experience-engine/README.md`
- `README.html`
- `details.html`

不建议修改：

- `procedure_contract.py`，除非发现字段 blocking scope 无法通过现有 payload 推导。
- `nvidia_digital_twin.py`，除非需要补极小 source ref 字段；NV01-B 应优先消费现有输出。
- `pyproject.toml`，本阶段不应新增 OpenUSD/Isaac 依赖。

## 8. 错误处理与边界

- 如果显式传入的 `--source-nv01a-dir` 不存在，应失败并指出缺失目录，不静默生成默认源。
- 如果显式传入的 `--source-nv01a-dir` 存在但缺少必需 NV01-A artifact，应失败并指出缺失文件，不静默生成默认源。
- 如果未传入 source dir，可生成 `_source_nv01a/`，与 NV01-A 的默认自举行为保持一致。
- 如果 K01 字段值缺失，应写入 blocking report，不应补默认工艺参数。
- 如果 `.usda` 静态 gate 失败，summary 应进入 `blocked_by_openusd_stage_contract_issue`。
- 如果 sensor layout / calibration 缺失，不能阻塞静态 USD authoring，但必须阻塞 `sensor_simulation`、`replicator_dataset` 和 `real_isaac_sim_replay`。
- 如果 Isaac Sim runtime 不存在，默认状态仍可生成 fixture，但必须保留 `blocked_by_missing_isaac_runtime` 和 `not_isaac_sim_runtime_validation`。

## 9. 测试策略

测试应聚焦“合同是否稳定”，不是测试外部 Isaac Sim：

1. Builder 测试：
   - 默认从 NV01-A payload 生成 2 个 task payload。
   - `.usda` 包含关键 prim 和 customData refs。
   - replay fixture 保留 stage ref、trajectory refs、procedure bindings 和 blocked reasons。
   - parameter audit 覆盖 47 个 K01 字段，并能识别 `welding_current_a`、`welding_voltage_v`、`heat_input_kj_per_mm`、`wps_number` 等阻塞项。
2. Validation 测试：
   - 完整 stage 通过静态 prim/ref gate。
   - 删除关键 prim 或 metadata 时报告 blocked。
3. Report 测试：
   - 默认命令写出所有顶层 artifact、per-task artifact 和 `_source_nv01a/`。
   - `generated_artifacts` 不包含预先存在的用户文件。
   - 显式 source dir 缺少 artifact 时失败。
4. 文档/边界测试：
   - summary markdown 明确写出不是 Isaac Sim runtime 验证、不是 policy training、不是正式 WPS/PQR、不是真实机器人执行。

相关验证命令：

```bash
cd weld-experience-engine
uv sync --extra dev --extra viz
uv run pytest tests/test_nv01_b_experiment_base.py tests/test_nv01_b_experiment_base_report.py -q
uv run python -m weldcore.skill_asset.nv01_b_experiment_base_report \
  --outdir artifacts/demo/nv01-b-experiment-base
uv run pytest -q
```

## 10. 非目标

- 不安装、封装或强依赖 Isaac Sim。
- 不引入 `pxr` / OpenUSD SDK 默认依赖。
- 不接 Omniverse Nucleus。
- 不导入真实 robot USD asset。
- 不执行 Isaac Sim replay。
- 不生成 Replicator dataset。
- 不训练 Isaac Lab policy。
- 不做真实 collision validation、IK validation、sensor photoreal calibration 或焊接质量验证。
- 不把 K01 参数集写成正式 WPS/PQR。
- 不宣称 `ready_for_robot_execution`。

## 11. 下一阶段衔接

NV01-B 完成后，下一阶段建议进入 **NV01-C Isaac Sim Runtime Import and Static Replay Validation**，但只有在以下输入至少部分具备后再开始：

- 可用 Isaac Sim 环境和版本记录。
- robot USD asset conversion 或可导入 URDF/articulation 方案。
- TCP/tool/workpiece frame 标定样例。
- 最小 sensor layout。
- 1 个任务的电流/电压/焊接速度/热输入可审查输入。

NV01-C 的目标也不应直接训练策略，而是先证明：NV01-B `.usda` 和 replay fixture 能被 Isaac Sim 打开、能加载 robot/workpiece/task prim、能按 trajectory source 做静态或低速 replay，并能输出 runtime validation report。
