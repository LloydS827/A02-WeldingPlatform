# weldcore — 焊接技能大师经验结构化引擎 (POC)

验证核心命门：大师焊接轨迹 → 结构化工艺参数(摆动模板/工作角/行进角/行进速度/层道) → 机器人可执行轨迹，且特征不丢。

闭环自证：合成理想轨迹 → 注入真实扰动 → decompose → recompose → 与已知 ground truth 比对。

## 运行

    pip install -e ".[dev,viz]"
    pytest -q
    python -m weldcore.report.generate   # 出图+数据表

## 当前 POC 能力

- `model/`：Trajectory、WeaveTemplate、GrooveGeometry、LayerPass、WeldProcess 工艺数据结构。
- `datagen/`：理想大师轨迹合成，以及手抖、漂移、无效停顿扰动注入。
- `decompose/`：中心线提取、摆幅/摆频检测、模板分类、姿态估计，输出结构化 WeldProcess。
- `recompose/`：结构化工艺参数重组为连续轨迹；缺少 scipy 时回退到正向合成轨迹。
- `metrics/`：往返 RMS、参数恢复误差、抗扰动失效边界。
- `report/`：生成 `report_out/roundtrip.png`、`robustness.png`、`evidence.json`、`robustness.csv`。

## 评测结论

最近一次 `python -m weldcore.report.generate` 的核心结果：

- 理想轨迹往返 RMS：0.1643 mm。
- 月牙、锯齿、梯形三类模板分类均正确。
- 摆幅误差首次超过 0.5 mm 阈值的手抖级别：0.5 mm。
- 摆频误差在当前扰动扫描范围内未越过 0.3 Hz 阈值。
