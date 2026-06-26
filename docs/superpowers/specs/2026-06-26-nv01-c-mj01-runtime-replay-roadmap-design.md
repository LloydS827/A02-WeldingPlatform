# NV01-C + MJ01 Runtime Replay Roadmap 设计

日期：2026-06-26

## 1. 背景

A02 当前已经收束为“机器人技能大师能力的焊接技能资产底座”。主线对象是 `ManipulationSkillAsset`，并已能把仿真 evidence、真实 URDF、nominal robot context、scene context、lightweight feasibility、K01 焊接工艺知识合同、A01/B06 mapping、专家审查记录、A02->A01 handoff 和 IP support matrix 汇总为可审查 evidence pack。

最近阶段已经完成：

- **K01 + NV01-A**：从焊接工艺参数 Excel 生成 47 个字段的工艺知识合同，并生成 OpenUSD / Isaac-oriented manifest、Isaac replay config、training readiness 和 stack alignment matrix。
- **NV01-B**：在不依赖 Isaac Sim、OpenUSD SDK、GPU 或 `pxr` 的前提下，写出静态 `openusd_stage.usda`、USD validation gate、Isaac replay fixture、K01 参数到仿真参数审计、sensor/annotation manifest、simulation blocking report 和 reproducibility manifest。
- **README 路线修订**：将下一阶段从单一 Isaac runtime gate 修订为“Isaac 重栈主线 + MuJoCo 轻量支线”。

现在项目的主要风险不是“是否能继续写更多 artifact”，而是下一阶段如果直接进入训练或真机执行，会越过两个关键证据问题：

1. NV01-B 生成的 OpenUSD / replay fixture 能否被目标运行时真实消费。
2. Isaac / OpenUSD / Omniverse 技术栈较重，是否需要一个轻量、学术化、低成本的反证支线来快速暴露机器人模型、轨迹、接触和控制假设问题。

因此下一阶段应进入 **NV01-C Isaac Sim Runtime Import and Static Replay Validation**，同时启动 **MJ01 MuJoCo Lightweight Replay Feasibility**。两者都必须消费同一套 `ManipulationSkillAsset`、`RobotContextSpec`、`SceneContextAsset` 和 K01 工艺知识合同，避免形成新的平行资产体系。

## 2. 目标

本阶段目标不是实现训练策略，也不是输出机器人可执行程序，而是形成下一阶段可执行路线和最小证据门槛：

```text
NV01-B static OpenUSD experiment base
-> NV01-C Isaac Sim runtime import/static replay validation
+ MJ01 MuJoCo lightweight URDF/MJCF replay feasibility
-> real context gap report
-> expert review / A01 validation candidate input
```

具体目标：

1. 明确 Isaac / OpenUSD 是工站级数字孪生、传感器、合成数据和未来 sim-to-real 主验证路线。
2. 明确 MuJoCo 是轻量、学术化、快速动力学验证和反证支线，不替代 OpenUSD 场景合同。
3. 固定 NV01-C 的最小验收：导入 NV01-B `openusd_stage.usda`，验证关键 prim 和 metadata，绑定 replay fixture，做静态或低速 trajectory replay，并输出 runtime validation report。
4. 固定 MJ01 的最小验收：验证当前真实 URDF / nominal robot context 能否形成 MuJoCo 可消费的 URDF/MJCF 最小模型，并 replay TCP trajectory candidate。
5. 固定下一阶段阻塞报告：robot USD/articulation、MJCF/URDF 模型质量、TCP/tool/workpiece 标定、sensor layout、H300 工站日志、电流/电压/热输入、工艺人员确认和专家审查结论。
6. 更新 README、details 和 HTML 阅读副本，使后续研发人员把 NV01-C 和 MJ01 看作下一阶段工作指引，而不是已完成能力。

## 3. 非目标

本阶段明确不做：

- Isaac Sim 安装、启动、扩展脚本或 runtime 执行实现。
- MuJoCo 依赖引入、MJCF converter、控制器、viewer 或训练实现。
- Replicator dataset 生成。
- Isaac Lab policy training。
- MuJoCo policy training。
- 真实机器人控制、真实碰撞验证或真实焊接质量验证。
- 正式 WPS/PQR。
- 大 UI、平台化页面或产品工作台。
- 把 MuJoCo、ManiSkill/SAPIEN、Gazebo/MoveIt 重置为与 OpenUSD / Isaac 同等的长期主底座候选。

## 4. 关键判断

### 4.1 主线判断

A02 的 canonical truth 仍是：

```text
ManipulationSkillAsset
+ WeldProcedureKnowledgeContract
+ RobotContextSpec
+ SceneContextAsset
+ SkillAssetEvidence
+ ExpertReviewRecord
```

OpenUSD、Isaac Sim、Isaac Lab、MuJoCo、ManiSkill/SAPIEN、Gazebo/MoveIt 都是消费或验证这些资产的运行时 / 工具链，不应反向替换 A02 技能资产本体。

### 4.2 Isaac 的角色

Isaac / OpenUSD 适合作为重栈主线，原因是它更贴近最终工站级数字孪生目标：

- OpenUSD 适合表达机器人、工件、工装、焊缝、传感器、坐标系、语义标签和工艺 metadata。
- Isaac Sim 适合做机器人导入、replay、传感器仿真、Replicator 合成数据、可视化和后续复杂环境验证。
- Isaac Lab 适合后续训练闭环，但必须在 runtime replay、真实上下文缺口和任务定义都清楚后再进入。

### 4.3 MuJoCo 的角色

MuJoCo 适合作为轻量支线，原因是它更便于快速暴露模型和控制假设问题：

- 可用于 URDF/MJCF 模型加载 sanity check。
- 可用于关节、mesh、惯性、接触和简化动力学检查。
- 可用于 TCP trajectory candidate 的轻量 replay。
- 可用于未来小规模控制原型，但本阶段不训练策略。

MuJoCo 的边界也必须明确：

- 不承载最终工站级数字孪生表达。
- 不替代 OpenUSD scene contract。
- 不直接输出真实机器人执行结论。
- 不绕过 K01 工艺知识合同、专家审查和真实工站数据缺口。

### 4.4 路线组合

本阶段采用：

```text
Isaac 重栈主线 + MuJoCo 轻量支线
```

不采用以下路线：

- **只走 Isaac**：风险是迭代成本高，runtime 环境工程问题会掩盖技能资产和轨迹假设问题。
- **只走 MuJoCo**：风险是偏离工站级数字孪生、传感器、合成数据和 OpenUSD 交换层目标。
- **多仿真器平行 bake-off**：风险是重回早期发散状态，削弱 `ManipulationSkillAsset` 主线。

## 5. 输出设计

### 5.1 文档输出

本阶段只做路线与执行计划沉淀，输出文件为：

- `docs/superpowers/specs/2026-06-26-nv01-c-mj01-runtime-replay-roadmap-design.md`
- `docs/superpowers/plans/2026-06-26-nv01-c-mj01-runtime-replay-roadmap.md`
- `README.md`
- `README.html`
- `details.md`
- `details.html`

### 5.2 README 输出

README 必须体现：

- 项目定位中说明 Isaac 是重底座主线，MuJoCo 是轻量验证和反证支线。
- 粗粒度路线图中同时出现：
  - `NV01-C Isaac Sim runtime 导入与静态 replay 验证`
  - `MJ01 MuJoCo URDF/MJCF replay 可行性评估`
- `重/轻仿真底座分层路线` 说明 Isaac / OpenUSD 和 MuJoCo 的职责边界。
- `下一阶段任务` 明确 NV01-C 为主线、MJ01 为支线。
- `边界` 明确 `not_isaac_sim_runtime_validation`、`not_mujoco_dynamics_validation` 和 `not_ready_for_robot_execution`。

### 5.3 details 输出

`details.md` 必须新增 2026-06-26 阶段记录，说明：

- 当前 README 已把后续路线修订为 “Isaac 重栈主线 + MuJoCo 轻量支线”。
- NV01-C 和 MJ01 是下一阶段建议，不是已完成 runtime。
- 下一阶段推荐先做 runtime / replay gate，再进入训练、真实碰撞、真实焊接质量或真机执行。
- 本阶段验证结果和仍保留边界，必须点名 `not_isaac_sim_runtime_validation`、`not_mujoco_dynamics_validation` 和 `not_ready_for_robot_execution`。

### 5.4 HTML 阅读副本

根目录 Markdown 更新后，必须同步更新：

- `README.html`
- `details.html`

HTML 只需要与现有轻量阅读副本风格一致，不需要引入 Mermaid renderer 或新前端依赖。

## 6. 后续阶段验收门槛

### 6.1 NV01-C 验收门槛

NV01-C 完成时至少应证明：

1. Isaac Sim runtime 环境、版本、启动方式和失败边界被记录。
2. `openusd_stage.usda` 可被 Isaac Sim 或可用 OpenUSD runtime 打开。
3. `/World`、robot、workpiece、weld task、seam path、TCP trajectory candidate、sensor placeholder 和 safety boundary prim 可定位。
4. replay fixture 能绑定 stage、trajectory source、TCP frame、tool frame 和 procedure metadata。
5. 能做静态或低速 trajectory replay。
6. 输出 runtime validation report，区分 passed、blocked 和 not-run 项。
7. 不把该结果写成 policy training、正式 WPS/PQR 或 robot execution。

### 6.2 MJ01 验收门槛

MJ01 完成时至少应证明：

1. 当前真实 URDF / nominal robot context 能否被 MuJoCo 直接消费，或需要 MJCF 最小转换。
2. 关节、mesh、frame、TCP frame 和简化工件/焊缝能否进入轻量模型。
3. TCP trajectory candidate 能否做简化 replay。
4. 输出 MuJoCo feasibility report，说明 model load、frame binding、trajectory replay、contact/dynamics assumptions 和 blocking fields。
5. 不把 MuJoCo replay 写成工站级数字孪生、真实碰撞验证、真实焊接质量验证或 robot execution。

### 6.3 共同验收门槛

两条路线都必须：

- 从 `ManipulationSkillAsset`、`RobotContextSpec`、`SceneContextAsset` 和 K01 工艺知识合同读取输入。
- 把结论写回 evidence / blocking report。
- 共享字段缺口词汇，避免各自造一套 ready/blocking 状态。
- 明确哪些输入缺失会阻塞真实 replay、sensor simulation、dataset generation、training design、expert review 和 A01 product validation。

## 7. 风险与缓解

| 风险 | 表现 | 缓解 |
| --- | --- | --- |
| Isaac runtime 环境过重 | 安装、GPU、版本、扩展问题占用过多时间 | NV01-C 只做 runtime import/static replay gate，不做训练或复杂传感器 |
| MuJoCo 支线发散 | 重新变成仿真器 bake-off | MJ01 只验证 URDF/MJCF replay 可行性，必须回写同一技能资产 evidence |
| README 过度承诺 | 读者误解为已经完成 runtime 或训练 | 边界中显式保留 `not_isaac_sim_runtime_validation`、`not_mujoco_dynamics_validation`、`not_ready_for_robot_execution` |
| 真实工站数据缺口被默认值掩盖 | 系统看似 ready，但缺 TCP/workpiece/sensor/process inputs | blocking report 必须列出真实标定、H300 日志、电流/电压/热输入和专家审查缺口 |
| 文档与实际可运行能力不一致 | README 指引与 CLI/report 状态冲突 | 本阶段只更新路线；实现阶段必须继续通过默认测试与报告入口验证 |

## 8. 验证计划

本阶段文档性变更的验证包括：

```bash
rg -n "MuJoCo|MJ01|NV01-C|重/轻仿真底座分层路线|not_isaac_sim_runtime_validation|not_mujoco_dynamics_validation|not_ready_for_robot_execution" README.md README.html details.md details.html
cd weld-experience-engine
uv run pytest -q
```

预期：

- README 和 HTML 阅读副本都包含 NV01-C + MJ01 路线。
- details 和 HTML 阅读副本都记录 2026-06-26 阶段判断。
- README/details 及 HTML 阅读副本都保留 `not_isaac_sim_runtime_validation`、`not_mujoco_dynamics_validation` 和 `not_ready_for_robot_execution` 边界。
- 默认测试继续全部通过。

## 9. 下一阶段建议

完成本阶段文档与路线沉淀后，下一阶段建议拆成两个可独立执行的 implementation spec：

1. **NV01-C Isaac Sim Runtime Import and Static Replay Validation**
   - 输入：NV01-B `openusd_stage.usda`、`isaac_replay_fixture.json`、K01 contract、robot/scene context。
   - 输出：runtime validation report、prim load report、frame/trajectory binding report、blocking report。

2. **MJ01 MuJoCo Lightweight Replay Feasibility**
   - 输入：真实 URDF、nominal robot context、scene context、TCP trajectory candidate、K01 contract。
   - 输出：MuJoCo model feasibility report、URDF/MJCF gap report、trajectory replay report、blocking report。

两个 implementation spec 都应避免训练、真机执行和真实质量验证，把目标限制在 runtime / replay gate。
