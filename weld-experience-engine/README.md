# weldcore — 焊接技能大师经验结构化引擎 (POC)

验证核心命门：大师焊接轨迹 → 结构化工艺参数(摆动模板/工作角/行进角/行进速度/层道) → 机器人可执行轨迹，且特征不丢。

闭环自证：合成理想轨迹 → 注入真实扰动 → decompose → recompose → 与已知 ground truth 比对。

## 运行

    uv sync --extra dev --extra viz
    uv run pytest -q
    uv run python -m weldcore.report.generate   # 出图+数据表
    uv run python -m weldcore.report.mvp_report # 技能迁移 MVP 证据包
    uv run python -m weldcore.report.scenario_report # 船舶场景资料底座与候选任务证据
    uv run python -m weldcore.report.data_foundation_report # 数据集与资料底座证据

如果本机尚未安装 `uv`，先参考 Astral 官方安装方式安装；临时备用方式仍可使用 `pip install -e ".[dev,viz]"`。

## 当前 POC 能力

- `model/`：Trajectory、WeaveTemplate、GrooveGeometry、LayerPass、WeldProcess 工艺数据结构。
- `datagen/`：理想大师轨迹合成，以及手抖、漂移、无效停顿扰动注入。
- `decompose/`：中心线提取、摆幅/摆频检测、模板分类、姿态估计，输出结构化 WeldProcess。
- `recompose/`：结构化工艺参数重组为连续轨迹；缺少 scipy 时回退到正向合成轨迹。
- `metrics/`：往返 RMS、参数恢复误差、抗扰动失效边界。
- `report/`：生成 `report_out/roundtrip.png`、`robustness.png`、`evidence.json`、`robustness.csv`。
- `sim/` + `transfer/`：轻量仿真样本、WeldSkillPackage 生成、条件迁移、迁移评测。
- `knowledge/`：公开资料来源、船舶焊接任务族、候选仿真场景和三层 gate。
- `viz/rerun_bridge.py`：可选 Rerun 回放边界；未安装 `rerun-sdk` 时不会影响测试。

## 技能迁移 MVP

`python -m weldcore.report.mvp_report` 会生成 `mvp_report_out/evidence.json`、`metrics.csv`、`transfer_summary.png`、`ip_notes.md`，用于证明从仿真样本到技能包、再到目标焊接条件迁移评测的最小闭环。

MVP 阶段的边界是：先验证结构化技能迁移机制，不把结果夸大为真实焊接质量结论。ManiSkill 仅作为机器人任务与 demonstration 数据范式的可选 adapter 方向，真机数据后续通过同一套 `SkillDataset` 接入。

`scenario_report` 用于生成公开资料来源、船舶焊接任务族、候选仿真场景和字段覆盖证据；它是 `SyntheticSkillDataset v2` 之前的知识闸门，不生成真机结论，也不纳入熔池路线。

默认输出目录为 `scenario_report_out/`，包含 `sources.json`、`task_families.json`、`scenarios.json`、`field_coverage.csv` 和 `evidence.md`。

`data_foundation_report` 用于生成资料来源、公开数据集、字段覆盖矩阵、任务证据映射和 `SyntheticSkillDataset v2` 计划输入。默认运行时输出目录为 `data_foundation_report_out/`，并刷新根目录 `docs/data-foundation/reports/` 下的中文报告；它完成的是资料底座 gate，不下载大文件，不生成批量仿真数据，不代表真实焊接质量验证，也不包含熔池路线。

## 评测结论

最近一次 `python -m weldcore.report.generate` 的核心结果：

- 理想轨迹往返 RMS：0.1643 mm。
- 月牙、锯齿、梯形三类模板分类均正确。
- 摆幅误差首次超过 0.5 mm 阈值的手抖级别：0.5 mm。
- 摆频误差在当前扰动扫描范围内未越过 0.3 Hz 阈值。
