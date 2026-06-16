# weldcore — 焊接技能资产引擎

`weldcore` 是 A02「焊接技能大师平台」的可运行引擎，用于把焊接经验、仿真输出、工艺字段和证据边界组织成可验证的焊接技能资产。

当前核心模型是：

```text
SimulationEvidenceBundle -> ManipulationSkillAsset
ManipulationSkillAsset + RobotBodyAsset(URDF)
  -> RobotContextSpec
  -> SceneContextAsset
  -> lightweight RobotFeasibilityResult
  -> SkillTransferAssessment
  -> ready_for_expert_review
```

其中 `ManipulationSkillAsset` 是当前 canonical 技能资产实例；`RobotBodyAsset` 是机器人身体上下文；`RobotContextSpec` 和 `SceneContextAsset` 是轻量迁移预检的上下文对象；`SkillTransferAssessment` 是迁移预检与专家审查候选判断对象。既有 `SkillDataset -> WeldSkillPackage -> evaluation / evidence` 仍保留为历史兼容和证据支撑层，POC、MVP、report 命令、simlite 和外部 adapter 都可以继续提供输入、验证或证据。

## 运行

```bash
uv sync --extra dev --extra viz
uv run pytest -q
```

如果本机尚未安装 `uv`，先参考 Astral 官方安装方式安装；临时备用方式仍可使用 `pip install -e ".[dev,viz]"`。

## 证据与历史支撑命令

既有 POC / MVP / report 命令仍可用，但它们用于技能资产证据、证据边界/仿真接入证据或历史支撑，不是默认研发主线本身。

技能资产证据命令：

```bash
uv run python -m weldcore.skill_asset.asset_report \
  --outdir artifacts/skill-assets/canonical
uv run python -m weldcore.report.mvp_report
```

`asset_report` 用于输出 `ManipulationSkillAsset`、`RobotBodyAsset`、`RobotContextSpec`、`SceneContextAsset`、`SkillTransferAssessment`、`RobotFeasibilityResult` 和 `SkillAssetEvidenceWritebackSummary` 七份 JSON；`mvp_report` 用于证明早期 `WeldSkillPackage` 闭环仍有效。

证据边界/仿真接入证据命令：

```bash
uv run python -m weldcore.report.data_foundation_report
uv run python -m weldcore.report.synthetic_v2_input_report
uv run python -m weldcore.report.simulation_ingest_report
```

历史支撑命令：

```bash
uv run python -m weldcore.report.generate
uv run python -m weldcore.report.scenario_report
```

这些命令用于复盘经验结构化 POC、技能迁移 MVP、资料底座 gate、`SyntheticSkillDataset v2` 输入规范 gate 和仿真输出接入 gate。它们不能被写成真实焊接质量验证、完整外部仿真器集成或 WPS/PQR。

## 当前能力

- `model/`：Trajectory、WeaveTemplate、GrooveGeometry、LayerPass、WeldProcess 等工艺数据结构。
- `datagen/`：理想大师轨迹合成，以及手抖、漂移、无效停顿扰动注入。
- `decompose/`：中心线提取、摆幅/摆频检测、模板分类、姿态估计，输出结构化 WeldProcess。
- `recompose/`：结构化工艺参数重组为连续轨迹；缺少 scipy 时回退到正向合成轨迹。
- `metrics/`：往返 RMS、参数恢复误差、抗扰动失效边界。
- `sim/`：simlite/mock bundle，作为 L0 稳定仿真和测试工具。
- `skill_asset/`：`ManipulationSkillAsset` 本体、从 `SimulationEvidenceBundle` 构建 skill asset、从真实 URDF 构建 `RobotBodyAsset`、绑定 `RobotContextSpec`、生成 `SceneContextAsset`、lightweight `RobotFeasibilityResult`、`SkillTransferAssessment` 和 `asset_report`。
- `transfer/`：`WeldSkillPackage` 生成、条件迁移和迁移评测。
- `knowledge/`：公开资料来源、船舶焊接任务族、候选仿真场景和 gate 支撑材料。
- `ingest/`：`SimulationOutputBundle` 导入边界，用于把仿真输出转为可审计数据。
- `weldcore.report`：当前证据与历史支撑报告生成器。
- `viz/rerun_bridge.py`：可选 Rerun 回放边界；未安装 `rerun-sdk` 时不会影响测试。

## 仿真与 adapter 边界

simlite 是 L0 稳定仿真和测试工具，用于保持默认项目可验证。它不是最终类机器人路线，也不代表真实焊接过程或真实质量验证。

ManiSkill、SAPIEN、Isaac、ROS、MoveIt、Gazebo 等外部仿真器和机器人生态是 adapter 候选。它们可以在后续用于机器人任务、运动学、可达性、碰撞、示教数据或 benchmark 评估，但不能替代 `ManipulationSkillAsset` 这个技能资产本体。

## 机器人工艺候选与预检边界

`weldcore.robot_process` 可以把 `SimulationEvidenceBundle` 转成 `RobotProcessPackageDraft`，并用 `RobotContextSpec` 与轻量 `RobotFeasibilityResult` 表达机器人上下文和可执行性预检结果。`weldcore.skill_asset` 现在也会把真实 URDF `RobotBodyAsset` 绑定为 nominal `RobotContextSpec`，再结合 `SceneContextAsset` 进入同一类 lightweight feasibility 预检。

当前默认只提供 `mock_6axis_welding_robot` 和 `lightweight_rule` 预检，用于验证数据结构与决策 pipeline。它最多把候选草案推进到 `ready_for_expert_review`，不表示机器人可以执行，也不表示 MoveIt/Gazebo、真实机器人、焊机过程参数或焊接质量已经验证。

当前真实资产位于 `docs/real-urdf/robot.urdf`，解析结果为 7 links、6 revolute joints、33 unique mesh files、66 mesh references，状态可达到 `usable_as_robot_body_context`。默认 `asset_report` 会生成 nominal robot context、默认 scene context 和 lightweight feasibility result，并把 `SkillTransferAssessment` 推进到 `ready_for_expert_review`。这仍不表示 TCP 已真实标定、工件坐标系已真实测量、场景碰撞已验证或真实机器人可执行。

## 当前边界

- 不把 POC / MVP 输出写成真实焊接质量结论。
- 不把 `SyntheticSkillDataset v2` 输入规范 gate 写成批量样本已经生成。
- 不把仿真输出接入 gate 写成完整 ManiSkill / Isaac / ROS 集成。
- 不把公开资料、仿真假设或报告结论写成 WPS/PQR。
- 不把任何单一仿真器、机器人框架或可视化工具写成项目核心对象。
- 不把 `ready_for_contextual_precheck` 写成 `ready_for_robot_execution`。
- 不把 `ready_for_expert_review` 写成 `ready_for_robot_execution`。
- 不把 lightweight `RobotFeasibilityResult` 写成完整 IK、真实碰撞检测或真实机器人执行验证。
