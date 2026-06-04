# 焊接技能单元

本页记录第一版 `WeldSkillUnit` 框架，用于后续资料补强、类机器人仿真任务拆分和 `WeldSkillPackage` 组织。

`WeldSkillUnit` 不是生产工艺卡，也不是 WPS/PQR。它描述的是一个可复用、可训练、可评测的焊接动作能力。

## 三层结构

```text
焊缝形态 / seam geometry
× 操作姿态 / welding position or robot posture
× 动作技能 / motion skill
```

## 第一版技能单元候选

| unit_id | 焊缝形态 | 操作姿态 | 动作技能 | 当前角色 |
| --- | --- | --- | --- | --- |
| `long-straight-horizontal-tracking` | 长直焊缝 | 横焊/近横焊 | 沿缝跟踪、枪姿保持、速度稳定 | 第一批核心 |
| `corner-horizontal-transition` | 包角/转角 | 横焊/近横焊 | 转角过渡、姿态连续、起收弧边界 | 第一批核心 |
| `u-seam-vertical-extension` | U 型缝 | 立焊 | U 型路径、复杂姿态、可达性扩展 | 后续复杂扩展 |

## 最小字段

第一版只需要：

- `unit_id`
- `name`
- `seam_geometry`
- `welding_position`
- `motion_skill`
- `robot_constraints`
- `required_sim_outputs`
- `evaluation_metrics`
- `evidence_requirements`
- `out_of_scope`

## 仿真需求

第一批核心技能单元需要类机器人仿真优先回答：

- 焊枪 TCP 是否能沿目标路径连续运动。
- 姿态是否能在横焊/近横焊约束下保持稳定。
- 转角处是否出现速度、姿态或路径不连续。
- 机器人约束是否导致不可达、碰撞或关节异常。
- 输出是否能进入 `SkillDataset` 和 `WeldSkillPackage`。

## 当前不做事项

- 不把 `WeldSkillUnit` 写成真实焊接质量结论。
- 不加入熔池、热过程、冶金或真实成形预测字段。
- 不替代 WPS/PQR。
- 不把 `u-seam-vertical-extension` 作为第一批实现起点。
