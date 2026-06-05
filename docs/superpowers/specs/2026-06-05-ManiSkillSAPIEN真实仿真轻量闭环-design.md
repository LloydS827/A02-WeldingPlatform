# ManiSkill/SAPIEN 真实仿真轻量闭环设计

## 1. 背景

项目已经完成 `WeldSkillPackage` 主线收敛、`WeldSkillUnit` 最小定义、R0/simlite baseline 和第一轮 simulation bake-off 证据。当前 bake-off 的结论是：R0/simlite 可以作为稳定基线，ManiSkill/SAPIEN 与 Gazebo/MoveIt 已被纳入候选路线，但外部真实仿真尚未真正运行。

下一阶段目标不是继续做路线讨论，也不是直接选择最终仿真器，而是启动第一条真实仿真工具闭环。该闭环应尽量降低人工搭建、人工示教、人工整理结果的工作量，以代码驱动方式完成任务生成、轻量运行、demo 生成和结果回写。

本阶段优先选择 ManiSkill/SAPIEN。理由是它更贴近技能数据生成、机器人任务表达、trajectory/demo 记录和后续机器人大脑训练输入；Gazebo/MoveIt 保留为后续机器人可执行性、IK、碰撞和工业执行链路验证路线。

## 2. 阶段目标

建立一条轻量但完整的真实仿真 pipeline：

```text
WeldSkillUnit
-> SimulationTaskSpec
-> ManiSkillTaskConfig
-> RuleBasedDemo
-> ManiSkill/SAPIEN Run
-> Raw Simulation Artifact
-> SimulatorAdapterResult
-> ExperienceDataset
-> SkillDataset compatibility export
-> SimulationEvidenceBundle
-> Bakeoff / next-step decision
```

本阶段终点是经验级数据集和证据闭环，不是机器人可执行工艺包。`SkillDataset` 只作为现有项目兼容出口，不代表本阶段产物已经成为机器人可执行工艺包或真实焊接质量数据。所有数据结构和 adapter 边界必须服务后续从经验资产迁移到机器人执行包的整体路线。

## 3. 本阶段必须完成

- 使用独立 conda 环境安装和运行 ManiSkill/SAPIEN，不污染当前 `uv` 项目环境。
- 保持当前 `uv` 默认项目环境轻量、稳定、可测试。
- 从两个已有核心技能单元自动生成仿真任务：
  - `long-straight-horizontal-tracking`
  - `corner-horizontal-transition`
- 每个任务生成一条 rule-based expert demo trajectory。
- 至少支持本机轻量 CPU/headless/state-based 运行路径。
- 输出统一 artifact，包括 task config、demo、trajectory、task status、metrics 和 failure boundary。
- 将真实仿真结果转回现有项目结构：
  - `SimulatorAdapterResult`
  - 经验级数据集
  - `SkillDataset` 兼容导出
  - `SimulationEvidenceBundle`
- 复用现有 evidence/report 体系，不把 D「证据报告」扩展成独立大工程。

## 4. 本阶段明确不做

- 不选择最终仿真器。
- 不做 GPU 并行、RL 训练或大规模数据生成。
- 不做完整工业机器人品牌、完整工位、夹具和碰撞场景。
- 不做熔池、热输入、冶金、成形或真实焊接质量仿真。
- 不接真实机器人、焊机、PLC 或现场总线。
- 不把仿真输出写成 WPS/PQR 或真实质量验证。
- 不扩展复杂文档系统。

## 5. 环境策略

采用双层环境：

```text
L0-dev：当前 Mac 本机轻量运行环境
L1-real：Linux + NVIDIA GPU 正式高吞吐仿真环境
```

当前阶段必须有 L0-dev 可运行路径。该路径优先使用 CPU/headless/state-based 模式，渲染、GPU 并行和视觉数据生成不作为硬指标。

依赖管理采用独立 conda 环境：

```text
当前项目 uv 环境：
- adapter 接口
- 任务生成器
- schema
- contract test
- report/evidence
- 不强依赖 ManiSkill/SAPIEN

独立 conda 环境：
- ManiSkill/SAPIEN
- 真实仿真运行
- raw artifact 输出
- spike runner
```

后续迁移到服务器时，pipeline 形状不变，只替换运行环境、runner 参数和批量调度方式。

## 6. 组件设计

### 6.1 Task Generator

职责：把现有 `SimulationTaskSpec` 转成 ManiSkill/SAPIEN spike 可读取的任务配置。

输入：项目已有两个默认 `SimulationTaskSpec`。

输出：可序列化的 `ManiSkillTaskConfig`，建议先保存为 JSON。

最小字段：

- `task_id`
- `unit_id`
- `seam_path`
- `tcp_frame`
- `orientation_constraint`
- `motion_constraint`
- `expected_outputs`
- `out_of_scope`

该组件不重新定义 `WeldSkillUnit`，只做工具侧配置翻译。

### 6.2 Demo Generator

职责：为每个任务生成一条 rule-based expert demo trajectory。

第一版只沿 `seam_path` 生成 TCP 位姿序列，并保留姿态约束。它不做人工示教、不做学习、不做复杂运动规划。

目标是：

- 可回放
- 可记录
- 可转数据
- 可作为后续小批量合成数据的种子

### 6.3 ManiSkill/SAPIEN Spike Runner

职责：在独立 conda 环境中读取 task config 和 demo，运行轻量真实仿真。

第一版场景允许简化：只要求表达路径、TCP 目标、任务状态和基础指标。若 ManiSkill/SAPIEN API、平台限制、机器人资产或系统依赖导致不能运行，runner 必须输出结构化失败结果，而不是只留下控制台报错。

本阶段的“真实仿真”只表示真实调用 ManiSkill/SAPIEN 运行器，并产生结构化仿真 artifact；它不表示物理焊接质量、工业机器人可执行性或工艺有效性已经得到验证。

### 6.4 Result Adapter

职责：把 raw simulation artifact 转成项目已有结构。

```text
Raw ManiSkill/SAPIEN Artifact
-> SimulatorAdapterResult
-> ExperienceDataset
-> SkillDataset compatibility export
-> SimulationEvidenceBundle
```

该层是防腐层。ManiSkill/SAPIEN 私有格式不能进入项目核心对象；后续换 Gazebo/MoveIt、Isaac Lab、RoboDK 或真机数据时，也应通过 adapter 进入 canonical schema。

### 6.5 Minimal Dev Entrypoint

只新增一个短文档和一个脚本入口：

```text
docs/simulation/maniskill-sapien-dev-env.md
scripts/run_maniskill_spike.sh
```

短文档只说明：

1. 为什么使用独立 conda 环境。
2. 如何创建环境。
3. 如何运行脚本。
4. 输出在哪里。
5. 常见 failure boundary。
6. 当前不做事项。

不复制官方教程，不新增复杂文档目录。

## 7. 数据来源整体规划

当前阶段的数据来源是仿真，但整体项目不能把仿真写成唯一来源。后续数据来源应包括：

- 仿真数据。
- 专家审核和专家修正。
- 真机机器人执行日志。
- 焊机过程数据。
- 焊后检测和质量反馈。

因此经验数据结构必须携带 source、review、validation、quality feedback 和 evidence boundary 等信息，不能默认 `source_type=simulation` 是唯一来源。

## 8. 经验到机器人迁移占位

本阶段只完成前半段：

```text
仿真
-> 经验级数据集
-> evidence
```

但整体闭环还包括后半段：

```text
WeldSkillPackage
-> RobotExecutionSpec
-> RobotProcessPackage
-> robot program / path / posture / process parameter recommendation
-> execution validation
-> evidence feedback
```

`RobotExecutionSpec` 和 `RobotProcessPackage` 暂不在本阶段完整实现，但它们是整体规划成立的重要部分。后续应表达：

- 机器人型号。
- TCP。
- 坐标系。
- 路径。
- 姿态。
- 速度。
- 工艺参数建议。
- 约束。
- 可达性。
- 碰撞边界。
- 执行验证状态。

本阶段产出的经验数据必须为这条迁移路线保留足够严谨、通用的接口。

## 9. 错误处理

所有真实仿真失败都必须变成结构化 failure boundary。

第一版至少区分：

- `environment_missing`：conda 环境、包或系统依赖缺失。
- `simulator_api_changed`：ManiSkill/SAPIEN API 与预期不一致。
- `task_generation_failed`：`SimulationTaskSpec` 转 task config 失败。
- `demo_generation_failed`：rule-based demo 生成失败。
- `simulation_run_failed`：仿真执行失败。
- `artifact_missing`：预期输出文件不存在。
- `adapter_conversion_failed`：raw artifact 转标准结果失败。

failure boundary 应进入 artifact、adapter result 和 evidence，而不是只存在于日志中。

## 10. 测试策略

测试分两层。

### 10.1 uv 默认测试层

默认测试不依赖 ManiSkill/SAPIEN。

覆盖：

- task config 生成。
- demo artifact 结构。
- raw artifact 到 `SimulatorAdapterResult` 的转换。
- evidence/report 生成。
- 真实仿真依赖缺失时不会破坏默认测试。

默认验证仍保持：

```bash
cd weld-experience-engine
uv run pytest -q
```

### 10.2 conda 真实仿真层

真实仿真由脚本触发，不作为默认 pytest 的强依赖。

脚本应支持：

- 指定 task id 或运行两个默认任务。
- 指定 output dir。
- 选择轻量运行模式。
- 成功时输出真实 artifact。
- 失败时输出结构化 failure boundary。

## 11. Artifact 约定

建议输出路径先保持简单：

```text
artifacts/simulation/maniskill-sapien/
```

每次运行至少保存：

- task config JSON。
- demo trajectory JSON。
- raw simulation result JSON。
- adapter result JSON。
- 简短 run summary。

后续服务器批量运行时，可以在该结构上增加 run id、timestamp、task variant 和环境元数据。

## 12. 成功标准

本阶段完成时应满足：

1. 当前 `uv` 默认项目环境仍可测试通过。
2. 独立 conda 环境有一份短文档说明。
3. 有一个标准脚本入口可触发 ManiSkill/SAPIEN spike。
4. 两个默认 `WeldSkillUnit` 可以自动生成 task config。
5. 每个 task 可以生成一条 rule-based demo。
6. 独立 conda 环境必须在本机轻量 CPU/headless/state-based 模式下至少成功跑通两个默认任务，并输出真实 ManiSkill/SAPIEN artifact。
7. 两个默认任务都必须完成 config、demo、raw artifact、adapter result、经验级数据集、`SkillDataset` 兼容导出和 evidence。
8. failure boundary 必须覆盖环境缺失、API 变化、任务生成失败、demo 生成失败、仿真失败、artifact 缺失和 adapter 转换失败等失败路径，但 failure boundary 不能替代第 6-7 条成功路径。
9. 文档明确说明本阶段不代表最终仿真器选择、真实焊接质量验证或 WPS/PQR。

## 13. 后续决策门

本阶段完成后，再决定是否进入服务器批量化。

可进入服务器阶段的条件：

- 本机 pipeline 形状已经跑通。
- task config、demo、raw artifact 和 adapter result 边界稳定。
- failure boundary 足够清楚，能支持批量运行排错。
- 两个默认 ManiSkill/SAPIEN 任务都能产出可回写 evidence。

服务器阶段重点才是：

- Linux/GPU 环境。
- 批量任务生成。
- 小批量合成数据。
- 更多路径变体和姿态约束。
- 更完整机器人模型和场景。
- 更接近机器人执行迁移的验证。

## 14. 资料参考

这些资料只作为工具边界和生态能力参考，不作为项目完成证明：

- ManiSkill documentation: https://maniskill.readthedocs.io/
- ManiSkill tasks: https://maniskill.readthedocs.io/en/latest/tasks/index.html
- ManiSkill installation: https://maniskill.readthedocs.io/en/latest/user_guide/getting_started/installation.html
- SAPIEN robotics documentation: https://sapien-sim.github.io/docs/user_guide/robotics/basic_robot.html
- MoveIt motion planning concepts: https://moveit.picknik.ai/main/doc/concepts/motion_planning.html

## 15. 设计验证口径

检查本设计是否成立时，重点看：

- 是否降低人工搭任务、跑仿真、示教和整理结果的需求。
- 是否保留当前项目默认可运行状态。
- 是否避免 ManiSkill/SAPIEN 私有格式污染核心 schema。
- 是否只把本阶段终点定义为经验级数据集，而不是机器人可执行工艺包。
- 是否为后续专家审核、真机数据和机器人执行迁移留下清晰位置。
- 是否保持文档系统克制。
