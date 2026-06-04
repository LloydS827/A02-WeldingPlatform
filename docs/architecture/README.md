# 架构总览

本目录描述 A02 焊接技能大师平台在 Physical AI 方向下的当前架构。

当前主线不是单一仿真器、机器人程序或报告命令，而是围绕 `WeldSkillPackage`
沉淀可学习、可迁移、可执行、可审计的焊接技能资产。

## 当前入口

- [五层系统架构](five-layer-system.md)
- [模块边界与 adapter 原则](module-boundaries.md)

## 核心判断

```text
工艺知识 / 动作经验 / 过程数据
-> SkillDataset
-> WeldSkillPackage
-> 机器人训练 / 类机器人仿真 / 执行基线
-> 评测、证据、边界
```
