# 仿真路线

本目录描述 A02 从 `ManipulationSkillAsset` 出发的仿真、数字孪生和训练闭环路线。

当前判断已经从“多个候选仿真器长期平行 bake-off”调整为：**OpenUSD / Isaac Sim / Isaac Lab 是未来真实仿真训练闭环的主底座**。A02 不重复造通用物理引擎、3D 场景标准、机器人仿真器或训练框架；A02 负责焊接技能资产、工艺知识、证据治理、专家审查和 A01/IP handoff。

- L0 simlite 仍是稳定测试工具。
- OpenUSD 是未来数字孪生交换层。
- Isaac Sim 是未来默认目标仿真运行时。
- Isaac Lab 是未来策略训练闭环目标层。
- Cosmos、Nucleus、Isaac ROS/Jetson 属于后续增强、协同或部署层，不进入当前默认路径。

这个路线选择不表示当前已经完成 Isaac Sim 集成、OpenUSD stage authoring、Isaac Lab 训练或真实机器人执行验证。

## 当前入口

- [类机器人仿真路线](robot-like-simulation-route.md)
- [ManiSkill/SAPIEN 本机轻量环境](maniskill-sapien-dev-env.md)
