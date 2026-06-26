# MJ01-A Local MuJoCo Probe + NV01-C0 Remote Isaac Preflight 设计

日期：2026-06-26

## 1. 背景

A02 当前已经完成 K01 + NV01-A、NV01-B 和 NV01-C + MJ01 readiness pack：

- K01 + NV01-A 把焊接工艺 Excel 字段合同、技能资产、机器人上下文、场景上下文和训练准备信息编译为 OpenUSD / Isaac-oriented manifest。
- NV01-B 生成最小 `openusd_stage.usda`、静态 USD validation report、Isaac replay fixture、K01 参数到仿真参数审计、sensor/annotation manifest、simulation blocking report 和 reproducibility manifest。
- NV01-C + MJ01 readiness pack 消费 NV01-B artifact，生成 Isaac runtime validation input manifest、MuJoCo lightweight replay feasibility report、runtime/replay blocking report、readiness reproducibility manifest 和 per-task runtime/replay 输入清单。

最新判断是：

- MuJoCo 可以在本地安装，作为下一阶段轻量 runtime probe。
- Isaac Sim 不适合在当前本地机器安装，应先生成远端/服务器 runtime preflight 输入和环境需求清单。

因此下一阶段不再只是 readiness 文档，也不直接跳到 Isaac runtime，而是实现 **MJ01-A Local MuJoCo Probe + NV01-C0 Remote Isaac Preflight**。它让本机能真实检查 MuJoCo 是否可用，并在可用时做最小模型/轨迹 probe；同时为后续服务器侧 Isaac Sim runner 固定 preflight artifact。

## 2. 关键决策

### 2.1 MuJoCo 作为 optional extra，不进入默认依赖

采用：

```toml
[project.optional-dependencies]
mujoco = ["mujoco>=3.2"]
```

默认 `uv run pytest -q` 不应要求 MuJoCo。需要本地 probe 时使用：

```bash
cd weld-experience-engine
uv sync --extra dev --extra viz --extra mujoco
```

原因：

- MuJoCo 官方 Python 包支持 `pip install mujoco`，Python wheel 内包含 MuJoCo library，适合本地轻量安装。
- A02 的默认仓库路径仍必须可安装、可测试、可复跑；不能因为没有本地 MuJoCo 就让默认测试失败。
- 本阶段需要“可以本地跑 MuJoCo”，但不需要把 MuJoCo 变成所有开发者默认依赖。

### 2.2 不做完整 URDF->MJCF 转换器

本阶段不实现通用 URDF/MJCF 转换器。MJ01-A 只做三层 probe：

1. `mujoco` Python runtime import/version probe。
2. 从 readiness pack 的 `mujoco_lightweight_replay_feasibility_report.json` 读取 `urdf_ref`，再解析对应 `robot_body_asset_report.json` 中的 `source_urdf`、links、joints、mesh refs。
3. 在 MuJoCo 可用时创建一个最小 MJCF sanity model，并尝试用 MuJoCo loader 读取真实 URDF；如果真实 URDF 因 mesh、路径、compiler 或 URDF 限制失败，记录为 `blocked_by_mujoco_model_load_error`，不把失败写成项目失败。

当前 readiness pack 的 `urdf_ref` 指向 `task-.../robot_body_asset_report.json`，不是直接 `.urdf` 文件。这是本阶段需要处理的真实输入形态。

### 2.3 Isaac Sim 只做远端 preflight

本阶段不安装、不启动、不导入 Isaac Sim。NV01-C0 只生成：

- 服务器/远端运行所需输入清单。
- 期望 Isaac Sim 版本、GPU/driver、启动方式、stage path、fixture path 和输出 report schema。
- 当前本地不能验证的项目和缺口。

状态必须保持：

- `not_isaac_sim_runtime_validation`
- `blocked_by_missing_remote_isaac_runtime`
- `not_policy_training_result`
- `not_formal_WPS_PQR`
- `not_ready_for_robot_execution`

## 3. 目标

新增可运行入口：

```bash
cd weld-experience-engine
uv run python -m weldcore.skill_asset.mj01_mujoco_probe_report \
  --outdir artifacts/demo/mj01-a-local-mujoco-probe
```

默认行为：

1. 如果未提供 `--source-readiness-dir`，在输出目录下生成 `_source_readiness/`，复用现有 `nv01_c_mj01_readiness_report`。
2. 读取 readiness pack：
   - `nv01_c_mj01_summary.json`
   - `mujoco_lightweight_replay_feasibility_report.json`
   - `isaac_runtime_validation_input_manifest.json`
   - `runtime_replay_blocking_report.json`
   - `readiness_reproducibility_manifest.json`
   - per-task `mujoco_task_replay_feasibility.json`
   - per-task `isaac_runtime_task_validation_input.json`
3. 生成 top-level MJ01-A/NV01-C0 summary。
4. 生成本地 MuJoCo runtime probe report。
5. 生成 MuJoCo model input resolution report。
6. 在 MuJoCo 可 import 时做最小 MJCF sanity probe；如果真实 URDF 可加载，再记录真实 URDF load status；如果失败，记录失败原因、诊断信息和下一步动作。
7. 生成 per-task trajectory dry-run input report，但不做控制器或真实动力学验证。
8. 生成 Isaac remote preflight report。

成功标准：

- 默认命令在未安装 MuJoCo 时也能运行并输出 `skipped_by_missing_mujoco_runtime`。
- 安装 MuJoCo extra 后，命令能输出 `runtime_probe_status = "available"`，并至少完成最小 MJCF sanity probe。
- 如果真实 URDF 因 mesh/path/compiler 问题不能被 MuJoCo 直接加载，报告必须明确记录错误与下一步，而不是失败退出。
- 所有 artifact 不序列化临时目录绝对路径；若需要表达真实 URDF 来源，使用稳定占位或相对说明。
- Isaac 侧只输出 remote preflight，不宣称本地 Isaac runtime validation。
- README、details 和 engine README 说明 MuJoCo 本地安装路径、默认非依赖边界、Isaac 远端策略和下一阶段建议。

## 4. 非目标

本阶段明确不做：

- 不安装或启动 Isaac Sim。
- 不实现 Isaac runtime import/replay。
- 不实现通用 URDF->MJCF 转换器。
- 不做 MuJoCo 真实动力学验证结论。
- 不做接触、碰撞、热过程或焊接质量仿真。
- 不做 MuJoCo policy training。
- 不做 Isaac Lab policy training。
- 不做真实 robot execution。
- 不做正式 WPS/PQR。

## 5. 输出契约

默认输出目录：

```text
artifacts/demo/mj01-a-local-mujoco-probe/
├── mj01_a_summary.md
├── mj01_a_summary.json
├── mj01_mujoco_runtime_probe_report.json
├── mj01_mujoco_model_input_resolution_report.json
├── mj01_mujoco_probe_report.json
├── nv01_c0_isaac_remote_preflight_report.json
├── mj01_a_reproducibility_manifest.json
├── _source_readiness/
│   └── ... NV01-C + MJ01 readiness pack artifacts ...
└── task-<unit-id>/
    ├── mj01_task_trajectory_dry_run_input.json
    └── nv01_c0_task_isaac_remote_preflight_input.json
```

### 5.1 `mj01_mujoco_runtime_probe_report.json`

至少包含：

- `report_id`
- `runtime_target = "MuJoCo"`
- `runtime_probe_status`
- `mujoco_python_import_status`
- `mujoco_version`
- `install_hint`
- `optional_dependency_extra = "mujoco"`
- `blocked_by`
- `readiness_boundary`

状态：

- 未安装：`runtime_probe_status = "skipped_by_missing_mujoco_runtime"`
- 已安装且 import 成功：`runtime_probe_status = "available"`
- import 出错：`runtime_probe_status = "blocked_by_mujoco_import_error"`

### 5.2 `mj01_mujoco_model_input_resolution_report.json`

至少包含：

- `report_id`
- `source_readiness_ref`
- `source_mujoco_feasibility_ref`
- `robot_body_asset_report_ref`
- `source_urdf_status`
- `source_urdf_ref`
- `link_count`
- `joint_count`
- `mesh_reference_count`
- `frame_binding_inputs`
- `trajectory_replay_inputs`
- `blocked_by`
- `readiness_boundary`

注意：

- `source_urdf_ref` 不写入本机绝对路径；用 `<robot_body_asset.source_urdf>` 或仓库相对路径。
- 若 `robot_body_asset_report.json` 缺失或缺 `source_urdf`，状态进入 `blocked_by_missing_robot_body_asset_source_urdf`。

### 5.3 `mj01_mujoco_probe_report.json`

至少包含：

- `report_id`
- `runtime_probe_status`
- `minimal_mjcf_probe_status`
- `real_urdf_load_status`
- `real_urdf_load_error`
- `model_load_diagnostics`
- `model_load_blocking_items`
- `real_urdf_load_next_step`
- `trajectory_dry_run_status`
- `task_reports`
- `blocked_by`
- `readiness_boundary`

状态边界：

- 未安装 MuJoCo：`minimal_mjcf_probe_status = "skipped_by_missing_mujoco_runtime"`
- 最小 MJCF 加载成功：`minimal_mjcf_probe_status = "passed_minimal_mjcf_sanity_probe"`
- 真实 URDF 加载失败：`real_urdf_load_status = "blocked_by_mujoco_model_load_error"`
- 真实 URDF 加载失败时，命令不应异常退出；`model_load_diagnostics` 至少记录错误类型、是否疑似 mesh/path/compiler/URDF 限制，`model_load_blocking_items` 记录阻塞项，`real_urdf_load_next_step` 给出下一步，例如 `repair_mesh_paths_before_mujoco_load` 或 `prepare_minimal_mjcf_adapter`
- 本阶段无动力学结论：readiness boundary 必须包含 `not_mujoco_dynamics_validation`

### 5.4 `nv01_c0_isaac_remote_preflight_report.json`

至少包含：

- `report_id`
- `runtime_target = "Isaac Sim"`
- `runtime_location = "remote_or_server_required"`
- `local_runtime_status = "not_installed_locally_by_design"`
- `remote_runtime_status = "blocked_by_missing_remote_isaac_runtime"`
- `source_stage_ref`
- `source_replay_fixture_ref`
- `required_prim_paths`
- `frame_bindings`
- `trajectory_bindings`
- `sensor_placeholders`
- `expected_remote_outputs`
- `expected_isaac_sim_version`
- `required_gpu_driver`
- `remote_launch_method`
- `remote_stage_path_policy`
- `remote_fixture_path_policy`
- `expected_runtime_report_schema`
- `blocked_by`
- `readiness_boundary`

默认建议：

- `expected_isaac_sim_version = "to_be_selected_on_remote_runtime"`
- `required_gpu_driver = "nvidia_driver_required_on_remote_runtime"`
- `remote_launch_method = "headless_or_workstation_server_runner"`
- `remote_stage_path_policy = "copy_openusd_stage_usda_to_remote_workspace"`
- `remote_fixture_path_policy = "copy_isaac_runtime_validation_input_manifest_and_replay_fixture_to_remote_workspace"`
- `expected_runtime_report_schema` 至少列出 `stage_import_status`、`required_prim_path_status`、`frame_binding_status`、`trajectory_binding_status`、`sensor_placeholder_status`、`runtime_errors`、`readiness_boundary`

## 6. 安装与运行建议

默认开发验证：

```bash
cd weld-experience-engine
uv sync --extra dev --extra viz
uv run pytest -q
```

本地 MuJoCo probe 验证：

```bash
cd weld-experience-engine
uv sync --extra dev --extra viz --extra mujoco
uv run python -m weldcore.skill_asset.mj01_mujoco_probe_report \
  --outdir artifacts/demo/mj01-a-local-mujoco-probe
```

如果本机无法安装 MuJoCo，本阶段仍可合并，但必须保证：

- 默认 tests 通过。
- MuJoCo 缺失路径输出 `skipped_by_missing_mujoco_runtime`。
- 文档明确本地安装命令和缺失时的预期状态。

## 7. 文件设计

新增：

- `weld-experience-engine/weldcore/skill_asset/mj01_mujoco_probe.py`
  - 读取 readiness pack。
  - 探测 MuJoCo Python runtime。
  - 解析 `robot_body_asset_report.json`。
  - 构建 MuJoCo model/input/probe payload。
  - 构建 Isaac remote preflight payload。
  - 不写文件。

- `weld-experience-engine/weldcore/skill_asset/mj01_mujoco_probe_report.py`
  - CLI/report 入口。
  - 默认生成 `_source_readiness/`。
  - 支持 `--source-readiness-dir`。
  - 写 JSON / Markdown artifact。

新增测试：

- `weld-experience-engine/tests/test_mj01_mujoco_probe.py`
- `weld-experience-engine/tests/test_mj01_mujoco_probe_report.py`

修改：

- `weld-experience-engine/pyproject.toml`
  - 增加 optional extra `mujoco`。
- `README.md`
- `README.html`
- `details.md`
- `details.html`
- `weld-experience-engine/README.md`

## 8. 验证计划

最小验证：

```bash
cd weld-experience-engine
uv run pytest tests/test_mj01_mujoco_probe.py tests/test_mj01_mujoco_probe_report.py -q
uv run pytest -q
```

MuJoCo extra 验证：

```bash
cd weld-experience-engine
uv sync --extra dev --extra viz --extra mujoco
uv run python -m weldcore.skill_asset.mj01_mujoco_probe_report \
  --outdir /tmp/a02-mj01-a-local-mujoco-probe-check
```

文档验证：

```bash
for file in README.md README.html details.md details.html weld-experience-engine/README.md; do
  rg -n "mj01_mujoco_probe_report" "$file"
  rg -n "MJ01-A|MuJoCo" "$file"
  rg -n "Isaac|remote|服务器|远端" "$file"
done
rg -n "not_mujoco_dynamics_validation|not_isaac_sim_runtime_validation|not_formal_WPS_PQR|not_ready_for_robot_execution" README.md README.html details.md details.html weld-experience-engine/README.md
```

## 9. 下一阶段建议

完成 MJ01-A + NV01-C0 后，下一阶段拆为：

1. **MJ01-B MuJoCo Trajectory Dry-run Replay Runner**
   - 复用 MJ01-A 输出的 per-task dry-run 输入、真实 URDF load 结论和 frame/trajectory binding 清单。
   - 目标是让一个最小轨迹 dry-run runner 稳定输出时间序列、frame binding、joint placeholder 和模型加载阻塞报告；不追求真实焊接动力学或策略训练。

2. **NV01-C1 Isaac Remote Import Smoke Validation**
   - 在服务器或远端 Isaac Sim 环境中消费 `nv01_c0_isaac_remote_preflight_report.json`。
   - 输出 stage import、fixture load、required prim、frame binding、trajectory binding 和 sensor placeholder smoke validation report。

两者仍不进入 policy training、正式 WPS/PQR 或真实 robot execution。
