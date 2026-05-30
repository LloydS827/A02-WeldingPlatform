# weldcore — 焊接技能大师经验结构化引擎 (POC)

验证核心命门：大师焊接轨迹 → 结构化工艺参数(摆动模板/工作角/行进角/行进速度/层道) → 机器人可执行轨迹，且特征不丢。

闭环自证：合成理想轨迹 → 注入真实扰动 → decompose → recompose → 与已知 ground truth 比对。

## 运行
    pip install -e ".[dev,viz]"
    pytest -q
    python -m weldcore.report.generate   # 出图+数据表
