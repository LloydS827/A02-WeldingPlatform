# ManiSkill/SAPIEN Dev Environment

This page records the minimal local environment for the first real simulator loop.
It is not a general ManiSkill tutorial and does not make ManiSkill/SAPIEN a core project dependency.

## Why Conda

The default `uv` project environment stays light and testable. ManiSkill/SAPIEN runs in an independent conda environment so simulator dependencies do not break the default workflow.

## Minimal Setup

```bash
conda create -n weld-maniskill python=3.10 -y
conda activate weld-maniskill
pip install -e ./weld-experience-engine
pip install mani-skill sapien
```

If the package names or platform support change, follow the official ManiSkill/SAPIEN installation docs and keep this page short.

## Run

```bash
./scripts/run_maniskill_spike.sh
```

Default output:

```text
artifacts/simulation/maniskill-sapien/
```

## Expected Outputs

- `task_config.json`
- `demo.json`
- `raw_artifact.json`
- `adapter_result.json`
- `experience_dataset.json`
- `evidence_bundle.json`
- `run_summary.json`

## Failure Boundaries

- `environment_missing`
- `simulator_api_changed`
- `task_generation_failed`
- `demo_generation_failed`
- `simulation_run_failed`
- `artifact_missing`
- `adapter_conversion_failed`

## Current Boundaries

- Not final simulator selection.
- Not robot executable process package.
- Not real welding quality validation.
- Not WPS/PQR.
- Not GPU batch generation or RL training.
