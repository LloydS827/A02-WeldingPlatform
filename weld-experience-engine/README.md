# weldcore — 焊接技能资产引擎

`weldcore` 是 A02 机器人技能大师能力的焊接技能资产底座的可运行引擎，用于把焊接经验、仿真输出、真实或脱敏工站数据、人工修正、专家审查和证据边界组织成可验证的 `ManipulationSkillAsset`。

当前核心模型是：

```text
SimulationEvidenceBundle / real robot log / human demonstration / H300 workcell run
-> ManipulationSkillAsset
+ RobotBodyAsset(URDF)
+ RobotContextSpec
+ SceneContextAsset
+ lightweight RobotFeasibilityResult
-> SkillTransferAssessment
-> ExpertReviewRecord
-> A02->A01 handoff / IP support
```

其中 `ManipulationSkillAsset` 是当前 canonical 技能资产实例；`RobotBodyAsset` 是机器人身体上下文；`RobotContextSpec` 和 `SceneContextAsset` 是迁移预检的上下文对象；`RobotFeasibilityResult` 是轻量预检结果；`SkillTransferAssessment` 和 `ExpertReviewRecord` 用于进入专家审查候选。既有 `SkillDataset -> WeldSkillPackage -> evaluation / evidence` 仍保留为历史兼容和 facade，不再是默认主线。

当前已实现 K01 + NV01-A Weld Procedure Knowledge Contract and NVIDIA-Native Digital Twin Foundation，并完成 NV01-B OpenUSD / Isaac Sim 可复现实验底座：以 `docs/焊接工艺数据库主要参数表.xlsx` 作为焊接工艺知识合同源，以 OpenUSD 作为未来数字孪生交换层，以 Isaac Sim 作为未来默认目标仿真运行时，以 Isaac Lab 作为后续训练闭环目标层。`weldcore` 当前生成面向这些重底座的 procedure contract、manifest/report 和静态 `.usda` 实验底座，而不是自研通用物理引擎、3D 场景标准或训练框架。

当前进一步新增 NV01-C + MJ01 readiness pack：它消费 NV01-B artifact，生成 Isaac runtime validation input manifest、MuJoCo lightweight replay feasibility report 和 runtime/replay blocking report。该能力用于准备下一阶段真实 runtime runner，不运行 Isaac Sim 或 MuJoCo，不导入 `pxr` 或 `mujoco`，也不宣称 runtime replay、MuJoCo dynamics validation、正式 WPS/PQR 或真实机器人执行。

## 运行

```bash
uv sync --extra dev --extra viz
uv run pytest -q
```

如果本机尚未安装 `uv`，先参考 Astral 官方安装方式安装；临时备用方式仍可使用 `pip install -e ".[dev,viz]"`。

## 默认技能资产报告

```bash
uv run python -m weldcore.skill_asset.asset_report \
  --outdir artifacts/skill-assets/canonical
```

`asset_report` 默认输出 12 份 JSON：

- `skill_asset_report.json`
- `robot_body_asset_report.json`
- `robot_context_spec.json`
- `scene_context_asset_report.json`
- `skill_transfer_assessment.json`
- `robot_feasibility_result.json`
- `skill_asset_evidence_writeback_summary.json`
- `skill_asset_evidence_source_catalog.json`
- `a01_b06_skill_asset_mapping.json`
- `expert_review_record.json`
- `a02_to_a01_product_validation_handoff.json`
- `ip_disclosure_support_matrix.json`

这些 artifact 用于服务 A01 产品验证、专家审查候选和 IP 交底准备。它们不是可直接下发给机器人控制器的程序，不是真实焊接质量验证，不是正式 WPS/PQR，也不是 Isaac Sim runtime 验证结论。

## 默认 Demo Evidence Pack

```bash
uv run python -m weldcore.skill_asset.demo_report \
  --outdir artifacts/demo/skill-asset-evidence
```

`asset_report` 是单任务 canonical 输出，默认生成一组 12 份 JSON artifact，用于检查当前技能资产主链路。`demo_report` 是多任务解释型 evidence pack，默认运行 2 个仿真任务；每个任务输出同名 12 份 canonical artifact 和 `simulation_evidence_bundle.json`，顶层输出 `demo_summary.md`、`demo_summary.json` 和 `demo_summary.html`。

`demo_report` 面向专家审查、A02->A01 handoff 和 IP evidence pack 讨论，默认状态是 `ready_for_expert_review` evidence / `ready_for_expert_review_candidate_pack`。它保留 `not_ready_for_robot_execution`、`simulation_only`、`not_full_ik_solver`、`not_real_collision_validation` 和 `not_real_welding_quality_validation` 边界，不是机器人控制器程序、生产派发包或真实机器人执行验证。

## K01 + NV01-A 数字孪生基础报告

```bash
uv run python -m weldcore.skill_asset.nvidia_digital_twin_report \
  --outdir artifacts/demo/nvidia-digital-twin-foundation
```

`nvidia_digital_twin_report` 默认读取焊接工艺 Excel 并在缺少 source demo 时生成 `_source_demo_evidence`，输出 `weld_procedure_knowledge_contract.json`、`weld_procedure_parameter_set.json`、`weld_procedure_validation_report.json`、`procedure_to_nv01_mapping_matrix.json`、`weld_skill_digital_twin_package.json`、`openusd_scene_manifest.json`、`isaac_sim_replay_config.json`、`domain_randomization_recipe.json`、`training_readiness_report.json`、`nvidia_stack_alignment_matrix.json` 和 per-task artifacts。

这个命令是合同和报告生成器，不需要 Isaac Sim。默认状态是 `ready_for_simulation_replay_package_design` / `ready_for_training_design_review`，同时保留 `not_formal_WPS_PQR`、`not_ready_for_robot_execution`、`not_isaac_sim_runtime_validation` 和 `not_policy_training_result` 边界。

## NV01-B 可复现实验底座

```bash
uv run python -m weldcore.skill_asset.nv01_b_experiment_base_report \
  --outdir artifacts/demo/nv01-b-experiment-base
```

`nv01_b_experiment_base_report` 默认生成 `_source_nv01a`，再输出最小 `openusd_stage.usda`、静态 USD validation report、Isaac replay fixture、procedure simulation parameter audit、sensor annotation manifest、simulation blocking report 和 reproducibility manifest。它不需要 Isaac Sim 或 OpenUSD SDK；默认状态仍是 `blocked_for_real_isaac_sim_replay`，不是 runtime replay、policy training、正式 WPS/PQR 或真实机器人执行验证。

## NV01-C + MJ01 Readiness Pack

```bash
uv run python -m weldcore.skill_asset.nv01_c_mj01_readiness_report \
  --outdir artifacts/demo/nv01-c-mj01-readiness-pack
```

`nv01_c_mj01_readiness_report` 默认生成 `_source_nv01b`，再输出 `isaac_runtime_validation_input_manifest.json`、`mujoco_lightweight_replay_feasibility_report.json`、`runtime_replay_blocking_report.json`、`readiness_reproducibility_manifest.json` 和 per-task runtime/replay 输入清单。默认状态是 `blocked_for_runtime_replay_validation`，其中 Isaac 侧保留 `blocked_by_missing_isaac_runtime`，MuJoCo 侧保留 `blocked_by_missing_mujoco_runtime`。该命令不需要 Isaac Sim、MuJoCo、OpenUSD SDK、GPU、`pxr` 或 `mujoco`，边界包含 `not_isaac_sim_runtime_validation`、`not_mujoco_dynamics_validation`、`not_policy_training_result`、`not_formal_WPS_PQR` 和 `not_ready_for_robot_execution`。

## 证据与历史支撑命令

既有 POC / MVP / report 命令仍可用，但它们用于技能资产 evidence、证据边界、仿真接入证据或历史支撑，不是默认研发主线本身。

```bash
uv run python -m weldcore.report.mvp_report
uv run python -m weldcore.report.data_foundation_report
uv run python -m weldcore.report.synthetic_v2_input_report
uv run python -m weldcore.report.simulation_ingest_report
uv run python -m weldcore.report.generate
uv run python -m weldcore.report.scenario_report
```

这些命令不能被写成真实焊接质量验证、完整外部仿真器集成或 WPS/PQR。

## 当前能力

- `skill_asset/`：`ManipulationSkillAsset` 本体、从 `SimulationEvidenceBundle` 构建 skill asset、从真实 URDF 构建 `RobotBodyAsset`、绑定 `RobotContextSpec`、生成 `SceneContextAsset`、lightweight `RobotFeasibilityResult`、`SkillTransferAssessment`、`ExpertReviewRecord`、A01/B06 mapping、A02->A01 handoff、IP support matrix 和 `asset_report`。
- `simulation_bakeoff/`：`SimulationTaskSpec`、`SimulatorAdapterResult`、`SimulationEvidenceBundle`、simlite 基线、ManiSkill/SAPIEN batch/accumulation/modeling 入口，以及 Gazebo/MoveIt 候选路线边界。
- `robot_process/`：`RobotContextSpec`、`RobotFeasibilityProbe`、`RobotFeasibilityResult` 和机器人候选草案兼容路径。
- `transfer/`：`WeldSkillPackage` 生成、条件迁移和迁移评测；当前作为历史兼容 / facade。
- `model/`：Trajectory、WeaveTemplate、GrooveGeometry、LayerPass、WeldProcess 等工艺数据结构。
- `datagen/`：理想大师轨迹合成，以及手抖、漂移、无效停顿扰动注入。
- `decompose/`：中心线提取、摆幅/摆频检测、模板分类、姿态估计，输出结构化 WeldProcess。
- `recompose/`：结构化工艺参数重组为连续轨迹；缺少 scipy 时回退到正向合成轨迹。
- `metrics/`：往返 RMS、参数恢复误差、抗扰动失效边界。
- `knowledge/`：公开资料来源、船舶焊接任务族、候选仿真场景和 gate 支撑材料。
- `ingest/`：`SimulationOutputBundle` 导入边界，用于把仿真输出转为可审计数据。
- `viz/rerun_bridge.py`：可选 Rerun 回放边界；未安装 `rerun-sdk` 时不会影响测试。

## 机器人工艺候选与预检边界

当前真实资产位于 `docs/real-urdf/robot.urdf`，解析结果为 7 links、6 revolute joints、33 unique mesh files、66 mesh references，状态可达到 `usable_as_robot_body_context`。默认 `asset_report` 会生成 nominal robot context、默认 scene context 和 lightweight feasibility result，并把 `SkillTransferAssessment` 推进到 `ready_for_expert_review`，把 `ExpertReviewRecord` 置为 `pending_expert_review`。

这仍不表示 TCP 已真实标定、工件坐标系已真实测量、场景碰撞已验证、真实机器人可执行或真实焊接质量已验证。

## 当前边界

- 不把 POC / MVP 输出写成真实焊接质量结论。
- 不把 `SyntheticSkillDataset v2` 输入规范 gate 写成批量样本已经生成。
- 不把仿真输出接入 gate 写成完整 ManiSkill / Isaac / ROS 集成。
- 不把公开资料、仿真假设或报告结论写成 WPS/PQR。
- 不把 Excel 字段表、K01 参数集、系统计算字段或仿真推导字段写成正式 WPS/PQR。
- 不把任何单一仿真器、机器人框架或可视化工具写成项目核心对象。
- 不把 OpenUSD / Isaac Sim / Isaac Lab 写成已接入的默认 runtime；当前只生成面向这些底座的 K01 + NV01-A manifest/report 合同和 NV01-B 静态 `.usda` 实验底座。
- 不把 `ready_for_contextual_precheck` 写成 `ready_for_robot_execution`。
- 不把 `ready_for_expert_review` 写成 `ready_for_robot_execution`。
- 不把 lightweight `RobotFeasibilityResult` 写成完整 IK、真实碰撞检测或真实机器人执行验证。
- 不把 A02->A01 handoff 写成生产派发包或控制器程序。
