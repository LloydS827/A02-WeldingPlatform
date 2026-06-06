# ManiSkill/SAPIEN 开发环境

本页记录第一条外部非 mock 仿真器最小闭环所需的本机轻量环境。
它不是通用 ManiSkill 教程，也不把 ManiSkill/SAPIEN 变成项目核心依赖。

## 为什么使用 Conda

默认 `uv` 项目环境保持轻量、可测试。ManiSkill/SAPIEN 放在独立 conda 环境中运行，避免仿真器依赖破坏默认工作流。

## 最小设置

```bash
conda create -n weld-maniskill python=3.10 -y
conda activate weld-maniskill
pip install -e ./weld-experience-engine
pip install mani-skill sapien
```

如果包名或平台支持发生变化，以官方 ManiSkill/SAPIEN 安装文档为准，并保持本页简短。

## 运行

```bash
./scripts/run_maniskill_spike.sh
```

默认输出目录：

```text
artifacts/simulation/maniskill-sapien/
```

## 预期输出

根输出：

- `run_summary.json`

每个 task 子目录输出：

- `task_config.json`
- `demo.json`
- `raw_artifact.json`
- `adapter_result.json`
- `experience_dataset.json`
- `evidence_bundle.json`

## 失败边界

- `environment_missing`
- `simulator_api_changed`
- `task_generation_failed`
- `demo_generation_failed`
- `simulation_run_failed`
- `artifact_missing`
- `adapter_conversion_failed`

## 当前边界

- 不是最终仿真器选择。
- 不是机器人可执行工艺包。
- 不做真实焊接质量验证。
- 不是 WPS/PQR。
- 不是 GPU 批量生成或 RL 训练。
