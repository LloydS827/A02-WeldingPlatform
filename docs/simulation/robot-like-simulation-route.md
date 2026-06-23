# 类机器人仿真路线

本页保留 L0-L3 仿真成熟度层，并更新 R0-R4 路线角色层。L 层描述仿真能力成熟度，R 层描述工具在项目中的角色，二者不能混用。

2026-06-23 路线判断：A02 未来真实仿真训练闭环的重底座优先采用 OpenUSD / Isaac Sim / Isaac Lab。其他仿真器和机器人框架可以继续作为轻量测试、历史支撑、对照 adapter 或反证来源，但不再作为同等长期默认候选。

## L0 几何与轨迹轻量仿真

用于稳定生成和测试几何、轨迹、姿态和 bundle 接入能力。当前 simlite/mock 输出属于这一层。

## L1 机器人运动学、可达性与碰撞仿真

用于评估机器人是否能在给定工位、姿态和路径约束下执行技能资产建议。下一阶段先把 `RobotBodyAsset`、`RobotContextSpec`、`SceneContextAsset` 和 `ManipulationSkillAsset.motion` 编译成 OpenUSD/Isaac-oriented manifest，再进入真实 Isaac Sim replay 或 collision validation。

## L2 机器人任务学习与 demonstration 仿真

用于支持 demonstration、任务学习、策略评估和机器人大脑训练输入。该层未来优先落到 Isaac Lab，当前只设计 observation、action、reward、randomization、dataset 和 expert gate 合同。

## L3 焊接过程、热输入和质量物理仿真

用于更高成本的热输入、熔池、成形和质量相关物理分析。该层不是当前起点，也不能替代真实焊接质量验证。

## R0-R4 路线角色层

| 角色层 | 候选 | 项目定位 | 当前动作 |
| --- | --- | --- | --- |
| R0 稳定样板 | simlite/mock bundle | 默认测试和 bundle 接入 baseline | 保持稳定，不扩展成复杂仿真器 |
| R1 数据与证据回放 | Rerun | 时间轴记录、回放、标注和调试证据 | 做可选回放样板，不成为核心依赖 |
| R2 NVIDIA-native 数字孪生底座 | OpenUSD、Isaac Sim、Isaac Lab | 未来主交换层、目标仿真运行时和训练闭环目标层 | 下一轮 NV01 生成数字孪生包、OpenUSD manifest、Isaac replay config、randomization recipe 和 training readiness report |
| R3 对照 adapter / 反证来源 | ManiSkill、SAPIEN、Gazebo/MoveIt、MuJoCo、PyBullet | 历史支撑、轻量对照、失败边界反证 | 不再作为同等默认主线；必要时通过同一 canonical schema 接入 |
| R4 工业落地对照 | RoboDK、ABB RobotStudio、Siemens Process Simulate | 离线编程、真实机器人品牌、虚拟调试和产线工具链对照 | 先调研，不进入 NV01 代码实现 |

## 决策矩阵

评估顺序固定为：

```text
技能资产证据 -> OpenUSD 世界模型 -> Isaac Sim replay / synthetic data -> Isaac Lab 训练设计 -> 工业落地对照
```

| 维度 | 权重 | 检查问题 |
| --- | ---: | --- |
| 技能资产证据可追溯 | 30% | 能否从 `ManipulationSkillAsset`、`SimulationEvidenceBundle`、`RobotContextSpec`、`SceneContextAsset` 和 `ExpertReviewRecord` 追溯到每个输出 |
| OpenUSD 世界模型表达 | 25% | 是否能表达 robot、workpiece、fixture、seam、sensor、frames、semantic labels 和 evidence binding |
| Isaac Sim replay / synthetic data 准备度 | 25% | 是否能描述 robot import、trajectory replay、sensor simulation、Replicator dataset 和 validation checks |
| Isaac Lab 训练设计准备度 | 15% | 是否能描述 observation、action、reward、termination、curriculum、dataset 和 expert gate |
| 工业落地对照 | 5% | 是否能保留离线编程、真实机器人生态、工位/夹具/部署参考 |

## 下一轮最小验证建议

下一轮采用 **NV01 NVIDIA-Native Weld Skill Digital Twin Foundation**。第一版不直接运行 Isaac Sim，而是把现有 Demo Evidence Pack 编译为 NVIDIA physical AI 工作流可消费的 manifest/report。

第一轮应输出：

- `WeldSkillDigitalTwinPackage`
- `openusd_scene_manifest`
- `isaac_sim_replay_config`
- `domain_randomization_recipe`
- `training_readiness_report`
- `nvidia_stack_alignment_matrix`

默认状态应是 `ready_for_simulation_replay_package_design` 和 `not_ready_for_policy_training`。这表示 A02 已能形成进入 Isaac Sim/Isaac Lab 的输入合同，不表示已完成 Isaac Sim runtime 验证。

## Adapter 评估口径

- adapter 是否能输出或转换为项目 canonical schema。
- adapter 是否能补强 `ManipulationSkillAsset` 的 trajectory、posture、context requirement、failure boundary、simulation readiness 或 training readiness。
- adapter 是否能围绕同一组 demo task 和 canonical artifact 比较。
- adapter 是否保持证据边界，不把仿真输出直接写成真实质量结论。
- NVIDIA adapter 不能替代 `ManipulationSkillAsset`；OpenUSD/Isaac artifact 必须能追溯到 A02 canonical evidence。
