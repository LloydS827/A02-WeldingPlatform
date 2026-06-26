# NV01-C + MJ01 Runtime Replay Readiness Pack 设计

日期：2026-06-26

## 1. 背景

A02 当前已经完成 K01 + NV01-A 和 NV01-B：

- K01 + NV01-A 把焊接工艺 Excel 字段合同、技能资产、机器人上下文、场景上下文和训练准备信息编译为 OpenUSD / Isaac-oriented manifest。
- NV01-B 在不依赖 Isaac Sim、OpenUSD SDK、GPU 或 `pxr` 的前提下，生成最小 `openusd_stage.usda`、静态 USD validation report、Isaac replay fixture、K01 参数到仿真参数审计、sensor/annotation manifest、simulation blocking report 和 reproducibility manifest。
- 最新路线已经确定为 **Isaac 重栈主线 + MuJoCo 轻量支线**：NV01-C 负责 Isaac Sim runtime import/static replay validation，MJ01 负责 MuJoCo lightweight URDF/MJCF replay feasibility。

下一阶段真正运行 Isaac Sim 或 MuJoCo 之前，需要先把“运行时验证需要什么输入、当前已有多少、缺什么会阻塞”变成可复跑 artifact。否则容易出现两类问题：

1. 为了追求 runtime demo 过早引入 Isaac / MuJoCo 环境依赖，导致默认仓库不可复跑。
2. 只停留在文档路线，缺少下一位研发人员可以直接交给 Isaac Sim 或 MuJoCo runtime 的输入清单。

因此本阶段设计一个 **NV01-C + MJ01 Runtime Replay Readiness Pack**：它消费 NV01-B 输出，生成面向 NV01-C 和 MJ01 的输入清单、静态可用性报告和共享阻塞报告。它不是 runtime 执行结果，也不声明 MuJoCo dynamics validation。

## 2. 目标

本阶段目标是新增一个可运行 report 入口：

```bash
cd weld-experience-engine
uv run python -m weldcore.skill_asset.nv01_c_mj01_readiness_report \
  --outdir artifacts/demo/nv01-c-mj01-readiness-pack
```

默认行为：

1. 如果未提供 `--source-nv01b-dir`，先在输出目录下生成 `_source_nv01b/`，复用现有 NV01-B report。
2. 读取 NV01-B 的 `openusd_stage.usda`、`openusd_stage_validation_report.json`、`isaac_replay_fixture.json`、`procedure_sim_parameter_audit.json`、`sensor_annotation_manifest.json`、`simulation_blocking_report.json` 和 `experiment_reproducibility_manifest.json`。
3. 生成 NV01-C Isaac runtime validation input manifest。
4. 生成 MJ01 MuJoCo lightweight replay feasibility report。
5. 生成共享 runtime/replay blocking report。
6. 生成 top-level summary Markdown/JSON。

成功标准：

- 默认命令可复跑，不需要 Isaac Sim、MuJoCo、OpenUSD SDK、GPU、`pxr` 或 `mujoco` Python 包。
- 输出明确区分：
  - `ready_for_isaac_runtime_validation_input_review`
  - `ready_for_mj01_lightweight_replay_input_review`
  - `blocked_by_missing_isaac_runtime`
  - `blocked_by_missing_mujoco_runtime`
  - `not_isaac_sim_runtime_validation`
  - `not_mujoco_dynamics_validation`
  - `not_formal_WPS_PQR`
  - `not_ready_for_robot_execution`
- README、details 和 engine README 都说明新入口、产物、边界和下一步。
- 默认测试继续通过。

## 3. 非目标

本阶段明确不做：

- 不安装或启动 Isaac Sim。
- 不安装或导入 MuJoCo。
- 不调用 `pxr` 或 OpenUSD SDK。
- 不把 URDF 转成正式 MJCF。
- 不做真实 physics / contact / collision validation。
- 不做 Replicator dataset。
- 不做 Isaac Lab 或 MuJoCo policy training。
- 不做真实 robot execution。
- 不做正式 WPS/PQR 或真实焊接质量验证。

## 4. 方案比较

### 方案 A：直接实现 Isaac Sim + MuJoCo runtime

优点：最贴近最终目标。

缺点：依赖 GPU、系统安装、许可/版本和外部 GUI/headless runtime。当前缺真实 TCP/tool/workpiece/sensor 标定和真实工站数据，过早 runtime 结果容易变成环境工程验证，而不是 A02 技能资产验证。

### 方案 B：只新增路线文档

优点：改动极小。

缺点：上一阶段已经完成路线文档。如果本阶段仍只写文档，无法把 NV01-B 产物推进为下一位研发人员可直接使用的 runtime input package。

### 方案 C：新增 runtime/replay readiness pack

优点：保持默认可复跑，同时把下一阶段 runtime 执行所需输入、阻塞项和验收报告结构固定下来。对 Isaac 和 MuJoCo 都提供可审查入口，但不伪造 runtime 成功。

缺点：仍不能证明 Isaac Sim 或 MuJoCo 已实际运行。

本阶段采用 **方案 C**。

## 5. 输出契约

默认输出目录：

```text
artifacts/demo/nv01-c-mj01-readiness-pack/
├── nv01_c_mj01_summary.md
├── nv01_c_mj01_summary.json
├── isaac_runtime_validation_input_manifest.json
├── mujoco_lightweight_replay_feasibility_report.json
├── runtime_replay_blocking_report.json
├── readiness_reproducibility_manifest.json
├── _source_nv01b/
│   └── ... NV01-B artifacts ...
└── task-<unit-id>/
    ├── isaac_runtime_task_validation_input.json
    ├── mujoco_task_replay_feasibility.json
    └── runtime_replay_task_blocking_report.json
```

如果传入 `--source-nv01b-dir`，则使用外部 NV01-B 目录，不复制绝对路径到 artifact，不生成 `_source_nv01b/`。

### 5.1 `isaac_runtime_validation_input_manifest.json`

至少包含：

- `manifest_id`
- `source_stage_ref`
- `source_replay_fixture_ref`
- `runtime_target`
- `runtime_status`
- `static_input_status`
- `required_prim_paths`
- `stage_validation_status`
- `frame_bindings`
- `trajectory_bindings`
- `procedure_parameter_bindings`
- `sensor_placeholders`
- `task_inputs`
- `blocked_by`
- `readiness_boundary`

默认：

- `runtime_target = "Isaac Sim"`
- `runtime_status = "blocked_by_missing_isaac_runtime"`
- `static_input_status = "ready_for_isaac_runtime_validation_input_review"`
- `readiness_boundary` 包含 `not_isaac_sim_runtime_validation`、`not_policy_training_result`、`not_formal_WPS_PQR`、`not_ready_for_robot_execution`

### 5.2 `mujoco_lightweight_replay_feasibility_report.json`

至少包含：

- `report_id`
- `runtime_target`
- `runtime_status`
- `model_input_status`
- `model_source`
- `urdf_ref`
- `mjcf_conversion_status`
- `frame_binding_inputs`
- `trajectory_replay_inputs`
- `contact_and_dynamics_assumptions`
- `task_reports`
- `blocked_by`
- `readiness_boundary`

默认：

- `runtime_target = "MuJoCo"`
- `runtime_status = "blocked_by_missing_mujoco_runtime"`
- `model_input_status = "ready_for_mj01_lightweight_replay_input_review"`
- `mjcf_conversion_status = "not_converted_to_mjcf"`
- `readiness_boundary` 包含 `not_mujoco_dynamics_validation`、`not_policy_training_result`、`not_formal_WPS_PQR`、`not_ready_for_robot_execution`

第一版可以从 NV01-B / NV01-A refs 中提取 `robot_body_asset_ref`、`tcp_frame_ref`、`tool_frame_ref`、trajectory source 和 task refs。它只形成 input review，不验证 MuJoCo 是否能加载模型。

### 5.3 `runtime_replay_blocking_report.json`

至少包含：

- `report_id`
- `overall_status`
- `scope_status`
- `blocking_items`
- `missing_runtime_inputs`
- `missing_calibrations`
- `missing_process_inputs`
- `next_required_inputs`
- `readiness_boundary`

默认 `readiness_boundary` 包含 `not_isaac_sim_runtime_validation`、`not_mujoco_dynamics_validation`、`not_policy_training_result`、`not_formal_WPS_PQR`、`not_ready_for_robot_execution`。

默认 scope：

- `isaac_runtime_validation`
- `mujoco_lightweight_replay`
- `sensor_simulation`
- `replicator_dataset`
- `policy_training`
- `expert_review`
- `a01_product_validation`
- `robot_execution`

默认 `overall_status = "blocked_for_runtime_replay_validation"`，因为缺 runtime、真实标定和真实工站输入。

### 5.4 Per-task outputs

每个任务至少输出：

- `isaac_runtime_task_validation_input.json`
- `mujoco_task_replay_feasibility.json`
- `runtime_replay_task_blocking_report.json`

每个 task artifact 必须包含：

- `task_id`
- `source_task_dir_ref`
- `stage_task_prim_ref`
- `trajectory_ref`
- `tcp_frame_ref`
- `tool_frame_ref`
- `workpiece_frame_ref`
- `procedure_parameter_refs`
- `blocked_by`
- `readiness_boundary`

默认 `readiness_boundary` 包含 `not_isaac_sim_runtime_validation`、`not_mujoco_dynamics_validation`、`not_policy_training_result`、`not_formal_WPS_PQR`、`not_ready_for_robot_execution`。

## 6. 状态词汇

新增状态 token：

| Token | 用途 |
| --- | --- |
| `ready_for_isaac_runtime_validation_input_review` | Isaac runtime 输入清单静态准备好，可交给外部 runtime 验证 |
| `ready_for_mj01_lightweight_replay_input_review` | MuJoCo 轻量 replay 输入清单静态准备好，可交给外部 MJ01 验证 |
| `blocked_by_missing_isaac_runtime` | 缺 Isaac runtime，不能宣称 runtime replay |
| `blocked_by_missing_mujoco_runtime` | 缺 MuJoCo runtime，不能宣称 dynamics / replay validation |
| `blocked_for_runtime_replay_validation` | 组合状态，表示 runtime/replay 仍被阻塞 |
| `not_isaac_sim_runtime_validation` | 边界：不是 Isaac Sim runtime 验证结果 |
| `not_mujoco_dynamics_validation` | 边界：不是 MuJoCo 动力学验证结果 |
| `not_policy_training_result` | 边界：不是策略训练结果 |
| `not_formal_WPS_PQR` | 边界：不是正式 WPS/PQR |
| `not_ready_for_robot_execution` | 边界：不是机器人可执行结论 |

不得新增同义 runtime token。

## 7. 文件设计

新增：

- `weld-experience-engine/weldcore/skill_asset/nv01_c_mj01_readiness.py`
  - 读取 NV01-B artifact。
  - 构建 Isaac input manifest、MuJoCo feasibility report、blocking report 和 task payloads。
  - 不写文件。

- `weld-experience-engine/weldcore/skill_asset/nv01_c_mj01_readiness_report.py`
  - CLI/report 入口。
  - 默认生成 `_source_nv01b/`。
  - 支持 `--source-nv01b-dir`。
  - 写 JSON / Markdown artifact。

新增测试：

- `weld-experience-engine/tests/test_nv01_c_mj01_readiness.py`
- `weld-experience-engine/tests/test_nv01_c_mj01_readiness_report.py`

更新文档：

- `README.md`
- `README.html`
- `details.md`
- `details.html`
- `weld-experience-engine/README.md`

## 8. 验证计划

最小验证：

```bash
cd weld-experience-engine
uv run pytest tests/test_nv01_c_mj01_readiness.py tests/test_nv01_c_mj01_readiness_report.py -q
uv run pytest -q
```

文档验证：

```bash
for file in README.md README.html details.md details.html weld-experience-engine/README.md; do
  rg -n "nv01_c_mj01_readiness_report" "$file"
  rg -n "NV01-C \\+ MJ01" "$file"
  rg -n "not_formal_WPS_PQR|正式 WPS/PQR" "$file"
done
rg -n "blocked_by_missing_mujoco_runtime|not_mujoco_dynamics_validation|not_isaac_sim_runtime_validation|not_ready_for_robot_execution" README.md README.html details.md details.html weld-experience-engine/README.md
```

预期：

- 新增 tests 通过。
- 全量 tests 通过。
- 每个 README/details/engine README/HTML 文件均包含新 report 入口、`NV01-C + MJ01` 和 WPS/PQR 边界；整体文档包含 runtime/MuJoCo/Isaac/robot execution 边界 token。

## 9. 下一阶段建议

完成 readiness pack 后，下一阶段可拆为两个独立 runtime spec：

1. **NV01-C Isaac Sim Runtime Runner**
   - 在真实 Isaac Sim 环境中消费 `isaac_runtime_validation_input_manifest.json`。
   - 输出真实 runtime validation report。

2. **MJ01 MuJoCo Lightweight Replay Runner**
   - 在可用 MuJoCo 环境中消费 `mujoco_lightweight_replay_feasibility_report.json`。
   - 输出 model load / frame binding / trajectory replay 结果。

这两个 runner 仍不应直接进入 policy training、真实 robot execution 或正式 WPS/PQR。
