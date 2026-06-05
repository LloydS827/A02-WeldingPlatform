# WeldSkillUnit 仿真最小验证与数字资产沉淀设计

## 1. 背景

项目已经完成第一轮瘦身、`WeldSkillUnit` 最小边界、R0-R3 路线角色层和 Rerun 证据回放边界。下一步不应继续停留在路线文档对比，也不应直接宣布最终仿真器，而应进入第一轮最小仿真验证。

本阶段目标是把仿真真正跑起来，并让仿真输出沉淀为项目可复用、可审计、可回放的数字资产。

关键判断：

- 仿真不是最终目的，数字资产才是本阶段的交付物。
- 第一轮验证应围绕 `WeldSkillUnit`，而不是围绕某个工具的演示能力。
- 第一轮不做熔池、热过程、冶金或真实成形预测。
- 第一轮不选择最终仿真器，只做最小 bake-off，判断哪条路线最适合进入下一轮 adapter 实现。

## 2. 总体目标

建立一条最小闭环：

```text
WeldSkillUnit
-> SimulationTaskSpec
-> SimulatorAdapter candidate
-> SimulatorAdapterResult
-> SimulationRunRecord / SimulationOutputBundle / SkillDataset
-> WeldSkillPackage evidence
-> Rerun replay
-> bake-off decision
```

这条链路要回答：

1. 焊接技能单元能否被翻译为机器人仿真任务。
2. 候选仿真路线能否输出项目需要的轨迹、姿态、状态、失败证据和评测指标。
3. 仿真结果能否回写为 `SkillDataset` / `WeldSkillPackage` 相关数字资产。
4. Rerun 能否把仿真过程和结果变成可阅读、可审计、可复盘的证据。

## 3. 第一轮技能单元范围

第一轮只验证两个核心单元：

| unit_id | 角色 | 验证重点 |
| --- | --- | --- |
| `long-straight-horizontal-tracking` | 第一批核心 | TCP 沿长直焊缝连续运动、枪姿稳定、速度稳定 |
| `corner-horizontal-transition` | 第一批核心 | 转角过渡、姿态连续、起收弧边界、速度/路径连续 |

`u-seam-vertical-extension` 暂不进入第一轮实现。它保留为后续复杂扩展，用于第二轮或第三轮验证复杂路径、立焊姿态和可达性挑战。

## 4. 第一轮候选路线

### 4.1 主验证线：ManiSkill / SAPIEN

项目定位：

- 快速构建机器人任务和仿真环境。
- 验证技能数据生成、任务状态、轨迹输出和后续机器人学习潜力。
- 更贴近项目长期目标中的机器人大脑训练输入。

第一轮只要求：

- 能表达简化焊缝路径和 TCP 运动目标。
- 能输出轨迹、姿态、任务状态、失败原因或评测指标。
- 能转换为项目 canonical schema。

不要求：

- 真实焊接过程物理。
- 完整工业机器人品牌工位。
- 大规模 RL 训练。

### 4.2 对照验证线：Gazebo / MoveIt

项目定位：

- 验证机器人可达性、IK、运动规划、碰撞和姿态约束。
- 更贴近后续真实机器人执行链路。
- 作为 ROS/工业执行生态的对照路线。

第一轮只要求：

- 能表达同一组 `WeldSkillUnit` 对应的目标路径。
- 能检查机器人模型是否可达、是否有明显碰撞或关节异常。
- 能输出规划结果或失败边界，并回写项目 schema。

不要求：

- 完整生产工位。
- 真实焊机控制。
- 工业 PLC/现场总线接入。

### 4.3 暂缓路线：Isaac Lab

Isaac Lab 保留为第二轮候选。它适合大规模机器人学习、GPU 加速仿真和更复杂的训练工作流，但第一轮引入会提高工程复杂度，容易让 bake-off 变成平台搭建任务。

第一轮只做资料审计，不写入核心依赖，不实现 adapter。

### 4.4 工业对照：RoboDK / RobotStudio / Process Simulate

这些工具保留为 R3 工业落地对照。第一轮只调研：

- 路径导入导出能力。
- 机器人品牌/型号覆盖。
- 离线编程和虚拟调试约束。
- 是否能作为后续工业验证或客户沟通参照。

第一轮不把它们写入核心 schema，不实现代码 adapter。

## 5. 数字资产对象

第一轮需要新增或明确以下概念边界。

### 5.1 SimulationTaskSpec

`SimulationTaskSpec` 是从 `WeldSkillUnit` 派生出的仿真任务说明。

最小字段：

- `task_id`
- `unit_id`
- `seam_path`
- `tcp_frame`
- `tool_orientation_constraint`
- `motion_constraint`
- `robot_constraint`
- `expected_outputs`
- `evaluation_metrics`
- `out_of_scope`

它不包含真实焊接质量、熔池、热过程或冶金字段。

### 5.2 SimulatorAdapterResult

`SimulatorAdapterResult` 是候选仿真路线的统一输出边界。

最小字段：

- `adapter_name`
- `task_id`
- `status`
- `tcp_trajectory`
- `tool_orientation`
- `planning_result`
- `failure_boundary`
- `metrics`
- `artifacts`
- `evidence_notes`

它用于隔离工具差异，避免项目核心对象被某个仿真器格式绑死。

### 5.3 SimulationEvidenceBundle

`SimulationEvidenceBundle` 是可审计证据包。

最小内容：

- `SimulationTaskSpec`
- `SimulatorAdapterResult`
- 转换后的 `SkillDataset`
- 可选 `WeldSkillPackage` evidence 引用
- Rerun 回放入口或记录路径
- bake-off 评分摘要

### 5.4 与既有仿真接入对象的关系

本阶段不另起一套仿真 schema。新增对象只承担 bake-off 边界和证据聚合职责。

- `SimulationTaskSpec` 是 `WeldSkillUnit` 到仿真任务的输入说明，不替代 `WeldSkillUnit`。
- `SimulatorAdapterResult` 是不同候选工具输出的归一化中间结果。它必须能生成或引用既有 `SimulationRunRecord`、`SimulationBundleManifest` 或 `SimulationOutputBundle`，不能绕过现有仿真输出接入 gate。
- `SimulationEvidenceBundle` 是证据聚合，不是新的核心资产对象。它应引用 `SimulationTaskSpec`、`SimulatorAdapterResult`、既有 run record/bundle manifest、转换后的 `SkillDataset` 和可选 `WeldSkillPackage` evidence。
- 数字资产主链仍然是 `SkillDataset -> WeldSkillPackage -> evidence`。bake-off 产生的新对象只服务仿真选型和证据审计。

## 6. 评价指标

第一轮评价指标固定为：

| 维度 | 权重 | 指标 |
| --- | ---: | --- |
| 数字资产回写能力 | 35% | 是否能生成 `SkillDataset` / evidence / Rerun replay |
| 机器人可执行性 | 30% | IK、可达性、碰撞、关节边界、姿态约束 |
| 技能单元表达能力 | 20% | 是否能表达长直跟踪和转角过渡两个 `WeldSkillUnit` |
| 工程接入成本 | 15% | 依赖复杂度、运行门槛、测试可自动化程度 |

通过条件：

- 两条候选路线都必须尝试同一组两个 `SimulationTaskSpec`，即长直横焊沿缝跟踪和包角横焊转角过渡。
- 候选路线可以失败，但失败也必须输出统一的 `failure_boundary`、`metrics` 或 evidence notes，才能进入评分。
- 至少一条路线能完整生成 `SimulationEvidenceBundle`。
- Rerun 能回放轨迹、姿态、任务状态或失败边界；但 Rerun replay 是可选证据导出样板，不得让核心模型、默认测试或基础报告命令依赖 `rerun-sdk`。
- 输出不能停留在工具私有格式，必须能回到项目 schema。

## 7. 推荐执行顺序

第一轮按以下顺序执行：

1. 定义 `SimulationTaskSpec` 和 `SimulatorAdapterResult` 的最小数据结构。
2. 从两个核心 `WeldSkillUnit` 生成两个 `SimulationTaskSpec`。
3. 先用 R0/simlite 生成 reference evidence，作为稳定 baseline。
4. 做 ManiSkill/SAPIEN 最小 spike，验证技能数据生成能力。
5. 做 Gazebo/MoveIt 最小 spike，验证机器人执行约束能力。
6. 把两条路线输出都转换为统一 `SimulationEvidenceBundle`。
7. 用 Rerun 回放 evidence。
8. 形成 bake-off 结论：选出下一轮 adapter 实现主路线和保留路线。

## 8. 不做事项

本阶段明确不做：

- 不选择最终仿真器。
- 不实现完整外部 simulator adapter。
- 不做大规模机器人学习训练。
- 不做真实焊接质量验证。
- 不生成或替代 WPS/PQR。
- 不做熔池、热过程、冶金或真实成形预测。
- 不接入真实机器人、焊机、PLC 或现场总线。
- 不把 Rerun 写成仿真器、控制总线或生产数据库。

## 9. 成功交付物

本阶段完成后应产生：

1. `SimulationTaskSpec` 最小模型和两个默认任务。
2. 至少一个 R0 baseline evidence bundle。
3. ManiSkill/SAPIEN 最小验证结果。
4. Gazebo/MoveIt 最小验证结果或明确失败边界。
5. Rerun evidence replay 样板；未安装 `rerun-sdk` 时，基础测试和默认报告命令仍必须可运行。
6. bake-off 评分表。
7. 下一轮 adapter 主路线建议。

## 10. 后续决策门

bake-off 结束后按以下规则决策：

- 如果 ManiSkill/SAPIEN 在数字资产回写和任务表达上明显更快，则它进入第一版 adapter 实现主线。
- 如果 Gazebo/MoveIt 在可达性、IK、碰撞和工业执行约束上明显更可靠，则它进入第一版 adapter 实现主线。
- 如果两者各有优势，则第一版主线选择 ManiSkill/SAPIEN，Gazebo/MoveIt 保留为执行可达性校验侧线。
- 如果两条路线都无法低成本回写项目 schema，则回退到 R0/simlite 扩展 reference task，同时重新定义 adapter 边界。

## 11. 资料参考

本设计只把外部工具作为候选路线和边界判断依据，不把官方资料写成项目完成证明。

- ManiSkill: https://www.maniskill.ai/
- SAPIEN: https://sapien.ucsd.edu/
- Isaac Lab: https://isaac-sim.github.io/IsaacLab/
- Gazebo: https://gazebosim.org/docs/
- MoveIt: https://moveit.picknik.ai/
- Rerun: https://rerun.io/docs
- RoboDK: https://robodk.com/doc/en/Basic-Guide.html

## 12. 验证方式

本 spec 自身的验证方式：

- 检查是否只定义第一轮 bake-off，不宣称最终仿真器已选择。
- 检查是否保留 Rerun 证据层边界。
- 检查是否排除熔池、热过程、冶金、真实质量验证和 WPS/PQR。
- 检查是否把仿真结果定义为可回写、可审计、可回放的数字资产。
