# WeldSkillUnit 驱动类机器人仿真路线准备 — 设计 Spec

日期：2026-06-04
版本：v0.1
适用项目：A02 焊接技能大师平台
阶段：项目级重构完成后，进入真正仿真接入前的路线准备

---

## 0. 结论先行

下一阶段不应直接选择或接入某个仿真器，而应先建立 **WeldSkillUnit 驱动的类机器人仿真路线决策框架**。

本阶段的核心问题是：

```text
我们要沉淀哪些焊接技能单元？
这些技能单元需要仿真系统提供哪些数据、执行约束、训练能力和证据？
哪些候选路线最适合作为后续最小验证实验？
```

因此，本阶段的主线是：

```text
WeldSkillUnit
-> 仿真需求与数据契约
-> 候选路线分层对比
-> 决策矩阵
-> 最小验证实验
-> 后续 implementation plan
```

当前明确不做：

- 不实现新的仿真器 adapter。
- 不选择唯一最终仿真器。
- 不接入熔池、热过程、冶金或高保真焊接物理仿真。
- 不声称仿真结果等于真实焊接质量验证。
- 不生成或替代 WPS/PQR。
- 不新增大量分散文档；本阶段先用一份 spec 承载路线设计，后续 implementation plan 再决定是否更新既有 current-route 文档。

---

## 1. 设计原则

### 1.1 技能资产先于工具选型

仿真器不是项目核心，`WeldSkillPackage` 才是核心对象。仿真路线必须服务技能资产沉淀，而不是反过来让某个工具决定项目结构。

本阶段先定义 `WeldSkillUnit`，再用它反推仿真系统需要提供的数据和评测能力。

### 1.2 只做类机器人仿真路线

当前仿真重点是：

- 轨迹、姿态、速度、工具中心点和任务状态。
- 机器人可达性、碰撞、连续性和运动规划约束。
- 可进入 `SkillDataset` / `WeldSkillPackage` 的数据输出。
- 可支撑 imitation learning、RL、policy evaluation 或 benchmark 的结构化记录。
- 可与 Rerun 这类记录/回放工具形成证据链。

当前排除：

- 熔池流体。
- 焊接热过程。
- 冶金组织变化。
- 熔深、成形和真实质量预测。
- 焊中闭环控制。

### 1.3 文档结构要克制

项目刚完成瘦身和重构，本阶段不能重新制造文档臃肿。

本阶段只新增这一份设计 spec。后续 implementation plan 如需落地，应优先更新既有文档：

- `docs/skill-assets/weld-skill-units.md`
- `docs/simulation/robot-like-simulation-route.md`
- `docs/evidence/README.md`
- `details.md`

除非确有独立长期价值，否则不新增新的路线文档、调研文档、矩阵文档或报告目录。

---

## 2. WeldSkillUnit 框架

`WeldSkillUnit` 是 `WeldSkillPackage` 之前的技能单元抽象，用来描述“一个可复用、可训练、可评测的焊接动作能力”。

它不是生产工艺卡，也不是 WPS/PQR。它是为了让仿真、数据、机器人执行和证据沉淀能够围绕同一个技能粒度协作。

### 2.1 三层结构

第一版采用三层结构：

```text
焊缝形态 / seam geometry
× 操作姿态 / welding position or robot posture
× 动作技能 / motion skill
```

其中：

- 焊缝形态回答“焊在哪里、几何形态是什么”。
- 操作姿态回答“以什么空间姿态和可达性约束执行”。
- 动作技能回答“机器人或焊枪需要稳定完成什么动作”。

### 2.2 第一版最小集合

第一批不铺开所有场景，先覆盖：

| 层级 | 第一批核心 | 复杂扩展 |
| --- | --- | --- |
| 焊缝形态 | 长直焊缝、包角 | U 型缝、多段转角、遮挡/狭窄可达性 |
| 操作姿态 | 横焊优先 | 立焊、仰焊、复杂机器人姿态切换 |
| 动作技能 | 枪姿保持、沿缝跟踪、速度稳定、转角过渡、起收弧边界 | 多层多道、避障、动态姿态重规划 |

第一版推荐的最小技能单元示例：

1. `long-straight-horizontal-tracking`
   - 长直焊缝 + 横焊/近横焊 + 沿缝跟踪与枪姿保持。
2. `corner-horizontal-transition`
   - 包角 + 横焊/近横焊 + 转角过渡与姿态连续性。
3. `u-seam-vertical-extension`
   - U 型缝 + 立焊 + 复杂扩展；仅作为后续验证储备，不作为第一批实现起点。

### 2.3 最小字段建议

后续如实现 `WeldSkillUnit` 数据结构，第一版字段应保持很小：

```text
unit_id
name
seam_geometry
welding_position
motion_skill
robot_constraints
required_sim_outputs
evaluation_metrics
evidence_requirements
out_of_scope
```

不要在第一版引入真实质量字段、熔池字段或焊接冶金字段。

---

## 3. 候选路线角色分层

候选路线不应放在同一层硬比，应按项目用途分层。这里使用 R0-R3 表示“路线角色层”，避免与现有 `docs/simulation/robot-like-simulation-route.md` 中的 L0-L3 仿真成熟度层混淆。后续更新既有 current-route 文档时，必须保持原 L0-L3 语义：L1 是机器人运动学/可达性/碰撞，L2 是任务学习，L3 是焊接过程/热输入/质量物理，且原 L3 仍不是当前起点。

### 3.1 R0：现有稳定样板层

**代表：simlite/mock bundle**

定位：

- 保持默认测试稳定。
- 生成最小可复现样本。
- 验证 `SimulationOutputBundle -> SkillDataset -> WeldSkillPackage` 的平台侧数据链。

边界：

- 不代表真实机器人执行。
- 不代表类机器人仿真路线已经完成。

### 3.2 R1：数据接入、回放与证据层

**代表：Rerun**

定位：

- 多模态时间轴记录。
- 轨迹、姿态、过程信号、仿真状态和评测结果的回放。
- 帮助检查仿真输出是否能形成可审计证据。

边界：

- Rerun 不是仿真器。
- Rerun 不是机器人控制总线。
- Rerun 应作为 `WeldSkillPackage.evidence` 的可视化和调试支撑层。

### 3.3 R2：机器人学习与任务仿真层

**候选：ManiSkill、SAPIEN、Isaac Lab、MuJoCo、Gazebo/MoveIt、PyBullet**

定位：

- 生成机器人任务数据。
- 支撑运动规划、可达性、碰撞、姿态约束和任务评测。
- 支撑 imitation learning、RL、policy evaluation 或 benchmark。

本层是后续最小验证实验的重点。

### 3.4 R3：工业离线编程与数字孪生对照层

**候选：RoboDK、ABB RobotStudio、Siemens Process Simulate**

定位：

- 离线编程。
- 工业机器人型号、工位、夹具、节拍和虚拟调试。
- 对照真实工程落地约束。

边界：

- 第一轮不作为实现对象。
- 第一轮用于校准工业落地要求，避免只停留在研究仿真语境。

---

## 4. 评估优先级与决策矩阵

路线评估优先级固定为：

```text
1. 技能数据生成
2. 机器人可执行性
3. 训练机器人大脑
4. 工业落地对照
```

建议权重：

| 维度 | 权重 | 说明 |
| --- | ---: | --- |
| 技能数据生成 | 40% | 是否能输出 `SkillDataset` / `WeldSkillPackage` 所需轨迹、姿态、任务状态、评测和 evidence |
| 机器人可执行性 | 30% | 是否支持机器人模型、可达性、碰撞、运动规划、姿态约束 |
| 训练机器人大脑 | 20% | 是否支持 demonstration、RL/IL、policy evaluation、benchmark |
| 工业落地对照 | 10% | 是否有离线编程、真实机器人生态、工位/夹具/部署对照价值 |

### 4.1 候选路线初步判断

| 路线 | 当前角色 | 优势 | 风险 / 缺口 | 第一轮验证方式 |
| --- | --- | --- | --- | --- |
| simlite | R0 稳定样板 | 已接入、测试稳定、可生成最小 bundle | 不是真实机器人仿真 | 保持 baseline，不扩展成复杂仿真器 |
| Rerun | R1 数据与证据回放 | 时间轴记录、可视化、多模态调试 | 不是仿真器，不做控制 | 回放 `SimulationOutputBundle`、轨迹、姿态、评测结果 |
| ManiSkill | R2 机器人学习/任务仿真 | 机器人任务、benchmark、RL/IL 语境强 | 焊接任务需自定义，工业机器人/焊接工位需适配 | 做长直焊缝 TCP 路径跟踪任务原型评估 |
| SAPIEN | R2 仿真底座 | 机器人仿真和物理环境能力强，可作为底层引擎 | 需要较多任务封装，不是现成焊接路线 | 评估是否适合自定义焊枪/工件/轨迹任务 |
| Isaac Lab | R2 机器人学习 | 面向机器人学习、RL/IL、GPU 仿真生态强 | 工程环境较重，接入成本高 | 桌面调研 + 最小机器人轨迹任务 feasibility |
| Gazebo/MoveIt | R2 机器人执行/规划 | ROS 生态、运动规划、可达性、碰撞、机器人模型 | 学习数据生成和 benchmark 能力不如专门学习平台直接 | 评估焊枪 TCP 轨迹、IK、碰撞和姿态约束 |
| MuJoCo / PyBullet | R2 轻量物理/控制 | 轻量、研究生态广、适合控制实验 | 工业机器人与焊接任务语义需自建 | 作为备选，不优先实现 |
| RoboDK | R3 工业对照 | 离线编程、机器人品牌和路径仿真价值 | 商业工具，不宜成为核心 schema | 调研 API 和路径导入/导出能力 |
| RobotStudio | R3 工业对照 | ABB 机器人离线编程和虚拟调试 | 强绑定 ABB 生态 | 调研真实部署约束 |
| Process Simulate | R3 工业对照 | 工厂/产线级机器人仿真和虚拟调试 | 工程复杂，商业工具 | 调研产线数字孪生约束 |

---

## 5. 最小验证实验

后续 implementation plan 不应一次性接入所有候选路线。建议定义三个最小实验。

### 5.1 实验 A：WeldSkillUnit 数据契约

目标：

- 在文档或最小数据结构中定义 `WeldSkillUnit`。
- 先覆盖 `long-straight-horizontal-tracking` 和 `corner-horizontal-transition`。
- 明确每个技能单元需要哪些仿真输出和评测指标。

验收：

- 能解释一个 `WeldSkillUnit` 如何进入 `SkillDataset` 和 `WeldSkillPackage`。
- 不引入熔池/热过程/真实质量字段。
- 不破坏现有测试。

### 5.2 实验 B：Rerun 证据回放样板

目标：

- 复用现有 simlite 或 `SimulationOutputBundle`。
- 将轨迹、姿态、任务状态、评测结果组织成可回放证据。
- 验证 Rerun 在数据接入层的价值。

验收：

- 核心模型不依赖 Rerun SDK 类型。
- 未安装 Rerun 时基础测试仍通过。
- 能说明回放结果如何关联到 `WeldSkillPackage.evidence`。

### 5.3 实验 C：R2 候选路线最小 bake-off

目标：

- 对 2 个以内 R2 候选路线做最小验证，不同时铺开全部工具。
- 推荐优先比较：
  - ManiSkill / SAPIEN 方向：技能数据生成和机器人学习语境。
  - Gazebo/MoveIt 方向：机器人可执行性、IK、碰撞、姿态约束。

验收：

- 每条路线都用同一组 `WeldSkillUnit` 和同一套输出契约比较。
- 输出不是“哪个工具更有名”，而是“哪个更适合当前技能资产路线”。
- 工业工具只作为 R3 对照调研，不进入第一轮代码实现。

---

## 6. 资料依据

本 spec 只引用官方文档、项目主页或工具方资料作为路线判断依据。后续 implementation plan 如需更深入，应新增“资料审计任务”，而不是在当前 spec 中堆长篇调研。

- ManiSkill：机器人仿真、benchmark、RL/IL 任务生态。参考 [ManiSkill](https://www.maniskill.ai/) 与 [ManiSkill Documentation](https://maniskill.readthedocs.io/en/latest/)。
- SAPIEN：机器人和物理环境仿真底座。参考 [SAPIEN Documentation](https://sapien-sim.github.io/docs/)。
- Isaac Lab：面向机器人学习的 Isaac Sim 应用框架。参考 [NVIDIA Isaac Lab](https://developer.nvidia.com/isaac/lab)。
- Gazebo / MoveIt：机器人仿真、ROS 生态、运动规划和可达性/碰撞约束。参考 [Gazebo](https://gazebosim.org/docs/) 与 [MoveIt](https://moveit.ai/)。
- MuJoCo：机器人、控制和强化学习常用物理仿真。参考 [MuJoCo Documentation](https://mujoco.readthedocs.io/)。
- Rerun：多模态数据记录、时间轴、回放和可视化。参考 [Rerun Documentation](https://docs.rerun.io/)。
- RoboDK：工业机器人仿真、离线编程和 API。参考 [RoboDK Documentation](https://robodk.com/doc/en/)。
- ABB RobotStudio：ABB 机器人离线编程和虚拟调试。参考 [ABB RobotStudio](https://www.abb.com/global/en/areas/robotics/products/software/robotstudio-suite/robotstudio-desktop)。
- Siemens Process Simulate：产线/机器人虚拟调试与数字孪生对照。参考 [Siemens robotics virtual commissioning](https://www.siemens.com/en-gb/technology/robotics-virtual-commissioning/)。

---

## 7. 后续计划边界

下一步 writing-plans 应围绕以下内容生成实施计划：

1. 更新既有 current-route 文档，而不是新增多个并列文档。
2. 如需代码，只新增最小 `WeldSkillUnit` 边界或 facade，并使用 TDD。
3. 建立候选路线决策矩阵的可维护版本。
4. 定义 Rerun 数据接入/回放样板，但保持 SDK 可选。
5. 定义 R2 候选路线 bake-off 的最小实验，不安装或接入全部工具。
6. 保持默认验证命令通过。

本 spec 完成的是路线准备设计，不完成仿真器选型、不完成仿真器接入、不完成真实焊接质量验证。
