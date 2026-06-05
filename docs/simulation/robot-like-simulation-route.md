# 类机器人仿真路线

本页保留 L0-L3 仿真成熟度层，并新增 R0-R3 候选路线角色层。L 层描述仿真能力成熟度，R 层描述候选工具在项目中的角色，二者不能混用。

## L0 几何与轨迹轻量仿真

用于稳定生成和测试几何、轨迹、姿态和 bundle 接入能力。当前 simlite/mock 输出属于这一层。

## L1 机器人运动学、可达性与碰撞仿真

用于评估机器人是否能在给定工位、姿态和路径约束下执行技能资产建议。下一阶段优先关注可达性、关节约束、碰撞和轨迹可执行性。

## L2 机器人任务学习与 demonstration 仿真

用于支持 demonstration、任务学习、策略评估和机器人大脑训练输入。该层依赖更清晰的 `WeldSkillUnit` 和 L1 执行边界。

## L3 焊接过程、热输入和质量物理仿真

用于更高成本的热输入、熔池、成形和质量相关物理分析。该层不是当前起点，也不能替代真实焊接质量验证。

## R0-R3 候选路线角色层

| 角色层 | 候选 | 项目定位 | 当前动作 |
| --- | --- | --- | --- |
| R0 稳定样板 | simlite/mock bundle | 默认测试和 bundle 接入 baseline | 保持稳定，不扩展成复杂仿真器 |
| R1 数据与证据回放 | Rerun | 时间轴记录、回放、标注和调试证据 | 做可选回放样板，不成为核心依赖 |
| R2 机器人学习与任务仿真 | ManiSkill、SAPIEN、Isaac Lab、Gazebo/MoveIt、MuJoCo、PyBullet | 技能数据生成、可执行性、训练与评测 | 下一轮最多选择 2 条路线做最小 bake-off |
| R3 工业落地对照 | RoboDK、ABB RobotStudio、Siemens Process Simulate | 离线编程、工位、机器人型号和虚拟调试对照 | 先调研，不进入第一轮代码实现 |

## 决策矩阵

评估顺序固定为：

```text
技能数据生成 -> 机器人可执行性 -> 训练机器人大脑 -> 工业落地对照
```

| 维度 | 权重 | 检查问题 |
| --- | ---: | --- |
| 技能数据生成 | 40% | 能否输出 `SkillDataset` / `WeldSkillPackage` 需要的轨迹、姿态、任务状态、评测和 evidence |
| 机器人可执行性 | 30% | 是否支持机器人模型、IK、碰撞、运动规划、姿态约束 |
| 训练机器人大脑 | 20% | 是否支持 demonstration、RL/IL、policy evaluation、benchmark |
| 工业落地对照 | 10% | 是否有离线编程、真实机器人生态、工位/夹具/部署参考 |

## 第一轮最小验证建议

第一条外部非 mock 仿真器最小闭环优先采用 ManiSkill/SAPIEN 本机轻量 CPU/headless/state-based 路线；其输出仍必须通过 adapter 回到项目 canonical schema，不代表最终仿真器选择。

- R1：用 Rerun 回放 simlite 或 `SimulationOutputBundle` 导入后的轨迹、姿态、任务状态和评测证据。
- R2：优先比较 ManiSkill/SAPIEN 方向和 Gazebo/MoveIt 方向。
- R3：只调研 API、路径导入导出、机器人品牌和虚拟调试约束，不写入核心 schema。

第一版实现应形成 `simulation_bakeoff_report`：同一组两个核心 `SimulationTaskSpec` 同时进入 R0/simlite、ManiSkill/SAPIEN 和 Gazebo/MoveIt 尝试；外部路线不可用时记录统一 failure boundary，而不是阻断默认测试。

## Adapter 评估口径

- adapter 是否能输出或转换为项目 canonical schema。
- adapter 是否能补强 `WeldSkillPackage` 的 trajectory、posture、applicability、failure boundary 或 robot execution suggestion。
- adapter 是否能围绕同一组 `WeldSkillUnit` 比较。
- adapter 是否保持证据边界，不把仿真输出直接写成真实质量结论。
