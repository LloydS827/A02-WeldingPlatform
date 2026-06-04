# 类机器人仿真路线

## L0 几何与轨迹轻量仿真

用于稳定生成和测试几何、轨迹、姿态和 bundle 接入能力。当前 simlite/mock 输出属于这一层。

## L1 机器人运动学、可达性与碰撞仿真

用于评估机器人是否能在给定工位、姿态和路径约束下执行技能资产建议。下一阶段优先关注可达性、关节约束、碰撞和轨迹可执行性。

## L2 机器人任务学习与 demonstration 仿真

用于支持 demonstration、任务学习、策略评估和机器人大脑训练输入。该层依赖更清晰的技能单元和 L1 执行边界。

## L3 焊接过程、热输入和质量物理仿真

用于更高成本的热输入、熔池、成形和质量相关物理分析。该层不是当前起点，也不能替代真实焊接质量验证。

## Adapter 评估口径

- adapter 是否能输出或转换为项目 canonical schema。
- adapter 是否能补强 `WeldSkillPackage` 的 trajectory、posture、applicability、failure boundary 或 robot execution suggestion。
- adapter 是否保持证据边界，不把仿真输出直接写成真实质量结论。
